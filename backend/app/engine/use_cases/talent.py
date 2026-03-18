"""
Use Case : Gestion des talents — trajectoire de carrière
Dimensions actives : P-J (D-A + motivation) sur plusieurs postes cibles
Output : matrice de readiness par échelon + poste recommandé suivant

Évalue la maturité psychométrique d'un candidat pour les postes
supérieurs dans la hiérarchie maritime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.use_cases._base import (
    ConfidenceLevel,
    _confidence_from_quality,
)
from app.engine.use_cases.training import (
    TraitGap,
    run as training_run,
    _readiness_label,
)
from app.engine.pe_fit.trait_extractor import extract_strict, extract_with_fallback


# ── Progression naturelle dans la hiérarchie maritime ────────────────────────

CAREER_PROGRESSIONS: Dict[str, List[str]] = {
    "Deckhand":     ["Bosun", "First Mate"],
    "Bosun":        ["First Mate", "Captain"],
    "First Mate":   ["Captain"],
    "Stewardess":   ["Chief Stewardess"],
    "2nd Engineer": ["Chief Engineer"],
}

# Seuils readiness pour la progression
_READY_THRESHOLD      = 70.0
_DEVELOPING_THRESHOLD = 50.0


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class PositionReadiness:
    position: str
    readiness_score: float
    readiness_label: str            # "READY" | "DEVELOPING" | "NOT_READY"
    key_gaps: List[TraitGap]        # top 3 gaps bloquants
    estimated_development_time: str # "< 6 mois" | "6-18 mois" | "> 18 mois"


@dataclass
class TalentResult:
    current_position: str
    current_readiness: float        # fit au poste actuel
    next_positions: List[PositionReadiness]
    recommended_next: Optional[str] # poste le plus accessible
    high_potential: bool            # readiness ≥ 70 sur au moins un poste supérieur
    talent_profile: str             # "SPECIALIST" | "GENERALIST" | "LEADER"
    confidence: ConfidenceLevel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _readiness_label_talent(score: float) -> str:
    """Labels spécifiques talent (seuil READY = 70, pas 80)."""
    if score >= _READY_THRESHOLD:
        return "READY"
    if score >= _DEVELOPING_THRESHOLD:
        return "DEVELOPING"
    return "NOT_READY"


def _development_time(readiness: float) -> str:
    if readiness >= _READY_THRESHOLD:
        return "< 6 mois"
    if readiness >= _DEVELOPING_THRESHOLD:
        return "6-18 mois"
    return "> 18 mois"


def _detect_talent_profile(snapshot: Dict) -> str:
    """
    Détermine le profil de talent :
    - LEADER     : conscientiousness ≥ 75 ET extraversion ≥ 65 ET GCA ≥ 70
    - SPECIALIST : GCA ≥ 75 ET openness ≥ 70 ET extraversion < 60
    - GENERALIST : sinon
    """
    c = extract_with_fallback(snapshot, "conscientiousness")
    e = extract_with_fallback(snapshot, "extraversion")
    gca = extract_with_fallback(snapshot, "gca")
    o = extract_with_fallback(snapshot, "openness")

    if c >= 75 and e >= 65 and gca >= 70:
        return "LEADER"
    if gca >= 75 and o >= 70 and e < 60:
        return "SPECIALIST"
    return "GENERALIST"


def _evaluate_position(
    snapshot: Dict,
    current_position: str,
    target_position: str,
) -> PositionReadiness:
    """Évalue la readiness pour un poste cible via training.run()."""
    training_result = training_run(
        candidate_snapshot=snapshot,
        current_position=current_position,
        target_position=target_position,
    )

    readiness = training_result.overall_readiness
    label = _readiness_label_talent(readiness)
    dev_time = _development_time(readiness)

    # Top 3 gaps bloquants = traits sous le niveau (gap > 0), priorisés
    key_gaps = [g for g in training_result.trait_gaps if g.gap > 0][:3]

    return PositionReadiness(
        position=target_position,
        readiness_score=readiness,
        readiness_label=label,
        key_gaps=key_gaps,
        estimated_development_time=dev_time,
    )


# ── Fonction principale ───────────────────────────────────────────────────────

def run(
    candidate_snapshot: Dict,
    current_position: str,
    target_positions: Optional[List[str]] = None,
) -> TalentResult:
    """
    Évalue la trajectoire de carrière d'un candidat.

    Args:
        candidate_snapshot : psychometric_snapshot du candidat
        current_position   : poste actuel (ex: "Deckhand")
        target_positions   : postes cibles à évaluer (None = progression naturelle)

    Returns:
        TalentResult avec matrice de readiness et recommandations
    """
    # ── 1. Déterminer les postes cibles ───────────────────────────────────────
    if target_positions is None:
        target_positions = CAREER_PROGRESSIONS.get(current_position, [])

    # ── 2. Readiness au poste actuel ─────────────────────────────────────────
    current_training = training_run(
        candidate_snapshot=candidate_snapshot,
        current_position=current_position,
        target_position=current_position,
    )
    current_readiness = current_training.overall_readiness

    # ── 3. Évaluation de chaque poste cible ──────────────────────────────────
    next_positions: List[PositionReadiness] = []
    for pos in target_positions:
        pr = _evaluate_position(candidate_snapshot, current_position, pos)
        next_positions.append(pr)

    # ── 4. Poste recommandé = celui avec le meilleur score de readiness ───────
    recommended_next: Optional[str] = None
    if next_positions:
        best = max(next_positions, key=lambda p: p.readiness_score)
        recommended_next = best.position

    # ── 5. High potential = readiness ≥ 70 sur au moins un poste supérieur ───
    high_potential = any(p.readiness_score >= _READY_THRESHOLD for p in next_positions)

    # ── 6. Profil de talent ───────────────────────────────────────────────────
    talent_profile = _detect_talent_profile(candidate_snapshot)

    # ── 7. Confidence ─────────────────────────────────────────────────────────
    has_psychometric = bool(
        candidate_snapshot.get("big_five") or candidate_snapshot.get("emotional_stability")
    )
    has_cognitive = bool(
        (candidate_snapshot.get("cognitive") or {}).get("gca_score")
        or (candidate_snapshot.get("cognitive") or {}).get("logical")
    )
    has_motivation = bool(candidate_snapshot.get("motivation"))

    data_quality = sum([has_psychometric, has_cognitive, has_motivation]) / 3.0
    confidence = _confidence_from_quality(data_quality)

    return TalentResult(
        current_position=current_position,
        current_readiness=current_readiness,
        next_positions=next_positions,
        recommended_next=recommended_next,
        high_potential=high_potential,
        talent_profile=talent_profile,
        confidence=confidence,
    )
