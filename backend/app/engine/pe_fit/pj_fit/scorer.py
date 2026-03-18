# engine/recruitment/pe_fit/pj_fit/scorer.py
"""
PJ-Fit Scorer — Person-Job Fit (C1 : Individual Performance).

Fusionne trois sources de logique :
    1. sme_score (C1 uniquement) → score principal basé sur les poids SME
    2. p_ind                     → score GCA+C+interaction (détail complémentaire)
    3. global_fit / centile_rank → classement relatif dans le pool

Score principal :
    Le PJ-Fit utilise le score SME C1 comme valeur de référence.
    C1 est défini par les poids {gca: 0.60, conscientiousness: 0.40} —
    calibrés sur Schmidt & Hunter (1998) et Sackett et al. (2022).

    Le P_ind (ω₁·GCA + ω₂·C + ω₃·GCA×C/100) est fourni en détail
    complémentaire pour l'audit et l'explication au client.

Centile dynamique :
    Si un pool est fourni ({crew_id: snapshot}), le centile du candidat
    dans ce pool est calculé et intégré dans overall_centile.

Sécurité :
    La safety barrier est évaluée en parallèle — elle produit un adjusted_score
    si des vetos sont déclenchés, mais ne modifie pas score/g_fit directement.

Labels de fit :
    STRONG_FIT   : score ≥ 75
    GOOD_FIT     : score ≥ 60
    MODERATE_FIT : score ≥ 40
    POOR_FIT     : score < 40

Imports :
    Tous les imports pointent vers pe_fit.* — aucune dépendance vers DNRE ou MLPSM.

Sources :
    Schmidt, F.L. & Hunter, J.E. (1998). Psychological Bulletin, 124(2).
    Sackett, P.R. et al. (2022). Journal of Applied Psychology, 107(10).
    Barrick, M.R. & Mount, M.K. (1991). Personnel Psychology, 44(1).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from app.engine.pe_fit.trait_extractor import extract_with_fallback, extract_strict
from app.engine.pe_fit.pj_fit.safety_barrier import (
    evaluate as evaluate_safety,
    SafetyBarrierResult,
    SafetyLevel,
)
from app.engine.pe_fit.pj_fit.centile_rank import (
    compute as centile_compute,
    CentileResult,
)
from app.engine.pe_fit.pj_fit.weights import DEFAULT_PJ_WEIGHTS


# ── Ré-exports des types provenant des sous-modules ───────────────────────────
# Permettent aux appelants de n'importer que depuis scorer.py


# ── Dataclasses internes (miroirs allégés de sme_score / p_ind) ───────────────

@dataclass
class TraitContribution:
    """Contribution d'un trait individuel au score SME."""
    trait:        str
    raw_score:    float
    weight:       float
    contribution: float
    is_fallback:  bool = False


@dataclass
class SMEScoreResult:
    """Résultat du calcul S_{i,c} pour C1 Individual Performance."""
    score:               float
    competency_key:      str
    competency_label:    str = ""
    trait_contributions: List[TraitContribution] = field(default_factory=list)
    total_weight:        float = 0.0
    data_quality:        float = 1.0
    flags:               List[str] = field(default_factory=list)
    formula_snapshot:    str = ""


@dataclass
class GCADetail:
    """Détail de la capacité cognitive."""
    gca_score:           float
    n_cognitive_tests:   int = 0


@dataclass
class ConscientiousnessDetail:
    """Détail de la conscienciosité."""
    c_score:          float
    reliability_flag: bool = True


@dataclass
class ExperienceDetail:
    """Détail de l'expérience."""
    years:         int = 0
    bonus_applied: float = 0.0
    note:          str = "Bonus expérience désactivé (Temps 1)"


@dataclass
class PIndResult:
    """Résultat du calcul P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA×C/100)."""
    score:            float
    interaction_term: float
    gca:              GCADetail
    conscientiousness: ConscientiousnessDetail
    experience:       ExperienceDetail
    data_quality:     float = 1.0
    flags:            List[str] = field(default_factory=list)
    formula_snapshot: str = ""


# ── Dataclass de résultat principal ───────────────────────────────────────────

