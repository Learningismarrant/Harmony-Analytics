# tests/engine/recruitment/dnre/test_dnre.py
"""
Tests unitaires du scoring PJ-Fit (ancien DNRE).
Redirigé vers pe_fit après suppression de DNRE/.

Couverture :
    - PJ-Fit scorer (C1 : Individual Performance) — équivalent sme_score C1
    - Centile rank dynamique (Tukey) — pe_fit/pj_fit/centile_rank
    - Safety barrier (pénalité continue) — pe_fit/pj_fit/safety_barrier
    - PEFit master : compute_batch via pipeline.run_batch
    - PE Fit compute (équivalent dnre.compute_single / compute_batch)

Les anciens modules DNRE/ ont été supprimés.
Toute la logique est désormais dans pe_fit/.
"""
import pytest

from app.engine.pe_fit.pj_fit import scorer as pj_scorer
from app.engine.pe_fit.pj_fit import centile_rank
from app.engine.pe_fit.pj_fit.safety_barrier import (
    SafetyLevel,
    VetoType,
    VetoRule,
    evaluate as safety_evaluate,
)
from app.engine.pe_fit import master as pe_fit_master
from app.engine.pe_fit.master import PEFitResult

pytestmark = pytest.mark.engine


# ═══════════════════════════════════════════════════════════
# FIXTURES
# ═══════════════════════════════════════════════════════════

@pytest.fixture
def snapshot_strong():
    """Profil idéal — tous traits élevés."""
    return {
        "big_five": {
            "agreeableness":     {"score": 80.0},
            "conscientiousness": {"score": 78.0},
            "openness":          {"score": 70.0},
            "neuroticism":       {"score": 22.0},   # ES = 78
        },
        "cognitive":  {"gca_score": 76.0, "n_tests": 2},
        "resilience": 74.0,
        "leadership_preferences": {
            "autonomy_preference": 0.60,
            "feedback_preference": 0.50,
            "structure_preference": 0.70,
        },
    }


@pytest.fixture
def snapshot_disqualified():
    """Profil avec ES < 15 → Hard Veto."""
    return {
        "big_five": {
            "agreeableness":     {"score": 65.0},
            "conscientiousness": {"score": 70.0},
            "openness":          {"score": 60.0},
            "neuroticism":       {"score": 92.0},   # ES = 8 → HARD VETO
        },
        "cognitive":  {"gca_score": 68.0, "n_tests": 1},
        "resilience": 20.0,
    }


@pytest.fixture
def snapshot_high_risk():
    """Profil avec ES entre 15-30 → Soft Veto."""
    return {
        "big_five": {
            "agreeableness":     {"score": 60.0},
            "conscientiousness": {"score": 65.0},
            "openness":          {"score": 58.0},
            "neuroticism":       {"score": 76.0},   # ES = 24 → SOFT VETO
        },
        "cognitive":  {"gca_score": 62.0, "n_tests": 1},
        "resilience": 38.0,
    }


@pytest.fixture
def snapshot_partial():
    """Profil avec données partielles — fallbacks."""
    return {
        "big_five": {
            "agreeableness": {"score": 70.0},
            # conscientiousness manquant
            "neuroticism": {"score": 35.0},
        },
        # pas de cognitive, pas de resilience
    }


@pytest.fixture
def crew_snapshots():
    return [
        {
            "big_five": {
                "agreeableness":     {"score": 73.0},
                "conscientiousness": {"score": 76.0},
                "neuroticism":       {"score": 27.0},
            }
        },
        {
            "big_five": {
                "agreeableness":     {"score": 68.0},
                "conscientiousness": {"score": 72.0},
                "neuroticism":       {"score": 31.0},
            }
        },
    ]


# ═══════════════════════════════════════════════════════════
# TESTS PJ-FIT SCORER (équivalent SME Score C1)
# ═══════════════════════════════════════════════════════════

