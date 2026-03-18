# pe_fit/master.py
"""
PE Fit — Person-Environment Fit Aggregator

Agrège les quatre dimensions du fit candidat-environnement :

    PJ Fit (Person-Job)          → adéquation aux exigences du poste
    PO Fit (Person-Organization) → adéquation à l'environnement yacht (JD-R)
    PT Fit (Person-Team)         → adéquation à l'équipe existante
    PS Fit (Person-Supervisor)   → adéquation au style du capitaine (LMX)

Formule du global_score :
    global_score = moyenne arithmétique des dimensions disponibles

    Dimensions "disponibles" = celles dont l'input n'est pas None.
    Exemple : si vessel_params absent → PO Fit ignoré dans la moyenne.

    Cette approche préserve l'interprétabilité : un score de 75 avec
    3 dimensions vaut "75 sur les 3 dimensions mesurées", pas "56 sur 4"
    avec une pénalisation pour données manquantes.

Sécurité :
    is_disqualified est propagé depuis PJ Fit (barrière non-compensatoire).
    Un candidat DISQUALIFIED a global_score contraint à la valeur pénalisée
    par la sigmoïde de sécurité du DNRE.

Aliases MLPSM (compatibilité) :
    Ce module expose _sigmoid_transform, SIGMOID_CENTER, SIGMOID_SCALE
    pour les tests qui importent ces utilitaires depuis le master PE Fit
    (cohérence avec MLPSM/master.py).

Architecture :
    - Zéro accès DB (pur calcul sur snapshots)
    - Chaque sous-module peut retourner None si données absentes
    - PEFitResult est sérialisable (to_matching_row / to_impact_report)
"""
from __future__ import annotations
import math as _math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.pj_fit import scorer as _pj_scorer
from app.engine.pe_fit.po_fit import f_env as _po_fit
from app.engine.pe_fit.pt_fit import f_team as _pt_fit
from app.engine.pe_fit.ps_fit import f_lmx as _ps_fit
from app.engine.pe_fit.pj_fit.needs_supplies import jdr as _jdr

from app.engine.pe_fit.pj_fit.scorer import PJFitResult
from app.engine.pe_fit.po_fit.f_env import FEnvResult
from app.engine.pe_fit.pt_fit.f_team import FTeamResult
from app.engine.pe_fit.ps_fit.f_lmx import FLmxResult
from app.engine.pe_fit.pj_fit.safety_barrier import SafetyLevel


# ── Aliases de compatibilité (MLPSM/master.py) ────────────────────────────────

SIGMOID_CENTER: float = 50.0
"""Point médian de l'échelle 0-100. y_raw = 50 → y_success = 50 (invariant)."""

SIGMOID_SCALE: float = 15.0
"""Contrôle l'étalement de la courbe sigmoïde."""


def _sigmoid_transform(y_raw: float) -> float:
    """
    Transformation sigmoïde centrée sur SIGMOID_CENTER.

    Formule :
        z = (y_raw − SIGMOID_CENTER) / SIGMOID_SCALE
        result = 100 × σ(z) = 100 / (1 + e^{−z})

    Returns:
        float ∈ (0.0, 100.0)
    """
    z = (y_raw - SIGMOID_CENTER) / SIGMOID_SCALE
    return round(100.0 / (1.0 + _math.exp(-z)), 1)


# ── Helpers internes ───────────────────────────────────────────────────────────

def _confidence_label(data_quality: float) -> str:
    """Label de confiance selon la qualité des données."""
    if data_quality >= 0.85:
        return "HIGH"
    elif data_quality >= 0.60:
        return "MEDIUM"
    return "LOW"


# ── Dataclass principale ───────────────────────────────────────────────────────

