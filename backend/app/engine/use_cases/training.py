"""
Use Case : Formation / Développement individuel
Dimensions actives : P-J uniquement (gap D-A + motivation)
Pas de safety barrier, pas de centile, pas de contexte équipe
Output : gap analysis par trait + plan de développement priorisé

Compare le profil actuel du candidat aux scores idéaux SME par poste.
Identifie les traits prioritaires à développer et les points forts.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.use_cases._base import (
    ConfidenceLevel,
    _confidence_from_quality,
)
from app.engine.pe_fit.pj_fit.profiles import get_ideal_profile, CATEGORY_MAPPING
from app.engine.pe_fit.pj_fit.motivation_fit import scorer as _mfit
from app.engine.pe_fit.trait_extractor import extract_strict


# ── Seuils de priorité ────────────────────────────────────────────────────────

_HIGH_GAP_THRESHOLD   = 25.0
_MEDIUM_GAP_THRESHOLD = 10.0

# Seuils readiness
_READY_THRESHOLD      = 80.0
_DEVELOPING_THRESHOLD = 60.0


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class TraitGap:
    trait: str
    current_score: float
    ideal_score: float
    gap: float              # ideal - current (positif = sous le niveau)
    priority: str           # "HIGH" | "MEDIUM" | "LOW"
    category: str           # "cognitive" | "personality" | "motivation"


@dataclass
class TrainingResult:
    current_position: str
    target_position: str
    overall_readiness: float        # % de fit actuel vs idéal (0-100)
    readiness_label: str            # "READY" | "DEVELOPING" | "GAP"
    trait_gaps: List[TraitGap]      # trié par priority desc, gap desc
    top_priorities: List[str]       # top 3 traits à développer
    strengths: List[str]            # top 3 traits au-dessus de l'idéal
    motivation_gaps: List           # gaps SDT si données disponibles
    confidence: ConfidenceLevel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _gap_priority(gap: float) -> str:
    if gap > _HIGH_GAP_THRESHOLD:
        return "HIGH"
    if gap > _MEDIUM_GAP_THRESHOLD:
        return "MEDIUM"
    return "LOW"


def _readiness_label(score: float) -> str:
    if score >= _READY_THRESHOLD:
        return "READY"
    if score >= _DEVELOPING_THRESHOLD:
        return "DEVELOPING"
    return "GAP"


def _priority_sort_key(tg: TraitGap) -> tuple:
    """Trie HIGH > MEDIUM > LOW, puis par gap décroissant."""
    priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
    return (priority_order.get(tg.priority, 3), -tg.gap)


def _extract_trait_score(snapshot: Dict, trait: str) -> Optional[float]:
    """
    Extrait le score brut d'un trait depuis le snapshot.
    Gère les catégories : personality (big_five), cognitive, motivation.
    """
    # Big Five
    bf = snapshot.get("big_five") or {}
    if trait in bf:
        val = bf[trait]
        if isinstance(val, dict):
            return float(val.get("score", 50.0))
        return float(val)

    # Cognitive sous-scores
    cog = snapshot.get("cognitive") or {}
    if trait in cog:
        return float(cog[trait])

    # Motivation
    mot = snapshot.get("motivation") or {}
    if trait in mot:
        return float(mot[trait])

    return None


def _build_trait_gaps(
    snapshot: Dict,
    ideal_profile: Dict,
) -> List[TraitGap]:
    """
    Construit la liste des gaps par trait en comparant snapshot vs profil idéal.
    """
    gaps: List[TraitGap] = []

    # Inverser CATEGORY_MAPPING pour lookup rapide
    trait_to_category: Dict[str, str] = {}
    for category, traits in CATEGORY_MAPPING.items():
        for t in traits:
            trait_to_category[t] = category

    for category_key, trait_dict in ideal_profile.items():
        # category_key = "personality" | "motivation" | "cognitive"
        for trait, ideal_val in trait_dict.items():
            ideal = float(ideal_val)
            current = _extract_trait_score(snapshot, trait)

            if current is None:
                current = 50.0  # fallback médian

            gap = ideal - current  # positif = en-dessous de l'idéal

            # Catégorie : on utilise la clé du profil directement
            category = category_key if category_key in ("personality", "motivation", "cognitive") \
                else trait_to_category.get(trait, "personality")

            gaps.append(TraitGap(
                trait=trait,
                current_score=round(current, 1),
                ideal_score=round(ideal, 1),
                gap=round(gap, 1),
                priority=_gap_priority(gap),
                category=category,
            ))

    return sorted(gaps, key=_priority_sort_key)


def _compute_overall_readiness(gaps: List[TraitGap]) -> float:
    """
    Calcule l'overall_readiness comme la moyenne inverse des gaps positifs.
    100 - (somme des gaps positifs normalisés / nb traits total)
    """
    if not gaps:
        return 100.0

    n = len(gaps)
    total_positive_gap = sum(max(0.0, g.gap) for g in gaps)
    # Normalisation : gap max théorique = 100 (idéal=100, current=0)
    avg_penalty = total_positive_gap / (n * 100.0)
    readiness = max(0.0, min(100.0, (1.0 - avg_penalty) * 100.0))
    return round(readiness, 1)


# ── Fonction principale ───────────────────────────────────────────────────────

def run(
    candidate_snapshot: Dict,
    current_position: str,
    target_position: Optional[str] = None,
) -> TrainingResult:
    """
    Analyse les gaps de développement d'un candidat pour un poste cible.

    Args:
        candidate_snapshot : psychometric_snapshot du candidat
        current_position   : poste actuel (ex: "Deckhand")
        target_position    : poste cible (None = même poste, plan d'amélioration)

    Returns:
        TrainingResult avec gap analysis et plan de développement
    """
    effective_target = target_position if target_position is not None else current_position

    # ── 1. Profil idéal du poste cible ────────────────────────────────────────
    ideal_profile = get_ideal_profile(effective_target)

    if ideal_profile is None:
        # Poste inconnu — retourner un résultat minimal
        return TrainingResult(
            current_position=current_position,
            target_position=effective_target,
            overall_readiness=50.0,
            readiness_label="DEVELOPING",
            trait_gaps=[],
            top_priorities=[],
            strengths=[],
            motivation_gaps=[],
            confidence=ConfidenceLevel.LOW,
        )

    # ── 2. Gaps par trait ─────────────────────────────────────────────────────
    trait_gaps = _build_trait_gaps(candidate_snapshot, ideal_profile)

    # ── 3. Overall readiness ──────────────────────────────────────────────────
    overall_readiness = _compute_overall_readiness(trait_gaps)
    readiness_label = _readiness_label(overall_readiness)

    # ── 4. Top priorités et forces ────────────────────────────────────────────
    # Priorités : traits où gap > 0 (sous le niveau), triés par gap décroissant
    underdeveloped = [g for g in trait_gaps if g.gap > 0]
    top_priorities = [g.trait for g in underdeveloped[:3]]

    # Forces : traits au-dessus de l'idéal (gap < 0), triés par |gap| décroissant
    strengths_gaps = sorted([g for g in trait_gaps if g.gap < 0], key=lambda g: g.gap)
    strengths = [g.trait for g in strengths_gaps[:3]]

    # ── 5. Gaps motivationnels (SDT) ─────────────────────────────────────────
    motivation_gaps_list = []
    mfit_result = _mfit.compute(candidate_snapshot, position=effective_target)
    if mfit_result is not None:
        motivation_gaps_list = mfit_result.dimension_gaps

    # ── 6. Confidence basée sur la qualité des données snapshot ──────────────
    n_traits = len(trait_gaps)
    n_fallback = sum(
        1 for g in trait_gaps if g.current_score == 50.0
    )
    data_quality = 1.0 - (n_fallback / n_traits) if n_traits > 0 else 0.0
    confidence = _confidence_from_quality(data_quality)

    return TrainingResult(
        current_position=current_position,
        target_position=effective_target,
        overall_readiness=overall_readiness,
        readiness_label=readiness_label,
        trait_gaps=trait_gaps,
        top_priorities=top_priorities,
        strengths=strengths,
        motivation_gaps=motivation_gaps_list,
        confidence=confidence,
    )
