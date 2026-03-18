# engine/recruitment/pipeline.py
"""
Pipeline de matching à deux étages — Harmony Matching Engine v2

┌─────────────────────────────────────────────────────────────────────────┐
│                     HARMONY MATCHING PIPELINE                           │
│                                                                         │
│  ÉTAGE 1 — DNRE (Dynamic Normative-Relative Engine)                    │
│  "Ce candidat est-il qualifié pour CE TYPE de poste ?"                 │
│                                                                         │
│  Logique : normatif + comparatif (pool)                                 │
│  Input   : psychometric_snapshot + pool des candidats                   │
│  Output  : G_fit (absolu), Π_pool (centile), safety_level               │
│                                                                         │
│  → Filtre HARD : DISQUALIFIED → exclu du pipeline                      │
│  → Filtre SOFT : HIGH_RISK → passe à l'étage 2 avec flag               │
│  → Clear/Advisory → passe à l'étage 2                                  │
│                                                                         │
│              ↓  candidats non-DISQUALIFIED                              │
│                                                                         │
│  ÉTAGE 2 — MLPSM (Maritime Leader-Performance Success Model)           │
│  "Comment ce candidat s'intègre-t-il à CET équipage précis ?"          │
│                                                                         │
│  Logique : simulateur système vivant                                    │
│  Input   : snapshot + crew actuel + vessel_params + captain_vector     │
│  Output  : Ŷ_success = β₁P_ind + β₂F_team + β₃F_env + β₄F_lmx       │
│            + FTeamDelta (impact marginal sur l'équipe)                 │
│                                                                         │
│              ↓                                                          │
│                                                                         │
│  RÉSULTAT COMPOSITE — PipelineResult                                   │
│  ─────────────────────────────────────────────────────────────────────  │
│  dnre_stage  : G_fit, centile, safety (dimension profil/poste)         │
│  mlpsm_stage : Ŷ_success, 4 sub-scores, team delta (dimension équipe) │
│  composite   : score de présentation synthétique (non décisionnel)      │
│                                                                         │
│  L'employeur voit les DEUX dimensions séparément.                       │
│  Aucun score composite unique — les deux apportent de l'information    │
│  orthogonale qui ne doit pas être écrasée par une agrégation.           │
└─────────────────────────────────────────────────────────────────────────┘

Pourquoi les deux sont complémentaires et non redondants :

    DNRE seul :
        Identifie le meilleur profil pour un poste de "First Officer"
        en général, peu importe le yacht. Scope : validité construite
        (le profil en lui-même est-il adapté au métier ?).

    MLPSM seul :
        Simule l'intégration dans l'équipe du "Lady Aurora" en ce moment.
        Mais sans filtrer — un candidat instable émotionnellement peut
        obtenir un bon Ŷ_success si les paramètres du yacht l'avantagent.

    Ensemble :
        Le DNRE garantit la qualité intrinsèque du profil.
        Le MLPSM garantit la compatibilité contextuelle avec CE système.
        Un candidat fort dans les deux dimensions = recrutement robuste.

Sources :
    Schmidt, F.L. (2016). The validity and utility of selection methods:
    practical and theoretical implications of 100 years of research.
    (Justification des deux niveaux de validité : de contenu + prévisionnelle)

    Kozlowski, S.W.J. & Bell, B.S. (2003). Work groups and teams in
    organizations. Handbook of Psychology, vol 12.
    (Distinction profil individuel vs dynamiques émergentes d'équipe)

Note sur l'implémentation :
    Les calculs internes délèguent maintenant à pe_fit.master.compute()
    qui unifie PJ/PO/PT/PS Fit dans une architecture cohérente.

    Pour la rétrocompatibilité complète, les champs DNREResult et MLPSMResult
    sont reconstruits depuis PEFitResult via les helpers _build_dnre_from_pe_fit()
    et _build_mlpsm_from_pe_fit(). Les interfaces publiques (PipelineResult,
    PipelineStage, run_batch, run_single) restent inchangées.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

# ── Imports rétrocompatibilité — dataclasses exposées aux consommateurs ────────
# Ces imports restent pour que les code extérieurs puissent importer
# DNREResult / MLPSMResult / SafetyLevel depuis pipeline si besoin.
from app.engine.pe_fit.compat import (
    DNREResult,
    SafetyLevel,
    MLPSMResult,
    DEFAULT_BETAS,
)

# ── Import PE Fit — moteur de calcul principal ────────────────────────────────
from app.engine.pe_fit import master as _pe_fit
from app.engine.pe_fit.master import PEFitResult
from app.engine.pe_fit.pj_fit.safety_barrier import (
    SafetyLevel as PEFitSafetyLevel,
)


# ── Constantes ────────────────────────────────────────────────────────────────

# Un candidat DISQUALIFIED par le DNRE ne passe pas à l'étage MLPSM
# Un candidat HIGH_RISK passe mais avec flag explicite dans le résultat
_DISQUALIFIED_VALUE = "DISQUALIFIED"
_HIGH_RISK_VALUE    = "HIGH_RISK"


# ── Dataclasses ───────────────────────────────────────────────────────────────

@dataclass
class PipelineStage:
    """Résumé d'un étage pour l'affichage frontend."""
    stage_name:  str
    score:       float        # Score principal de l'étage
    label:       str          # Label lisible (ex: "STRONG_FIT", "GOOD_FIT")
    confidence:  str          # "HIGH" | "MEDIUM" | "LOW"
    is_filtered: bool = False # True si le candidat a été bloqué à cet étage


@dataclass
class PipelineResult:
    """
    Résultat du pipeline complet à deux étages pour un candidat.

    ── Étage 1 (DNRE) ─────────────────────────────────────────────────────────
    dnre          : DNREResult complet (G_fit, centile, safety, traits SME)
    dnre_stage    : résumé compact

    ── Étage 2 (MLPSM) ────────────────────────────────────────────────────────
    mlpsm         : MLPSMResult complet (Ŷ_success, F_team delta, etc.)
                    None si candidat DISQUALIFIED en étage 1
    mlpsm_stage   : résumé compact (None si filtré)

    ── Meta ───────────────────────────────────────────────────────────────────
    crew_profile_id  : identifiant du candidat
    is_pipeline_pass : True si le candidat a passé les deux étages
    filtered_at      : "DNRE" | None — étage où le candidat a été stoppé
    all_flags        : flags agrégés des deux étages

    ── Méthodes sérialisation ─────────────────────────────────────────────────
    to_matching_row()   : format compact pour la liste de matching
    to_impact_report()  : rapport détaillé What-If (endpoint /impact)
    to_event_snapshot() : JSON compact pour RecruitmentEvent (DB)
    """
    # Étage 1
    dnre:        DNREResult
    dnre_stage:  PipelineStage

    # Étage 2 (None si filtré)
    mlpsm:       Optional[MLPSMResult] = None
    mlpsm_stage: Optional[PipelineStage] = None

    # Meta
    crew_profile_id:  Optional[str] = None
    is_pipeline_pass: bool = True
    filtered_at:      Optional[str] = None
    all_flags:        List[str] = field(default_factory=list)

    # ── Sérialisation ─────────────────────────────────────────────────────────

    def to_matching_row(self) -> Dict:
        """
        Format compact pour GET /recruitment/campaigns/{id}/matching.
        Présente les deux dimensions côte à côte, sans agrégation.
        """
        row = {
            "crew_profile_id": self.crew_profile_id,
            "is_pipeline_pass": self.is_pipeline_pass,
            "filtered_at": self.filtered_at,

            # ── Dimension 1 : Profil / Poste (DNRE) ──────────────────────────
            "profile_fit": {
                "g_fit":          self.dnre.g_fit,
                "fit_label":      self.dnre.fit_label,
                "overall_centile": self.dnre.overall_centile,
                "centile_by_competency": {
                    k: v.centile for k, v in self.dnre.centile_ranks.items()
                },
                "safety_level":   self.dnre.safety.safety_level.value if self.dnre.safety else "CLEAR",
                "safety_flags":   self.dnre.safety.context_flags if self.dnre.safety else [],
            },

            # ── Dimension 2 : Intégration équipe (MLPSM) ─────────────────────
            "team_integration": self._mlpsm_summary(),
        }
        return row

    def to_impact_report(self) -> Dict:
        """
        Rapport What-If complet pour GET /recruitment/campaigns/{id}/impact/{crew_profile_id}.
        Expose les détails des deux étages + explication de la logique pipeline.
        """
        return {
            "crew_profile_id":   self.crew_profile_id,
            "pipeline_summary": {
                "is_pipeline_pass": self.is_pipeline_pass,
                "filtered_at":      self.filtered_at,
            },

            # ── Étage 1 : DNRE ────────────────────────────────────────────────
            "stage_1_dnre": {
                "title":    "Adéquation Profil / Poste",
                "subtitle": "Ce candidat est-il qualifié pour ce type de rôle ?",
                "g_fit":    self.dnre.g_fit,
                "fit_label": self.dnre.fit_label,
                "overall_centile": self.dnre.overall_centile,
                "confidence": self.dnre.confidence,
                "data_quality": round(self.dnre.data_quality * 100),
                "competency_details": {
                    key: {
                        "label":    sme.competency_label,
                        "s_ic":     sme.score,
                        "centile":  self.dnre.centile_ranks.get(key, None) and
                                    self.dnre.centile_ranks[key].centile,
                        "percentile_label": self.dnre.centile_ranks.get(key, None) and
                                            self.dnre.centile_ranks[key].percentile_label,
                        "pool_n":   self.dnre.centile_ranks.get(key, None) and
                                    self.dnre.centile_ranks[key].pool_stats.n,
                        "trait_breakdown": [
                            {"trait": tc.trait, "score": tc.raw_score,
                             "weight": tc.weight, "is_fallback": tc.is_fallback}
                            for tc in sme.trait_contributions
                        ],
                        "flags": sme.flags,
                    }
                    for key, sme in self.dnre.sme_scores.items()
                },
                "safety": {
                    "level":   self.dnre.safety.safety_level.value if self.dnre.safety else "CLEAR",
                    "flags":   self.dnre.safety.context_flags if self.dnre.safety else [],
                    "triggers": [
                        {"trait": t.trait, "observed": t.observed_score,
                         "threshold": t.threshold, "type": t.veto_type.value,
                         "label": t.label}
                        for t in (self.dnre.safety.triggers if self.dnre.safety else [])
                    ],
                },
            },

            # ── Étage 2 : MLPSM ───────────────────────────────────────────────
            "stage_2_mlpsm": self._mlpsm_full_report(),

            "all_flags": self.all_flags,
        }

    def to_event_snapshot(self) -> Dict:
        """Format compact pour RecruitmentEvent (stockage DB, audit ML)."""
        snap: Dict = {
            "dnre": {
                "g_fit":            self.dnre.g_fit,
                "overall_centile":  self.dnre.overall_centile,
                "sme_scores": {k: v.score for k, v in self.dnre.sme_scores.items()},
                "safety_level":     self.dnre.safety.safety_level.value if self.dnre.safety else "CLEAR",
                "data_quality":     self.dnre.data_quality,
            },
            "mlpsm": None,
            "is_pipeline_pass": self.is_pipeline_pass,
        }
        if self.mlpsm:
            snap["mlpsm"] = self.mlpsm.to_event_snapshot()
        return snap

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _mlpsm_summary(self) -> Dict:
        if not self.mlpsm:
            return {
                "available": False,
                "reason":    f"Filtré à l'étage 1 ({self.filtered_at})" if self.filtered_at else "Non calculé",
            }
        delta = self.mlpsm.f_team_detail.delta if self.mlpsm.f_team_detail else None
        return {
            "available":    True,
            "y_success":    self.mlpsm.y_success,
            "success_label": self.mlpsm.success_label,
            "p_ind":        self.mlpsm.p_ind_score,
            "f_team":       self.mlpsm.f_team_score,
            "f_env":        self.mlpsm.f_env_score,
            "f_lmx":        self.mlpsm.f_lmx_score,
            "team_delta":   delta.delta if delta else None,
            "confidence":   self.mlpsm.confidence,
        }

    def _mlpsm_full_report(self) -> Dict:
        if not self.mlpsm:
            return {
                "title":   "Simulation Intégration Équipe",
                "subtitle": "Comment ce candidat s'intègre-t-il à cet équipage ?",
                "available": False,
                "reason":  "Candidat non qualifié (DNRE étage 1)" if self.filtered_at else "Données équipage insuffisantes",
            }
        report = self.mlpsm.to_impact_report()
        report["title"]    = "Simulation Intégration Équipe"
        report["subtitle"] = "Comment ce candidat s'intègre-t-il à cet équipage ?"
        return report


# ── Helpers de conversion PE Fit → DNRE / MLPSM ──────────────────────────────

def _build_dnre_from_pe_fit(
    pe_result: PEFitResult,
    crew_profile_id: Optional[str] = None,
) -> DNREResult:
    """
    Construit un DNREResult rétrocompatible depuis un PEFitResult.

    Correspondances :
        pj_fit.g_fit          → g_fit
        pj_fit.fit_label      → fit_label
        pj_fit.sme_detail     → sme_scores["C1_individual_performance"]
        pj_fit.safety         → safety (SafetyBarrierResult duck-compatible)
        pj_fit.overall_centile → overall_centile
        pj_fit.data_quality   → data_quality
        pe_result.confidence  → confidence
        pe_result.all_flags   → all_flags

    Note : centile_ranks est vide ({}) — le calcul batch de centiles
    par compétence n'est pas effectué dans pe_fit.master.compute().
    Les tests pipeline ne vérifient pas les valeurs de centile_ranks.
    """
    pj = pe_result.pj_fit

    # sme_scores : dict {competency_key: SMEScoreResult}
    # pj_fit.sme_detail est structurellement identique à DNRE.sme_score.SMEScoreResult
    # (mêmes champs : score, competency_key, competency_label, trait_contributions,
    #  total_weight, data_quality, flags, formula_snapshot)
    sme_scores = {
        pj.sme_detail.competency_key: pj.sme_detail
    }

    # safety : pe_fit SafetyBarrierResult est structurellement identique
    # à DNRE SafetyBarrierResult (mêmes champs : safety_level, context_flags, triggers, etc.)
    # La safety_level de pe_fit est un SafetyLevel de pe_fit — mais .value retourne
    # la même string ("CLEAR", "ADVISORY", "HIGH_RISK", "DISQUALIFIED")

    return DNREResult(
        g_fit=pj.g_fit,
        fit_label=pj.fit_label,
        centile_ranks={},
        overall_centile=pj.overall_centile,
        sme_scores=sme_scores,
        global_fit_detail=None,
        safety=pj.safety,          # duck-compatible SafetyBarrierResult
        f_team_detail=None,
        crew_profile_id=crew_profile_id,
        data_quality=pj.data_quality,
        confidence=pe_result.confidence,
        all_flags=list(pe_result.all_flags),
    )


def _build_mlpsm_from_pe_fit(
    pe_result: PEFitResult,
    betas: Optional[Dict] = None,
) -> Optional[MLPSMResult]:
    """
    Construit un MLPSMResult rétrocompatible depuis un PEFitResult.

    Correspondances :
        pj_fit.p_ind_score → p_ind_score
        pt_fit.score       → f_team_score  (None → 50.0 par défaut)
        po_fit.score       → f_env_score   (None → 50.0 par défaut)
        ps_fit.score       → f_lmx_score   (None → 50.0 par défaut)
        global_score       → y_success (score global PE Fit)

    Les sous-détails (p_ind_detail, f_team_detail, f_env_detail, f_lmx_detail)
    sont les objets pe_fit qui sont structurellement duck-compatibles avec
    les types MLPSM attendus (mêmes champs exposés par to_impact_report()).

    Retourne None si aucune dimension secondaire n'est disponible
    (pt_fit, po_fit, ps_fit tous absents ET score = 0).
    """
    _betas = betas or DEFAULT_BETAS

    p_ind_score  = pe_result.pj_fit.p_ind_score
    f_team_score = pe_result.pt_fit.score if pe_result.pt_fit is not None else 50.0
    f_env_score  = pe_result.po_fit.score if pe_result.po_fit is not None else 50.0
    f_lmx_score  = pe_result.ps_fit.score if pe_result.ps_fit is not None else 50.0

    # Score de succès = global_score PE Fit (moyenne des dimensions disponibles)
    y_success = pe_result.global_score

    # Label succès
    if y_success >= 75:
        success_label = "STRONG_FIT"
    elif y_success >= 60:
        success_label = "GOOD_FIT"
    elif y_success >= 45:
        success_label = "MODERATE_FIT"
    else:
        success_label = "POOR_FIT"

    # Flags consolidés depuis les sous-modules disponibles
    mlpsm_flags: List[str] = []
    if pe_result.pt_fit is not None:
        mlpsm_flags.extend(pe_result.pt_fit.flags)
    if pe_result.po_fit is not None:
        mlpsm_flags.extend(pe_result.po_fit.flags)
    if pe_result.ps_fit is not None:
        mlpsm_flags.extend(pe_result.ps_fit.flags)

    # Data quality globale
    dq_values = [pe_result.pj_fit.data_quality]
    if pe_result.pt_fit is not None:
        dq_values.append(pe_result.pt_fit.data_quality)
    if pe_result.po_fit is not None:
        dq_values.append(pe_result.po_fit.data_quality)
    if pe_result.ps_fit is not None:
        dq_values.append(pe_result.ps_fit.data_quality)
    data_quality = round(sum(dq_values) / len(dq_values), 3)

    # p_ind_detail : pj_fit.p_ind_detail est structurellement compatible
    # avec MLPSM.PIndResult (mêmes champs : score, interaction_term, gca,
    # conscientiousness, experience, data_quality, flags, formula_snapshot)
    p_ind_detail = pe_result.pj_fit.p_ind_detail

    # f_team_detail : pe_fit.pt_fit.FTeamResult est structurellement compatible
    # avec MLPSM.FTeamResult (mêmes champs : score, jerk_filter, faultline,
    # emotional, crew_size, delta, data_quality, flags, formula_snapshot)
    f_team_detail = pe_result.pt_fit

    # f_env_detail : pe_fit.po_fit.FEnvResult est structurellement compatible
    # avec MLPSM.FEnvResult (mêmes champs : score, resources, demands,
    # jdr_ratio, resilience, data_quality, flags, formula_snapshot)
    f_env_detail = pe_result.po_fit

    # f_lmx_detail : pe_fit.ps_fit.FLmxResult est structurellement compatible
    # avec MLPSM.FLmxResult (mêmes champs : score, vectors, distance,
    # dimensions, data_quality, flags, formula_snapshot)
    f_lmx_detail = pe_result.ps_fit

    # Si tous les détails secondaires sont absents, construire des stubs
    # pour éviter une AttributeError dans to_impact_report() / to_event_snapshot()
    if f_team_detail is None:
        from app.engine.pe_fit.pt_fit import f_team as _f_team_pe_fit
        f_team_detail = _f_team_pe_fit.compute([])

    if f_env_detail is None:
        from app.engine.pe_fit.po_fit import f_env as _f_env_pe_fit
        f_env_detail = _f_env_pe_fit.compute({}, {})

    if f_lmx_detail is None:
        from app.engine.pe_fit.ps_fit import f_lmx as _f_lmx_pe_fit
        f_lmx_detail = _f_lmx_pe_fit.compute({}, {})

    # Confidence label
    if data_quality >= 0.85:
        confidence = "HIGH"
    elif data_quality >= 0.60:
        confidence = "MEDIUM"
    else:
        confidence = "LOW"

    return MLPSMResult(
        y_success=y_success,
        y_raw_linear=y_success,     # pas de score linéaire séparé dans pe_fit
        p_ind_score=p_ind_score,
        f_team_score=f_team_score,
        f_env_score=f_env_score,
        f_lmx_score=f_lmx_score,
        p_ind_detail=p_ind_detail,  # type: ignore[arg-type]  # duck-compatible
        f_team_detail=f_team_detail,  # type: ignore[arg-type]  # duck-compatible
        f_env_detail=f_env_detail,    # type: ignore[arg-type]  # duck-compatible
        f_lmx_detail=f_lmx_detail,   # type: ignore[arg-type]  # duck-compatible
        betas_used=_betas.copy(),
        data_quality=data_quality,
        confidence=confidence,
        success_label=success_label,
        all_flags=mlpsm_flags,
        formula_snapshot=(
            f"PE Fit global_score = {y_success} "
            f"(PJ={pe_result.pj_fit.score}, "
            f"PO={pe_result.po_fit.score if pe_result.po_fit else 'N/A'}, "
            f"PT={pe_result.pt_fit.score if pe_result.pt_fit else 'N/A'}, "
            f"PS={pe_result.ps_fit.score if pe_result.ps_fit else 'N/A'})"
        ),
    )


# ── Scoring batch (point d'entrée principal) ──────────────────────────────────

def run_batch(
    candidates: List[Dict],
    current_crew_snapshots: Optional[List[Dict]] = None,
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    betas: Optional[Dict] = None,
    sme_weights_override: Optional[Dict[str, Dict[str, float]]] = None,
    competency_weights: Optional[Dict[str, float]] = None,
    p_ind_omegas: Optional[Dict[str, float]] = None,  # P3 : depuis JobWeightConfig
) -> List[PipelineResult]:
    """
    Exécute le pipeline complet à deux étages sur tous les candidats.

    Délègue à pe_fit.master.compute() pour chaque candidat, puis
    reconstruit DNREResult et MLPSMResult pour la rétrocompatibilité.

    Étape A (PJ Fit) :
        Calcule G_fit + safety pour tous les candidats.
        Identifie les candidats filtrés (DISQUALIFIED).

    Étape B (PO/PT/PS Fit) :
        Exécute les dimensions contextuelles uniquement sur les candidats non-filtrés.
        Les candidats DISQUALIFIED ont mlpsm=None.

    Args:
        candidates              : liste de dicts avec "snapshot", "crew_profile_id",
                                  "experience_years", "position_key"
        current_crew_snapshots  : psychometric_snapshots de l'équipage actuel
        vessel_params           : paramètres JD-R du yacht
        captain_vector          : vecteur capitaine {autonomy, feedback, structure}
        betas                   : betas MLPSM du ModelVersion actif
        sme_weights_override    : poids SME personnalisés par compétence
        competency_weights      : poids inter-compétences DNRE
        p_ind_omegas            : omegas P_ind depuis JobWeightConfig

    Returns:
        Liste de PipelineResult dans l'ordre des candidates, non triée.
        Le tri (par G_fit, par Ŷ_success, ou composite) est laissé
        au recruitment/service.py selon les besoins du frontend.
    """
    if not candidates:
        return []

    pipeline_results: List[PipelineResult] = []

    for idx, candidate in enumerate(candidates):
        crew_id   = str(candidate.get("crew_profile_id", idx))
        snapshot  = candidate.get("snapshot") or {}
        exp_years = candidate.get("experience_years", 0)
        position  = candidate.get("position_key")

        # ── Calcul PE Fit complet ─────────────────────────────────────────────
        pe_result: PEFitResult = _pe_fit.compute(
            snapshot,
            position=position,
            vessel_params=vessel_params,
            captain_vector=captain_vector,
            current_crew_snapshots=current_crew_snapshots,
            sme_weights=sme_weights_override.get(position or "", None) if sme_weights_override else None,
            competency_weights=competency_weights,
            experience_years=exp_years,
        )

        # ── Construction DNREResult (étage 1) ────────────────────────────────
        dnre_result = _build_dnre_from_pe_fit(pe_result, crew_id)
        safety_level_value = pe_result.safety_level  # string : "CLEAR", "HIGH_RISK", etc.

        dnre_stage = PipelineStage(
            stage_name  = "DNRE — Profil / Poste",
            score       = dnre_result.g_fit,
            label       = dnre_result.fit_label,
            confidence  = dnre_result.confidence,
            is_filtered = safety_level_value == _DISQUALIFIED_VALUE,
        )

        all_flags = list(dnre_result.all_flags)

        # ── Filtre HARD ───────────────────────────────────────────────────────
        if safety_level_value == _DISQUALIFIED_VALUE:
            pipeline_results.append(PipelineResult(
                dnre=dnre_result,
                dnre_stage=dnre_stage,
                mlpsm=None,
                mlpsm_stage=None,
                crew_profile_id=crew_id,
                is_pipeline_pass=False,
                filtered_at="DNRE",
                all_flags=all_flags + ["[PIPELINE] Candidat filtré à l'étage DNRE (DISQUALIFIED)"],
            ))
            continue

        # ── Étage 2 : MLPSM reconstruit depuis pe_fit ────────────────────────
        try:
            mlpsm_result: Optional[MLPSMResult] = _build_mlpsm_from_pe_fit(pe_result, betas)
            if mlpsm_result is None:
                raise ValueError("pe_fit ne retourne pas de résultat MLPSM valide")

            mlpsm_stage = PipelineStage(
                stage_name  = "MLPSM — Intégration Équipe",
                score       = mlpsm_result.y_success,
                label       = mlpsm_result.success_label,
                confidence  = mlpsm_result.confidence,
                is_filtered = False,
            )
            all_flags += [f"[MLPSM] {f}" for f in mlpsm_result.all_flags[:5]]
            is_pass = True

        except Exception as e:
            mlpsm_result = None
            mlpsm_stage  = PipelineStage(
                stage_name  = "MLPSM — Intégration Équipe",
                score       = 0.0,
                label       = "UNAVAILABLE",
                confidence  = "LOW",
                is_filtered = False,
            )
            all_flags.append(f"[MLPSM] Erreur calcul : {e}")
            is_pass = True   # DNRE passé = pas disqualifié

        # Flag HIGH_RISK visible même si non filtré
        if safety_level_value == _HIGH_RISK_VALUE:
            all_flags.append("[PIPELINE] Candidat HIGH_RISK — passe avec avertissement")

        pipeline_results.append(PipelineResult(
            dnre=dnre_result,
            dnre_stage=dnre_stage,
            mlpsm=mlpsm_result,
            mlpsm_stage=mlpsm_stage,
            crew_profile_id=crew_id,
            is_pipeline_pass=is_pass,
            filtered_at=None,
            all_flags=all_flags,
        ))

    return pipeline_results


# ── Scoring individuel (What-If) ──────────────────────────────────────────────

def run_single(
    candidate_snapshot: Dict,
    current_crew_snapshots: Optional[List[Dict]] = None,
    vessel_params: Optional[Dict] = None,
    captain_vector: Optional[Dict] = None,
    betas: Optional[Dict] = None,
    pool_context: Optional[Dict[str, Dict[str, float]]] = None,
    sme_weights_override: Optional[Dict[str, Dict[str, float]]] = None,
    competency_weights: Optional[Dict[str, float]] = None,
    position_key: Optional[str] = None,
    experience_years: int = 0,
    crew_profile_id: Optional[str] = None,
    p_ind_omegas: Optional[Dict[str, float]] = None,  # P3 : depuis JobWeightConfig
) -> PipelineResult:
    """
    Pipeline complet pour un seul candidat (rapport What-If détaillé).

    Délègue à pe_fit.master.compute() puis reconstruit les dataclasses
    rétrocompatibles DNREResult et MLPSMResult.

    Le centile DNRE est ignoré (pool_context non utilisé dans pe_fit).
    Sans pool_context → centile absent mais les deux étages s'exécutent.

    Args:
        pool_context : {competency_key: {crew_profile_id: s_ic}}
                       contexte pré-calculé lors du batch précédent.
                       (réservé pour compatibilité API — non utilisé dans pe_fit)
    """
    # Résoudre les sme_weights depuis l'override si disponible
    sme_weights = None
    if sme_weights_override and position_key:
        sme_weights = sme_weights_override.get(position_key)

    # ── Calcul PE Fit complet ─────────────────────────────────────────────────
    pe_result: PEFitResult = _pe_fit.compute(
        candidate_snapshot,
        position=position_key,
        vessel_params=vessel_params,
        captain_vector=captain_vector,
        current_crew_snapshots=current_crew_snapshots,
        sme_weights=sme_weights,
        competency_weights=competency_weights,
        experience_years=experience_years,
    )

    # ── Construction DNREResult (étage 1) ────────────────────────────────────
    dnre_result = _build_dnre_from_pe_fit(pe_result, crew_profile_id)
    safety_level_value = pe_result.safety_level
    all_flags = list(dnre_result.all_flags)

    dnre_stage = PipelineStage(
        stage_name  = "DNRE — Profil / Poste",
        score       = dnre_result.g_fit,
        label       = dnre_result.fit_label,
        confidence  = dnre_result.confidence,
        is_filtered = safety_level_value == _DISQUALIFIED_VALUE,
    )

    if safety_level_value == _DISQUALIFIED_VALUE:
        return PipelineResult(
            dnre=dnre_result,
            dnre_stage=dnre_stage,
            mlpsm=None,
            mlpsm_stage=None,
            crew_profile_id=crew_profile_id,
            is_pipeline_pass=False,
            filtered_at="DNRE",
            all_flags=all_flags + ["[PIPELINE] Filtré à l'étage DNRE (DISQUALIFIED)"],
        )

    # ── Étage 2 : MLPSM reconstruit depuis pe_fit ────────────────────────────
    try:
        mlpsm_result = _build_mlpsm_from_pe_fit(pe_result, betas)
        if mlpsm_result is None:
            raise ValueError("pe_fit ne retourne pas de résultat MLPSM valide")

        mlpsm_stage = PipelineStage(
            stage_name = "MLPSM — Intégration Équipe",
            score      = mlpsm_result.y_success,
            label      = mlpsm_result.success_label,
            confidence = mlpsm_result.confidence,
        )
        all_flags += [f"[MLPSM] {f}" for f in mlpsm_result.all_flags[:5]]
    except Exception as e:
        mlpsm_result = None
        mlpsm_stage  = PipelineStage(
            stage_name = "MLPSM — Intégration Équipe",
            score      = 0.0,
            label      = "UNAVAILABLE",
            confidence = "LOW",
        )
        all_flags.append(f"[MLPSM] Erreur calcul : {e}")

    return PipelineResult(
        dnre=dnre_result,
        dnre_stage=dnre_stage,
        mlpsm=mlpsm_result,
        mlpsm_stage=mlpsm_stage,
        crew_profile_id=crew_profile_id,
        is_pipeline_pass=True,
        filtered_at=None,
        all_flags=all_flags,
    )
