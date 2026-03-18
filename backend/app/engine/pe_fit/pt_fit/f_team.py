# engine/recruitment/pe_fit/pt_fit/f_team.py
"""
F_team — Compatibilité d'Équipe (Person-Team Fit)

Adaptation de MLPSM/f_team.py pour le sous-module pe_fit.
Les extractions de traits utilisent extract_with_fallback() depuis pe_fit.trait_extractor.

Formule :
    F_team = wₐ·min(A_i) + w_c·μ(C_i) + wₑ·μ(ES_i) - wσ·σ(C_i)

    Poids validés Bell (2007) — ρ équivalents :
        A_min=0.27, C_mean=0.27, ES_mean=0.25, σC=-0.19
    Somme des poids absolus = 1.00 :
        W_JERK_FILTER(0.30) + W_MEAN_C(0.30) + W_EMOTIONAL_BUFFER(0.28) + W_FAULTLINE_RISK(0.12)

Conserver compute() et compute_delta() avec signatures identiques à MLPSM/f_team.py.
Ajouter compute_fit() avec retour None si current_crew_snapshots absent ou vide.

Sources :
    Bell, B.S. (2007). Longitudinal relationships of personality and group performance.
        Journal of Applied Psychology, 92(2), 362-376.
    Hackman, J.R. (2002). Leading Teams. Harvard Business School Press.
    Lau, D.C. & Murnighan, J.K. (1998). Faultlines. Academy of Mgmt.
    Jordan, P.J. et al. (2002). Emotional intelligence in teams. Small Group Research.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional
import statistics

from app.engine.pe_fit.trait_extractor import extract_with_fallback, extract_strict
from app.engine.pe_fit.pt_fit.weights import (
    W_JERK_FILTER,
    W_MEAN_C,
    W_FAULTLINE_RISK,
    W_EMOTIONAL_BUFFER,
    JERK_FILTER_DANGER,
    FAULTLINE_DANGER,
    ES_MINIMUM_THRESHOLD,
    MIN_CREW_SIZE,
)


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class JerkFilterDetail:
    min_agreeableness: float
    weakest_member_position: Optional[str] = None
    scores_all: List[float] = field(default_factory=list)
    risk_detected: bool = False


@dataclass
class FaultlineRiskDetail:
    sigma_conscientiousness: float
    mean_conscientiousness: float
    scores_all: List[float] = field(default_factory=list)
    risk_detected: bool = False


@dataclass
class EmotionalBufferDetail:
    mean_emotional_stability: float
    min_emotional_stability: float
    scores_all: List[float] = field(default_factory=list)
    risk_detected: bool = False


@dataclass
class FTeamDelta:
    f_team_before: float
    f_team_after: float
    delta: float
    jerk_filter_delta: float
    faultline_risk_delta: float
    emotional_buffer_delta: float
    net_impact: str = ""


@dataclass
class FTeamResult:
    score: float
    jerk_filter: JerkFilterDetail
    faultline: FaultlineRiskDetail
    emotional: EmotionalBufferDetail
    crew_size: int = 0
    delta: Optional[FTeamDelta] = None
    data_quality: float = 1.0
    flags: list[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Extraction des inputs depuis les snapshots ────────────────────────────────

def _get_agreeableness(snapshot: Dict) -> Optional[float]:
    return extract_strict(snapshot, "agreeableness")


def _get_conscientiousness(snapshot: Dict) -> Optional[float]:
    return extract_strict(snapshot, "conscientiousness")


def _get_emotional_stability(snapshot: Dict) -> Optional[float]:
    """
    Utilise extract_strict() qui gère la dérivation emotional_stability = 100 - neuroticism.
    """
    return extract_strict(snapshot, "emotional_stability")


# ── Calcul interne ────────────────────────────────────────────────────────────

def _compute_from_snapshots(snapshots: List[Dict]) -> tuple[FTeamResult, list[str]]:
    flags: list[str] = []
    data_quality = 1.0

    agreeableness_scores: list[float]    = []
    conscientiousness_scores: list[float] = []
    es_scores: list[float]               = []

    for snap in snapshots:
        a = _get_agreeableness(snap)
        c = _get_conscientiousness(snap)
        e = _get_emotional_stability(snap)

        if a is not None:
            agreeableness_scores.append(a)
        if c is not None:
            conscientiousness_scores.append(c)
        if e is not None:
            es_scores.append(e)

    n = len(snapshots)
    missing = []
    if len(agreeableness_scores) < n:
        missing.append("agreeableness")
        data_quality -= 0.15
    if len(conscientiousness_scores) < n:
        missing.append("conscientiousness")
        data_quality -= 0.15
    if len(es_scores) < n:
        missing.append("emotional_stability")
        data_quality -= 0.10
    if missing:
        flags.append(f"PARTIAL_DATA: {', '.join(missing)} manquant(s) pour certains membres")

    # Fallback valeurs médianes
    while len(agreeableness_scores) < n:
        agreeableness_scores.append(50.0)
    while len(conscientiousness_scores) < n:
        conscientiousness_scores.append(50.0)
    while len(es_scores) < n:
        es_scores.append(50.0)

    # Jerk Filter (modèle disjonctif)
    min_a = min(agreeableness_scores)
    jerk_risk = min_a < JERK_FILTER_DANGER
    if jerk_risk:
        flags.append(f"JERK_RISK: agréabilité minimale à {min_a:.1f} (seuil: {JERK_FILTER_DANGER})")

    jerk_detail = JerkFilterDetail(
        min_agreeableness=min_a,
        scores_all=agreeableness_scores,
        risk_detected=jerk_risk,
    )

    # Faultline Risk (variance conscienciosité)
    sigma_c = statistics.stdev(conscientiousness_scores) if len(conscientiousness_scores) > 1 else 0.0
    mean_c  = statistics.mean(conscientiousness_scores)
    fl_risk = sigma_c > FAULTLINE_DANGER
    if fl_risk:
        flags.append(
            f"FAULTLINE_RISK: σ(C) = {sigma_c:.1f} > {FAULTLINE_DANGER} (conflits standards)"
        )

    faultline_detail = FaultlineRiskDetail(
        sigma_conscientiousness=sigma_c,
        mean_conscientiousness=mean_c,
        scores_all=conscientiousness_scores,
        risk_detected=fl_risk,
    )

    # Emotional Buffer (modèle additif)
    mean_es = statistics.mean(es_scores)
    min_es  = min(es_scores)
    es_risk = mean_es < ES_MINIMUM_THRESHOLD
    if es_risk:
        flags.append(f"EMOTIONAL_FRAGILITY: μ(ES) = {mean_es:.1f} < {ES_MINIMUM_THRESHOLD}")

    emotional_detail = EmotionalBufferDetail(
        mean_emotional_stability=mean_es,
        min_emotional_stability=min_es,
        scores_all=es_scores,
        risk_detected=es_risk,
    )

    # Calcul F_team — Bell (2007) : A_min + μ(C) + μ(ES) - σ(C)
    sigma_c_norm = min(sigma_c / 35.0, 1.0) * 100.0
    f_team_raw = (
        (min_a         * W_JERK_FILTER)
        + (mean_c        * W_MEAN_C)
        + (mean_es       * W_EMOTIONAL_BUFFER)
        - (sigma_c_norm  * W_FAULTLINE_RISK)
    )
    score = round(max(0.0, min(100.0, f_team_raw)), 1)

    formula = (
        f"F_team = ({min_a:.1f}×{W_JERK_FILTER})"
        f" + ({mean_c:.1f}×{W_MEAN_C})"
        f" + ({mean_es:.1f}×{W_EMOTIONAL_BUFFER})"
        f" - ({sigma_c_norm:.1f}×{W_FAULTLINE_RISK})"
        f" = {f_team_raw:.1f} → {score}"
    )

    result = FTeamResult(
        score=score,
        jerk_filter=jerk_detail,
        faultline=faultline_detail,
        emotional=emotional_detail,
        crew_size=n,
        data_quality=max(0.0, data_quality),
        flags=flags,
        formula_snapshot=formula,
    )
    return result, flags


# ── Points d'entrée publics ───────────────────────────────────────────────────

def compute(
    all_snapshots: List[Dict],
) -> FTeamResult:
    """
    Calcule F_team pour une équipe donnée (candidat inclus dans la liste).

    Signature identique à MLPSM/f_team.compute().

    Args:
        all_snapshots : liste des psychometric_snapshot de TOUS les membres

    Returns:
        FTeamResult avec score final et détail des 3 sous-composantes.
    """
    if len(all_snapshots) < MIN_CREW_SIZE:
        return FTeamResult(
            score=50.0,
            jerk_filter=JerkFilterDetail(min_agreeableness=50.0),
            faultline=FaultlineRiskDetail(
                sigma_conscientiousness=0.0,
                mean_conscientiousness=50.0,
            ),
            emotional=EmotionalBufferDetail(
                mean_emotional_stability=50.0,
                min_emotional_stability=50.0,
            ),
            crew_size=len(all_snapshots),
            data_quality=0.5,
            flags=["CREW_TOO_SMALL: moins de 2 membres, F_team non significatif (50.0 par défaut)"],
        )

    result, _ = _compute_from_snapshots(all_snapshots)
    return result


def compute_delta(
    current_crew_snapshots: List[Dict],
    candidate_snapshot: Dict,
) -> FTeamResult:
    """
    Calcule l'impact MARGINAL du candidat sur l'équipe existante.

    Signature identique à MLPSM/f_team.compute_delta().

    Args:
        current_crew_snapshots : snapshots de l'équipe actuelle (sans candidat)
        candidate_snapshot     : snapshot du candidat

    Returns:
        FTeamResult avec .delta renseigné.
    """
    if len(current_crew_snapshots) >= MIN_CREW_SIZE:
        result_before, _ = _compute_from_snapshots(current_crew_snapshots)
        score_before = result_before.score
    else:
        score_before = 50.0

    all_snapshots = current_crew_snapshots + [candidate_snapshot]
    result_after, _ = _compute_from_snapshots(all_snapshots)
    score_after = result_after.score

    if len(current_crew_snapshots) >= MIN_CREW_SIZE:
        jf_delta = (
            result_after.jerk_filter.min_agreeableness
            - result_before.jerk_filter.min_agreeableness
        )
        fl_delta = (
            result_after.faultline.sigma_conscientiousness
            - result_before.faultline.sigma_conscientiousness
        )
        eb_delta = (
            result_after.emotional.mean_emotional_stability
            - result_before.emotional.mean_emotional_stability
        )
    else:
        jf_delta = fl_delta = eb_delta = 0.0

    global_delta = score_after - score_before
    if global_delta > 3.0:
        net = "POSITIVE"
    elif global_delta < -3.0:
        net = "NEGATIVE"
    else:
        net = "NEUTRAL"

    result_after.delta = FTeamDelta(
        f_team_before=score_before,
        f_team_after=score_after,
        delta=round(global_delta, 1),
        jerk_filter_delta=round(jf_delta, 1),
        faultline_risk_delta=round(fl_delta, 1),
        emotional_buffer_delta=round(eb_delta, 1),
        net_impact=net,
    )

    if global_delta > 5.0:
        result_after.flags.append(f"TEAM_POSITIVE_IMPACT: +{global_delta:.1f} sur F_team")
    elif global_delta < -5.0:
        result_after.flags.append(f"TEAM_NEGATIVE_IMPACT: {global_delta:.1f} sur F_team")

    return result_after


def compute_baseline(
    current_crew_snapshots: List[Dict],
) -> FTeamResult:
    """
    Évalue la santé de l'équipe actuelle sans candidat.
    Alias sémantique de compute() — résultats identiques.

    Args:
        current_crew_snapshots : snapshots de l'équipe actuelle

    Returns:
        FTeamResult identique à compute(current_crew_snapshots)
    """
    return compute(current_crew_snapshots)


def compute_fit(
    snapshot: Dict,
    current_crew_snapshots: list[Dict] | None = None,
) -> Optional[FTeamResult]:
    """
    Retourne None si équipe trop petite (< 1 membre).

    Args:
        snapshot               : psychometric_snapshot du candidat
        current_crew_snapshots : snapshots de l'équipe actuelle (sans candidat)

    Returns:
        FTeamResult ou None
    """
    if not current_crew_snapshots:
        return None
    all_snaps = current_crew_snapshots + [snapshot]
    return compute(all_snaps)