@dataclass
class PJFitResult:
    """
    Résultat complet du calcul PJ-Fit pour un candidat.

    score         → score principal 0-100 (= SME C1 score, D-A fit)
    p_ind_score   → score GCA+C+interaction (depuis p_ind)
    g_fit         → alias de score (compatibilité pipeline DNRE)
    fit_label     → "STRONG_FIT" | "GOOD_FIT" | "MODERATE_FIT" | "POOR_FIT"

    sme_detail    → détail SME C1 (trait contributions, weights)
    p_ind_detail  → détail P_ind (formule, terme d'interaction)

    centile       → centile du candidat dans le pool (None si pas de pool)
    centile_detail → détail du calcul centile
    overall_centile → valeur numérique du centile (0.0 si pas de pool)

    safety        → résultat de la barrière de sécurité

    ns_fit_score  → N-S Fit score JD-R (None si vessel_params absent)
    motivation_score → motivation fit SDT (None si position absente)
    pj_aggregate_score → moyenne des sous-dimensions disponibles (D-A + NS + motivation)

    data_quality  → qualité des données d'entrée (0.0 - 1.0)
    confidence    → "HIGH" | "MEDIUM" | "LOW"
    all_flags     → liste consolidée de tous les avertissements
    """
    score:         float
    p_ind_score:   float
    g_fit:         float   # alias de score pour compatibilité pipeline

    fit_label:     str

    sme_detail:    SMEScoreResult
    p_ind_detail:  PIndResult

    centile:       Optional[float] = None
    centile_detail: Optional[CentileResult] = None
    overall_centile: float = 0.0

    safety:        Optional[SafetyBarrierResult] = None

    ns_fit_score:        Optional[float] = None   # N-S Fit score (JDR)
    motivation_score:    Optional[float] = None   # motivation_fit score
    pj_aggregate_score:  Optional[float] = None   # moyenne des sous-dimensions disponibles

    data_quality:  float = 1.0
    confidence:    str = "HIGH"
    all_flags:     List[str] = field(default_factory=list)


# ── Constantes P_ind ──────────────────────────────────────────────────────────

_OMEGA_GCA    = 0.55
_OMEGA_C      = 0.35
_OMEGA_I      = 0.10
_FALLBACK_GCA = 50.0
_FALLBACK_C   = 50.0


# ── Helpers internes ──────────────────────────────────────────────────────────

def _compute_sme_c1(
    snapshot: Dict,
    weights: Dict[str, float],
) -> SMEScoreResult:
    """
    Calcule S_{i,C1} = Σ(w_t · x_{i,t}) / Σ(w_t).

    Formule identique à DNRE/sme_score.compute() pour C1.
    Utilise extract_with_fallback() pour l'extraction des traits.
    """
    flags: List[str] = []
    trait_contributions: List[TraitContribution] = []
    weighted_sum   = 0.0
    total_weight   = 0.0
    fallback_count = 0

    for trait, weight in weights.items():
        x_it = extract_with_fallback(snapshot, trait)
        is_fallback = extract_strict(snapshot, trait) is None
        contribution = weight * x_it

        if is_fallback:
            fallback_count += 1
            flags.append(f"FALLBACK_{trait.upper()}: score médian utilisé (50.0)")

        trait_contributions.append(TraitContribution(
            trait=trait,
            raw_score=round(x_it, 1),
            weight=weight,
            contribution=round(contribution, 2),
            is_fallback=is_fallback,
        ))
        weighted_sum += contribution
        total_weight += weight

    if total_weight == 0:
        return SMEScoreResult(
            score=_FALLBACK_GCA,
            competency_key="C1_individual_performance",
            competency_label="Performance Individuelle",
            flags=["ZERO_WEIGHT: somme des poids = 0"],
            data_quality=0.0,
        )

    s_ic = weighted_sum / total_weight
    score = round(max(0.0, min(100.0, s_ic)), 1)

    n_traits = len(weights)
    data_quality = round(1.0 - (fallback_count / n_traits), 3) if n_traits > 0 else 0.0

    contrib_str = " + ".join(
        f"{tc.weight}×{tc.raw_score:.0f}" for tc in trait_contributions
    )
    formula = (
        f"S[C1] = ({contrib_str}) / {total_weight} = {s_ic:.1f} → {score}"
    )

    return SMEScoreResult(
        score=score,
        competency_key="C1_individual_performance",
        competency_label="Performance Individuelle",
        trait_contributions=trait_contributions,
        total_weight=total_weight,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )


