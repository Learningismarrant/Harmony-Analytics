# engine/recruitment/master.py
"""
MLPSM — Multi-Level Predictive Stability Model
Équation maîtresse du moteur de recrutement Harmony.

Ŷ_success = β₁·P_ind + β₂·F_team + β₃·F_env + β₄·F_lmx + ε

Architecture :
    master.py orchestre les 4 sous-modules.
    Chaque sous-module est indépendant, testable séparément,
    et retourne une dataclass riche exploitable par les services.

    ┌──────────────────────────────────────────────────────┐
    │                   MASTER.PY                          │
    │                                                      │
    │  candidate_snapshot ──► p_ind.compute()             │
    │                         └─► PIndResult              │
    │                                                      │
    │  [crew_snapshots + candidate] ──► f_team.compute()  │
    │                         └─► FTeamResult             │
    │                                                      │
    │  candidate_snapshot + vessel_params ──► f_env()     │
    │                         └─► FEnvResult              │
    │                                                      │
    │  candidate_snapshot + captain_vector ──► f_lmx()   │
    │                         └─► FLmxResult              │
    │                                                      │
    │  Ŷ = β₁·P + β₂·FT + β₃·FE + β₄·FL                 │
    │  └─► MLPSMResult (tout consolidé)                   │
    └──────────────────────────────────────────────────────┘

Règle des betas :
    Temps 1 — priors littérature (DEFAULT_BETAS)
    Temps 2 — régression sur RecruitmentEvents avec y_actual renseigné
    Le service injecte les betas depuis ModelVersion.get_active_model_betas()

Règles d'architecture :
    - Zéro accès DB dans ce fichier (ni dans les sous-modules)
    - Toutes les données arrivent via les snapshots hydratés par le service
    - Le résultat MLPSMResult est sérialisable (pour RecruitmentEvent)
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Optional

from app.engine.recruitment.MLPSM import p_ind as _p_ind
from  app.engine.recruitment.MLPSM import f_team as _f_team
from app.engine.recruitment.MLPSM import f_env as _f_env
from app.engine.recruitment.MLPSM import f_lmx as _f_lmx
from app.engine.recruitment.MLPSM.p_ind  import PIndResult
from app.engine.recruitment.MLPSM.f_team import FTeamResult
from app.engine.recruitment.MLPSM.f_env  import FEnvResult
from app.engine.recruitment.MLPSM.f_lmx  import FLmxResult


# ── Betas par défaut (priors littérature — Temps 1) ──────────────────────────

DEFAULT_BETAS: Dict[str, float] = {
    "b1_p_ind":  0.25,   # Performance individuelle — Schmidt & Hunter (1998)
    "b2_f_team": 0.35,   # Compatibilité équipe — dominant en yachting (isolement)
    "b3_f_env":  0.20,   # Compatibilité environnement JD-R
    "b4_f_lmx":  0.20,   # Compatibilité leadership Captain's Shadow
}


# ── Labels de confiance selon la qualité des données ─────────────────────────

def _confidence_label(data_quality: float) -> str:
    if data_quality >= 0.85:
        return "HIGH"
    elif data_quality >= 0.60:
        return "MEDIUM"
    else:
        return "LOW"


def _success_label(score: float) -> str:
    if score >= 75:
        return "STRONG_FIT"
    elif score >= 60:
        return "GOOD_FIT"
    elif score >= 45:
        return "MODERATE_FIT"
    else:
        return "POOR_FIT"


# ── Dataclass de résultat consolidé ───────────────────────────────────────────

@dataclass
class MLPSMResult:
    """
    Résultat complet du MLPSM pour un candidat sur un yacht donné.

    ── Scores ──────────────────────────────────────────────────────────────────
    y_success    → score final Ŷ (0-100), stocké dans RecruitmentEvent
    p_ind_score  → sous-score P_ind (0-100)
    f_team_score → sous-score F_team (0-100)
    f_env_score  → sous-score F_env (0-100)
    f_lmx_score  → sous-score F_lmx (0-100)

    ── Détails complets de chaque sous-module ──────────────────────────────────
    p_ind_detail  → PIndResult  (GCA, C, experience)
    f_team_detail → FTeamResult (jerk filter, faultline, emotional buffer, delta)
    f_env_detail  → FEnvResult  (ressources, demandes, ratio JD-R, résilience)
    f_lmx_detail  → FLmxResult  (vecteurs, distance, écart par dimension)

    ── Meta ────────────────────────────────────────────────────────────────────
    betas_used    → snapshot des betas utilisés (versioning RecruitmentEvent)
    data_quality  → qualité globale des données (moyenne pondérée des 4 sous-modules)
    confidence    → "HIGH" | "MEDIUM" | "LOW"
    success_label → "STRONG_FIT" | "GOOD_FIT" | "MODERATE_FIT" | "POOR_FIT"
    all_flags     → tous les avertissements de tous les sous-modules
    formula_snapshot → equation résolue avec valeurs numériques (audit/debug)
    """
    # Scores principaux
    y_success:    float
    p_ind_score:  float
    f_team_score: float
    f_env_score:  float
    f_lmx_score:  float

    # Détails complets (accès direct aux sous-mesures)
    p_ind_detail:  PIndResult
    f_team_detail: FTeamResult
    f_env_detail:  FEnvResult
    f_lmx_detail:  FLmxResult

    # Meta
    betas_used:       Dict[str, float] = field(default_factory=lambda: DEFAULT_BETAS.copy())
    data_quality:     float = 1.0
    confidence:       str = "HIGH"
    success_label:    str = "GOOD_FIT"
    all_flags:        List[str] = field(default_factory=list)
    formula_snapshot: str = ""

    def to_event_snapshot(self) -> Dict:
        """
        Sérialise les données nécessaires pour stocker dans RecruitmentEvent.
        Ne contient pas les détails internes (allège le JSON en DB).
        """
        return {
            "y_success_predicted": self.y_success,
            "p_ind_score":         self.p_ind_score,
            "f_team_score":        self.f_team_score,
            "f_env_score":         self.f_env_score,
            "f_lmx_score":         self.f_lmx_score,
            "beta_weights_snapshot": self.betas_used,
            "data_quality":        self.data_quality,
            "confidence":          self.confidence,
            "flags_summary":       self.all_flags[:10],  # Cap à 10 flags en DB
        }

    def to_impact_report(self) -> Dict:
        """
        Rapport What-If structuré — exposé par l'endpoint /impact.
        Inclut les deltas F_team si compute_with_delta() a été appelé.
        """
        delta = self.f_team_detail.delta

        return {
            "y_success_predicted": self.y_success,
            "success_label":       self.success_label,
            "confidence":          self.confidence,
            "data_quality":        round(self.data_quality * 100),

            "scores": {
                "p_ind":  {"value": self.p_ind_score,  "weight": self.betas_used["b1_p_ind"]},
                "f_team": {"value": self.f_team_score, "weight": self.betas_used["b2_f_team"]},
                "f_env":  {"value": self.f_env_score,  "weight": self.betas_used["b3_f_env"]},
                "f_lmx":  {"value": self.f_lmx_score,  "weight": self.betas_used["b4_f_lmx"]},
            },

            "team_impact": {
                "f_team_before":          delta.f_team_before if delta else None,
                "f_team_after":           delta.f_team_after if delta else None,
                "delta":                  delta.delta if delta else None,
                "net_impact":             delta.net_impact if delta else None,
                "jerk_filter_delta":      delta.jerk_filter_delta if delta else None,
                "faultline_risk_delta":   delta.faultline_risk_delta if delta else None,
                "emotional_buffer_delta": delta.emotional_buffer_delta if delta else None,
            },

            "environment": {
                "jdr_ratio":         self.f_env_detail.jdr_ratio.raw_ratio,
                "jdr_status":        self.f_env_detail.jdr_ratio.equilibrium_status,
                "resilience":        self.f_env_detail.resilience.resilience_raw,
            },

            "leadership": {
                "compatibility_label": self.f_lmx_detail.distance.compatibility_label,
                "normalized_distance": self.f_lmx_detail.distance.normalized_distance,
                "dimension_gaps": [
                    {
                        "dimension":   d.dimension,
                        "gap":         d.gap,
                        "direction":   d.gap_direction,
                        "label":       d.gap_label,
                    }
                    for d in self.f_lmx_detail.dimensions
                ],
            },

            "flags": self.all_flags,
            "formula": self.formula_snapshot,
        }


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    candidate_snapshot: Dict,
    current_crew_snapshots: List[Dict],
    vessel_params: Dict,
    captain_vector: Dict,
    betas: Optional[Dict[str, float]] = None,
    experience_years: int = 0,
    position_key: Optional[str] = None,
) -> MLPSMResult:
    """
    Calcule le score de succès prédit pour un candidat sur un yacht donné.
    Mode standard : F_team calculé avec le candidat intégré (score post-recrutement).

    Args:
        candidate_snapshot      : CrewProfile.psychometric_snapshot
        current_crew_snapshots  : liste des snapshots de l'équipe actuelle
        vessel_params           : vessel_snapshot["jdr_params"]
        captain_vector          : Yacht.captain_leadership_vector
        betas                   : betas actifs depuis ModelVersion (DEFAULT_BETAS si None)
        experience_years        : CrewProfile.experience_years
        position_key            : YachtPosition.value (réservé Temps 2)

    Returns:
        MLPSMResult complet — scores + détails de chaque sous-module
    """
    betas = betas or DEFAULT_BETAS

    # ── 1. P_ind ─────────────────────────────────────────────
    p_ind_result = _p_ind.compute(
        candidate_snapshot,
        experience_years=experience_years,
        position_key=position_key,
    )

    # ── 2. F_team (avec candidat intégré) ────────────────────
    all_snapshots = current_crew_snapshots + [candidate_snapshot]
    f_team_result = _f_team.compute(all_snapshots)

    # ── 3. F_env ──────────────────────────────────────────────
    f_env_result = _f_env.compute(candidate_snapshot, vessel_params)

    # ── 4. F_lmx ──────────────────────────────────────────────
    f_lmx_result = _f_lmx.compute(candidate_snapshot, captain_vector)

    # ── 5. Équation maîtresse ─────────────────────────────────
    return _aggregate(
        p_ind_result, f_team_result, f_env_result, f_lmx_result, betas
    )


def compute_with_delta(
    candidate_snapshot: Dict,
    current_crew_snapshots: List[Dict],
    vessel_params: Dict,
    captain_vector: Dict,
    betas: Optional[Dict[str, float]] = None,
    experience_years: int = 0,
    position_key: Optional[str] = None,
) -> MLPSMResult:
    """
    Variante avec calcul du delta F_team (impact marginal du candidat).
    Utiliser pour le rapport What-If et le simulateur.

    Différence avec compute() :
        f_team_detail.delta est renseigné avec FTeamDelta
        (f_team_before, f_team_after, delta par dimension)

    Usage typique :
        result = master.compute_with_delta(...)
        delta = result.f_team_detail.delta.delta  # +/- impact global
        report = result.to_impact_report()         # Rapport complet
    """
    betas = betas or DEFAULT_BETAS

    p_ind_result  = _p_ind.compute(candidate_snapshot, experience_years, position_key)
    f_team_result = _f_team.compute_delta(current_crew_snapshots, candidate_snapshot)
    f_env_result  = _f_env.compute(candidate_snapshot, vessel_params)
    f_lmx_result  = _f_lmx.compute(candidate_snapshot, captain_vector)

    return _aggregate(
        p_ind_result, f_team_result, f_env_result, f_lmx_result, betas
    )


# ── Agrégation interne ────────────────────────────────────────────────────────

def _aggregate(
    p_ind_result:  PIndResult,
    f_team_result: FTeamResult,
    f_env_result:  FEnvResult,
    f_lmx_result:  FLmxResult,
    betas: Dict[str, float],
) -> MLPSMResult:
    """
    Applique l'équation maîtresse et consolide tous les résultats.
    """
    p  = p_ind_result.score
    ft = f_team_result.score
    fe = f_env_result.score
    fl = f_lmx_result.score

    b1 = betas["b1_p_ind"]
    b2 = betas["b2_f_team"]
    b3 = betas["b3_f_env"]
    b4 = betas["b4_f_lmx"]

    y_raw = (b1 * p) + (b2 * ft) + (b3 * fe) + (b4 * fl)
    y_success = round(max(0.0, min(100.0, y_raw)), 1)

    # ── Qualité globale des données ───────────────────────────
    # Moyenne pondérée par les betas (le sous-module le plus influent
    # a plus d'impact sur la confiance globale)
    total_beta = b1 + b2 + b3 + b4
    data_quality = round(
        (b1 * p_ind_result.data_quality
         + b2 * f_team_result.data_quality
         + b3 * f_env_result.data_quality
         + b4 * f_lmx_result.data_quality) / total_beta,
        3,
    )

    # ── Consolidation des flags ───────────────────────────────
    all_flags: List[str] = []
    for module_name, result in [
        ("[P_ind]",  p_ind_result),
        ("[F_team]", f_team_result),
        ("[F_env]",  f_env_result),
        ("[F_lmx]",  f_lmx_result),
    ]:
        for flag in result.flags:
            all_flags.append(f"{module_name} {flag}")

    # ── Formula snapshot ──────────────────────────────────────
    formula = (
        f"Ŷ = {b1}×{p} + {b2}×{ft} + {b3}×{fe} + {b4}×{fl}"
        f" = {b1*p:.1f} + {b2*ft:.1f} + {b3*fe:.1f} + {b4*fl:.1f}"
        f" = {y_raw:.1f} → {y_success}"
    )

    return MLPSMResult(
        y_success=y_success,
        p_ind_score=p,
        f_team_score=ft,
        f_env_score=fe,
        f_lmx_score=fl,
        p_ind_detail=p_ind_result,
        f_team_detail=f_team_result,
        f_env_detail=f_env_result,
        f_lmx_detail=f_lmx_result,
        betas_used=betas.copy(),
        data_quality=data_quality,
        confidence=_confidence_label(data_quality),
        success_label=_success_label(y_success),
        all_flags=all_flags,
        formula_snapshot=formula,
    )


# ── Utilitaire : batch scoring ────────────────────────────────────────────────

def compute_batch(
    candidates: List[Dict],   # [{"snapshot": ..., "experience_years": ..., "position_key": ...}]
    current_crew_snapshots: List[Dict],
    vessel_params: Dict,
    captain_vector: Dict,
    betas: Optional[Dict[str, float]] = None,
    with_delta: bool = False,
) -> List[MLPSMResult]:
    """
    Score un batch de candidats sur le même yacht.
    Utile pour le matching en campagne : tous les candidats notés en une passe.

    Args:
        candidates  : liste de dicts avec {"snapshot", "experience_years", "position_key"}
        with_delta  : si True, calcule compute_with_delta() pour chaque candidat

    Returns:
        Liste de MLPSMResult, dans le même ordre que candidates.
        Triée par y_success décroissant si nécessaire côté service.
    """
    fn = compute_with_delta if with_delta else compute
    results = []

    for candidate in candidates:
        result = fn(
            candidate_snapshot=candidate["snapshot"],
            current_crew_snapshots=current_crew_snapshots,
            vessel_params=vessel_params,
            captain_vector=captain_vector,
            betas=betas,
            experience_years=candidate.get("experience_years", 0),
            position_key=candidate.get("position_key"),
        )
        results.append(result)

    return results