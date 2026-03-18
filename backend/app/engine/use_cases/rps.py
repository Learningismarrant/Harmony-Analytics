"""
Use Case : Risques Psychosociaux (RPS)
Dimensions actives : N-S fit (JDR) + P-T (monitoring) + P-S (LMX)
Pas de P-J D-A (déjà recrutés et performants), pas de Safety barrier
Output : niveau de risque global + facteurs déclencheurs + recommandations

Le scoring RPS inverse le NS fit : plus les ressources sont faibles et les
demandes élevées, plus le risque de burnout est fort. Le PT monitoring
détecte les risques de friction collective, et le PS fit (LMX) identifie
les incompatibilités managériales.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from app.engine.use_cases._base import (
    ConfidenceLevel,
    UseCaseAlert,
    _confidence_from_quality,
)
from app.engine.pe_fit.pj_fit.needs_supplies import jdr as _jdr
from app.engine.pe_fit.pt_fit import f_team as _pt
from app.engine.pe_fit.ps_fit import f_lmx as _ps
from app.engine.pe_fit.pt_fit.weights import (
    JERK_FILTER_DANGER,
    FAULTLINE_DANGER,
)


# ── Seuils de risque ─────────────────────────────────────────────────────────

_CRITICAL_RISK_THRESHOLD = 75.0
_HIGH_RISK_THRESHOLD     = 55.0
_MODERATE_RISK_THRESHOLD = 35.0

# Seuils LMX critique (score LMX bas = fort risque)
_LMX_CRITICAL_THRESHOLD = 35.0   # score LMX < 35 → critique

# Malus de risque pour les signaux PT
_JERK_RISK_MALUS     = 15.0
_FAULTLINE_RISK_MALUS = 10.0


# ── Enums et dataclasses ──────────────────────────────────────────────────────

class RiskLevel(str, Enum):
    LOW      = "LOW"       # aucun signal
    MODERATE = "MODERATE"  # 1-2 signaux ADVISORY
    HIGH     = "HIGH"      # 1+ signal WARNING ou 3+ ADVISORY
    CRITICAL = "CRITICAL"  # signal CRITICAL ou combinaison sévère


@dataclass
class MemberRisk:
    crew_id: Optional[int]
    burnout_risk_score: float   # NS fit inversé (100 - ns_score)
    lmx_score: Optional[float]
    risk_factors: List[str]     # facteurs déclencheurs pour ce membre


@dataclass
class RpsResult:
    global_risk_level: RiskLevel
    team_risk_score: float          # 0-100 (higher = more risk)
    member_risks: List[MemberRisk]
    active_risk_factors: List[str]  # facteurs au niveau équipe
    alerts: List[UseCaseAlert]
    recommendations: List[str]
    confidence: ConfidenceLevel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _ns_to_burnout_risk(ns_score: Optional[float]) -> float:
    """Inverse le NS fit : score burnout = 100 - NS fit."""
    if ns_score is None:
        return 50.0  # fallback médian (absence de données = risque inconnu)
    return round(100.0 - ns_score, 1)


def _classify_risk(
    team_risk_score: float,
    critical_lmx_count: int,
) -> RiskLevel:
    """
    Classification :
    - CRITICAL si score ≥ 75 OU ps_label CRITICAL sur ≥ 2 membres
    - HIGH si score ≥ 55 OU ps_label CRITICAL sur 1 membre
    - MODERATE si score ≥ 35
    - LOW sinon
    """
    if team_risk_score >= _CRITICAL_RISK_THRESHOLD or critical_lmx_count >= 2:
        return RiskLevel.CRITICAL
    if team_risk_score >= _HIGH_RISK_THRESHOLD or critical_lmx_count == 1:
        return RiskLevel.HIGH
    if team_risk_score >= _MODERATE_RISK_THRESHOLD:
        return RiskLevel.MODERATE
    return RiskLevel.LOW


def _build_rps_recommendations(
    global_risk: RiskLevel,
    jerk_risk: bool,
    faultline_risk: bool,
    critical_lmx_count: int,
    member_risks: List[MemberRisk],
) -> List[str]:
    recos: List[str] = []

    if global_risk in (RiskLevel.HIGH, RiskLevel.CRITICAL):
        recos.append(
            "Évaluation RPS approfondie recommandée avant la prochaine saison charter"
        )

    if jerk_risk:
        recos.append(
            "Conflit latent détecté — entretien individuel avec le membre le plus hostile"
        )

    if faultline_risk:
        recos.append(
            "Divergence d'éthique de travail — réunion de recadrage des standards collectifs"
        )

    if critical_lmx_count >= 1:
        recos.append(
            "Incompatibilité(s) managériale(s) — médiation entre capitaine et membres concernés"
        )

    # Membres à haut risque de burnout
    high_burnout = [m for m in member_risks if m.burnout_risk_score >= 65.0]
    if high_burnout:
        count = len(high_burnout)
        recos.append(
            f"{count} membre(s) à risque élevé de burnout — "
            "révision de la charge de travail et des ressources"
        )

    return recos


# ── Fonction principale ───────────────────────────────────────────────────────

def run(
    crew_snapshots: List[Dict],
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    crew_ids: Optional[List[int]] = None,
) -> RpsResult:
    """
    Évalue le niveau de risque psychosocial de l'équipe.

    Args:
        crew_snapshots  : snapshots de toute l'équipe
        vessel_params   : paramètres JD-R du yacht (active N-S fit pour chaque membre)
        captain_vector  : vecteur leadership du capitaine (active PS fit)
        crew_ids        : IDs des membres (même ordre que crew_snapshots)

    Returns:
        RpsResult avec global_risk_level et recommandations
    """
    alerts: List[UseCaseAlert] = []
    active_risk_factors: List[str] = []
    member_risks: List[MemberRisk] = []

    # ── 1. PT monitoring (risques collectifs) ─────────────────────────────────
    ft_result = _pt.compute(crew_snapshots)
    jerk_risk     = ft_result.jerk_filter.risk_detected
    faultline_risk = ft_result.faultline.risk_detected
    emotional_fragility = ft_result.emotional.risk_detected

    if jerk_risk:
        active_risk_factors.append(
            f"JERK_RISK: A_min={ft_result.jerk_filter.min_agreeableness:.1f} "
            f"< {JERK_FILTER_DANGER}"
        )
        alerts.append(UseCaseAlert(
            code="JERK_RISK",
            severity="WARNING",
            message=f"Agréabilité minimale critique : {ft_result.jerk_filter.min_agreeableness:.1f}",
            dimension="pt",
        ))

    if faultline_risk:
        active_risk_factors.append(
            f"FAULTLINE_RISK: σ(C)={ft_result.faultline.sigma_conscientiousness:.1f} "
            f"> {FAULTLINE_DANGER}"
        )
        alerts.append(UseCaseAlert(
            code="FAULTLINE_RISK",
            severity="WARNING",
            message=(
                f"Fracture d'équipe potentielle : "
                f"σ(C) = {ft_result.faultline.sigma_conscientiousness:.1f}"
            ),
            dimension="pt",
        ))

    if emotional_fragility:
        active_risk_factors.append(
            f"EMOTIONAL_FRAGILITY: μ(ES)={ft_result.emotional.mean_emotional_stability:.1f}"
        )
        alerts.append(UseCaseAlert(
            code="EMOTIONAL_FRAGILITY",
            severity="WARNING",
            message=(
                f"Fragilité émotionnelle collective : "
                f"μ(ES) = {ft_result.emotional.mean_emotional_stability:.1f}"
            ),
            dimension="pt",
        ))

    # ── 2. Risques individuels (NS fit + LMX) ─────────────────────────────────
    individual_risk_scores: List[float] = []
    critical_lmx_count = 0

    for idx, snap in enumerate(crew_snapshots):
        crew_id = crew_ids[idx] if crew_ids and idx < len(crew_ids) else None
        risk_factors_member: List[str] = []

        # N-S Fit (burnout risk)
        ns_score: Optional[float] = None
        if vessel_params:
            jdr_result = _jdr.compute(snap, vessel_params)
            if jdr_result is not None:
                ns_score = jdr_result.score
                if jdr_result.buffer.equilibrium_status == "BURNOUT_RISK":
                    risk_factors_member.append(
                        f"BURNOUT_RISK: NS_fit={ns_score:.1f} "
                        f"(overload={jdr_result.buffer.overload_factor:.2f})"
                    )

        burnout_risk_score = _ns_to_burnout_risk(ns_score)
        individual_risk_scores.append(burnout_risk_score)

        # LMX (incompatibilité managériale)
        lmx_score: Optional[float] = None
        if captain_vector:
            lmx_result = _ps.compute_fit(snap, captain_vector)
            if lmx_result is not None:
                lmx_score = lmx_result.score
                if lmx_result.distance.compatibility_label == "CRITICAL":
                    risk_factors_member.append(
                        f"LMX_CRITICAL: score={lmx_score:.1f}"
                    )
                    critical_lmx_count += 1
                    alerts.append(UseCaseAlert(
                        code="LMX_CRITICAL",
                        severity="CRITICAL",
                        message=(
                            f"Incompatibilité managériale critique pour membre "
                            f"#{crew_id if crew_id is not None else idx} "
                            f"(score LMX : {lmx_score:.1f})"
                        ),
                        dimension="ps",
                    ))

        member_risks.append(MemberRisk(
            crew_id=crew_id,
            burnout_risk_score=burnout_risk_score,
            lmx_score=lmx_score,
            risk_factors=risk_factors_member,
        ))

    # ── 3. Team risk score ────────────────────────────────────────────────────
    if individual_risk_scores:
        base_risk = sum(individual_risk_scores) / len(individual_risk_scores)
    else:
        base_risk = 50.0

    # Malus pour risques collectifs PT
    malus = 0.0
    if jerk_risk:
        malus += _JERK_RISK_MALUS
    if faultline_risk:
        malus += _FAULTLINE_RISK_MALUS

    team_risk_score = round(min(100.0, base_risk + malus), 1)

    # ── 4. Niveau de risque global ────────────────────────────────────────────
    global_risk = _classify_risk(team_risk_score, critical_lmx_count)

    # ── 5. Recommandations ────────────────────────────────────────────────────
    recommendations = _build_rps_recommendations(
        global_risk, jerk_risk, faultline_risk, critical_lmx_count, member_risks
    )

    # ── 6. Confidence ────────────────────────────────────────────────────────
    has_vessel = bool(vessel_params)
    has_captain = bool(captain_vector)
    has_psychometric = bool(crew_snapshots and (
        crew_snapshots[0].get("big_five") or crew_snapshots[0].get("emotional_stability")
    ))

    data_quality = sum([has_vessel, has_captain, has_psychometric]) / 3.0
    confidence = _confidence_from_quality(data_quality)

    return RpsResult(
        global_risk_level=global_risk,
        team_risk_score=team_risk_score,
        member_risks=member_risks,
        active_risk_factors=active_risk_factors,
        alerts=alerts,
        recommendations=recommendations,
        confidence=confidence,
    )
