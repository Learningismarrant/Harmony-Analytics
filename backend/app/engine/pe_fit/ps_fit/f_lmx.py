# engine/recruitment/pe_fit/ps_fit/f_lmx.py
"""
F_lmx — Compatibilité Leadership (Person-Supervisor Fit)

Adaptation de MLPSM/f_lmx.py pour le sous-module pe_fit.
Les extractions de préférences de leadership utilisent extract_with_fallback()
depuis pe_fit.trait_extractor.

Formule :
    F_lmx = (1 - ‖L_capt - V_crew‖ / d_max) × 100

Conserver compute() avec signature identique à MLPSM/f_lmx.py.
Ajouter compute_fit() avec retour None si captain_vector absent ou vide.

Sources :
    Graen, G.B. & Uhl-Bien, M. (1995). Relationship-based approach to leadership.
    Leadership Quarterly, 6(2).
    Dulebohn, J.H. et al. (2012). A meta-analysis of LMX. Journal of Management.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional
import math

from app.engine.pe_fit.trait_extractor import extract_with_fallback, extract_strict
from app.engine.pe_fit.ps_fit.weights import (
    W_AUTONOMY,
    W_FEEDBACK,
    W_STRUCTURE,
    CRITICAL_DISTANCE_THRESHOLD,
    LOW_DATA_THRESHOLD,
)


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class DimensionGap:
    dimension: str
    captain_value: float
    crew_preference: float
    gap: float
    gap_direction: str
    gap_label: str


@dataclass
class VectorDetail:
    captain_autonomy_given: float
    captain_feedback_style: float
    captain_structure_imposed: float
    captain_data_completeness: float
    crew_autonomy_preference: float
    crew_feedback_preference: float
    crew_structure_preference: float
    crew_data_completeness: float


@dataclass
class DistanceDetail:
    euclidean_distance: float
    d_max: float
    normalized_distance: float
    compatibility: float
    compatibility_label: str


@dataclass
class FLmxResult:
    score: float
    vectors: VectorDetail
    distance: DistanceDetail
    dimensions: list[DimensionGap] = field(default_factory=list)
    data_quality: float = 1.0
    flags: list[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Extraction des préférences candidat ──────────────────────────────────────

def _extract_crew_preferences(candidate_snapshot: Dict) -> tuple[float, float, float, float]:
    """
    Extrait les préférences de leadership via extract_with_fallback().

    Priorité :
    1. snapshot.leadership_preferences (dédié)
    2. Dérivation depuis Big Five :
       - autonomy_pref ≈ Openness × 0.6 + (1 - Agreeableness/100) × 0.4
       - feedback_pref ≈ Openness
       - structure_pref ≈ Conscientiousness
    3. Fallback 0.5

    Returns:
        (autonomy, feedback, structure, completeness)
    """
    lp = candidate_snapshot.get("leadership_preferences") or {}
    fallback_count = 0

    # Autonomy preference
    autonomy = lp.get("autonomy_preference")
    if autonomy is None:
        o = extract_strict(candidate_snapshot, "openness")
        a = extract_strict(candidate_snapshot, "agreeableness")
        if o is not None:
            autonomy = min(1.0, (float(o) / 100.0) * 0.6 + (1 - float(a or 50) / 100.0) * 0.4)
        else:
            autonomy = 0.5
            fallback_count += 1

    # Feedback preference
    feedback = lp.get("feedback_preference")
    if feedback is None:
        o = extract_strict(candidate_snapshot, "openness")
        if o is not None:
            feedback = float(o) / 100.0
        else:
            feedback = 0.5
            fallback_count += 1

    # Structure preference
    structure = lp.get("structure_preference")
    if structure is None:
        c = extract_strict(candidate_snapshot, "conscientiousness")
        if c is not None:
            structure = float(c) / 100.0
        else:
            structure = 0.5
            fallback_count += 1

    completeness = 1.0 - (fallback_count / 3.0)
    return float(autonomy), float(feedback), float(structure), completeness


def _extract_captain_vector(captain_vector: Dict) -> tuple[float, float, float, float]:
    """
    Extrait le vecteur capitaine.

    Attendu : {"autonomy_given": 0.6, "feedback_style": 0.4, "structure_imposed": 0.7}
    """
    fallback_count = 0

    autonomy = captain_vector.get("autonomy_given")
    if autonomy is None:
        autonomy = 0.5
        fallback_count += 1

    feedback = captain_vector.get("feedback_style")
    if feedback is None:
        feedback = 0.5
        fallback_count += 1

    structure = captain_vector.get("structure_imposed")
    if structure is None:
        structure = 0.5
        fallback_count += 1

    completeness = 1.0 - (fallback_count / 3.0)
    return float(autonomy), float(feedback), float(structure), completeness


# ── Analyse par dimension ─────────────────────────────────────────────────────

def _analyze_dimension(dim: str, capt: float, crew: float, threshold: float = 0.30) -> DimensionGap:
    gap = abs(capt - crew)
    direction = "ALIGNED"
    if gap > threshold:
        direction = "CAPTAIN_MORE" if capt > crew else "CREW_MORE"

    labels = {
        "autonomy": {
            "ALIGNED": "Niveau d'autonomie compatible",
            "CAPTAIN_MORE": "Le capitaine délègue plus que le candidat ne souhaite",
            "CREW_MORE": "Le candidat veut plus d'autonomie que le capitaine n'en donne",
        },
        "feedback": {
            "ALIGNED": "Style de feedback compatible",
            "CAPTAIN_MORE": "Le capitaine donne plus de feedback que le candidat n'en attend",
            "CREW_MORE": "Le candidat attend plus de coaching que le capitaine n'en donne",
        },
        "structure": {
            "ALIGNED": "Niveau de structure compatible",
            "CAPTAIN_MORE": "Le capitaine est plus procédurier que le candidat ne préfère",
            "CREW_MORE": "Le candidat préfère plus de structure que le capitaine n'en impose",
        },
    }

    return DimensionGap(
        dimension=dim,
        captain_value=round(capt, 3),
        crew_preference=round(crew, 3),
        gap=round(gap, 3),
        gap_direction=direction,
        gap_label=labels.get(dim, {}).get(direction, ""),
    )


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    captain_vector: Dict,
) -> FLmxResult:
    """
    Calcule F_lmx pour un candidat avec un capitaine donné.

    Signature identique à MLPSM/f_lmx.compute().

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        captain_vector     : Yacht.captain_leadership_vector

    Returns:
        FLmxResult avec score final et analyse détaillée par dimension.
    """
    flags: list[str] = []
    data_quality = 1.0

    capt_a, capt_f, capt_s, capt_completeness = _extract_captain_vector(captain_vector)
    crew_a, crew_f, crew_s, crew_completeness  = _extract_crew_preferences(candidate_snapshot)

    if capt_completeness < LOW_DATA_THRESHOLD:
        flags.append(
            f"CAPTAIN_DATA_INCOMPLETE: vecteur capitaine à {capt_completeness*100:.0f}% "
            f"— configurer Yacht.captain_leadership_vector pour un score fiable"
        )
        data_quality -= 0.35

    if crew_completeness < LOW_DATA_THRESHOLD:
        flags.append(
            "CREW_PREFERENCES_ESTIMATED: préférences candidat dérivées du Big Five "
            "(leadership_preferences non disponible)"
        )
        data_quality -= 0.20

    dim_gaps = [
        _analyze_dimension("autonomy",  capt_a, crew_a),
        _analyze_dimension("feedback",  capt_f, crew_f),
        _analyze_dimension("structure", capt_s, crew_s),
    ]

    for d in dim_gaps:
        if d.gap > 0.50:
            flags.append(
                f"CRITICAL_GAP_{d.dimension.upper()}: écart de {d.gap:.2f} → {d.gap_label}"
            )

    dist_sq = (
        W_AUTONOMY  * (capt_a - crew_a) ** 2
        + W_FEEDBACK  * (capt_f - crew_f) ** 2
        + W_STRUCTURE * (capt_s - crew_s) ** 2
    )
    distance = math.sqrt(dist_sq)

    d_max      = math.sqrt(W_AUTONOMY + W_FEEDBACK + W_STRUCTURE)
    normalized = distance / d_max

    if normalized < 0.25:
        compat_label = "EXCELLENT"
    elif normalized < 0.45:
        compat_label = "GOOD"
    elif normalized < CRITICAL_DISTANCE_THRESHOLD:
        compat_label = "TENSION"
        flags.append(f"LMX_TENSION: distance normalisée = {normalized:.2f} — friction probable")
    else:
        compat_label = "CRITICAL"
        flags.append(f"LMX_CRITICAL: distance = {normalized:.2f} — incompatibilité structurelle")

    dist_detail = DistanceDetail(
        euclidean_distance=round(distance, 4),
        d_max=round(d_max, 4),
        normalized_distance=round(normalized, 4),
        compatibility=round(1.0 - normalized, 4),
        compatibility_label=compat_label,
    )

    f_lmx_raw = (1.0 - normalized) * 100.0
    score = round(max(0.0, min(100.0, f_lmx_raw)), 1)

    vectors = VectorDetail(
        captain_autonomy_given=capt_a,
        captain_feedback_style=capt_f,
        captain_structure_imposed=capt_s,
        captain_data_completeness=capt_completeness,
        crew_autonomy_preference=crew_a,
        crew_feedback_preference=crew_f,
        crew_structure_preference=crew_s,
        crew_data_completeness=crew_completeness,
    )

    formula = (
        f"F_lmx = (1 - ‖{[capt_a, capt_f, capt_s]} - {[crew_a, crew_f, crew_s]}‖ / {d_max:.3f})"
        f" = (1 - {distance:.3f}/{d_max:.3f}) × 100"
        f" = {f_lmx_raw:.1f} → {score}"
    )

    return FLmxResult(
        score=score,
        vectors=vectors,
        distance=dist_detail,
        dimensions=dim_gaps,
        data_quality=max(0.0, data_quality),
        flags=flags,
        formula_snapshot=formula,
    )


def compute_fit(
    snapshot: Dict,
    captain_vector: Dict | None = None,
) -> Optional[FLmxResult]:
    """
    Retourne None si captain_vector est None ou vide.

    Args:
        snapshot        : psychometric_snapshot du CrewProfile
        captain_vector  : Yacht.captain_leadership_vector (None → retourne None)

    Returns:
        FLmxResult ou None
    """
    if not captain_vector:
        return None
    return compute(snapshot, captain_vector)
