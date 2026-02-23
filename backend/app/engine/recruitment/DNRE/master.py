# engine/recruitment/dnre/master.py
"""
DNRE — Dynamic Normative-Relative Engine
Moteur de matching psychométrique pour la plateforme Harmony.

Remplace le MLPSM comme équation de matching.
Les sous-modules MLPSM (p_ind, f_team, f_env, f_lmx) restent disponibles
pour alimenter les scores de traits — le DNRE les agrège différemment.

Architecture du scoring :

    ┌─────────────────────────────────────────────────────────────────┐
    │                        DNRE MASTER                              │
    │                                                                 │
    │  psychometric_snapshot                                          │
    │         │                                                       │
    │         ▼                                                       │
    │  ① sme_score.compute_all_competencies()                        │
    │         │  S_{i,c} pour chaque compétence (K=4)                │
    │         │                                                       │
    │  ② safety_barrier.evaluate()                                   │
    │         │  Veto non-compensatoire sur traits critiques          │
    │         │  → DISQUALIFIED / HIGH_RISK / ADVISORY / CLEAR       │
    │         │                                                       │
    │  ③ global_fit.compute()                                        │
    │         │  G_fit = (1/K) Σ S_{i,c}                             │
    │         │  (suspendu si DISQUALIFIED)                           │
    │         │                                                       │
    │  ④ centile_rank.compute_batch()          [MODE BATCH REQUIS]   │
    │         │  Π_{i,c} pour chaque compétence                      │
    │         │  Calculé après que TOUS les candidats sont scorés     │
    │         │                                                       │
    │  ⑤ Agrégation finale → DNREResult                              │
    │         g_fit + centile_ranks + safety + détails               │
    └─────────────────────────────────────────────────────────────────┘

Note sur l'ordre de calcul :
    Les étapes ①②③ sont calculées par candidat (indépendantes).
    L'étape ④ (centile) nécessite TOUS les candidats — elle est exécutée
    en batch après que tous les G_fit sont connus.
    compute_batch() orchestre les 4 étapes dans le bon ordre.

Relation DNRE / MLPSM :
    Le MLPSM calculait Ŷ = β₁P + β₂FT + β₃FE + β₄FL avec des betas fixes.
    Le DNRE calcule G_fit = (1/K) Σ S_{i,c} avec des poids SME contextuels
    et ajoute la dimension normative (centile) et la sécurité (veto).

    Les sub-scores MLPSM (p_ind, f_team, f_env, f_lmx) restent exposés
    dans le DNREResult pour la compatibilité et l'audit.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.recruitment.DNRE import sme_score as _sme_score
from app.engine.recruitment.DNRE import centile_rank as _centile_rank
from app.engine.recruitment.DNRE import safety_barrier as _safety_barrier
from app.engine.recruitment.DNRE import global_fit as _global_fit
from app.engine.recruitment.DNRE.sme_score import (
    SMEScoreResult, ALL_COMPETENCIES, DEFAULT_SME_WEIGHTS
)
from app.engine.recruitment.DNRE.centile_rank import CentileResult, PoolStats
from app.engine.recruitment.DNRE.safety_barrier import SafetyBarrierResult, SafetyLevel
from app.engine.recruitment.DNRE.global_fit import GlobalFitResult

# Sous-modules MLPSM — disponibles pour les détails de traits
from app.engine.recruitment.MLPSM import f_team as _f_team
from app.engine.recruitment.MLPSM.f_team import FTeamResult


# ── Labels de score ───────────────────────────────────────────────────────────

def _fit_label(g_fit: float, safety: SafetyLevel) -> str:
    if safety == SafetyLevel.DISQUALIFIED:
        return "DISQUALIFIED"
    if safety == SafetyLevel.HIGH_RISK:
        return "HIGH_RISK"
    if g_fit >= 75:   return "STRONG_FIT"
    if g_fit >= 60:   return "GOOD_FIT"
    if g_fit >= 45:   return "MODERATE_FIT"
    return "POOR_FIT"


def _confidence_label(data_quality: float, pool_n: int) -> str:
    if data_quality >= 0.85 and pool_n >= 5:  return "HIGH"
    if data_quality >= 0.60 and pool_n >= 2:  return "MEDIUM"
    return "LOW"


# ── Dataclasses de résultat ───────────────────────────────────────────────────

@dataclass
class DNREResult:
    """
    Résultat complet du DNRE pour un candidat.

    ── Scores principaux ──────────────────────────────────────────────────────
    g_fit            → G_fit ∈ [0, 100] — score absolu global
    fit_label        → "STRONG_FIT" | "GOOD_FIT" | "MODERATE_FIT" | "POOR_FIT"
                        | "HIGH_RISK" | "DISQUALIFIED"

    ── Centiles par compétence ────────────────────────────────────────────────
    centile_ranks    → {competency_key: CentileResult} — rang dans le pool
    overall_centile  → centile moyen sur toutes les compétences

    ── Détails par compétence ─────────────────────────────────────────────────
    sme_scores       → {competency_key: SMEScoreResult} — S_{i,c} + traits
    global_fit_detail → GlobalFitResult — détail agrégation G_fit

    ── Sécurité ──────────────────────────────────────────────────────────────
    safety           → SafetyBarrierResult — vetos + safety_level

    ── Impact équipe (optionnel — compute_with_team_delta()) ────────────────
    f_team_detail    → FTeamResult depuis le module MLPSM (avec delta)

    ── Meta ──────────────────────────────────────────────────────────────────
    crew_profile_id  → identifiant du candidat
    data_quality     → qualité globale des données
    confidence       → "HIGH" | "MEDIUM" | "LOW"
    all_flags        → tous les avertissements
    """
    g_fit:            float
    fit_label:        str

    # Centiles
    centile_ranks:    Dict[str, CentileResult] = field(default_factory=dict)
    overall_centile:  float = 0.0

    # Détails
    sme_scores:       Dict[str, SMEScoreResult] = field(default_factory=dict)
    global_fit_detail: Optional[GlobalFitResult] = None
    safety:           Optional[SafetyBarrierResult] = None

    # Impact équipe (optionnel)
    f_team_detail:    Optional[FTeamResult] = None

    # Meta
    crew_profile_id:  Optional[str] = None
    data_quality:     float = 1.0
    confidence:       str = "HIGH"
    all_flags:        List[str] = field(default_factory=list)

    def to_matching_row(self) -> Dict:
        """
        Format compact pour la liste de matching.
        Exposé par GET /recruitment/campaigns/{id}/matching.
        """
        centile_by_comp = {
            k: v.centile for k, v in self.centile_ranks.items()
        }
        return {
            "crew_profile_id":    self.crew_profile_id,
            "g_fit":              self.g_fit,
            "fit_label":          self.fit_label,
            "overall_centile":    self.overall_centile,
            "centile_by_competency": centile_by_comp,
            "safety_level":       self.safety.safety_level.value if self.safety else "CLEAR",
            "safety_flags":       self.safety.context_flags if self.safety else [],
            "confidence":         self.confidence,
            "data_quality":       round(self.data_quality * 100),
        }

    def to_impact_report(self) -> Dict:
        """
        Rapport What-If détaillé pour l'endpoint /impact/{crew_profile_id}.
        Inclut les détails de chaque compétence + centile + vetos.
        """
        delta = self.f_team_detail.delta if self.f_team_detail else None

        competency_details = {}
        for key, sme in self.sme_scores.items():
            centile = self.centile_ranks.get(key)
            competency_details[key] = {
                "label":       sme.competency_label,
                "s_ic":        sme.score,
                "centile":     centile.centile if centile else None,
                "rank":        centile.rank if centile else None,
                "pool_n":      centile.pool_stats.n if centile else None,
                "pool_mean":   centile.pool_stats.mean if centile else None,
                "percentile_label": centile.percentile_label if centile else None,
                "trait_breakdown": [
                    {
                        "trait":       tc.trait,
                        "score":       tc.raw_score,
                        "weight":      tc.weight,
                        "is_fallback": tc.is_fallback,
                    }
                    for tc in sme.trait_contributions
                ],
                "data_quality": round(sme.data_quality * 100),
                "flags":        sme.flags,
            }

        return {
            "crew_profile_id":   self.crew_profile_id,
            "g_fit":             self.g_fit,
            "fit_label":         self.fit_label,
            "overall_centile":   self.overall_centile,
            "confidence":        self.confidence,
            "data_quality":      round(self.data_quality * 100),

            "competency_details": competency_details,

            "safety": {
                "level":   self.safety.safety_level.value if self.safety else "CLEAR",
                "flags":   self.safety.context_flags if self.safety else [],
                "triggers": [
                    {
                        "trait":    t.trait,
                        "observed": t.observed_score,
                        "threshold": t.threshold,
                        "type":     t.veto_type.value,
                        "label":    t.label,
                    }
                    for t in (self.safety.triggers if self.safety else [])
                ],
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

            "all_flags": self.all_flags,
        }

    def to_event_snapshot(self) -> Dict:
        """Format compact pour RecruitmentEvent (stockage DB)."""
        return {
            "g_fit":            self.g_fit,
            "overall_centile":  self.overall_centile,
            "sme_scores": {
                k: v.score for k, v in self.sme_scores.items()
            },
            "safety_level":     self.safety.safety_level.value if self.safety else "CLEAR",
            "data_quality":     self.data_quality,
            "flags_summary":    self.all_flags[:10],
        }


# ── Scoring individuel (étapes 1-3) ───────────────────────────────────────────

def _score_candidate(
    candidate_snapshot: Dict,
    sme_weights_override: Optional[Dict[str, Dict[str, float]]] = None,
    competency_weights: Optional[Dict[str, float]] = None,
    current_crew_snapshots: Optional[List[Dict]] = None,
    captain_vector: Optional[Dict] = None,
    vessel_params: Optional[Dict] = None,
    position_key: Optional[str] = None,
    crew_profile_id: Optional[str] = None,
) -> tuple[DNREResult, Dict[str, float]]:
    """
    Étapes 1-3 pour un candidat individuel.
    Retourne (DNREResult_partiel, {competency_key: s_ic}).
    Le centile (étape 4) est ajouté en batch dans compute_batch().
    """
    flags: List[str] = []

    # ── Étape 1 : Scores SME ─────────────────────────────────
    sme_results = _sme_score.compute_all_competencies(
        candidate_snapshot,
        sme_weights_override=sme_weights_override,
    )
    sme_scores_flat = {k: v.score for k, v in sme_results.items()}

    # Collecte des data_qualities pour chaque compétence
    dq_map = {k: v.data_quality for k, v in sme_results.items()}

    # Flags des sous-modules SME
    for key, result in sme_results.items():
        for flag in result.flags:
            flags.append(f"[SME:{key}] {flag}")

    # ── Étape 2 : Barrière de sécurité ───────────────────────
    # G_fit provisoire pour l'évaluation de la barrière
    provisional_gfit = sum(sme_scores_flat.values()) / max(len(sme_scores_flat), 1)
    safety = _safety_barrier.evaluate(
        candidate_snapshot,
        g_fit_score=provisional_gfit,
        position_key=position_key,
    )

    for flag in safety.context_flags:
        flags.append(f"[SAFETY] {flag}")

    # ── Étape 3 : G_fit ──────────────────────────────────────
    if safety.safety_level == SafetyLevel.DISQUALIFIED:
        # Veto HARD — agrégation suspendue
        gfit_result = _global_fit.compute(sme_scores_flat, competency_weights, dq_map)
        gfit_result.g_fit = 0.0
        gfit_result.flags.append("G_FIT_SUSPENDED: veto HARD déclenché")
        flags.append("[GLOBAL_FIT] Agrégation suspendue — DISQUALIFIED")
    else:
        gfit_result = _global_fit.compute(sme_scores_flat, competency_weights, dq_map)

    for flag in gfit_result.flags:
        flags.append(f"[GLOBAL_FIT] {flag}")

    # ── Impact équipe (optionnel) ────────────────────────────
    f_team_result = None
    if current_crew_snapshots is not None and len(current_crew_snapshots) >= 1:
        all_snaps = current_crew_snapshots + [candidate_snapshot]
        f_team_result = _f_team.compute_delta(current_crew_snapshots, candidate_snapshot)
        for flag in f_team_result.flags:
            flags.append(f"[F_TEAM] {flag}")

    # ── Qualité globale ──────────────────────────────────────
    dq_values = list(dq_map.values())
    data_quality = round(sum(dq_values) / len(dq_values), 3) if dq_values else 1.0

    # Résultat partiel (centile ajouté après le batch)
    result = DNREResult(
        g_fit=gfit_result.g_fit,
        fit_label=_fit_label(gfit_result.g_fit, safety.safety_level),
        sme_scores=sme_results,
        global_fit_detail=gfit_result,
        safety=safety,
        f_team_detail=f_team_result,
        crew_profile_id=crew_profile_id,
        data_quality=data_quality,
        all_flags=flags,
    )

    return result, sme_scores_flat


# ── Point d'entrée batch ───────────────────────────────────────────────────────

def compute_batch(
    candidates: List[Dict],
    current_crew_snapshots: Optional[List[Dict]] = None,
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    sme_weights_override: Optional[Dict[str, Dict[str, float]]] = None,
    competency_weights: Optional[Dict[str, float]] = None,
) -> List[DNREResult]:
    """
    Calcule le DNRE pour tous les candidats d'une campagne.

    ORDRE OBLIGATOIRE :
    1. Scores SME + Safety + G_fit pour chaque candidat (indépendant)
    2. Centile par compétence en batch (nécessite tous les scores)
    3. Enrichissement des DNREResult avec les centiles

    Args:
        candidates : [
            {
                "snapshot":         Dict,       # psychometric_snapshot
                "crew_profile_id":  str,
                "experience_years": int,        # (optionnel)
                "position_key":     str,        # (optionnel)
            }
        ]
        current_crew_snapshots : snapshots de l'équipage actuel (pour F_team delta)
        vessel_params          : paramètres JD-R du yacht (pour C3 enrichissement Temps 2)
        captain_vector         : vecteur capitaine (pour C4 enrichissement Temps 2)
        sme_weights_override   : poids SME par compétence personnalisés
        competency_weights     : poids inter-compétences (uniforme si None)

    Returns:
        Liste de DNREResult dans le même ordre que candidates, triée par g_fit desc.
    """
    if not candidates:
        return []

    # ── Étapes 1-3 : scoring individuel ──────────────────────
    partial_results: List[DNREResult] = []
    all_sme_scores: List[Dict[str, float]] = []   # [{competency: s_ic}]

    for candidate in candidates:
        snapshot   = candidate.get("snapshot") or {}
        crew_id    = str(candidate.get("crew_profile_id", ""))
        position   = candidate.get("position_key")

        result, sme_flat = _score_candidate(
            candidate_snapshot=snapshot,
            sme_weights_override=sme_weights_override,
            competency_weights=competency_weights,
            current_crew_snapshots=current_crew_snapshots,
            captain_vector=captain_vector,
            vessel_params=vessel_params,
            position_key=position,
            crew_profile_id=crew_id,
        )
        partial_results.append(result)
        all_sme_scores.append(sme_flat)

    # ── Étape 4 : Centile batch par compétence ────────────────
    # Pour chaque compétence, on calcule le centile de tous les candidats
    # en une passe (compute_batch est O(n log n) par compétence)

    centiles_by_competency: Dict[str, Dict[str, _centile_rank.CentileResult]] = {}

    for competency_key in ALL_COMPETENCIES:
        # Pool : {crew_profile_id: S_{i,c}}
        pool_scores = {
            str(candidates[idx].get("crew_profile_id", idx)): sme_flat.get(competency_key, 50.0)
            for idx, sme_flat in enumerate(all_sme_scores)
        }
        centiles_by_competency[competency_key] = _centile_rank.compute_batch(
            pool_scores, competency_key
        )

    # ── Enrichissement avec les centiles ─────────────────────
    for idx, result in enumerate(partial_results):
        crew_id = str(candidates[idx].get("crew_profile_id", idx))

        centile_ranks: Dict[str, _centile_rank.CentileResult] = {}
        centile_values: List[float] = []

        for competency_key in ALL_COMPETENCIES:
            centile_result = centiles_by_competency[competency_key].get(crew_id)
            if centile_result:
                centile_ranks[competency_key] = centile_result
                centile_values.append(centile_result.centile)

        overall_centile = round(sum(centile_values) / len(centile_values), 1) if centile_values else 0.0
        pool_n = max(c.pool_stats.n for c in centile_ranks.values()) if centile_ranks else 0

        result.centile_ranks = centile_ranks
        result.overall_centile = overall_centile
        result.confidence = _confidence_label(result.data_quality, pool_n)

    return partial_results


# ── Scoring individuel (pour What-If / rapport détaillé) ─────────────────────

def compute_single(
    candidate_snapshot: Dict,
    current_crew_snapshots: Optional[List[Dict]] = None,
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    pool_context: Optional[Dict[str, Dict[str, float]]] = None,
    sme_weights_override: Optional[Dict[str, Dict[str, float]]] = None,
    competency_weights: Optional[Dict[str, float]] = None,
    position_key: Optional[str] = None,
    crew_profile_id: Optional[str] = None,
) -> DNREResult:
    """
    Calcule le DNRE pour un seul candidat.
    Utile pour le rapport What-If individuel (GET /impact/{crew_profile_id}).

    Le centile est calculé si pool_context est fourni.
    Si pool_context est None → centile absent (confidence = LOW).

    Args:
        pool_context : {competency_key: {crew_profile_id: s_ic}}
                       contexte pré-calculé du pool (depuis la liste de matching)
    """
    result, sme_flat = _score_candidate(
        candidate_snapshot=candidate_snapshot,
        sme_weights_override=sme_weights_override,
        competency_weights=competency_weights,
        current_crew_snapshots=current_crew_snapshots,
        captain_vector=captain_vector,
        vessel_params=vessel_params,
        position_key=position_key,
        crew_profile_id=crew_profile_id,
    )

    if pool_context:
        centile_ranks: Dict[str, _centile_rank.CentileResult] = {}
        centile_values: List[float] = []

        for competency_key in ALL_COMPETENCIES:
            comp_pool = pool_context.get(competency_key, {})
            candidate_s_ic = sme_flat.get(competency_key, 50.0)
            pool_scores_list = list(comp_pool.values())

            centile_result = _centile_rank.compute(
                candidate_score=candidate_s_ic,
                pool_scores=pool_scores_list,
                competency_key=competency_key,
            )
            centile_ranks[competency_key] = centile_result
            centile_values.append(centile_result.centile)

        result.centile_ranks = centile_ranks
        result.overall_centile = round(sum(centile_values) / len(centile_values), 1) if centile_values else 0.0
        pool_n = max((c.pool_stats.n for c in centile_ranks.values()), default=0)
        result.confidence = _confidence_label(result.data_quality, pool_n)
    else:
        result.all_flags.append("[CENTILE] Pool absent — centile non calculé")
        result.confidence = "LOW"

    return result