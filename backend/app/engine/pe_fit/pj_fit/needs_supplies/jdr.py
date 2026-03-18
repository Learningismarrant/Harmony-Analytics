"""
P-J Fit — Needs-Supplies sub-dimension
Modèle JD-R (Bakker & Demerouti, 2007) reformulé comme buffer effect.

Formule :
    NS_fit = (R_score / 100) × (1 - overload_factor) × resilience_modulator × 100

    R_score         = score de ressources pondéré (0-100)
    overload_factor = activation du buffer quand demandes > capacité individuelle
                      = sigmoid(k · (D_score - resilience_threshold))
                      k = 0.12, threshold = resilience individuelle (ou 50.0)
    resilience_modulator = resilience / 100

Différence vs ancienne formulation (ratio linéaire) :
    L'ancien R/D ratio sous-estimait l'effet non-linéaire des demands élevées
    en environnement ICE (Palinkas & Suedfeld, 2008 ; Bakker et al., 2005).
    Le buffer effect : les ressources modèrent l'effet des demands, mais
    au-delà du seuil de résilience individuelle, les demands deviennent
    dominantes de façon accélérée.

Sources :
    Bakker, A.B., & Demerouti, E. (2007). The Job Demands-Resources model.
        Journal of Managerial Psychology, 22(3), 309-328.
    Bakker, A.B., et al. (2005). Job resources buffer the impact of job demands
        on burnout. Journal of Vocational Behavior, 65(1), 1-17.
    Edwards, J.R. (1991). Person-job fit. International Review of I/O Psychology, 6.
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.trait_extractor import extract_with_fallback

# ── Poids ressources ──────────────────────────────────────────────────────────
W_SALARY_INDEX     = 0.40
W_REST_DAYS_RATIO  = 0.35
W_PRIVATE_CABIN    = 0.25

# ── Poids demandes ────────────────────────────────────────────────────────────
W_CHARTER_INTENSITY    = 0.60
W_MANAGEMENT_PRESSURE  = 0.40

# ── Paramètres buffer ─────────────────────────────────────────────────────────
BUFFER_K              = 0.12    # pente de la sigmoïde d'activation
BURNOUT_RISK_THRESHOLD = 0.40   # overload_factor > 0.40 → BURNOUT_RISK
COMFORT_THRESHOLD     = 0.15   # overload_factor < 0.15 → COMFORTABLE
RESILIENCE_FALLBACK   = 50.0


@dataclass
class ResourceScore:
    raw: float
    salary_contrib: float
    rest_contrib: float
    cabin_contrib: float


@dataclass
class DemandScore:
    raw: float
    charter_contrib: float
    management_contrib: float


@dataclass
class BufferEffect:
    overload_factor: float          # sigmoid activation [0, 1]
    resilience_threshold: float     # seuil individuel
    equilibrium_status: str         # "COMFORTABLE" | "BALANCED" | "BURNOUT_RISK"


@dataclass
class JDRResult:
    score: float                    # NS_fit ∈ [0, 100]
    resources: ResourceScore
    demands: DemandScore
    buffer: BufferEffect
    resilience_raw: float
    resilience_source: str
    data_quality: float
    flags: List[str] = field(default_factory=list)
    formula_snapshot: str = ""


def _sigmoid(x: float, k: float) -> float:
    try:
        return 1.0 / (1.0 + math.exp(-k * x))
    except OverflowError:
        return 0.0 if x < 0 else 1.0


def compute(
    candidate_snapshot: Dict,
    vessel_params: Optional[Dict] = None,
) -> Optional["JDRResult"]:
    """
    Calcule le N-S P-J Fit via le modèle JD-R avec buffer effect.
    Retourne None si vessel_params absent (dimension non calculable).
    """
    if not vessel_params:
        return None

    flags: List[str] = []
    missing_params = 0
    total_params = 5

    def _get(key: str, default: float) -> tuple[float, bool]:
        v = vessel_params.get(key)
        if v is None:
            return default, True
        return float(v), False

    salary_idx, m1    = _get("salary_index", 0.5)
    rest_days,  m2    = _get("rest_days_ratio", 0.5)
    cabin,      m3    = _get("private_cabin_ratio", 0.5)
    charter,    m4    = _get("charter_intensity", 0.5)
    mgmt_press, m5    = _get("management_pressure", 0.5)

    for missing, name in [(m1,"salary_index"),(m2,"rest_days_ratio"),
                          (m3,"private_cabin_ratio"),(m4,"charter_intensity"),
                          (m5,"management_pressure")]:
        if missing:
            missing_params += 1
            flags.append(f"FALLBACK_{name.upper()}: valeur par défaut 0.5 utilisée")

    # Scores ressources et demandes [0-100]
    r_raw = (W_SALARY_INDEX * salary_idx + W_REST_DAYS_RATIO * rest_days + W_PRIVATE_CABIN * cabin) * 100
    d_raw = (W_CHARTER_INTENSITY * charter + W_MANAGEMENT_PRESSURE * mgmt_press) * 100

    # Résilience individuelle (seuil buffer)
    resilience_val = candidate_snapshot.get("resilience")
    resilience_source = "snapshot.resilience"
    if resilience_val is None:
        es_val = candidate_snapshot.get("emotional_stability")
        if es_val is None:
            bf = candidate_snapshot.get("big_five") or {}
            n = bf.get("neuroticism")
            if n is not None:
                n_score = n.get("score", n) if isinstance(n, dict) else n
                resilience_val = 100.0 - float(n_score)
                resilience_source = "big_five.neuroticism_derived"
            else:
                resilience_val = RESILIENCE_FALLBACK
                resilience_source = "fallback_median"
                flags.append("FALLBACK_RESILIENCE: score médian 50.0 utilisé")
        else:
            resilience_val = float(es_val)
            resilience_source = "snapshot.emotional_stability"
    else:
        resilience_val = float(resilience_val)

    resilience_threshold = float(resilience_val)

    # Buffer effect : sigmoid centré sur le seuil de résilience individuelle
    # overload_factor augmente quand D_score dépasse le seuil de résilience
    overload_factor = _sigmoid(d_raw - resilience_threshold, BUFFER_K)

    # NS_fit = ressources × (1 - overload) × résilience_modulator
    resilience_mod = resilience_val / 100.0
    ns_fit_raw = (r_raw / 100.0) * (1.0 - overload_factor) * resilience_mod * 100.0
    score = round(max(0.0, min(100.0, ns_fit_raw)), 1)

    # Statut d'équilibre
    if overload_factor > BURNOUT_RISK_THRESHOLD:
        status = "BURNOUT_RISK"
        flags.append(f"BURNOUT_RISK: overload_factor={overload_factor:.2f} > {BURNOUT_RISK_THRESHOLD}")
    elif overload_factor < COMFORT_THRESHOLD:
        status = "COMFORTABLE"
    else:
        status = "BALANCED"

    data_quality = round(1.0 - (missing_params / total_params), 3)

    formula = (
        f"NS_fit = ({r_raw:.1f}/100) × (1 - {overload_factor:.3f}) "
        f"× ({resilience_val:.1f}/100) × 100 = {score}"
    )

    return JDRResult(
        score=score,
        resources=ResourceScore(
            raw=round(r_raw, 1),
            salary_contrib=round(W_SALARY_INDEX * salary_idx * 100, 1),
            rest_contrib=round(W_REST_DAYS_RATIO * rest_days * 100, 1),
            cabin_contrib=round(W_PRIVATE_CABIN * cabin * 100, 1),
        ),
        demands=DemandScore(
            raw=round(d_raw, 1),
            charter_contrib=round(W_CHARTER_INTENSITY * charter * 100, 1),
            management_contrib=round(W_MANAGEMENT_PRESSURE * mgmt_press * 100, 1),
        ),
        buffer=BufferEffect(
            overload_factor=round(overload_factor, 4),
            resilience_threshold=round(resilience_threshold, 1),
            equilibrium_status=status,
        ),
        resilience_raw=round(resilience_val, 1),
        resilience_source=resilience_source,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )
