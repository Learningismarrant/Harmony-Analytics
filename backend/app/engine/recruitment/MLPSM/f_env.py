# engine/recruitment/f_env.py
"""
F_env — Compatibilité Environnementale (Job Demands-Resources Model)

Mesure l'adéquation entre les ressources du yacht et ses exigences,
pondérée par la capacité du candidat à absorber le stress résiduel.

Formule de base (Temps 1) :
    F_env = (R_yacht / D_yacht) × Resilience_ind

    R_yacht = ressources du yacht (salaire, repos, intimité)
    D_yacht = demandes du yacht   (intensité charters, pression management)
    Resilience_ind = capacité individuelle à gérer la pression

    Interprétation du ratio JD-R :
    ┌──────────────┬──────────────────────────────────────────┐
    │ Ratio < 0.5  │ Demandes >> Ressources → burnout risk   │
    │ Ratio ~ 1.0  │ Équilibre J-R                           │
    │ Ratio > 1.5  │ Ressources >> Demandes → confort élevé  │
    └──────────────┴──────────────────────────────────────────┘

    La résilience individuelle module le ratio :
    - Candidat résilient (ES élevée) tolère un ratio < 1 sans burnout
    - Candidat fragile (ES faible) a besoin d'un ratio > 1 pour tenir

Évolution Temps 2 :
    - Intégration des observed_scores du vessel_snapshot
      (workload_felt des surveys valide ou invalide la prédiction JD-R)
    - Pondérations R_yacht par poste (le Chef a besoin de plus d'espace
      personnel qu'un deckhand — private_cabin_ratio plus important)
    - Modèle d'adaptation : ajustement selon durée d'embarquement prévue
    - Facteur saisonnalité (charter haute saison vs basse saison)

Sources académiques :
    Bakker, A.B. & Demerouti, E. (2007). The Job Demands-Resources
    model: State of the art. Journal of Managerial Psychology, 22(3).

    Schaufeli, W.B. & Taris, T.W. (2014). A Critical Review of the
    JD-R Model. Bridging Occupational and Organizational Psychology.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Optional


# ── Pondérations des ressources yacht ────────────────────────────────────────

# Ressources (R_yacht) — ce que le yacht offre
W_SALARY_INDEX       = 0.40   # Rémunération — prédicteur engagement le plus fort
W_REST_DAYS_RATIO    = 0.35   # Jours de repos — critique pour le burnout marin
W_PRIVATE_CABIN      = 0.25   # Espace privé — essentiel en isolement prolongé

# Demandes (D_yacht) — ce que le yacht exige
W_CHARTER_INTENSITY  = 0.60   # Intensité charters — charge opérationnelle principale
W_MANAGEMENT_PRESSURE = 0.40  # Pression management — charge émotionnelle / relationnelle

# Cap du ratio JD-R (évite les outliers si ressources >> demandes)
JDR_RATIO_CAP = 2.0

# Seuils d'alerte
BURNOUT_RISK_THRESHOLD   = 0.40   # Ratio JD-R en-dessous = risque burnout
COMFORT_THRESHOLD        = 1.50   # Ratio JD-R au-dessus = environnement confortable
RESILIENCE_LOW_THRESHOLD = 40.0   # En-dessous = candidat vulnérable à l'environnement


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class ResourcesDetail:
    """
    Détail des ressources du yacht (R_yacht).
    Chaque valeur est normalisée 0.0-1.0.
    """
    salary_index: float
    rest_days_ratio: float
    private_cabin_ratio: float
    r_yacht: float              # Score agrégé pondéré 0.0-1.0


@dataclass
class DemandsDetail:
    """
    Détail des demandes du yacht (D_yacht).
    Chaque valeur est normalisée 0.0-1.0.
    """
    charter_intensity: float
    management_pressure: float
    d_yacht: float              # Score agrégé pondéré 0.0-1.0


@dataclass
class JDRRatioDetail:
    """
    Ratio ressources / demandes et son interprétation.
    """
    raw_ratio: float            # R_yacht / D_yacht (non cappé)
    capped_ratio: float         # Cappé à JDR_RATIO_CAP
    equilibrium_status: str     # "BURNOUT_RISK" | "BALANCED" | "COMFORTABLE"
    equilibrium_score: float    # Score 0-100 dérivé du ratio


@dataclass
class ResilienceDetail:
    """
    Détail de la résilience individuelle du candidat.
    Sert de modulateur du ratio JD-R.
    """
    resilience_raw: float       # Score brut 0-100 (depuis snapshot)
    resilience_norm: float      # Normalisé 0.0-1.0
    source: str = ""            # "snapshot.resilience" | "big_five.ES" | "fallback"
    is_low: bool = False


@dataclass
class FEnvResult:
    """
    Résultat complet du calcul F_env.

    score        → valeur finale 0-100, injectée dans l'équation maîtresse
    resources    → détail R_yacht (3 sous-dimensions)
    demands      → détail D_yacht (2 sous-dimensions)
    jdr_ratio    → ratio et interprétation de l'équilibre
    resilience   → modulateur individuel
    data_quality → 0.0-1.0
    flags        → alertes détectées (burnout_risk, données manquantes...)
    """
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
    Extrait la résilience depuis le psychometric_snapshot.

    Priorité :
    1. snapshot.resilience (valeur dédiée si test résilience passé)
    2. snapshot.emotional_stability (proxy — ES ≈ tolérance au stress)
    3. 100 - neuroticism (fallback Big Five)
    4. 50.0 (médiane — dernier recours avec flag)
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

    # 2. Stabilité émotionnelle comme proxy
    es = candidate_snapshot.get("emotional_stability")
    if es is None:
        bf = candidate_snapshot.get("big_five") or {}
        es_raw = bf.get("emotional_stability") or bf.get("neuroticism")
        if es_raw is not None:
            # Si c'est neuroticism, on inverse
            key = "neuroticism" if "neuroticism" in bf else "emotional_stability"
            val = bf.get(key)
            if isinstance(val, dict):
                val = val.get("score", 50.0)
            es = (100.0 - float(val)) if key == "neuroticism" else float(val)

    if es is not None:
        val = float(es)
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
    """
    Extrait les paramètres JD-R depuis le vessel_params.
    vessel_params = vessel_snapshot.jdr_params (alimenté par vessel/repository)
    Toutes les valeurs sont attendues normalisées 0.0-1.0.
    """
    # Ressources
    salary      = vessel_params.get("salary_index", 0.5)
    rest        = vessel_params.get("rest_days_ratio", 0.5)
    cabin       = vessel_params.get("private_cabin_ratio", 0.5)

    r_yacht = (salary * W_SALARY_INDEX) + (rest * W_REST_DAYS_RATIO) + (cabin * W_PRIVATE_CABIN)

    resources = ResourcesDetail(
        salary_index=float(salary),
        rest_days_ratio=float(rest),
        private_cabin_ratio=float(cabin),
        r_yacht=round(r_yacht, 4),
    )

    # Demandes
    charter  = vessel_params.get("charter_intensity", 0.5)
    pressure = vessel_params.get("management_pressure", 0.5)

    d_yacht = (charter * W_CHARTER_INTENSITY) + (pressure * W_MANAGEMENT_PRESSURE)
    d_yacht = max(d_yacht, 0.01)  # éviter division par zéro

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

    Args:
        candidate_snapshot : psychometric_snapshot du CrewProfile
        vessel_params      : paramètres JD-R du yacht
                             Extrait de vessel_snapshot["jdr_params"] :
                             {
                               "salary_index": 0.7,
                               "rest_days_ratio": 0.6,
                               "private_cabin_ratio": 0.5,
                               "charter_intensity": 0.8,
                               "management_pressure": 0.5
                             }
                             Si vessel_params vide → données manquantes, fallback à 0.5

    Returns:
        FEnvResult avec score final et détail de chaque dimension.
    """
    flags: list[str] = []
    data_quality = 1.0

    # ── Données manquantes ────────────────────────────────────
    if not vessel_params:
        flags.append("NO_VESSEL_PARAMS: paramètres JD-R absents, fallback à l'équilibre (0.5)")
        data_quality -= 0.40
        vessel_params = {}

    if not candidate_snapshot.get("resilience") and not candidate_snapshot.get("emotional_stability"):
        big_five = candidate_snapshot.get("big_five") or {}
        if not big_five.get("neuroticism") and not big_five.get("emotional_stability"):
            flags.append("RESILIENCE_MISSING: aucun proxy de résilience disponible, médiane utilisée")
            data_quality -= 0.25

    # ── 1. Extraction ────────────────────────────────────────
    resources, demands = _extract_jdr_params(vessel_params)
    resilience = _extract_resilience(candidate_snapshot)

    if resilience.is_low:
        flags.append(f"LOW_RESILIENCE: résilience à {resilience.resilience_raw:.1f} < {RESILIENCE_LOW_THRESHOLD}")

    # ── 2. Ratio JD-R ─────────────────────────────────────────
    raw_ratio   = resources.r_yacht / demands.d_yacht
    capped_ratio = min(raw_ratio, JDR_RATIO_CAP)

    # Interprétation du ratio
    if raw_ratio < BURNOUT_RISK_THRESHOLD:
        status = "BURNOUT_RISK"
        flags.append(f"BURNOUT_RISK: ratio JD-R = {raw_ratio:.2f} (demandes >> ressources)")
    elif raw_ratio >= COMFORT_THRESHOLD:
        status = "COMFORTABLE"
    else:
        status = "BALANCED"

    # Score 0-100 depuis le ratio cappé
    equilibrium_score = (capped_ratio / JDR_RATIO_CAP) * 100.0

    jdr_detail = JDRRatioDetail(
        raw_ratio=round(raw_ratio, 3),
        capped_ratio=round(capped_ratio, 3),
        equilibrium_status=status,
        equilibrium_score=round(equilibrium_score, 1),
    )

    # ── 3. Modulation par la résilience ──────────────────────
    # Un candidat résilient compense un ratio JD-R défavorable
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