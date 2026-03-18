# pe_fit/master.py
"""
PE Fit — Person-Environment Fit Aggregator

Agrège les sept dimensions du fit candidat-environnement selon le
référentiel théorique Harmony Analytics v0.7 (cadre P-E fit, Kristof-Brown 2005).

Taxonomie et pondérations (document de référence §5.3) :
    Famille 1+2 — PJ fit D-A   (Person-Job / Demands-Abilities)     0.28
    Famille 2   — PJ fit N-S   (Person-Job / Needs-Supplies / JD-R) 0.25
    Famille 3   — PO fit       (Person-Organization)                 0.18  ← PENDING
    Famille 4   — PG fit       (Person-Group / Bell 2007)            0.16
    Famille 5   — PS fit       (Person-Supervisor / LMX)             0.13
    Famille 6   — Fit physique-environnemental                       0.05
    Famille 7   — Fit mobilité-temporel                              0.05

global_score = Σ(w_i × score_i) / Σ(w_i pour dimensions disponibles)

Les dimensions "disponibles" sont celles dont l'input n'est pas None.
La renormalisation est automatique : un score de 75 avec 5 dimensions vaut
"75 sur les 5 dimensions mesurées", pondérées selon leurs poids respectifs.

Statut PO fit :
    La dimension PO fit (congruence de valeurs / CES) est implémentée en Famille 3.
    Elle contribue au global_score avec un poids de 0.18.
    Le module po_fit/f_env (legacy JDR / F_env) est conservé pour la rétrocompatibilité
    et le reporting détaillé, mais ne contribue PAS au global_score car il est
    conceptuellement identique au N-S fit déjà comptabilisé via pj_fit.ns_fit_score.

Sécurité :
    is_disqualified est propagé depuis PJ Fit (barrière non-compensatoire).

Aliases MLPSM (compatibilité) :
    Ce module expose _sigmoid_transform, SIGMOID_CENTER, SIGMOID_SCALE.

Architecture :
    - Zéro accès DB (pur calcul sur snapshots)
    - Chaque sous-module peut retourner None si données absentes
    - PEFitResult est sérialisable (to_matching_row / to_impact_report)

Sources :
    Kristof-Brown, A.L., Zimmerman, R.D., & Johnson, E.C. (2005).
        Consequences of individuals' fit at work. Personnel Psychology, 58, 281–342.
    Document de référence Harmony Analytics v0.7, §5.3.
"""
from __future__ import annotations
import math as _math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.pj_fit import scorer as _pj_scorer
from app.engine.pe_fit.po_fit import f_env as _po_fit
from app.engine.pe_fit.po_fit import f_values as _po_values_fit
from app.engine.pe_fit.pt_fit import f_team as _pt_fit
from app.engine.pe_fit.ps_fit import f_lmx as _ps_fit
from app.engine.pe_fit.physical_fit import f_physical as _physical_fit
from app.engine.pe_fit.mobility_fit import f_mobility as _mobility_fit

from app.engine.pe_fit.pj_fit.scorer import PJFitResult
from app.engine.pe_fit.po_fit.f_env import FEnvResult
from app.engine.pe_fit.po_fit.f_values import POValuesResult
from app.engine.pe_fit.pt_fit.f_team import FTeamResult
from app.engine.pe_fit.ps_fit.f_lmx import FLmxResult
from app.engine.pe_fit.physical_fit.f_physical import FPhysicalResult
from app.engine.pe_fit.mobility_fit.f_mobility import FMobilityResult
from app.engine.pe_fit.pj_fit.safety_barrier import SafetyLevel


# ── Pondérations globales (document de référence §5.3) ────────────────────────

DIMENSION_WEIGHTS: Dict[str, float] = {
    "da_fit":         0.28,   # D-A fit  — pj_fit.score
    "ns_fit":         0.25,   # N-S fit  — pj_fit.ns_fit_score (JD-R)
    "po_values_fit":  0.18,   # PO fit   — po_values_fit.score (congruence valeurs / CES)
    "pg_fit":         0.16,   # PG fit   — pt_fit.score (Bell 2007)
    "ps_fit":         0.13,   # PS fit   — ps_fit.score (LMX)
    "physical_fit":   0.05,   # Fam. 6   — physical_fit.score
    "mobility_fit":   0.05,   # Fam. 7   — mobility_fit.score
}
"""
Pondérations théoriques par dimension (somme = 1.10 > 1.0 intentionnel pour
renormalisation automatique sur dimensions disponibles).
"""


