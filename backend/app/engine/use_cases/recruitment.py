"""
Use Case : Recrutement
Dimensions actives : P-J (D-A + N-S + motivation) + P-T (delta) + P-S + Safety
Output : décision HIRE/CONDITIONAL/DISQUALIFY + score de fit global + centile pool

La décision prend en compte la safety barrier en premier (non-compensatoire),
puis le score global agrégé des dimensions disponibles.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.use_cases._base import (
    ConfidenceLevel,
    DataAvailability,
    UseCaseAlert,
    _build_data_availability,
    _confidence_from_quality,
)
from app.engine.pe_fit.pj_fit import scorer as _pj_scorer
from app.engine.pe_fit.pt_fit import f_team as _pt
from app.engine.pe_fit.ps_fit import f_lmx as _ps
from app.engine.pe_fit.pj_fit.safety_barrier import SafetyLevel


# ── Seuils de décision ────────────────────────────────────────────────────────

_HIRE_THRESHOLD       = 65.0
_DISQUALIFY_THRESHOLD = 45.0


# ── Dataclass de résultat ─────────────────────────────────────────────────────

@dataclass
class RecruitmentResult:
    decision: str                   # "HIRE" | "CONDITIONAL" | "DISQUALIFY"
    global_fit_score: float         # moyenne pondérée des dimensions disponibles
    centile: Optional[float]        # centile vs pool (None si pool < 2)
    centile_label: str
    pj_score: float                 # D-A fit
    ns_score: Optional[float]       # N-S fit (JDR)
    motivation_score: Optional[float]
    pt_delta: Optional[float]       # impact marginal sur l'équipe (delta F_team)
    ps_score: Optional[float]       # PS fit (LMX)
    safety_level: str               # "CLEAR" | "ADVISORY" | "HIGH_RISK" | "DISQUALIFIED"
    alerts: List[UseCaseAlert]      = field(default_factory=list)
    data_availability: DataAvailability = field(default_factory=lambda: DataAvailability(
        has_psychometric=False, has_cognitive=False, has_motivation=False,
        has_vessel_params=False, has_captain_vector=False, has_crew_snapshots=False,
        completeness=0.0,
    ))
    confidence: ConfidenceLevel     = ConfidenceLevel.LOW
    dimensions_used: List[str]      = field(default_factory=list)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _centile_label(centile: Optional[float]) -> str:
    if centile is None:
        return "N/A"
    if centile >= 90:
        return "Top 10%"
    if centile >= 75:
        return "Top 25%"
    if centile >= 50:
        return "Above median"
    if centile >= 25:
        return "Below median"
    return "Bottom 25%"


def _decide(global_fit_score: float, safety_level: str) -> str:
    """
    Logique de décision :
    - DISQUALIFY si safety_level == "DISQUALIFIED"
    - DISQUALIFY si global_fit_score < 45
    - HIRE si global_fit_score >= 65 et safety_level in ("CLEAR", "ADVISORY")
    - CONDITIONAL sinon (score 45-65, ou HIGH_RISK)
    """
    if safety_level == "DISQUALIFIED":
        return "DISQUALIFY"
    if global_fit_score < _DISQUALIFY_THRESHOLD:
        return "DISQUALIFY"
    if global_fit_score >= _HIRE_THRESHOLD and safety_level in ("CLEAR", "ADVISORY"):
        return "HIRE"
    return "CONDITIONAL"


# ── Fonction principale ───────────────────────────────────────────────────────

def run(
    candidate_snapshot: Dict,
    position: str,
    pool: List[Dict],
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    current_crew_snapshots: Optional[List[Dict]] = None,
    sme_weights: Optional[Dict] = None,
    experience_years: int = 0,
) -> RecruitmentResult:
    """
    Orchestre le calcul de fit pour un recrutement.

    Args:
        candidate_snapshot      : psychometric_snapshot du candidat
        position                : YachtPosition.value (ex: "Captain")
        pool                    : liste de snapshots des autres candidats pour le centile
        vessel_params           : paramètres JD-R du yacht (active N-S fit)
        captain_vector          : vecteur leadership du capitaine (active PS fit)
        current_crew_snapshots  : snapshots de l'équipe actuelle (active PT delta)
        sme_weights             : poids SME C1 personnalisés
        experience_years        : années d'expérience du candidat

    Returns:
        RecruitmentResult avec décision HIRE / CONDITIONAL / DISQUALIFY
    """
    alerts: List[UseCaseAlert] = []
    dimensions_used: List[str] = []
    scores_for_global: List[float] = []

    # ── 1. PJ-Fit (D-A + optionnel N-S + motivation) ─────────────────────────
    # Le pool pour centile : dict {idx: snapshot}
    pool_dict: Optional[Dict[str, Dict]] = None
    if pool and len(pool) >= 2:
        pool_dict = {str(i): s for i, s in enumerate(pool)}

    pj_result = _pj_scorer.compute(
        snapshot=candidate_snapshot,
        position=position,
        pool=pool_dict,
        sme_weights=sme_weights,
        experience_years=experience_years,
        vessel_params=vessel_params,
    )

    pj_score = pj_result.score
    ns_score = pj_result.ns_fit_score
    motivation_score = pj_result.motivation_score
    safety = pj_result.safety

    dimensions_used.append("pj")
    scores_for_global.append(pj_score)

    if ns_score is not None:
        dimensions_used.append("ns")
        scores_for_global.append(ns_score)

    if motivation_score is not None:
        dimensions_used.append("motivation")
        scores_for_global.append(motivation_score)

    # Centile
    centile_val: Optional[float] = pj_result.centile
    centile_lbl = _centile_label(centile_val)

    # Safety level
    safety_level_str = safety.safety_level.value if safety else "CLEAR"

    # Alertes safety
    if safety and safety.triggers:
        for trigger in safety.triggers:
            severity = "CRITICAL" if trigger.veto_type.value == "HARD" else "WARNING"
            alerts.append(UseCaseAlert(
                code=f"SAFETY_{trigger.trait.upper()}",
                severity=severity,
                message=trigger.label,
                dimension="pj",
            ))

    # ── 2. PT delta (impact marginal) ────────────────────────────────────────
    pt_delta: Optional[float] = None
    if current_crew_snapshots:
        pt_result = _pt.compute_delta(current_crew_snapshots, candidate_snapshot)
        if pt_result.delta is not None:
            pt_delta = pt_result.delta.delta
            dimensions_used.append("pt")
            # Le delta PT est un impact marginal, pas un score absolu —
            # on l'intègre comme un bonus/malus sur le score global
            # Normalisation : delta ∈ [-100, +100] → contribution ∈ [0, 100]
            pt_normalized = max(0.0, min(100.0, 50.0 + pt_delta))
            scores_for_global.append(pt_normalized)

            if pt_result.delta.net_impact == "NEGATIVE":
                alerts.append(UseCaseAlert(
                    code="PT_NEGATIVE_IMPACT",
                    severity="WARNING",
                    message=f"Le candidat dégrade le F_team de {abs(pt_delta):.1f} points",
                    dimension="pt",
                ))
            if pt_result.jerk_filter.risk_detected:
                alerts.append(UseCaseAlert(
                    code="JERK_RISK",
                    severity="WARNING",
                    message=(
                        f"Agréabilité minimale de l'équipe après intégration : "
                        f"{pt_result.jerk_filter.min_agreeableness:.1f}"
                    ),
                    dimension="pt",
                ))

    # ── 3. PS fit (LMX) ───────────────────────────────────────────────────────
    ps_score: Optional[float] = None
    if captain_vector:
        ps_result = _ps.compute_fit(candidate_snapshot, captain_vector)
        if ps_result is not None:
            ps_score = ps_result.score
            dimensions_used.append("ps")
            scores_for_global.append(ps_score)

            if ps_result.distance.compatibility_label == "CRITICAL":
                alerts.append(UseCaseAlert(
                    code="LMX_CRITICAL",
                    severity="CRITICAL",
                    message=(
                        "Incompatibilité structurelle avec le style de leadership du capitaine "
                        f"(distance normalisée : {ps_result.distance.normalized_distance:.2f})"
                    ),
                    dimension="ps",
                ))
            elif ps_result.distance.compatibility_label == "TENSION":
                alerts.append(UseCaseAlert(
                    code="LMX_TENSION",
                    severity="WARNING",
                    message="Friction probable avec le style de management du capitaine",
                    dimension="ps",
                ))

    # ── 4. Score global agrégé (moyenne simple des dimensions disponibles) ────
    global_fit_score = round(sum(scores_for_global) / len(scores_for_global), 1)

    # ── 5. Décision ───────────────────────────────────────────────────────────
    decision = _decide(global_fit_score, safety_level_str)

    # ── 6. Confidence ─────────────────────────────────────────────────────────
    data_avail = _build_data_availability(
        candidate_snapshot,
        vessel_params=vessel_params,
        captain_vector=captain_vector,
        crew_snapshots=current_crew_snapshots,
    )
    confidence = _confidence_from_quality(data_avail.completeness)

    return RecruitmentResult(
        decision=decision,
        global_fit_score=global_fit_score,
        centile=centile_val,
        centile_label=centile_lbl,
        pj_score=pj_score,
        ns_score=ns_score,
        motivation_score=motivation_score,
        pt_delta=pt_delta,
        ps_score=ps_score,
        safety_level=safety_level_str,
        alerts=alerts,
        data_availability=data_avail,
        confidence=confidence,
        dimensions_used=dimensions_used,
    )
