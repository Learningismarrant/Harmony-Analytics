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
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.recruitment.DNRE import master as _dnre
from app.engine.recruitment.DNRE.master import DNREResult
from app.engine.recruitment.DNRE.safety_barrier import SafetyLevel
from app.engine.recruitment.MLPSM import master as _mlpsm
from app.engine.recruitment.MLPSM.master import MLPSMResult


# ── Constantes ────────────────────────────────────────────────────────────────

# Un candidat DISQUALIFIED par le DNRE ne passe pas à l'étage MLPSM
# Un candidat HIGH_RISK passe mais avec flag explicite dans le résultat
HARD_FILTER_LEVELS = {SafetyLevel.DISQUALIFIED}


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

    Étape A (DNRE batch) :
        Calcule G_fit + centile (batch obligatoire pour le centile) pour tous.
        Identifie les candidats filtrés (DISQUALIFIED).

    Étape B (MLPSM individuel) :
        Exécute le simulateur uniquement sur les candidats non-filtrés.
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

    Returns:
        Liste de PipelineResult dans l'ordre des candidates, non triée.
        Le tri (par G_fit, par Ŷ_success, ou composite) est laissé
        au recruitment/service.py selon les besoins du frontend.
    """
    if not candidates:
        return []

    # ── Étape A : DNRE batch ─────────────────────────────────────────────────
    dnre_results: List[DNREResult] = _dnre.compute_batch(
        candidates=candidates,
        current_crew_snapshots=current_crew_snapshots,
        vessel_params=vessel_params,
        captain_vector=captain_vector,
        sme_weights_override=sme_weights_override,
        competency_weights=competency_weights,
    )

    # ── Étape B : MLPSM individuel sur les candidats qualifiés ───────────────
    pipeline_results: List[PipelineResult] = []

    for idx, (candidate, dnre_result) in enumerate(zip(candidates, dnre_results)):
        crew_id    = str(candidate.get("crew_profile_id", idx))
        snapshot   = candidate.get("snapshot") or {}
        exp_years  = candidate.get("experience_years", 0)
        position   = candidate.get("position_key", "")
        safety_lvl = dnre_result.safety.safety_level if dnre_result.safety else SafetyLevel.CLEAR

        # Construction de l'étage 1
        dnre_stage = PipelineStage(
            stage_name  = "DNRE — Profil / Poste",
            score       = dnre_result.g_fit,
            label       = dnre_result.fit_label,
            confidence  = dnre_result.confidence,
            is_filtered = safety_lvl in HARD_FILTER_LEVELS,
        )

        all_flags = list(dnre_result.all_flags)

        # ── Filtre HARD ───────────────────────────────────────────────────────
        if safety_lvl in HARD_FILTER_LEVELS:
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

        # ── Étage 2 : MLPSM ──────────────────────────────────────────────────
        try:
            mlpsm_result: MLPSMResult = _mlpsm.compute_with_delta(
                candidate_snapshot=snapshot,
                current_crew_snapshots=current_crew_snapshots or [],
                vessel_params=vessel_params or {},
                captain_vector=captain_vector or {},
                betas=betas,
                experience_years=exp_years,
                position_key=position,
                p_ind_omegas=p_ind_omegas,
            )
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
            # MLPSM non calculable (données insuffisantes) — pas bloquant
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
        if safety_lvl == SafetyLevel.HIGH_RISK:
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

    Le centile DNRE est calculé si pool_context est fourni.
    Sans pool_context → centile absent mais les deux étages s'exécutent.

    Args:
        pool_context : {competency_key: {crew_profile_id: s_ic}}
                       contexte pré-calculé lors du batch précédent.
    """
    # ── Étage 1 : DNRE ───────────────────────────────────────────────────────
    dnre_result = _dnre.compute_single(
        candidate_snapshot=candidate_snapshot,
        current_crew_snapshots=current_crew_snapshots,
        vessel_params=vessel_params,
        captain_vector=captain_vector,
        pool_context=pool_context,
        sme_weights_override=sme_weights_override,
        competency_weights=competency_weights,
        position_key=position_key,
        crew_profile_id=crew_profile_id,
    )

    safety_lvl = dnre_result.safety.safety_level if dnre_result.safety else SafetyLevel.CLEAR
    all_flags  = list(dnre_result.all_flags)

    dnre_stage = PipelineStage(
        stage_name  = "DNRE — Profil / Poste",
        score       = dnre_result.g_fit,
        label       = dnre_result.fit_label,
        confidence  = dnre_result.confidence,
        is_filtered = safety_lvl in HARD_FILTER_LEVELS,
    )

    if safety_lvl in HARD_FILTER_LEVELS:
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

    # ── Étage 2 : MLPSM ──────────────────────────────────────────────────────
    try:
        mlpsm_result = _mlpsm.compute_with_delta(
            candidate_snapshot=candidate_snapshot,
            current_crew_snapshots=current_crew_snapshots or [],
            vessel_params=vessel_params or {},
            captain_vector=captain_vector or {},
            betas=betas,
            experience_years=experience_years,
            position_key=position_key or "",
            p_ind_omegas=p_ind_omegas,
        )
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