# ── Aliases de compatibilité (MLPSM/master.py) ────────────────────────────────

SIGMOID_CENTER: float = 50.0
SIGMOID_SCALE: float = 15.0


def _sigmoid_transform(y_raw: float) -> float:
    """
    Transformation sigmoïde centrée sur SIGMOID_CENTER.
    z = (y_raw − SIGMOID_CENTER) / SIGMOID_SCALE
    result = 100 × σ(z)
    """
    z = (y_raw - SIGMOID_CENTER) / SIGMOID_SCALE
    return round(100.0 / (1.0 + _math.exp(-z)), 1)


# ── Helpers internes ───────────────────────────────────────────────────────────

def _confidence_label(data_quality: float) -> str:
    if data_quality >= 0.85:
        return "HIGH"
    elif data_quality >= 0.60:
        return "MEDIUM"
    return "LOW"


def _weighted_global_score(
    scores: Dict[str, Optional[float]],
    weights: Dict[str, float],
) -> float:
    """
    Calcule le score global pondéré avec renormalisation automatique.

    Formule :
        global_score = Σ(w_i × s_i) / Σ(w_i)
        où la somme ne porte que sur les dimensions disponibles (s_i non None).

    Args:
        scores  : {dimension: score | None}  — None = dimension absente
        weights : {dimension: poids_théorique}

    Returns:
        Score ∈ [0.0, 100.0]
    """
    total_w = 0.0
    total_ws = 0.0
    for dim, score in scores.items():
        if score is not None and dim in weights:
            w = weights[dim]
            total_w += w
            total_ws += w * score
    if total_w == 0.0:
        return 0.0
    return round(total_ws / total_w, 1)


# ── Dataclass principale ───────────────────────────────────────────────────────