class TestPJFitScorer:
    """Tests du scorer PJ-Fit (C1 Individual Performance — équivalent sme_score)."""

    def test_strong_candidate_high_score(self, snapshot_strong):
        result = pj_scorer.compute(snapshot_strong)
        # PJ-Fit utilise gca (0.60) + conscientiousness (0.40)
        assert result.score >= 60.0
        assert result.data_quality > 0.5

    def test_formula_c1_matches_manual_calc(self, snapshot_strong):
        """S[C1] = (0.60×76 + 0.40×78) / 1.0 = 76.8"""
        result = pj_scorer.compute(snapshot_strong)
        expected = (0.60 * 76.0 + 0.40 * 78.0) / 1.0
        assert abs(result.score - expected) < 0.5

    def test_partial_snapshot_uses_fallback(self, snapshot_partial):
        result = pj_scorer.compute(snapshot_partial)
        # GCA manquant → fallback ; conscientiousness manquant → fallback
        assert result.data_quality < 1.0
        # Flag FALLBACK présent dans le résultat SME ou P_ind
        has_fallback_flag = (
            any("FALLBACK" in f or "MISSING" in f for f in result.all_flags)
        )
        assert has_fallback_flag

    def test_p_ind_score_in_bounds(self, snapshot_strong):
        result = pj_scorer.compute(snapshot_strong)
        assert 0.0 <= result.p_ind_score <= 100.0

    def test_fit_label_assigned(self, snapshot_strong):
        result = pj_scorer.compute(snapshot_strong)
        assert result.fit_label in ("STRONG_FIT", "GOOD_FIT", "MODERATE_FIT", "POOR_FIT")

    def test_g_fit_alias_equals_score(self, snapshot_strong):
        result = pj_scorer.compute(snapshot_strong)
        assert result.g_fit == result.score


# ═══════════════════════════════════════════════════════════
# TESTS CENTILE RANK (Étape 2 — pe_fit/pj_fit/centile_rank)
# ═══════════════════════════════════════════════════════════

class TestCentileRank:

    def test_best_in_pool_top_centile(self):
        pool = [40.0, 50.0, 60.0, 70.0, 80.0]
        result = centile_rank.compute(candidate_score=80.0, pool_scores=pool)
        assert result.centile >= 80.0

    def test_worst_in_pool_low_centile(self):
        pool = [40.0, 50.0, 60.0, 70.0, 80.0]
        result = centile_rank.compute(candidate_score=40.0, pool_scores=pool)
        assert result.centile <= 20.0

    def test_median_candidate_near_50(self):
        pool = [30.0, 40.0, 50.0, 60.0, 70.0]
        result = centile_rank.compute(candidate_score=50.0, pool_scores=pool)
        assert 40.0 <= result.centile <= 60.0

    def test_tukey_formula_ex_aequo(self):
        """Deux candidats à 60.0 doivent recevoir le même centile via f_i/2."""
        pool = [40.0, 60.0, 60.0, 80.0]
        r1 = centile_rank.compute(60.0, pool)
        r2 = centile_rank.compute(60.0, pool)
        assert r1.centile == r2.centile
        assert r1.f_i == 2   # deux ex-aequo

    def test_empty_pool_returns_50(self):
        result = centile_rank.compute(candidate_score=75.0, pool_scores=[])
        assert result.centile == 50.0
        assert result.confidence == "LOW"

    def test_singleton_returns_50(self):
        result = centile_rank.compute(candidate_score=75.0, pool_scores=[75.0])
        assert result.centile == 50.0

    def test_small_pool_medium_confidence(self):
        pool = [40.0, 75.0, 80.0]
        result = centile_rank.compute(75.0, pool)
        assert result.confidence == "MEDIUM"

    def test_large_pool_high_confidence(self):
        pool = [float(x) for x in range(0, 100, 10)]  # 10 candidats
        result = centile_rank.compute(50.0, pool)
        assert result.confidence == "HIGH"

    def test_rank_coherent(self):
        pool = [30.0, 50.0, 70.0, 85.0, 90.0]
        result = centile_rank.compute(90.0, pool)
        assert result.rank == 1

    def test_centile_clamped_0_100(self):
        result = centile_rank.compute(100.0, [100.0, 100.0, 100.0])
        assert 0.0 <= result.centile <= 100.0