def _compute_p_ind(
    snapshot: Dict,
    experience_years: int = 0,
) -> PIndResult:
    """
    Calcule P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA×C/100).

    Logique identique à MLPSM/p_ind.compute().
    Utilise extract_with_fallback() pour l'extraction des traits.
    """
    flags: List[str] = []
    data_quality = 1.0

    # ── Extraction GCA ──────────────────────────────────────
    gca_raw = extract_with_fallback(snapshot, "gca")
    gca_fallback = extract_strict(snapshot, "gca") is None
    cog = snapshot.get("cognitive") or {}
    n_tests = cog.get("n_tests", 0)

    if gca_fallback or n_tests == 0:
        flags.append("GCA_MISSING: aucun test cognitif passé, score médian utilisé (50.0)")
        data_quality -= 0.35
        n_tests = 0

    gca_detail = GCADetail(gca_score=gca_raw, n_cognitive_tests=n_tests)

    # ── Extraction Conscienciosité ───────────────────────────
    big_five = snapshot.get("big_five") or {}
    if big_five is None:
        flags.append("BIG_FIVE_MISSING: snapshot Big Five absent, C = 50.0 par défaut")
        data_quality -= 0.15

    c_raw = extract_with_fallback(snapshot, "conscientiousness")
    c_fallback = extract_strict(snapshot, "conscientiousness") is None
    c_data = big_five.get("conscientiousness") or {} if big_five else {}
    reliable = (
        c_data.get("reliable", True) if isinstance(c_data, dict) else True
    )
    if not reliable:
        flags.append("C_UNRELIABLE: test conscienciosité jugé non fiable (social desirability)")
        data_quality -= 0.20

    c_detail = ConscientiousnessDetail(c_score=c_raw, reliability_flag=reliable)

    data_quality = max(0.0, data_quality)

    # ── Calcul P_ind ─────────────────────────────────────────
    gca = gca_detail.gca_score
    c   = c_detail.c_score

    interaction_raw     = (gca * c) / 100.0
    interaction_contrib = _OMEGA_I * interaction_raw

    p_ind_raw = (gca * _OMEGA_GCA) + (c * _OMEGA_C) + interaction_contrib
    score = round(max(0.0, min(100.0, p_ind_raw)), 1)

    exp_detail = ExperienceDetail(years=experience_years)

    formula = (
        f"P_ind = ({gca:.1f} × {_OMEGA_GCA})"
        f" + ({c:.1f} × {_OMEGA_C})"
        f" + ({gca:.1f} × {c:.1f} / 100 × {_OMEGA_I})"
        f" = {gca * _OMEGA_GCA:.1f} + {c * _OMEGA_C:.1f}"
        f" + {interaction_contrib:.1f}"
        f" = {p_ind_raw:.1f} → {score}"
    )

    return PIndResult(
        score=score,
        interaction_term=round(interaction_contrib, 2),
        gca=gca_detail,
        conscientiousness=c_detail,
        experience=exp_detail,
        data_quality=data_quality,
        flags=flags,
        formula_snapshot=formula,
    )


def _fit_label(score: float) -> str:
    """Attribue un label de fit selon le score SME C1."""
    if score >= 75:
        return "STRONG_FIT"
    if score >= 60:
        return "GOOD_FIT"
    if score >= 40:
        return "MODERATE_FIT"
    return "POOR_FIT"


def _confidence(data_quality: float) -> str:
    if data_quality >= 0.8:
        return "HIGH"
    if data_quality >= 0.5:
        return "MEDIUM"
    return "LOW"


# ── Fonction principale ───────────────────────────────────────────────────────