@dataclass
class PEFitResult:
    """
    Résultat agrégé du PE Fit pour un candidat.

    ── Scores par dimension ─────────────────────────────────────────────────
    pj_fit        → Person-Job Fit D-A (toujours calculé)
    po_fit        → F_env legacy / JD-R (reporting uniquement, hors global_score)
    pt_fit        → PG fit / F_team Bell 2007 (None si équipe absente)
    ps_fit        → PS fit / F_lmx LMX (None si captain_vector absent)
    physical_fit  → Fit physique-environnemental Fam.6 (None si données absentes)
    mobility_fit  → Fit mobilité-temporel Fam.7 (None si données absentes)

    ── Score global ─────────────────────────────────────────────────────────
    global_score → moyenne pondérée des dimensions disponibles ∈ [0, 100]
                   Pondérations : DA=0.28, NS=0.25, PO=0.18, PG=0.16, PS=0.13,
                                  Phys=0.05, Mob=0.05
                   Renormalisée automatiquement sur dimensions présentes.

    ── Sécurité (depuis pj_fit) ─────────────────────────────────────────────
    safety_level    → "CLEAR" | "ADVISORY" | "HIGH_RISK" | "DISQUALIFIED"
    is_disqualified → True si safety_level == "DISQUALIFIED"

    ── Meta ─────────────────────────────────────────────────────────────────
    data_quality → qualité globale des données
    confidence   → "HIGH" | "MEDIUM" | "LOW"
    all_flags    → tous les avertissements de tous les sous-modules
    """
    # Scores par dimension
    pj_fit:         PJFitResult
    po_fit:         Optional[FEnvResult]       # legacy JDR — reporting uniquement
    po_values_fit:  Optional[POValuesResult]   # PO fit Fam. 3 — congruence valeurs CES
    pt_fit:         Optional[FTeamResult]      # PG fit
    ps_fit:         Optional[FLmxResult]       # PS fit
    physical_fit:   Optional[FPhysicalResult]  # Fam. 6
    mobility_fit:   Optional[FMobilityResult]  # Fam. 7

    # Score global pondéré (7 familles, renormalisé)
    global_score: float

    # Sécurité
    safety_level:    str
    is_disqualified: bool

    # Meta
    data_quality: float = 1.0
    confidence:   str = "HIGH"
    all_flags:    List[str] = field(default_factory=list)

    def to_matching_row(self) -> Dict:
        """Format compact pour la liste de matching."""
        row: Dict = {
            "pj_fit_score":        self.pj_fit.score,
            "pj_aggregate_score":  self.pj_fit.pj_aggregate_score,
            "ns_fit_score":        self.pj_fit.ns_fit_score,
            "motivation_score":    self.pj_fit.motivation_score,
            "po_fit_score":        self.po_fit.score if self.po_fit else None,
            "po_values_fit_score": self.po_values_fit.score if self.po_values_fit else None,
            "pt_fit_score":        self.pt_fit.score if self.pt_fit else None,
            "ps_fit_score":        self.ps_fit.score if self.ps_fit else None,
            "physical_fit_score":  self.physical_fit.score if self.physical_fit else None,
            "mobility_fit_score":  self.mobility_fit.score if self.mobility_fit else None,
            "global_score":        self.global_score,
            "safety_level":        self.safety_level,
            "is_disqualified":     self.is_disqualified,
            "confidence":          self.confidence,
            "data_quality":        round(self.data_quality * 100),
        }
        if self.pj_fit.safety:
            row["safety_flags"] = self.pj_fit.safety.context_flags
        else:
            row["safety_flags"] = []
        return row

    def to_impact_report(self) -> Dict:
        """Rapport détaillé pour l'endpoint /impact."""
        report: Dict = {
            "global_score":    self.global_score,
            "safety_level":    self.safety_level,
            "is_disqualified": self.is_disqualified,
            "confidence":      self.confidence,
            "data_quality":    round(self.data_quality * 100),

            "dimension_weights": {
                k: v for k, v in DIMENSION_WEIGHTS.items()
            },

            "pj_fit": {
                "score":           self.pj_fit.score,
                "p_ind_score":     self.pj_fit.p_ind_score,
                "fit_label":       self.pj_fit.fit_label,
                "overall_centile": self.pj_fit.overall_centile,
                "ns_fit_score":    self.pj_fit.ns_fit_score,
                "motivation_score": self.pj_fit.motivation_score,
                "safety": {
                    "level": self.safety_level,
                    "flags": (
                        self.pj_fit.safety.context_flags
                        if self.pj_fit.safety else []
                    ),
                },
                "flags": self.pj_fit.all_flags,
            },
        }

        # PO Fit legacy (F_env — reporting uniquement, hors global_score)
        if self.po_fit:
            report["po_fit"] = {
                "score":      self.po_fit.score,
                "jdr_ratio":  self.po_fit.jdr_ratio.raw_ratio,
                "jdr_status": self.po_fit.jdr_ratio.equilibrium_status,
                "resilience": self.po_fit.resilience.resilience_raw,
                "note":       "Legacy JD-R (F_env) — hors global_score.",
                "flags":      self.po_fit.flags,
            }
        else:
            report["po_fit"] = None

        # PO Fit — congruence valeurs CES (Famille 3, poids 0.18)
        if self.po_values_fit:
            report["po_values_fit"] = {
                "score": self.po_values_fit.score,
                "dimensions": [
                    {
                        "dimension":         d.dimension,
                        "candidate_raw":     d.candidate_raw,
                        "environment_level": d.environment_level,
                        "score":             d.score,
                        "weight":            d.weight,
                    }
                    for d in self.po_values_fit.dimensions
                ],
                "data_quality": self.po_values_fit.data_quality,
                "flags":        self.po_values_fit.flags,
            }
        else:
            report["po_values_fit"] = None

        # PG Fit (PT — Bell 2007)
        if self.pt_fit:
            report["pt_fit"] = {
                "score":             self.pt_fit.score,
                "min_agreeableness": self.pt_fit.jerk_filter.min_agreeableness,
                "mean_es":           self.pt_fit.emotional.mean_emotional_stability,
                "sigma_c":           self.pt_fit.faultline.sigma_conscientiousness,
                "crew_size":         self.pt_fit.crew_size,
                "flags":             self.pt_fit.flags,
            }
        else:
            report["pt_fit"] = None

        # PS Fit (LMX)
        if self.ps_fit:
            report["ps_fit"] = {
                "score":               self.ps_fit.score,
                "compatibility_label": self.ps_fit.distance.compatibility_label,
                "normalized_distance": self.ps_fit.distance.normalized_distance,
                "dimension_gaps": [
                    {
                        "dimension": d.dimension,
                        "gap":       d.gap,
                        "direction": d.gap_direction,
                        "label":     d.gap_label,
                    }
                    for d in self.ps_fit.dimensions
                ],
                "flags": self.ps_fit.flags,
            }
        else:
            report["ps_fit"] = None

        # Fit physique-environnemental (Fam. 6)
        if self.physical_fit:
            report["physical_fit"] = {
                "score": self.physical_fit.score,
                "dimensions": [
                    {
                        "dimension":          d.dimension,
                        "candidate_raw":      d.candidate_raw,
                        "environment_level":  d.environment_level,
                        "score":              round(d.score * 100, 1),
                        "weight":             d.weight,
                    }
                    for d in self.physical_fit.dimensions
                ],
                "flags": self.physical_fit.flags,
            }
        else:
            report["physical_fit"] = None

        # Fit mobilité-temporel (Fam. 7)
        if self.mobility_fit:
            report["mobility_fit"] = {
                "score": self.mobility_fit.score,
                "dimensions": [
                    {
                        "dimension":          d.dimension,
                        "candidate_raw":      d.candidate_raw,
                        "environment_level":  d.environment_level,
                        "score":              round(d.score * 100, 1),
                        "weight":             d.weight,
                    }
                    for d in self.mobility_fit.dimensions
                ],
                "flags": self.mobility_fit.flags,
            }
        else:
            report["mobility_fit"] = None

        report["all_flags"] = self.all_flags
        return report