# ═══════════════════════════════════════════════════════════
# TESTS SAFETY BARRIER — Pénalité Continue
# ═══════════════════════════════════════════════════════════

class TestSafetyBarrier:
    """
    La barrière de sécurité utilise une pénalité logistique continue.
    Comportement attendu :
        - CLEAR      : penalty_multiplier=1.0, adjusted_score=None
        - ADVISORY   : penalty_multiplier=1.0, adjusted_score=None
        - HIGH_RISK  : 0 < penalty_multiplier < 1, adjusted_score < g_fit
        - DISQUALIFIED : penalty_multiplier ≈ 0, adjusted_score ≈ 0 (quasi-nul)
    """

    def test_strong_candidate_clear(self, snapshot_strong):
        result = safety_evaluate(snapshot_strong, g_fit_score=70.0)
        assert result.safety_level == SafetyLevel.CLEAR
        assert not result.g_fit_suspended
        assert result.adjusted_score is None
        assert result.penalty_multiplier == 1.0

    def test_disqualified_es_below_15_penalty_near_zero(self, snapshot_disqualified):
        """ES=8 (< seuil HARD 15) → safety_level=DISQUALIFIED."""
        result = safety_evaluate(snapshot_disqualified, g_fit_score=65.0)
        assert result.safety_level == SafetyLevel.DISQUALIFIED
        assert result.g_fit_suspended
        hard_triggers = [t for t in result.triggers if t.veto_type == VetoType.HARD]
        assert len(hard_triggers) >= 1

        # Score quasi-nul (pénalité continue)
        assert result.adjusted_score is not None
        assert result.adjusted_score < 5.0
        assert result.adjusted_score > 0.0
        assert result.penalty_multiplier < 0.10

    def test_disqualified_penalty_multiplier_logged_per_trigger(self, snapshot_disqualified):
        """Chaque VetoTrigger porte son penalty_multiplier individuel."""
        result = safety_evaluate(snapshot_disqualified, g_fit_score=65.0)
        for t in result.triggers:
            if t.veto_type == VetoType.HARD:
                assert 0.0 < t.penalty_multiplier < 0.5

    def test_high_risk_es_between_15_30_score_reduced(self, snapshot_high_risk):
        """ES=24 (entre seuils HARD 15 et SOFT 30) → HIGH_RISK."""
        g_fit = 60.0
        result = safety_evaluate(snapshot_high_risk, g_fit_score=g_fit)
        assert result.safety_level == SafetyLevel.HIGH_RISK
        assert result.g_fit_suspended
        assert result.adjusted_score is not None
        assert result.adjusted_score < g_fit
        assert result.adjusted_score > 0.0
        assert 0.0 < result.penalty_multiplier < 1.0

    def test_penalite_croissante_avec_distance_au_seuil(self):
        snap_close = {
            "big_five": {
                "agreeableness":     {"score": 60.0},
                "conscientiousness": {"score": 65.0},
                "neuroticism":       {"score": 75.0},   # ES = 25
            }
        }
        snap_far = {
            "big_five": {
                "agreeableness":     {"score": 60.0},
                "conscientiousness": {"score": 65.0},
                "neuroticism":       {"score": 82.0},   # ES = 18
            }
        }
        result_close = safety_evaluate(snap_close, g_fit_score=65.0)
        result_far   = safety_evaluate(snap_far,   g_fit_score=65.0)

        assert result_close.safety_level == SafetyLevel.HIGH_RISK
        assert result_far.safety_level   == SafetyLevel.HIGH_RISK
        assert result_close.penalty_multiplier > result_far.penalty_multiplier
        assert result_close.adjusted_score > result_far.adjusted_score

    def test_penalite_continue_dans_zone_declenchee(self):
        """Continuité de la pénalité logistique dans la zone en dessous du seuil."""
        def make_snap(es: float) -> dict:
            neuroticism = 100.0 - es
            return {
                "big_five": {
                    "agreeableness":     {"score": 60.0},
                    "conscientiousness": {"score": 65.0},
                    "neuroticism":       {"score": neuroticism},
                }
            }

        result_27 = safety_evaluate(make_snap(27.0), g_fit_score=65.0)
        result_22 = safety_evaluate(make_snap(22.0), g_fit_score=65.0)
        result_16 = safety_evaluate(make_snap(16.0), g_fit_score=65.0)

        assert result_27.safety_level == SafetyLevel.HIGH_RISK
        assert result_22.safety_level == SafetyLevel.HIGH_RISK
        assert result_16.safety_level == SafetyLevel.HIGH_RISK

        assert result_27.penalty_multiplier > result_22.penalty_multiplier > result_16.penalty_multiplier

        diff_27_22 = result_27.penalty_multiplier - result_22.penalty_multiplier
        diff_22_16 = result_22.penalty_multiplier - result_16.penalty_multiplier
        assert diff_27_22 < 0.30, f"Saut trop brusque entre ES=27 et ES=22 : {diff_27_22:.3f}"
        assert diff_22_16 < 0.30, f"Saut trop brusque entre ES=22 et ES=16 : {diff_22_16:.3f}"

    def test_advisory_resilience_low(self):
        snapshot = {
            "big_five": {
                "agreeableness":     {"score": 70.0},
                "conscientiousness": {"score": 68.0},
                "neuroticism":       {"score": 35.0},
            },
            "cognitive": {"gca_score": 65.0},
            "resilience": 28.0,   # < 35 → ADVISORY
        }
        result = safety_evaluate(snapshot, g_fit_score=65.0)
        assert result.safety_level == SafetyLevel.ADVISORY
        assert not result.g_fit_suspended
        assert result.adjusted_score is None
        assert result.penalty_multiplier == 1.0

    def test_advisory_ne_penalise_pas_le_score(self):
        snap_advisory = {
            "big_five": {
                "agreeableness":     {"score": 80.0},
                "conscientiousness": {"score": 28.0},  # < 35 → ADVISORY
                "neuroticism":       {"score": 30.0},
            },
            "resilience": 32.0,
        }
        result = safety_evaluate(snap_advisory, g_fit_score=70.0)
        assert result.safety_level == SafetyLevel.ADVISORY
        assert result.penalty_multiplier == 1.0
        assert result.adjusted_score is None

    def test_custom_rules_applied(self, snapshot_strong):
        custom_rules = [
            VetoRule(
                trait="gca",
                threshold=80.0,
                veto_type=VetoType.SOFT,
                label="GCA insuffisant pour ce poste",
            )
        ]
        # GCA = 76 mais seuil = 80 → SOFT VETO → score réduit
        result = safety_evaluate(
            snapshot_strong, g_fit_score=70.0, veto_rules=custom_rules
        )
        assert result.safety_level == SafetyLevel.HIGH_RISK
        assert result.adjusted_score < 70.0

    def test_custom_rule_steepness_override(self, snapshot_strong):
        custom_rules = [
            VetoRule(
                trait="gca",
                threshold=80.0,
                veto_type=VetoType.SOFT,
                label="Règle test steepness personnalisé",
                steepness=0.50,
            )
        ]
        result = safety_evaluate(
            snapshot_strong, g_fit_score=70.0, veto_rules=custom_rules
        )
        assert result.safety_level == SafetyLevel.HIGH_RISK
        trigger = result.triggers[0]
        assert trigger.penalty_multiplier < 0.20

    def test_position_scoped_rule_not_applied(self, snapshot_strong):
        captain_rules = [
            VetoRule(
                trait="gca",
                threshold=80.0,
                veto_type=VetoType.HARD,
                label="GCA minimal Capitaine",
                positions_scope=["Captain"],
            )
        ]
        result = safety_evaluate(
            snapshot_strong,
            g_fit_score=70.0,
            veto_rules=captain_rules,
            position_key="Deckhand",
        )
        assert result.safety_level == SafetyLevel.CLEAR

    def test_unmeasured_trait_no_veto(self):
        snapshot = {"big_five": {"agreeableness": {"score": 70.0}}}
        result = safety_evaluate(snapshot, g_fit_score=65.0)
        es_triggers = [t for t in result.triggers if t.trait == "emotional_stability"]
        assert len(es_triggers) == 0

    def test_penalty_multiplier_expose_dans_result(self, snapshot_strong):
        result = safety_evaluate(snapshot_strong, g_fit_score=70.0)
        assert hasattr(result, "penalty_multiplier")
        assert isinstance(result.penalty_multiplier, float)
        assert 0.0 <= result.penalty_multiplier <= 1.0

    def test_audit_trail_contient_penalite(self, snapshot_high_risk):
        result = safety_evaluate(snapshot_high_risk, g_fit_score=60.0)
        penalty_entries = [line for line in result.audit_trail if "penalty=" in line]
        assert len(penalty_entries) > 0


