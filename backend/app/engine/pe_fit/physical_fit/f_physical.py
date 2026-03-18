# pe_fit/physical_fit/f_physical.py
"""
F_physical — Fit physique-environnemental (Famille 6)

Mesure l'adéquation entre les tolérances individuelles du candidat
et les conditions physiques de l'environnement embarqué.

Architecture de mesure :
    Série P (candidat)   : snapshot['maritime_tolerance'][dim]  ∈ [0, 100]
    Série E (poste)      : vessel_params['maritime_conditions'][dim] ∈ [0, 1]
    Score_dim(i)         : 1 − |P_norm(i) − E(i)|

    P_norm(i) = P(i) / 100    → ramène la réponse Likert 0-100 vers [0, 1]

Cas spécial — dimension 6.3 (risque physique) :
    Sur-fit dangereux : candidat trop insouciant face à un poste faible risque.
    Pénalité symétrique si P_norm >> E (sur-fit > RISK_OVERFIT_MARGIN).

Pondérations intra-famille (weights.py) :
    6.1  espace restreint  0.25
    6.2  isolement         0.25
    6.3  risque physique   0.25
    6.4  rythmes           0.20
    6.5  météo             0.05

Retourne None si aucune donnée candidate ET aucune donnée poste disponible.

Sources :
    Document de référence Harmony Analytics v0.7, §2.2 (Famille 6), §3 (PSI)
    Chuang, Shen & Judge (2016) — Score_dim = 1 − |P − E| / max_écart
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.physical_fit.weights import (
    W_CONFINED_SPACE,
    W_ISOLATION,
    W_PHYSICAL_RISK,
    W_SCHEDULE,
    W_WEATHER,
    LOW_TOLERANCE_THRESHOLD,
    RISK_OVERFIT_MARGIN,
)


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class PhysicalDimScore:
    """Score PSI pour une dimension de la famille 6."""
    dimension: str
    candidate_raw: Optional[float]    # valeur brute snapshot (0-100), None si absente
    environment_level: Optional[float]  # niveau E du poste (0-1), None si absent
    score: float                       # PSI normalisé ∈ [0, 1]
    weight: float
    flags: List[str] = field(default_factory=list)


@dataclass
class FPhysicalResult:
    """
    Résultat du fit physique-environnemental (Famille 6).

    score        : score global ∈ [0, 100]
    dimensions   : détail par dimension (6.1 à 6.5)
    data_quality : qualité des données (1.0 si complètes, dégradée si partielles)
    flags        : avertissements
    """
    score: float
    dimensions: List[PhysicalDimScore]
    data_quality: float = 1.0
    flags: List[str] = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _psi_dim(
    p_raw: Optional[float],
    e_level: Optional[float],
    *,
    default_score: float = 0.5,
) -> float:
    """
    Calcule le PSI pour une dimension unique.

    PSI = 1 − |P_norm − E|
    où P_norm = p_raw / 100 (ramène 0-100 → 0-1).

    Si l'une des valeurs est absente, retourne default_score (médiane = pas d'information).
    """
    if p_raw is None or e_level is None:
        return default_score
    p_norm = p_raw / 100.0
    return round(max(0.0, min(1.0, 1.0 - abs(p_norm - e_level))), 4)


def _score_physical_risk(
    p_raw: Optional[float],
    e_level: Optional[float],
) -> tuple[float, List[str]]:
    """
    Dimension 6.3 — Rapport au risque physique.

    Sur-fit pénalisé : P_norm >> E_level → candidat trop insouciant
    pour un poste peu risqué (signal dangereux).
    Sous-fit pénalisé classiquement (|P_norm − E_level|).

    Returns:
        (score_0_1, flags)
    """
    flags: List[str] = []
    if p_raw is None or e_level is None:
        return 0.5, flags

    p_norm = p_raw / 100.0
    base_score = _psi_dim(p_raw, e_level)

    # Détection sur-fit dangereux
    overfit = p_norm - e_level
    if overfit > RISK_OVERFIT_MARGIN / 100.0:
        flags.append(
            f"PHYSICAL_RISK_OVERFIT: candidat {p_raw:.0f}/100 >> poste {e_level*100:.0f}/100"
            f" (écart {overfit*100:.0f}pts) — risque d'insouciance"
        )
        # Pénalité symétrique : traiter le sur-fit comme un sous-fit
        penalized = 1.0 - overfit
        base_score = round(max(0.0, min(1.0, penalized)), 4)

    return base_score, flags


# ── Extraction ────────────────────────────────────────────────────────────────

def _extract_maritime_tolerance(snapshot: Dict) -> Dict[str, Optional[float]]:
    """
    Extrait les tolérances maritimes du snapshot.

    Clés attendues dans snapshot['maritime_tolerance'] :
        confined_space_tolerance    (6.1) ∈ [0, 100]
        isolation_tolerance         (6.2) ∈ [0, 100]
        physical_risk_tolerance     (6.3) ∈ [0, 100]
        schedule_tolerance          (6.4) ∈ [0, 100]
        weather_tolerance           (6.5) ∈ [0, 100]

    Retourne dict avec None pour les clés absentes.
    """
    mt = snapshot.get("maritime_tolerance") or {}
    return {
        "confined_space":  mt.get("confined_space_tolerance"),
        "isolation":       mt.get("isolation_tolerance"),
        "physical_risk":   mt.get("physical_risk_tolerance"),
        "schedule":        mt.get("schedule_tolerance"),
        "weather":         mt.get("weather_tolerance"),
    }


def _extract_maritime_conditions(vessel_params: Dict) -> Dict[str, Optional[float]]:
    """
    Extrait les conditions maritimes du poste depuis vessel_params.

    Clés attendues dans vessel_params['maritime_conditions'] :
        space_constraint_level   (6.1) ∈ [0, 1]
        isolation_level          (6.2) ∈ [0, 1]
        physical_risk_level      (6.3) ∈ [0, 1]
        schedule_irregularity    (6.4) ∈ [0, 1]
        weather_exposure         (6.5) ∈ [0, 1]

    Retourne dict avec None pour les clés absentes.
    """
    mc = vessel_params.get("maritime_conditions") or {}
    return {
        "confined_space":  mc.get("space_constraint_level"),
        "isolation":       mc.get("isolation_level"),
        "physical_risk":   mc.get("physical_risk_level"),
        "schedule":        mc.get("schedule_irregularity"),
        "weather":         mc.get("weather_exposure"),
    }


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    vessel_params: Dict,
) -> FPhysicalResult:
    """
    Calcule le fit physique-environnemental (Famille 6).

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        vessel_params      : paramètres du poste (doit contenir 'maritime_conditions')

    Returns:
        FPhysicalResult avec score global et détail par dimension.
    """
    flags: List[str] = []
    data_quality = 1.0

    p_vals = _extract_maritime_tolerance(candidate_snapshot)
    e_vals = _extract_maritime_conditions(vessel_params)

    # Comptage des données manquantes
    p_missing = sum(1 for v in p_vals.values() if v is None)
    e_missing = sum(1 for v in e_vals.values() if v is None)

    if p_missing > 0:
        flags.append(
            f"MARITIME_TOLERANCE_PARTIAL: {p_missing}/5 dimensions candidat absentes — médiane utilisée"
        )
        data_quality -= p_missing * 0.08

    if e_missing > 0:
        flags.append(
            f"MARITIME_CONDITIONS_PARTIAL: {e_missing}/5 conditions poste absentes — médiane utilisée"
        )
        data_quality -= e_missing * 0.06

    # ── Dimension 6.1 — Espace restreint ─────────────────────────────────────
    dim_flags_61: List[str] = []
    score_61 = _psi_dim(p_vals["confined_space"], e_vals["confined_space"])
    p_61 = p_vals["confined_space"]
    if p_61 is not None and p_61 < LOW_TOLERANCE_THRESHOLD:
        dim_flags_61.append(
            f"LOW_CONFINED_SPACE_TOLERANCE: {p_61:.0f}/100 — risque d'inconfort prolongé"
        )
        flags.extend(dim_flags_61)

    dim_61 = PhysicalDimScore(
        dimension="confined_space_6.1",
        candidate_raw=p_61,
        environment_level=e_vals["confined_space"],
        score=score_61,
        weight=W_CONFINED_SPACE,
        flags=dim_flags_61,
    )

    # ── Dimension 6.2 — Isolement géographique ───────────────────────────────
    dim_flags_62: List[str] = []
    score_62 = _psi_dim(p_vals["isolation"], e_vals["isolation"])
    p_62 = p_vals["isolation"]
    if p_62 is not None and p_62 < LOW_TOLERANCE_THRESHOLD:
        dim_flags_62.append(
            f"LOW_ISOLATION_TOLERANCE: {p_62:.0f}/100 — risque de détresse à bord"
        )
        flags.extend(dim_flags_62)

    dim_62 = PhysicalDimScore(
        dimension="isolation_6.2",
        candidate_raw=p_62,
        environment_level=e_vals["isolation"],
        score=score_62,
        weight=W_ISOLATION,
        flags=dim_flags_62,
    )

    # ── Dimension 6.3 — Risque physique (sur-fit ET sous-fit) ────────────────
    score_63, dim_flags_63 = _score_physical_risk(
        p_vals["physical_risk"], e_vals["physical_risk"]
    )
    flags.extend(dim_flags_63)

    dim_63 = PhysicalDimScore(
        dimension="physical_risk_6.3",
        candidate_raw=p_vals["physical_risk"],
        environment_level=e_vals["physical_risk"],
        score=score_63,
        weight=W_PHYSICAL_RISK,
        flags=dim_flags_63,
    )

    # ── Dimension 6.4 — Rythmes atypiques ────────────────────────────────────
    dim_flags_64: List[str] = []
    score_64 = _psi_dim(p_vals["schedule"], e_vals["schedule"])
    p_64 = p_vals["schedule"]
    if p_64 is not None and p_64 < LOW_TOLERANCE_THRESHOLD:
        dim_flags_64.append(
            f"LOW_SCHEDULE_TOLERANCE: {p_64:.0f}/100 — sensibilité aux horaires atypiques"
        )
        flags.extend(dim_flags_64)

    dim_64 = PhysicalDimScore(
        dimension="schedule_tolerance_6.4",
        candidate_raw=p_64,
        environment_level=e_vals["schedule"],
        score=score_64,
        weight=W_SCHEDULE,
        flags=dim_flags_64,
    )

    # ── Dimension 6.5 — Conditions météo ─────────────────────────────────────
    dim_65 = PhysicalDimScore(
        dimension="weather_tolerance_6.5",
        candidate_raw=p_vals["weather"],
        environment_level=e_vals["weather"],
        score=_psi_dim(p_vals["weather"], e_vals["weather"]),
        weight=W_WEATHER,
        flags=[],
    )

    dimensions = [dim_61, dim_62, dim_63, dim_64, dim_65]

    # ── Score global pondéré (Σ w_i × s_i) / Σ w_i ──────────────────────────
    total_weight = sum(d.weight for d in dimensions)
    raw_score = sum(d.score * d.weight for d in dimensions) / total_weight
    score = round(raw_score * 100.0, 1)

    return FPhysicalResult(
        score=score,
        dimensions=dimensions,
        data_quality=max(0.0, round(data_quality, 3)),
        flags=flags,
    )


def compute_fit(
    snapshot: Dict,
    vessel_params: Optional[Dict] = None,
) -> Optional[FPhysicalResult]:
    """
    Retourne None si vessel_params est None/vide OU si aucune donnée maritime
    n'est présente dans snapshot ET vessel_params.

    Args:
        snapshot      : psychometric_snapshot du CrewProfile
        vessel_params : paramètres du poste (None → retourne None)

    Returns:
        FPhysicalResult ou None
    """
    if not vessel_params:
        return None

    # Vérifie qu'au moins une donnée maritime est présente
    has_candidate_data = bool(snapshot.get("maritime_tolerance"))
    has_vessel_data = bool(vessel_params.get("maritime_conditions"))

    if not has_candidate_data and not has_vessel_data:
        return None

    return compute(snapshot, vessel_params)
