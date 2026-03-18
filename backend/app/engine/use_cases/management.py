"""
Use Case : Management — monitoring équipe existante
Dimensions actives : P-T (baseline équipe entière) + P-S (LMX par membre)
Pas de P-J (déjà recrutés), pas de Safety barrier, pas de centile
Output : santé d'équipe + alertes individuelles + recommandations

Références :
    Bell, B.S. (2007). Journal of Applied Psychology, 92(2).
    Graen, G.B. & Uhl-Bien, M. (1995). Leadership Quarterly, 6(2).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.use_cases._base import (
    ConfidenceLevel,
    UseCaseAlert,
    _confidence_from_quality,
)
from app.engine.pe_fit.pt_fit import f_team as _pt
from app.engine.pe_fit.ps_fit import f_lmx as _ps
from app.engine.pe_fit.pt_fit.weights import (
    JERK_FILTER_DANGER,
    FAULTLINE_DANGER,
    ES_MINIMUM_THRESHOLD,
)


# ── Seuils santé équipe ───────────────────────────────────────────────────────

_HEALTHY_THRESHOLD  = 65.0
_AT_RISK_THRESHOLD  = 45.0

# Seuils LMX
_LMX_EXCELLENT_THRESHOLD = 75.0
_LMX_GOOD_THRESHOLD      = 55.0
_LMX_TENSION_THRESHOLD   = 35.0


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class MemberStatus:
    crew_id: Optional[int]
    ps_score: Optional[float]       # LMX avec capitaine
    ps_label: str                   # "EXCELLENT" | "GOOD" | "TENSION" | "CRITICAL"
    alerts: List[UseCaseAlert] = field(default_factory=list)


@dataclass
class ManagementResult:
    team_health_score: float        # F_team global (0-100)
    team_health_label: str          # "HEALTHY" | "AT_RISK" | "CRITICAL"
    jerk_risk: bool                 # min(A) < seuil
    faultline_risk: bool            # σ(C) > seuil
    emotional_fragility: bool       # μ(ES) < seuil
    member_statuses: List[MemberStatus]
    team_alerts: List[UseCaseAlert]
    recommendations: List[str]
    crew_size: int
    confidence: ConfidenceLevel


# ── Helpers ───────────────────────────────────────────────────────────────────

def _health_label(score: float) -> str:
    if score >= _HEALTHY_THRESHOLD:
        return "HEALTHY"
    if score >= _AT_RISK_THRESHOLD:
        return "AT_RISK"
    return "CRITICAL"


def _lmx_label(score: float) -> str:
    if score >= _LMX_EXCELLENT_THRESHOLD:
        return "EXCELLENT"
    if score >= _LMX_GOOD_THRESHOLD:
        return "GOOD"
    if score >= _LMX_TENSION_THRESHOLD:
        return "TENSION"
    return "CRITICAL"


def _build_recommendations(
    jerk_risk: bool,
    faultline_risk: bool,
    emotional_fragility: bool,
    member_statuses: List[MemberStatus],
    crew_ids: Optional[List[int]],
) -> List[str]:
    recos: List[str] = []

    if jerk_risk:
        recos.append(
            "Identifier le membre avec agréabilité la plus basse "
            "— entretien individuel recommandé"
        )

    if faultline_risk:
        recos.append(
            "Divergence d'éthique de travail détectée "
            "— clarification des standards collectifs"
        )

    if emotional_fragility:
        recos.append(
            "Vulnérabilité émotionnelle collective "
            "— surveiller charge lors de la prochaine saison charter"
        )

    for status in member_statuses:
        if status.ps_label == "CRITICAL":
            identifier = (
                f"membre #{status.crew_id}" if status.crew_id is not None else "un membre"
            )
            recos.append(
                f"Incompatibilité structurelle avec le capitaine pour {identifier} "
                "— médiation ou repositionnement"
            )

    return recos


# ── Fonction principale ───────────────────────────────────────────────────────

def run(
    crew_snapshots: List[Dict],
    captain_vector: Optional[Dict] = None,
    crew_ids: Optional[List[int]] = None,
) -> ManagementResult:
    """
    Orchestre l'analyse de santé d'une équipe existante.

    Args:
        crew_snapshots  : snapshots de toute l'équipe
        captain_vector  : vecteur leadership du capitaine (active LMX individuel)
        crew_ids        : IDs des membres pour lier les alertes (même ordre que crew_snapshots)

    Returns:
        ManagementResult avec team_health_score, alertes et recommandations
    """
    team_alerts: List[UseCaseAlert] = []

    # ── 1. F_team baseline (Bell 2007) ────────────────────────────────────────
    ft_result = _pt.compute(crew_snapshots)

    team_health_score = ft_result.score
    jerk_risk         = ft_result.jerk_filter.risk_detected
    faultline_risk    = ft_result.faultline.risk_detected
    emotional_fragility = ft_result.emotional.risk_detected

    if jerk_risk:
        team_alerts.append(UseCaseAlert(
            code="JERK_RISK",
            severity="WARNING",
            message=(
                f"Agréabilité minimale critique : "
                f"{ft_result.jerk_filter.min_agreeableness:.1f} "
                f"(seuil : {JERK_FILTER_DANGER})"
            ),
            dimension="pt",
        ))

    if faultline_risk:
        team_alerts.append(UseCaseAlert(
            code="FAULTLINE_RISK",
            severity="WARNING",
            message=(
                f"Variance de conscienciosité élevée : "
                f"σ(C) = {ft_result.faultline.sigma_conscientiousness:.1f} "
                f"(seuil : {FAULTLINE_DANGER})"
            ),
            dimension="pt",
        ))

    if emotional_fragility:
        team_alerts.append(UseCaseAlert(
            code="EMOTIONAL_FRAGILITY",
            severity="WARNING",
            message=(
                f"Fragilité émotionnelle collective : "
                f"μ(ES) = {ft_result.emotional.mean_emotional_stability:.1f} "
                f"(seuil : {ES_MINIMUM_THRESHOLD})"
            ),
            dimension="pt",
        ))

    # ── 2. LMX individuel par membre ─────────────────────────────────────────
    member_statuses: List[MemberStatus] = []

    for idx, snap in enumerate(crew_snapshots):
        crew_id = crew_ids[idx] if crew_ids and idx < len(crew_ids) else None
        member_alerts: List[UseCaseAlert] = []

        ps_score: Optional[float] = None
        ps_label = "N/A"

        if captain_vector:
            lmx_result = _ps.compute_fit(snap, captain_vector)
            if lmx_result is not None:
                ps_score = lmx_result.score
                ps_label = _lmx_label(ps_score)

                if ps_label == "CRITICAL":
                    member_alerts.append(UseCaseAlert(
                        code="LMX_CRITICAL",
                        severity="CRITICAL",
                        message=(
                            "Incompatibilité structurelle avec le style de leadership "
                            f"du capitaine (score LMX : {ps_score:.1f})"
                        ),
                        dimension="ps",
                    ))
                elif ps_label == "TENSION":
                    member_alerts.append(UseCaseAlert(
                        code="LMX_TENSION",
                        severity="WARNING",
                        message=f"Friction potentielle avec le capitaine (score LMX : {ps_score:.1f})",
                        dimension="ps",
                    ))

        member_statuses.append(MemberStatus(
            crew_id=crew_id,
            ps_score=ps_score,
            ps_label=ps_label,
            alerts=member_alerts,
        ))

    # ── 3. Recommandations ────────────────────────────────────────────────────
    recommendations = _build_recommendations(
        jerk_risk, faultline_risk, emotional_fragility, member_statuses, crew_ids
    )

    # ── 4. Confidence ────────────────────────────────────────────────────────
    confidence = _confidence_from_quality(ft_result.data_quality)

    return ManagementResult(
        team_health_score=team_health_score,
        team_health_label=_health_label(team_health_score),
        jerk_risk=jerk_risk,
        faultline_risk=faultline_risk,
        emotional_fragility=emotional_fragility,
        member_statuses=member_statuses,
        team_alerts=team_alerts,
        recommendations=recommendations,
        crew_size=len(crew_snapshots),
        confidence=confidence,
    )