# ═══════════════════════════════════════════════════════════
# TESTS PE FIT MASTER (équivalent DNRE master)
# ═══════════════════════════════════════════════════════════

class TestPEFitMaster:
    """
    Tests du master PE Fit qui remplace compute_batch/compute_single du DNRE.
    On utilise pe_fit.master.compute() sur chaque snapshot et on vérifie
    les propriétés attendues du PEFitResult.
    """

    def test_compute_returns_pe_fit_result(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert isinstance(result, PEFitResult)

    def test_strong_beats_high_risk(self, snapshot_strong, snapshot_high_risk):
        strong = pe_fit_master.compute(snapshot_strong)
        risky  = pe_fit_master.compute(snapshot_high_risk)
        assert strong.pj_fit.score > risky.pj_fit.score

    def test_disqualified_safety_level(self, snapshot_disqualified):
        result = pe_fit_master.compute(snapshot_disqualified)
        assert result.is_disqualified
        assert result.safety_level == SafetyLevel.DISQUALIFIED.value

    def test_global_score_in_bounds(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert 0.0 <= result.global_score <= 100.0

    def test_confidence_label_present(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert result.confidence in ("HIGH", "MEDIUM", "LOW")

    def test_data_quality_in_bounds(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert 0.0 <= result.data_quality <= 1.0

    def test_f_team_detail_with_crew(self, snapshot_strong, crew_snapshots):
        result = pe_fit_master.compute(
            snapshot_strong,
            current_crew_snapshots=crew_snapshots,
        )
        # PT Fit calculé quand équipe fournie
        assert result.pt_fit is not None
        assert 0.0 <= result.pt_fit.score <= 100.0

    def test_f_team_none_without_crew(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert result.pt_fit is None

    def test_po_fit_none_without_vessel_params(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert result.po_fit is None

    def test_ps_fit_none_without_captain_vector(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert result.ps_fit is None

    def test_all_flags_list(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        assert isinstance(result.all_flags, list)

    def test_to_matching_row_structure(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        row = result.to_matching_row()
        assert "pj_fit_score" in row
        assert "global_score" in row
        assert "safety_level" in row
        assert "confidence" in row

    def test_to_impact_report_structure(self, snapshot_strong):
        result = pe_fit_master.compute(snapshot_strong)
        report = result.to_impact_report()
        assert "global_score" in report
        assert "pj_fit" in report
        assert "safety_level" in report
