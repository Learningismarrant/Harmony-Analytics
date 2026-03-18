# pe_fit/mobility_fit/f_mobility.py
"""
F_mobility — Fit mobilité-temporel (Famille 7)

Mesure l'adéquation entre la situation de mobilité personnelle du candidat
et les contraintes temporelles / géographiques du poste.

Architecture de mesure :
    Série P (candidat)   : snapshot['mobility_profile'][dim]     ∈ [0, 100]
    Série E (poste)      : vessel_params['mobility_requirements'][dim] ∈ [0, 1]
    Score_dim(i)         : 1 − |P_norm(i) − E(i)|

    P_norm(i) = P(i) / 100

Dimension 7.2 — durée embarquement :
    E est la durée en semaines (entier) → normalisé via breakpoints :
    < 4 sem → 0.25 | 4-12 → 0.50 | 12-26 → 0.75 | ≥ 26 → 1.0

Pondérations intra-famille (weights.py) :
    7.1  mobilité situation       0.35
    7.2  durée embarquement       0.35
    7.3  incertitude programme    0.20
    7.4  rapport contrat          0.10

Retourne None si aucune donnée candidate ET aucune donnée poste disponible.

Sources :
    Document de référence Harmony Analytics v0.7, §2.2 (Famille 7), §3 (PSI)
    Chuang, Shen & Judge (2016) — Score_dim = 1 − |P − E| / max_écart
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.mobility_fit.weights import (
    W_MOBILITY,
    W_EMBARKATION,
    W_UNCERTAINTY,
    W_CONTRACT,
    LOW_FLEXIBILITY_THRESHOLD,
    EMBARKATION_DURATION_BREAKPOINTS,
)


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class MobilityDimScore:
    """Score PSI pour une dimension de la famille 7."""
    dimension: str
    candidate_raw: Optional[float]      # valeur brute snapshot (0-100), None si absente
    environment_level: Optional[float]  # niveau E normalisé (0-1), None si absent
    score: float                        # PSI ∈ [0, 1]
    weight: float
    flags: List[str] = field(default_factory=list)


@dataclass
class FMobilityResult:
    """
    Résultat du fit mobilité-temporel (Famille 7).

    score        : score global ∈ [0, 100]
    dimensions   : détail par dimension (7.1 à 7.4)
    data_quality : qualité des données
    flags        : avertissements
    """
    score: float
    dimensions: List[MobilityDimScore]
    data_quality: float = 1.0
    flags: List[str] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _psi_dim(
    p_raw: Optional[float],
    e_level: Optional[float],
    *,
    default_score: float = 0.5,
) -> float:
    """PSI = 1 − |P_norm − E|. Retourne default_score si données absentes."""
    if p_raw is None or e_level is None:
        return default_score
    p_norm = p_raw / 100.0
    return round(max(0.0, min(1.0, 1.0 - abs(p_norm - e_level))), 4)


def _normalize_embarkation_weeks(weeks: Optional[float]) -> Optional[float]:
    """
    Convertit la durée d'embarquement (semaines) en niveau normalisé [0, 1].

    Breakpoints (EMBARKATION_DURATION_BREAKPOINTS = [4, 12, 26]) :
        < 4  semaines → 0.25  (contrat court)
        4–12 semaines → 0.50  (saison standard)
        12–26 semaines → 0.75 (longue saison)
        ≥ 26 semaines → 1.00  (très long / permanent)
    """
    if weeks is None:
        return None
    bp = EMBARKATION_DURATION_BREAKPOINTS  # [4, 12, 26]
    levels = [0.25, 0.50, 0.75, 1.00]
    for i, threshold in enumerate(bp):
        if weeks < threshold:
            return levels[i]
    return levels[-1]


# ── Extraction ────────────────────────────────────────────────────────────────

def _extract_mobility_profile(snapshot: Dict) -> Dict[str, Optional[float]]:
    """
    Extrait le profil de mobilité du candidat depuis le snapshot.

    Clés attendues dans snapshot['mobility_profile'] :
        mobility_flexibility     (7.1) ∈ [0, 100]
        embarkation_tolerance    (7.2) ∈ [0, 100]
        uncertainty_tolerance    (7.3) ∈ [0, 100]
        contract_flexibility     (7.4) ∈ [0, 100]
    """
    mp = snapshot.get("mobility_profile") or {}
    return {
        "mobility":     mp.get("mobility_flexibility"),
        "embarkation":  mp.get("embarkation_tolerance"),
        "uncertainty":  mp.get("uncertainty_tolerance"),
        "contract":     mp.get("contract_flexibility"),
    }


def _extract_mobility_requirements(vessel_params: Dict) -> Dict[str, Optional[float]]:
    """
    Extrait les exigences de mobilité du poste depuis vessel_params.

    Clés attendues dans vessel_params['mobility_requirements'] :
        mobility_level           (7.1) ∈ [0, 1]
        embarkation_weeks        (7.2) numérique (semaines) → normalisé auto
        schedule_unpredictability (7.3) ∈ [0, 1]  (0=stable, 1=très imprévisible)
        contract_permanence      (7.4) ∈ [0, 1]  (0=saisonnier, 1=permanent)
            → inversé pour le scoring : candidat high flexibility fit mieux sur contrat saisonnier
    """
    mr = vessel_params.get("mobility_requirements") or {}

    mobility_level    = mr.get("mobility_level")
    embarkation_weeks = mr.get("embarkation_weeks")
    unpredictability  = mr.get("schedule_unpredictability")
    contract_perm     = mr.get("contract_permanence")

    # Normalisation durée embarquement
    embarkation_norm = _normalize_embarkation_weeks(embarkation_weeks)

    # contract_permanence : inversé pour le scoring E
    # Un poste saisonnier (permanence=0) requiert haute flexibilité contractuelle (E=1.0)
    contract_e = (1.0 - float(contract_perm)) if contract_perm is not None else None

    return {
        "mobility":    float(mobility_level) if mobility_level is not None else None,
        "embarkation": embarkation_norm,
        "uncertainty": float(unpredictability) if unpredictability is not None else None,
        "contract":    contract_e,
    }


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    vessel_params: Dict,
) -> FMobilityResult:
    """
    Calcule le fit mobilité-temporel (Famille 7).

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        vessel_params      : paramètres du poste (doit contenir 'mobility_requirements')

    Returns:
        FMobilityResult avec score global et détail par dimension.
    """
    flags: List[str] = []
    data_quality = 1.0

    p_vals = _extract_mobility_profile(candidate_snapshot)
    e_vals = _extract_mobility_requirements(vessel_params)

    p_missing = sum(1 for v in p_vals.values() if v is None)
    e_missing = sum(1 for v in e_vals.values() if v is None)

    if p_missing > 0:
        flags.append(
            f"MOBILITY_PROFILE_PARTIAL: {p_missing}/4 dimensions candidat absentes — médiane utilisée"
        )
        data_quality -= p_missing * 0.10

    if e_missing > 0:
        flags.append(
            f"MOBILITY_REQUIREMENTS_PARTIAL: {e_missing}/4 exigences poste absentes — médiane utilisée"
        )
        data_quality -= e_missing * 0.08

    # ── Dimension 7.1 — Mobilité géographique ────────────────────────────────
    dim_flags_71: List[str] = []
    score_71 = _psi_dim(p_vals["mobility"], e_vals["mobility"])
    p_71 = p_vals["mobility"]
    if p_71 is not None and p_71 < LOW_FLEXIBILITY_THRESHOLD and (e_vals["mobility"] or 0) > 0.5:
        dim_flags_71.append(
            f"LOW_MOBILITY_FLEXIBILITY: {p_71:.0f}/100 — situation personnelle potentiellement incompatible"
        )
        flags.extend(dim_flags_71)

    dim_71 = MobilityDimScore(
        dimension="mobility_situation_7.1",
        candidate_raw=p_71,
        environment_level=e_vals["mobility"],
        score=score_71,
        weight=W_MOBILITY,
        flags=dim_flags_71,
    )

    # ── Dimension 7.2 — Durée embarquement ───────────────────────────────────
    dim_flags_72: List[str] = []
    score_72 = _psi_dim(p_vals["embarkation"], e_vals["embarkation"])
    p_72 = p_vals["embarkation"]
    if p_72 is not None and p_72 < LOW_FLEXIBILITY_THRESHOLD and (e_vals["embarkation"] or 0) > 0.5:
        dim_flags_72.append(
            f"LOW_EMBARKATION_TOLERANCE: {p_72:.0f}/100 — durée embarquement probablement trop longue"
        )
        flags.extend(dim_flags_72)

    dim_72 = MobilityDimScore(
        dimension="embarkation_duration_7.2",
        candidate_raw=p_72,
        environment_level=e_vals["embarkation"],
        score=score_72,
        weight=W_EMBARKATION,
        flags=dim_flags_72,
    )

    # ── Dimension 7.3 — Incertitude de programme ─────────────────────────────
    dim_73 = MobilityDimScore(
        dimension="schedule_uncertainty_7.3",
        candidate_raw=p_vals["uncertainty"],
        environment_level=e_vals["uncertainty"],
        score=_psi_dim(p_vals["uncertainty"], e_vals["uncertainty"]),
        weight=W_UNCERTAINTY,
        flags=[],
    )

    # ── Dimension 7.4 — Contrat non-permanent ────────────────────────────────
    dim_74 = MobilityDimScore(
        dimension="contract_flexibility_7.4",
        candidate_raw=p_vals["contract"],
        environment_level=e_vals["contract"],
        score=_psi_dim(p_vals["contract"], e_vals["contract"]),
        weight=W_CONTRACT,
        flags=[],
    )

    dimensions = [dim_71, dim_72, dim_73, dim_74]

    # ── Score global pondéré ──────────────────────────────────────────────────
    total_weight = sum(d.weight for d in dimensions)
    raw_score = sum(d.score * d.weight for d in dimensions) / total_weight
    score = round(raw_score * 100.0, 1)

    return FMobilityResult(
        score=score,
        dimensions=dimensions,
        data_quality=max(0.0, round(data_quality, 3)),
        flags=flags,
    )


def compute_fit(
    snapshot: Dict,
    vessel_params: Optional[Dict] = None,
) -> Optional[FMobilityResult]:
    """
    Retourne None si vessel_params est None/vide OU si aucune donnée de mobilité
    n'est présente dans snapshot ET vessel_params.

    Args:
        snapshot      : psychometric_snapshot du CrewProfile
        vessel_params : paramètres du poste (None → retourne None)

    Returns:
        FMobilityResult ou None
    """
    if not vessel_params:
        return None

    has_candidate_data = bool(snapshot.get("mobility_profile"))
    has_vessel_data    = bool(vessel_params.get("mobility_requirements"))

    if not has_candidate_data and not has_vessel_data:
        return None

    return compute(snapshot, vessel_params)
