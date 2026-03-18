"""
P-J Fit — Motivation sub-dimension (SDT)
Distance cosinus entre profil SDT candidat et profil idéal par poste.

Formule :
    motivation_fit = (1 - cosine_distance(v_candidat, v_idéal)) × 100

    v_candidat = vecteur normalisé des 6 régulations SDT du candidat
    v_idéal    = vecteur normalisé du profil idéal du poste
    cosine_distance = 1 - (v·w / (|v|·|w|))

Justification distance cosinus vs euclidienne :
    C'est le pattern relatif entre régulations (autonome vs contrôlée)
    qui prédit les outcomes, pas les niveaux absolus.
    (Sheldon & Elliot, 1999 ; Gagné & Deci, 2005)

Régulations SDT (6 dimensions) :
    intrinsic          — motivation par le plaisir intrinsèque
    identified         — régulation identifiée (valeurs personnelles)
    introjected        — régulation introjectée (pression interne)
    extrinsic_social   — régulation externe sociale (reconnaissance)
    extrinsic_material — régulation externe matérielle (salaire)
    amotivation        — absence de motivation

Sources :
    Deci, E.L., Koestner, R., & Ryan, R.M. (1999). Meta-analytic review.
        Psychological Bulletin, 125(6), 627-668.
    Gagné, M., & Deci, E.L. (2005). SDT and work motivation.
        Journal of Organizational Behavior, 26(4), 331-362.
    Sheldon, K.M., & Elliot, A.J. (1999). Goal striving, need satisfaction.
        Journal of Personality and Social Psychology, 76(3), 482-497.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

# ── Dimensions SDT dans l'ordre canonique ────────────────────────────────────
SDT_DIMENSIONS = [
    "intrinsic",
    "identified",
    "introjected",
    "extrinsic_social",
    "extrinsic_material",
    "amotivation",
]

SDT_FALLBACK = 50.0


# ── Profils idéaux par poste (Phase 0 — SME panel) ───────────────────────────
# Scores 0-100 sur chaque régulation SDT.
# Pattern : autonome (intrinsic + identified) élevé, contrôlé + amotivation bas.
# TODO Temps 2 : recalibrer via Q-sort motivationnel + données empiriques.

MOTIVATION_PROFILES: Dict[str, Dict[str, float]] = {
    "Captain": {
        "intrinsic": 90, "identified": 88, "introjected": 30,
        "extrinsic_social": 55, "extrinsic_material": 45, "amotivation": 5
    },
    "First Mate": {
        "intrinsic": 82, "identified": 85, "introjected": 35,
        "extrinsic_social": 60, "extrinsic_material": 50, "amotivation": 8
    },
    "Chief Engineer": {
        "intrinsic": 92, "identified": 78, "introjected": 25,
        "extrinsic_social": 40, "extrinsic_material": 55, "amotivation": 5
    },
    "Bosun": {
        "intrinsic": 75, "identified": 82, "introjected": 40,
        "extrinsic_social": 65, "extrinsic_material": 65, "amotivation": 10
    },
    "Deckhand": {
        "intrinsic": 65, "identified": 78, "introjected": 45,
        "extrinsic_social": 72, "extrinsic_material": 72, "amotivation": 12
    },
    "Chief Stewardess": {
        "intrinsic": 82, "identified": 88, "introjected": 35,
        "extrinsic_social": 85, "extrinsic_material": 55, "amotivation": 5
    },
    "Stewardess": {
        "intrinsic": 72, "identified": 78, "introjected": 42,
        "extrinsic_social": 88, "extrinsic_material": 65, "amotivation": 10
    },
    "Chef": {
        "intrinsic": 95, "identified": 72, "introjected": 30,
        "extrinsic_social": 50, "extrinsic_material": 55, "amotivation": 5
    },
    "2nd Engineer": {
        "intrinsic": 85, "identified": 80, "introjected": 30,
        "extrinsic_social": 45, "extrinsic_material": 58, "amotivation": 7
    },
}

MOTIVATION_PROFILES_NORM = {k.lower(): v for k, v in MOTIVATION_PROFILES.items()}


@dataclass
class DimensionGap:
    dimension: str
    candidate_score: float
    ideal_score: float
    gap: float          # candidat - idéal


@dataclass
class MotivationFitResult:
    score: float                    # motivation_fit ∈ [0, 100]
    cosine_similarity: float        # [0, 1]
    cosine_distance: float          # 1 - similarity
    position: Optional[str]
    dimension_gaps: List[DimensionGap] = field(default_factory=list)
    fallback_count: int = 0
    data_quality: float = 1.0
    flags: List[str] = field(default_factory=list)
    formula_snapshot: str = ""


def _extract_sdt_vector(snapshot: Dict) -> Tuple[List[float], int]:
    """
    Extrait le vecteur SDT depuis le snapshot.
    Cherche dans snapshot['motivation'] ou snapshot directement.
    Retourne (vecteur 6D, nb_fallbacks).
    """
    motivation = snapshot.get("motivation") or {}
    vector = []
    fallbacks = 0

    for dim in SDT_DIMENSIONS:
        val = motivation.get(dim)
        if val is None:
            val = snapshot.get(dim)
        if val is None:
            vector.append(SDT_FALLBACK)
            fallbacks += 1
        else:
            vector.append(float(val))

    return vector, fallbacks


def _normalize_vector(v: List[float]) -> List[float]:
    """Normalise un vecteur (norme L2). Retourne le vecteur original si norme=0."""
    norm = math.sqrt(sum(x * x for x in v))
    if norm == 0:
        return v
    return [x / norm for x in v]


def _cosine_distance(v1: List[float], v2: List[float]) -> float:
    """Distance cosinus ∈ [0, 2]. Normalisée ici sur [0, 1] via /2."""
    n1 = _normalize_vector(v1)
    n2 = _normalize_vector(v2)
    dot = sum(a * b for a, b in zip(n1, n2))
    dot = max(-1.0, min(1.0, dot))  # clip pour erreurs numériques
    cosine_similarity = (dot + 1.0) / 2.0  # remapper [-1,1] → [0,1]
    return 1.0 - cosine_similarity


def compute(
    candidate_snapshot: Dict,
    position: Optional[str] = None,
    ideal_profile: Optional[Dict[str, float]] = None,
) -> Optional["MotivationFitResult"]:
    """
    Calcule le motivation_fit via distance cosinus SDT.

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        position           : poste cible (ex: "Captain") — utilisé pour
                             chercher le profil idéal si ideal_profile absent
        ideal_profile      : profil idéal personnalisé (override)

    Returns:
        MotivationFitResult, ou None si aucun profil idéal disponible
        et aucune donnée SDT candidat.
    """
    flags: List[str] = []

    # Profil idéal
    profile = ideal_profile
    if profile is None and position:
        profile = MOTIVATION_PROFILES_NORM.get(position.lower())
    if profile is None:
        return None  # pas de profil idéal → dimension non calculable

    # Vecteur candidat
    candidate_vec, fallback_count = _extract_sdt_vector(candidate_snapshot)
    if fallback_count == len(SDT_DIMENSIONS):
        flags.append("NO_SDT_DATA: aucune donnée motivationnelle — dimension non fiable")

    # Vecteur idéal (dans le même ordre que SDT_DIMENSIONS)
    ideal_vec = [profile.get(dim, SDT_FALLBACK) for dim in SDT_DIMENSIONS]

    # Distance cosinus
    dist = _cosine_distance(candidate_vec, ideal_vec)
    similarity = 1.0 - dist
    score = round(max(0.0, min(100.0, similarity * 100.0)), 1)

    # Gaps par dimension (pour le diagnostic)
    dimension_gaps = [
        DimensionGap(
            dimension=dim,
            candidate_score=round(c, 1),
            ideal_score=round(i, 1),
            gap=round(c - i, 1),
        )
        for dim, c, i in zip(SDT_DIMENSIONS, candidate_vec, ideal_vec)
    ]

    data_quality = round(1.0 - (fallback_count / len(SDT_DIMENSIONS)), 3)
    if fallback_count > 0:
        flags.append(f"FALLBACK_SDT: {fallback_count}/{len(SDT_DIMENSIONS)} dimensions en fallback médian")

    formula = (
        f"motivation_fit = (1 - cosine_dist({[round(x,1) for x in candidate_vec]}, "
        f"{[round(x,1) for x in ideal_vec]})) × 100 = {score}"
    )

    return MotivationFitResult(
        score=score,
        cosine_similarity=round(similarity, 4),
        cosine_distance=round(dist, 4),
        position=position,
        dimension_gaps=dimension_gaps,
        fallback_count=fallback_count,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )
