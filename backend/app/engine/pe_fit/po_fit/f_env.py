# engine/recruitment/pe_fit/po_fit/f_env.py
# DÉPRÉCIÉ — JD-R déplacé dans pj_fit/needs_supplies/jdr.py (P-J N-S Fit)
# Ce fichier est conservé pour la rétrocompatibilité (po_fit/f_env reste importable).
"""
F_env — Compatibilité Environnementale (Person-Organization Fit)

Adaptation de MLPSM/f_env.py pour le sous-module pe_fit.
Les extractions de traits utilisent extract_with_fallback() depuis pe_fit.trait_extractor.

Formule :
    F_env = (R_yacht / D_yacht) × Resilience_ind × 100  (cappé à 100)

Conserver compute() avec signature identique à MLPSM/f_env.py.
Ajouter compute_fit() avec retour None gracieux si vessel_params absent.

Sources :
    Bakker, A.B. & Demerouti, E. (2007). The Job Demands-Resources model.
    Journal of Managerial Psychology, 22(3).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional

from app.engine.pe_fit.trait_extractor import extract_with_fallback, extract_strict
from app.engine.pe_fit.po_fit.weights import (
    W_SALARY_INDEX,
    W_REST_DAYS_RATIO,
    W_PRIVATE_CABIN,
    W_CHARTER_INTENSITY,
    W_MANAGEMENT_PRESSURE,
    JDR_RATIO_CAP,
    BURNOUT_RISK_THRESHOLD,
    COMFORT_THRESHOLD,
    RESILIENCE_LOW_THRESHOLD,
)


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class ResourcesDetail:
    salary_index: float
    rest_days_ratio: float
    private_cabin_ratio: float
    r_yacht: float


@dataclass
class DemandsDetail:
    charter_intensity: float
    management_pressure: float
    d_yacht: float


@dataclass
class JDRRatioDetail:
    raw_ratio: float
    capped_ratio: float
    equilibrium_status: str
    equilibrium_score: float


@dataclass
class ResilienceDetail:
    resilience_raw: float
    resilience_norm: float
    source: str = ""
    is_low: bool = False


@dataclass
class FEnvResult:
    score: float
    resources: ResourcesDetail
    demands: DemandsDetail
    jdr_ratio: JDRRatioDetail
    resilience: ResilienceDetail
    data_quality: float = 1.0
    flags: list[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Extraction des inputs ─────────────────────────────────────────────────────

def _extract_resilience(candidate_snapshot: Dict) -> ResilienceDetail:
    """
    Extrait la résilience via extract_with_fallback().

    Ordre :
    1. snapshot.resilience
    2. snapshot.emotional_stability / big_five.emotional_stability
    3. 100 - big_five.neuroticism
    4. fallback 50.0
    """
    # 1. Score résilience dédié
    resilience = candidate_snapshot.get("resilience")
    if resilience is not None:
        val = float(resilience)
        return ResilienceDetail(
            resilience_raw=val,
            resilience_norm=val / 100.0,
            source="snapshot.resilience",
            is_low=val < RESILIENCE_LOW_THRESHOLD,
        )

    # 2. Stabilité émotionnelle — top-level, big_five.emotional_stability, ou 100-neuroticism
    es_val = candidate_snapshot.get("emotional_stability")
    if es_val is None:
        big_five = candidate_snapshot.get("big_five") or {}
        bf_es = big_five.get("emotional_stability")
        if bf_es is not None:
            es_val = float(bf_es.get("score", bf_es) if isinstance(bf_es, dict) else bf_es)
        elif big_five.get("neuroticism") is not None:
            es_val = extract_strict(candidate_snapshot, "emotional_stability")

    if es_val is not None:
        val = float(es_val)
        return ResilienceDetail(
            resilience_raw=val,
            resilience_norm=val / 100.0,
            source="big_five.emotional_stability",
            is_low=val < RESILIENCE_LOW_THRESHOLD,
        )

    # 3. Fallback médiane
    return ResilienceDetail(
        resilience_raw=50.0,
        resilience_norm=0.50,
        source="fallback_median",
        is_low=False,
    )


def _extract_jdr_params(vessel_params: Dict) -> tuple[ResourcesDetail, DemandsDetail]:
    salary  = vessel_params.get("salary_index", 0.5)
    rest    = vessel_params.get("rest_days_ratio", 0.5)
    cabin   = vessel_params.get("private_cabin_ratio", 0.5)

    r_yacht = (salary * W_SALARY_INDEX) + (rest * W_REST_DAYS_RATIO) + (cabin * W_PRIVATE_CABIN)

    resources = ResourcesDetail(
        salary_index=float(salary),
        rest_days_ratio=float(rest),
        private_cabin_ratio=float(cabin),
        r_yacht=round(r_yacht, 4),
    )

    charter  = vessel_params.get("charter_intensity", 0.5)
    pressure = vessel_params.get("management_pressure", 0.5)

    d_yacht = (charter * W_CHARTER_INTENSITY) + (pressure * W_MANAGEMENT_PRESSURE)
    d_yacht = max(d_yacht, 0.01)

    demands = DemandsDetail(
        charter_intensity=float(charter),
        management_pressure=float(pressure),
        d_yacht=round(d_yacht, 4),
    )

    return resources, demands


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    vessel_params: Dict,
) -> FEnvResult:
    """
    Calcule F_env pour un candidat sur un yacht donné.

    Signature identique à MLPSM/f_env.compute().

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        vessel_params      : paramètres JD-R du yacht

    Returns:
        FEnvResult avec score final et détail de chaque dimension.
    """
    flags: list[str] = []
    data_quality = 1.0

    if not vessel_params:
        flags.append("NO_VESSEL_PARAMS: paramètres JD-R absents, fallback à l'équilibre (0.5)")
        data_quality -= 0.40
        vessel_params = {}

    # Vérification résilience disponible
    resilience_raw = candidate_snapshot.get("resilience")
    es_raw = candidate_snapshot.get("emotional_stability")
    big_five = candidate_snapshot.get("big_five") or {}
    if resilience_raw is None and es_raw is None:
        if not big_five.get("neuroticism") and not big_five.get("emotional_stability"):
            flags.append("RESILIENCE_MISSING: aucun proxy de résilience disponible, médiane utilisée")
            data_quality -= 0.25

    # Extraction
    resources, demands = _extract_jdr_params(vessel_params)
    resilience = _extract_resilience(candidate_snapshot)

    if resilience.is_low:
        flags.append(
            f"LOW_RESILIENCE: résilience à {resilience.resilience_raw:.1f} < {RESILIENCE_LOW_THRESHOLD}"
        )

    # Ratio JD-R
    raw_ratio    = resources.r_yacht / demands.d_yacht
    capped_ratio = min(raw_ratio, JDR_RATIO_CAP)

    if raw_ratio < BURNOUT_RISK_THRESHOLD:
        status = "BURNOUT_RISK"
        flags.append(f"BURNOUT_RISK: ratio JD-R = {raw_ratio:.2f} (demandes >> ressources)")
    elif raw_ratio >= COMFORT_THRESHOLD:
        status = "COMFORTABLE"
    else:
        status = "BALANCED"

    equilibrium_score = (capped_ratio / JDR_RATIO_CAP) * 100.0

    jdr_detail = JDRRatioDetail(
        raw_ratio=round(raw_ratio, 3),
        capped_ratio=round(capped_ratio, 3),
        equilibrium_status=status,
        equilibrium_score=round(equilibrium_score, 1),
    )

    # Modulation par la résilience
    f_env_raw = (capped_ratio / JDR_RATIO_CAP) * resilience.resilience_norm * 100.0
    score = round(max(0.0, min(100.0, f_env_raw)), 1)

    formula = (
        f"F_env = (R={resources.r_yacht:.3f} / D={demands.d_yacht:.3f})"
        f" × Resilience={resilience.resilience_norm:.2f}"
        f" = {raw_ratio:.2f} → cappé {capped_ratio:.2f}"
        f" → {f_env_raw:.1f} → {score}"
    )

    return FEnvResult(
        score=score,
        resources=resources,
        demands=demands,
        jdr_ratio=jdr_detail,
        resilience=resilience,
        data_quality=max(0.0, data_quality),
        flags=flags,
        formula_snapshot=formula,
    )


def compute_fit(
    snapshot: Dict,
    vessel_params: Dict | None = None,
) -> Optional[FEnvResult]:
    """
    Retourne None si vessel_params est None ou vide.

    Args:
        snapshot      : psychometric_snapshot du CrewProfile
        vessel_params : paramètres JD-R du yacht (None → retourne None)

    Returns:
        FEnvResult ou None
    """
    if not vessel_params:
        return None
    return compute(snapshot, vessel_params)