@dataclass
class PEFitResult:
    """
    Résultat agrégé du PE Fit pour un candidat.

    ── Scores par dimension ─────────────────────────────────────────────────
    pj_fit       → Person-Job Fit (toujours calculé)
    po_fit       → Person-Organization / F_env (None si vessel_params absent)
    pt_fit       → Person-Team / F_team (None si équipe absente)
    ps_fit       → Person-Supervisor / F_lmx (None si captain_vector absent)

    ── Score global ─────────────────────────────────────────────────────────
    global_score → moyenne pondérée des dimensions disponibles ∈ [0, 100]

    ── Sécurité (depuis pj_fit) ─────────────────────────────────────────────
    safety_level    → SafetyLevel.value : "CLEAR" | "ADVISORY" |
                      "HIGH_RISK" | "DISQUALIFIED"
    is_disqualified → True si safety_level == "DISQUALIFIED"

    ── Meta ─────────────────────────────────────────────────────────────────
    data_quality → qualité globale des données (moyenne des dimensions)
    confidence   → "HIGH" | "MEDIUM" | "LOW"
    all_flags    → tous les avertissements de tous les sous-modules
    """
    # Scores par dimension
    pj_fit:  PJFitResult
    po_fit:  Optional[FEnvResult]   # None si vessel_params absent
    pt_fit:  Optional[FTeamResult]  # None si équipe absente
    ps_fit:  Optional[FLmxResult]   # None si captain_vector absent

    # Score global
    global_score: float             # moyenne des dimensions disponibles

    # Sécurité
    safety_level:    str            # SafetyLevel.value
    is_disqualified: bool           # True si DISQUALIFIED

    # Meta
    data_quality: float = 1.0
    confidence:   str = "HIGH"
    all_flags:    List[str] = field(default_factory=list)

    def to_matching_row(self) -> Dict:
        """
        Format compact pour la liste de matching.
        Exposé par les endpoints de recrutement.
        """
        row: Dict = {
            "pj_fit_score":        self.pj_fit.score,
            "pj_aggregate_score":  self.pj_fit.pj_aggregate_score,
            "ns_fit_score":        self.pj_fit.ns_fit_score,
            "motivation_score":    self.pj_fit.motivation_score,
            "po_fit_score":        self.po_fit.score if self.po_fit else None,
            "pt_fit_score":        self.pt_fit.score if self.pt_fit else None,
            "ps_fit_score":        self.ps_fit.score if self.ps_fit else None,
            "global_score":        self.global_score,
            "safety_level":        self.safety_level,
            "is_disqualified":     self.is_disqualified,
            "confidence":          self.confidence,
            "data_quality":        round(self.data_quality * 100),
        }
        # Flags de sécurité depuis pj_fit
        if self.pj_fit.safety:
            row["safety_flags"] = self.pj_fit.safety.context_flags
        else:
            row["safety_flags"] = []
        return row

    def to_impact_report(self) -> Dict:
        """
        Rapport détaillé pour l'endpoint /impact.
        Expose les détails de chaque dimension disponible.
        """
        report: Dict = {
            "global_score":   self.global_score,
            "safety_level":   self.safety_level,
            "is_disqualified": self.is_disqualified,
            "confidence":     self.confidence,
            "data_quality":   round(self.data_quality * 100),

            "pj_fit": {
                "score":       self.pj_fit.score,
                "p_ind_score": self.pj_fit.p_ind_score,
                "fit_label":   self.pj_fit.fit_label,
                "overall_centile": self.pj_fit.overall_centile,
                "safety": {
                    "level":   self.safety_level,
                    "flags":   (
                        self.pj_fit.safety.context_flags
                        if self.pj_fit.safety else []
                    ),
                },
                "flags":       self.pj_fit.all_flags,
            },
        }

        # PO Fit (F_env)
        if self.po_fit:
            report["po_fit"] = {
                "score":      self.po_fit.score,
                "jdr_ratio":  self.po_fit.jdr_ratio.raw_ratio,
                "jdr_status": self.po_fit.jdr_ratio.equilibrium_status,
                "resilience": self.po_fit.resilience.resilience_raw,
                "flags":      self.po_fit.flags,
            }
        else:
            report["po_fit"] = None

        # PT Fit (F_team)
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

        # PS Fit (F_lmx)
        if self.ps_fit:
            report["ps_fit"] = {
                "score":                self.ps_fit.score,
                "compatibility_label":  self.ps_fit.distance.compatibility_label,
                "normalized_distance":  self.ps_fit.distance.normalized_distance,
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
) -> PEFitResult:
    """
    Calcule le PE Fit global pour un candidat.

    Étapes :
        1. PJ Fit (toujours) — score G_fit + barrière de sécurité
        2. PO Fit si vessel_params fourni et non vide
        3. PT Fit si current_crew_snapshots fourni et non vide
        4. PS Fit si captain_vector fourni et non vide
        5. global_score = moyenne des scores disponibles
        6. safety_level / is_disqualified depuis pj_fit.safety

    Args:
        snapshot                : psychometric_snapshot du CrewProfile
        position                : YachtPosition.value (filtre veto + poids SME)
        pool                    : pool de candidats {crew_id: snapshot}
                                  (réservé centile Temps 2)
        vessel_params           : paramètres JD-R du yacht (active PO Fit)
        captain_vector          : vecteur capitaine (active PS Fit)
        current_crew_snapshots  : équipe actuelle (active PT Fit)
        sme_weights             : poids SME personnalisés
        competency_weights      : poids inter-compétences pour G_fit
        experience_years        : années d'expérience (réservé Temps 2)

    Returns:
        PEFitResult agrégé avec global_score et détail par dimension.
    """
    all_flags: List[str] = []

    # ── 1. PJ Fit (toujours calculé) ─────────────────────────
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

    # ── 2. PO Fit (si vessel_params) ─────────────────────────
    po_result: Optional[FEnvResult] = _po_fit.compute_fit(snapshot, vessel_params)
    if po_result:
        for flag in po_result.flags:
            all_flags.append(f"[PO] {flag}")
    else:
        all_flags.append("[PO] vessel_params absent — PO Fit non calculé")

    # ── 3. PT Fit (si équipe) ─────────────────────────────────
    pt_result: Optional[FTeamResult] = _pt_fit.compute_fit(snapshot, current_crew_snapshots)
    if pt_result:
        for flag in pt_result.flags:
            all_flags.append(f"[PT] {flag}")
    else:
        all_flags.append("[PT] current_crew_snapshots absent — PT Fit non calculé")

    # ── 4. PS Fit (si capitaine) ──────────────────────────────
    ps_result: Optional[FLmxResult] = _ps_fit.compute_fit(snapshot, captain_vector)
    if ps_result:
        for flag in ps_result.flags:
            all_flags.append(f"[PS] {flag}")
    else:
        all_flags.append("[PS] captain_vector absent — PS Fit non calculé")

    # ── 5. Global score — moyenne des dimensions disponibles ──
    available_scores: List[float] = [pj_result.score]
    if po_result is not None:
        available_scores.append(po_result.score)
    if pt_result is not None:
        available_scores.append(pt_result.score)
    if ps_result is not None:
        available_scores.append(ps_result.score)

    global_score = round(sum(available_scores) / len(available_scores), 1)

    # ── 6. Sécurité ───────────────────────────────────────────
    if pj_result.safety:
        safety_level = pj_result.safety.safety_level.value
    else:
        safety_level = SafetyLevel.CLEAR.value

    is_disqualified = safety_level == SafetyLevel.DISQUALIFIED.value

    # ── 7. Qualité globale ────────────────────────────────────
    dq_values: List[float] = [pj_result.data_quality]
    if po_result is not None:
        dq_values.append(po_result.data_quality)
    if pt_result is not None:
        dq_values.append(pt_result.data_quality)
    if ps_result is not None:
        dq_values.append(ps_result.data_quality)

    data_quality = round(sum(dq_values) / len(dq_values), 3)

    return PEFitResult(
        pj_fit=pj_result,
        po_fit=po_result,
        pt_fit=pt_result,
        ps_fit=ps_result,
        global_score=global_score,
        safety_level=safety_level,
        is_disqualified=is_disqualified,
        data_quality=data_quality,
        confidence=_confidence_label(data_quality),
        all_flags=all_flags,
    )
