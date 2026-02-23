# engine/recruitment/simulator.py
"""
Simulateur d'impact recrutement — What-If Analysis.

"Que se passe-t-il si j'embauche ce candidat sur ce yacht ?"

Retourne un rapport delta complet sur toutes les dimensions.
Fonction pure — toutes les données sont injectées par le service.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from engine.MLPSM.master import compute_y_success, RecruitmentScore
from engine.team.harmony import compute_delta as compute_harmony_delta


@dataclass
class ImpactReport:
    # Score global avant/après
    y_success_predicted: float
    p_ind: float
    f_team: float
    f_env: float
    f_lmx: float

    # Delta F_team détaillé (l'impact le plus important dans le yachting)
    f_team_delta: float
    jerk_filter_delta: float       # Impact sur min(agréabilité)
    faultline_risk_delta: float    # Impact sur σ(conscienciosité)
    emotional_buffer_delta: float  # Impact sur μ(stabilité émotionnelle)
    performance_delta: float

    # Flags automatiques
    flags: List[str] = field(default_factory=list)

    # Qualité de la prédiction
    data_completeness: float = 0.0
    confidence_label: str = "N/A"


def simulate_impact(
    candidate_snapshot: Dict,
    current_crew_snapshots: List[Dict],
    vessel_params: Dict,
    captain_vector: Dict,
    betas: Optional[Dict] = None,
) -> ImpactReport:
    """
    Calcule l'impact complet du recrutement d'un candidat.

    Args:
        candidate_snapshot: psychometric_snapshot du candidat
        current_crew_snapshots: snapshots de l'équipe actuellement à bord
        vessel_params: paramètres JD-R depuis vessel_snapshot
        captain_vector: vecteur leadership du capitaine
        betas: betas du ModelVersion actif
    """
    # 1. Score Ŷ_success
    score: RecruitmentScore = compute_y_success(
        candidate_snapshot=candidate_snapshot,
        current_crew_snapshots=current_crew_snapshots,
        vessel_params=vessel_params,
        captain_vector=captain_vector,
        betas=betas,
    )

    # 2. Delta F_team détaillé (avant / après)
    team_delta = compute_harmony_delta(
        current_snapshots=current_crew_snapshots,
        candidate_snapshot=candidate_snapshot,
    )

    # 3. Niveau de confiance selon la complétude des données
    confidence = _get_confidence_label(score.completeness)

    return ImpactReport(
        y_success_predicted=score.y_success,
        p_ind=score.p_ind,
        f_team=score.f_team,
        f_env=score.f_env,
        f_lmx=score.f_lmx,

        f_team_delta=team_delta["f_team_delta"],
        jerk_filter_delta=team_delta["jerk_filter_delta"],
        faultline_risk_delta=team_delta["faultline_risk_delta"],
        emotional_buffer_delta=team_delta["emotional_buffer_delta"],
        performance_delta=team_delta["performance_delta"],

        flags=team_delta["flags"],
        data_completeness=score.completeness,
        confidence_label=confidence,
    )


def _get_confidence_label(completeness: float) -> str:
    if completeness >= 0.85:
        return "HIGH — Prédiction fiable"
    elif completeness >= 0.60:
        return "MEDIUM — Données partielles, prédiction indicative"
    else:
        return "LOW — Compléter le profil psychométrique pour une prédiction valide"