# ── Calcul principal ───────────────────────────────────────────────────────────

def compute(
    snapshot: Dict,
    *,
    position: Optional[str] = None,
    pool: Optional[Dict[str, Dict]] = None,
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    current_crew_snapshots: Optional[List[Dict]] = None,
    sme_weights: Optional[Dict[str, Dict[str, float]]] = None,
    competency_weights: Optional[Dict[str, float]] = None,
    experience_years: int = 0,
) -> "PEFitResult":
    """
    Calcule le PE Fit global pour un candidat.

    Étapes :
        1. PJ Fit (toujours) — D-A score + N-S score (JD-R) + motivation
        2. PO Fit legacy si vessel_params — F_env (reporting, hors global_score)
        2.5. PO Fit valeurs CES si vessel_params['org_values'] — Famille 3 (poids 0.18)
        3. PG Fit si current_crew_snapshots — Bell 2007
        4. PS Fit si captain_vector — LMX
        5. Fit physique si vessel_params['maritime_conditions'] + snapshot['maritime_tolerance']
        6. Fit mobilité si vessel_params['mobility_requirements'] + snapshot['mobility_profile']
        7. global_score = Σ(w_i × s_i) / Σ(w_i disponibles)
           Pondérations : DA=0.28, NS=0.25, PO=0.18, PG=0.16, PS=0.13, Phys=0.05, Mob=0.05

    Args:
        snapshot                : psychometric_snapshot du CrewProfile
        position                : YachtPosition.value
        pool                    : pool de candidats (centile Temps 2)
        vessel_params           : paramètres du poste (active PO legacy + Phys + Mob)
        captain_vector          : vecteur capitaine (active PS Fit)
        current_crew_snapshots  : équipe actuelle (active PG Fit)
        sme_weights             : poids SME personnalisés
        competency_weights      : poids inter-compétences
        experience_years        : années d'expérience (Temps 2)

    Returns:
        PEFitResult agrégé avec global_score pondéré et détail par dimension.
    """
    all_flags: List[str] = []

    # ── 1. PJ Fit (toujours) ─────────────────────────────────────────────────
    pj_result = _pj_scorer.compute(
        snapshot,
        position=position,
        pool=pool,
        sme_weights=sme_weights,
        experience_years=experience_years,
        vessel_params=vessel_params,
    )
    for flag in pj_result.all_flags:
        all_flags.append(f"[PJ] {flag}")

    # ── 2. PO Fit legacy (F_env / JD-R — reporting uniquement) ──────────────
    po_result: Optional[FEnvResult] = _po_fit.compute_fit(snapshot, vessel_params)
    if po_result:
        for flag in po_result.flags:
            all_flags.append(f"[PO_LEGACY] {flag}")
    else:
        all_flags.append("[PO] vessel_params absent — PO legacy non calculé")

    # ── 2.5. PO Fit valeurs CES (Famille 3 — congruence, poids 0.18) ─────────
    po_values_result: Optional[POValuesResult] = _po_values_fit.compute_values_fit(
        snapshot, vessel_params
    )
    if po_values_result:
        for flag in po_values_result.flags:
            all_flags.append(f"[PO_VALUES] {flag}")
    else:
        all_flags.append("[PO_VALUES] données valeurs absentes — PO fit valeurs non calculé")

    # ── 3. PG Fit (Bell 2007) ────────────────────────────────────────────────
    pt_result: Optional[FTeamResult] = _pt_fit.compute_fit(snapshot, current_crew_snapshots)
    if pt_result:
        for flag in pt_result.flags:
            all_flags.append(f"[PG] {flag}")
    else:
        all_flags.append("[PG] current_crew_snapshots absent — PG Fit non calculé")

    # ── 4. PS Fit (LMX) ──────────────────────────────────────────────────────
    ps_result: Optional[FLmxResult] = _ps_fit.compute_fit(snapshot, captain_vector)
    if ps_result:
        for flag in ps_result.flags:
            all_flags.append(f"[PS] {flag}")
    else:
        all_flags.append("[PS] captain_vector absent — PS Fit non calculé")

    # ── 5. Fit physique-environnemental (Fam. 6) ─────────────────────────────
    physical_result: Optional[FPhysicalResult] = _physical_fit.compute_fit(
        snapshot, vessel_params
    )
    if physical_result:
        for flag in physical_result.flags:
            all_flags.append(f"[PHYS] {flag}")
    else:
        all_flags.append("[PHYS] données maritimes absentes — Fit physique non calculé")

    # ── 6. Fit mobilité-temporel (Fam. 7) ────────────────────────────────────
    mobility_result: Optional[FMobilityResult] = _mobility_fit.compute_fit(
        snapshot, vessel_params
    )
    if mobility_result:
        for flag in mobility_result.flags:
            all_flags.append(f"[MOB] {flag}")
    else:
        all_flags.append("[MOB] données mobilité absentes — Fit mobilité non calculé")

    # ── 7. Global score pondéré ───────────────────────────────────────────────
    #
    # Mapping des dimensions disponibles vers leurs scores :
    #   da_fit        → pj_fit.score              (D-A, toujours)
    #   ns_fit        → pj_fit.ns_fit_score       (N-S / JD-R, si vessel_params)
    #   po_values_fit → po_values_fit.score       (PO / CES, si org_values présentes)
    #   pg_fit        → pt_fit.score              (PG / Bell, si équipe)
    #   ps_fit        → ps_fit.score              (PS / LMX, si capitaine)
    #   physical_fit  → physical_fit.score        (Fam.6, si données maritimes)
    #   mobility_fit  → mobility_fit.score        (Fam.7, si données mobilité)
    #
    dim_scores: Dict[str, Optional[float]] = {
        "da_fit":         pj_result.score,
        "ns_fit":         pj_result.ns_fit_score,
        "po_values_fit":  po_values_result.score if po_values_result is not None else None,
        "pg_fit":         pt_result.score if pt_result is not None else None,
        "ps_fit":         ps_result.score if ps_result is not None else None,
        "physical_fit":   physical_result.score if physical_result is not None else None,
        "mobility_fit":   mobility_result.score if mobility_result is not None else None,
    }

    global_score = _weighted_global_score(dim_scores, DIMENSION_WEIGHTS)

    # ── 8. Sécurité ───────────────────────────────────────────────────────────
    if pj_result.safety:
        safety_level = pj_result.safety.safety_level.value
    else:
        safety_level = SafetyLevel.CLEAR.value

    is_disqualified = safety_level == SafetyLevel.DISQUALIFIED.value

    # ── 9. Qualité globale ────────────────────────────────────────────────────
    dq_values: List[float] = [pj_result.data_quality]
    if po_result is not None:
        dq_values.append(po_result.data_quality)
    if po_values_result is not None:
        dq_values.append(po_values_result.data_quality)
    if pt_result is not None:
        dq_values.append(pt_result.data_quality)
    if ps_result is not None:
        dq_values.append(ps_result.data_quality)
    if physical_result is not None:
        dq_values.append(physical_result.data_quality)
    if mobility_result is not None:
        dq_values.append(mobility_result.data_quality)

    data_quality = round(sum(dq_values) / len(dq_values), 3)

    return PEFitResult(
        pj_fit=pj_result,
        po_fit=po_result,
        po_values_fit=po_values_result,
        pt_fit=pt_result,
        ps_fit=ps_result,
        physical_fit=physical_result,
        mobility_fit=mobility_result,
        global_score=global_score,
        safety_level=safety_level,
        is_disqualified=is_disqualified,
        data_quality=data_quality,
        confidence=_confidence_label(data_quality),
        all_flags=all_flags,
    )