def compute(
    snapshot: Dict,
    position: Optional[str] = None,
    pool: Optional[Dict[str, Dict]] = None,
    sme_weights: Optional[Dict[str, float]] = None,
    experience_years: int = 0,
    vessel_params: Optional[Dict] = None,
) -> PJFitResult:
    """
    Calcule le PJ-Fit (Person-Job Fit) pour un candidat.

    Args:
        snapshot         : psychometric_snapshot du CrewProfile
        position         : YachtPosition.value — utilisé pour les vetos position-scoped
                           et le profil motivationnel idéal
        pool             : {crew_id: snapshot} pour le calcul du centile dynamique.
                           None → centile non calculé, overall_centile = 0.0
        sme_weights      : poids SME C1 personnalisés (DEFAULT_PJ_WEIGHTS si None)
        experience_years : années d'expérience du candidat
        vessel_params    : paramètres JD-R du yacht (active N-S Fit JDR)

    Returns:
        PJFitResult avec score, p_ind_score, fit_label, safety, centile,
        ns_fit_score, motivation_score, pj_aggregate_score.

    Étapes :
        1. Score SME C1 = Σ(w_t · x_{i,t}) / Σ(w_t)  [gca, conscientiousness]
        2. Score P_ind = ω₁·GCA + ω₂·C + ω₃·(GCA×C/100)
        3. Score principal = SME C1 (D-A fit — P_ind = détail complémentaire)
        4. Safety barrier = évaluation des vetos psychométriques
        5. Centile = rang dans le pool fourni (optionnel)
        6. N-S Fit (JDR) = buffer effect si vessel_params fourni
        7. Motivation Fit (SDT) = distance cosinus si position fourni
        8. pj_aggregate = moyenne des sous-dimensions disponibles
    """
    from app.engine.pe_fit.pj_fit.needs_supplies import jdr as _jdr
    from app.engine.pe_fit.pj_fit.motivation_fit import scorer as _mfit

    weights = sme_weights or DEFAULT_PJ_WEIGHTS

    # ── 1. Score SME C1 ─────────────────────────────────────
    sme_result = _compute_sme_c1(snapshot, weights)

    # ── 2. Score P_ind ───────────────────────────────────────
    p_ind_result = _compute_p_ind(snapshot, experience_years)

    # ── 3. Score principal et qualité ───────────────────────
    da_score = sme_result.score
    score = da_score
    data_quality = min(sme_result.data_quality, p_ind_result.data_quality)

    # ── 4. Safety barrier ────────────────────────────────────
    safety_result = evaluate_safety(
        candidate_snapshot=snapshot,
        g_fit_score=score,
        position_key=position,
    )

    # ── 5. Centile dynamique (si pool fourni) ─────────────────
    centile_result: Optional[CentileResult] = None
    centile_value:  Optional[float] = None
    overall_centile: float = 0.0

    if pool:
        # Calculer le score SME C1 pour chaque candidat du pool
        pool_scores: List[float] = []
        for _, pool_snapshot in pool.items():
            pool_sme = _compute_sme_c1(pool_snapshot, weights)
            pool_scores.append(pool_sme.score)

        centile_result = centile_compute(
            candidate_score=score,
            pool_scores=pool_scores,
            competency_key="C1_individual_performance",
        )
        centile_value   = centile_result.centile
        overall_centile = centile_result.centile

    # ── 6. N-S Fit (JDR) — optionnel si vessel_params fourni ──
    jdr_result = _jdr.compute(snapshot, vessel_params)
    ns_fit_score: Optional[float] = jdr_result.score if jdr_result is not None else None

    # ── 7. Motivation Fit — optionnel si position fourni ──────
    motivation_result = _mfit.compute(snapshot, position)
    motivation_score: Optional[float] = motivation_result.score if motivation_result is not None else None

    # ── 8. Score P-J agrégé = moyenne des sous-dimensions disponibles
    # Poids égaux jusqu'au retrain empirique (N≥150)
    # score (D-A) est toujours présent
    sub_scores = [da_score]
    if ns_fit_score is not None:
        sub_scores.append(ns_fit_score)
    if motivation_score is not None:
        sub_scores.append(motivation_score)
    pj_aggregate = round(sum(sub_scores) / len(sub_scores), 1)

    # ── 9. Consolidation des flags ────────────────────────────
    all_flags: List[str] = []
    all_flags.extend(sme_result.flags)
    all_flags.extend(p_ind_result.flags)
    if safety_result.context_flags:
        all_flags.extend(safety_result.context_flags)
    if centile_result and centile_result.flags:
        all_flags.extend(centile_result.flags)
    if jdr_result and jdr_result.flags:
        all_flags.extend([f"[NS] {f}" for f in jdr_result.flags])
    if motivation_result and motivation_result.flags:
        all_flags.extend([f"[MOT] {f}" for f in motivation_result.flags])

    return PJFitResult(
        score=score,
        p_ind_score=p_ind_result.score,
        g_fit=score,
        fit_label=_fit_label(score),
        sme_detail=sme_result,
        p_ind_detail=p_ind_result,
        centile=centile_value,
        centile_detail=centile_result,
        overall_centile=overall_centile,
        safety=safety_result,
        ns_fit_score=ns_fit_score,
        motivation_score=motivation_score,
        pj_aggregate_score=pj_aggregate,
        data_quality=data_quality,
        confidence=_confidence(data_quality),
        all_flags=all_flags,
    )
