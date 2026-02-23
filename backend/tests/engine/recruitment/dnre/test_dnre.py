# tests/engine/recruitment/dnre/test_dnre.py
"""
Tests unitaires du DNRE.
Zéro DB — toutes les données sont des fixtures JSON in-memory.
"""
import pytest
from app.engine.recruitment.DNRE import sme_score, centile_rank, safety_barrier, global_fit
from app.engine.recruitment.DNRE import master as dnre
from app.engine.recruitment.DNRE.safety_barrier import SafetyLevel, VetoType, VetoRule


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
# TESTS SME SCORE (Étape 1)
# ═══════════════════════════════════════════════════════════

class TestSMEScore:

    def test_strong_candidate_high_score(self, snapshot_strong):
        result = sme_score.compute(snapshot_strong, sme_score.COMPETENCY_INDIVIDUAL_PERFORMANCE)
        assert result.score >= 60.0
        assert len(result.trait_contributions) == 2   # GCA + C
        assert result.data_quality == 1.0

    def test_formula_matches_manual_calc(self, snapshot_strong):
        """Vérification manuelle : S = (0.6×76 + 0.4×78) / 1.0"""
        result = sme_score.compute(snapshot_strong, sme_score.COMPETENCY_INDIVIDUAL_PERFORMANCE)
        expected = (0.60 * 76.0 + 0.40 * 78.0) / 1.0
        assert abs(result.score - expected) < 0.1

    def test_partial_snapshot_uses_fallback(self, snapshot_partial):
        result = sme_score.compute(snapshot_partial, sme_score.COMPETENCY_INDIVIDUAL_PERFORMANCE)
        # GCA manquant → fallback 50.0
        gca_contrib = next(tc for tc in result.trait_contributions if tc.trait == "gca")
        assert gca_contrib.is_fallback
        assert any("FALLBACK_GCA" in f for f in result.flags)
        assert result.data_quality < 1.0

    def test_custom_sme_weights_applied(self, snapshot_strong):
        custom_weights = {"gca": 1.0, "conscientiousness": 0.0}
        result = sme_score.compute(
            snapshot_strong,
            sme_score.COMPETENCY_INDIVIDUAL_PERFORMANCE,
            sme_weights=custom_weights,
        )
        # Avec poids C=0, seul GCA compte → score ≈ 76
        assert abs(result.score - 76.0) < 1.0

    def test_all_competencies_computed(self, snapshot_strong):
        all_results = sme_score.compute_all_competencies(snapshot_strong)
        assert set(all_results.keys()) == set(sme_score.ALL_COMPETENCIES)
        for key, result in all_results.items():
            assert 0.0 <= result.score <= 100.0

    def test_team_fit_includes_emotional_stability(self, snapshot_strong):
        result = sme_score.compute(snapshot_strong, sme_score.COMPETENCY_TEAM_FIT)
        trait_keys = [tc.trait for tc in result.trait_contributions]
        assert "emotional_stability" in trait_keys

    def test_leadership_fit_uses_preferences(self, snapshot_strong):
        result = sme_score.compute(snapshot_strong, sme_score.COMPETENCY_LEADERSHIP_FIT)
        # 0.6 × 100 = 60 pour autonomy (0.6 × 100), etc.
        assert result.score > 0
        assert result.data_quality == 1.0   # preferences présentes → pas de fallback

    def test_unknown_competency_returns_fallback(self, snapshot_strong):
        result = sme_score.compute(snapshot_strong, "C99_unknown")
        assert "NO_WEIGHTS" in result.flags[0]
        assert result.data_quality == 0.0


# ═══════════════════════════════════════════════════════════
# TESTS CENTILE RANK (Étape 2)
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

    def test_batch_all_candidates(self):
        scores = {"A": 80.0, "B": 60.0, "C": 40.0}
        results = centile_rank.compute_batch(scores, "C1")
        assert len(results) == 3
        assert results["A"].centile > results["B"].centile > results["C"].centile

    def test_rank_coherent(self):
        pool = [30.0, 50.0, 70.0, 85.0, 90.0]
        result = centile_rank.compute(90.0, pool)
        assert result.rank == 1

    def test_centile_clamped_0_100(self):
        result = centile_rank.compute(100.0, [100.0, 100.0, 100.0])
        assert 0.0 <= result.centile <= 100.0


# ═══════════════════════════════════════════════════════════
# TESTS SAFETY BARRIER
# ═══════════════════════════════════════════════════════════

class TestSafetyBarrier:

    def test_strong_candidate_clear(self, snapshot_strong):
        result = safety_barrier.evaluate(snapshot_strong, g_fit_score=70.0)
        assert result.safety_level == SafetyLevel.CLEAR
        assert not result.g_fit_suspended
        assert result.adjusted_score is None

    def test_disqualified_es_below_15(self, snapshot_disqualified):
        result = safety_barrier.evaluate(snapshot_disqualified, g_fit_score=65.0)
        assert result.safety_level == SafetyLevel.DISQUALIFIED
        assert result.g_fit_suspended
        assert result.adjusted_score == 0.0
        hard_triggers = [t for t in result.triggers if t.veto_type == VetoType.HARD]
        assert len(hard_triggers) >= 1

    def test_high_risk_es_between_15_30(self, snapshot_high_risk):
        result = safety_barrier.evaluate(snapshot_high_risk, g_fit_score=60.0)
        assert result.safety_level == SafetyLevel.HIGH_RISK
        assert result.g_fit_suspended
        assert result.adjusted_score == 60.0   # Score maintenu mais annoté

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
        result = safety_barrier.evaluate(snapshot, g_fit_score=65.0)
        assert result.safety_level == SafetyLevel.ADVISORY
        assert not result.g_fit_suspended
        assert result.adjusted_score is None

    def test_custom_rules_applied(self, snapshot_strong):
        custom_rules = [
            VetoRule(
                trait="gca",
                threshold=80.0,    # Seuil très élevé
                veto_type=VetoType.SOFT,
                label="GCA insuffisant pour ce poste",
            )
        ]
        # GCA fort = 76 mais seuil = 80 → SOFT VETO
        result = safety_barrier.evaluate(
            snapshot_strong, g_fit_score=70.0, veto_rules=custom_rules
        )
        assert result.safety_level == SafetyLevel.HIGH_RISK

    def test_position_scoped_rule_not_applied(self, snapshot_strong):
        """Règle scoped à Captain ne s'applique pas à un Deckhand."""
        captain_rules = [
            VetoRule(
                trait="gca",
                threshold=80.0,
                veto_type=VetoType.HARD,
                label="GCA minimal Capitaine",
                positions_scope=["Captain"],
            )
        ]
        result = safety_barrier.evaluate(
            snapshot_strong,
            g_fit_score=70.0,
            veto_rules=captain_rules,
            position_key="Deckhand",    # Pas dans positions_scope
        )
        assert result.safety_level == SafetyLevel.CLEAR

    def test_unmeasured_trait_no_veto(self):
        """Un trait non mesuré ne déclenche pas de veto."""
        snapshot = {"big_five": {"agreeableness": {"score": 70.0}}}
        # ES absent → veto ES non applicable
        result = safety_barrier.evaluate(snapshot, g_fit_score=65.0)
        es_triggers = [t for t in result.triggers if t.trait == "emotional_stability"]
        assert len(es_triggers) == 0


# ═══════════════════════════════════════════════════════════
# TESTS GLOBAL FIT (Étape 3)
# ═══════════════════════════════════════════════════════════

class TestGlobalFit:

    def test_uniform_weights_average(self):
        scores = {"C1": 80.0, "C2": 60.0, "C3": 70.0, "C4": 50.0}
        result = global_fit.compute(scores)
        expected = (80 + 60 + 70 + 50) / 4
        assert abs(result.g_fit - expected) < 0.2

    def test_custom_weights_applied(self):
        scores = {"C1": 100.0, "C2": 0.0}
        weights = {"C1": 2.0, "C2": 1.0}
        result = global_fit.compute(scores, competency_weights=weights)
        # C1 pèse 2/3 → G_fit = (2/3 × 100 + 1/3 × 0) ≈ 66.7
        assert abs(result.g_fit - 66.7) < 0.5

    def test_empty_scores_returns_zero(self):
        result = global_fit.compute({})
        assert result.g_fit == 0.0

    def test_contributions_sum_to_g_fit(self):
        scores = {"C1": 80.0, "C2": 60.0, "C3": 70.0, "C4": 50.0}
        result = global_fit.compute(scores)
        total = sum(c.contribution for c in result.contributions)
        assert abs(total - result.g_fit) < 0.1

    def test_k_competencies_correct(self):
        scores = {"C1": 70.0, "C2": 65.0, "C3": 75.0}
        result = global_fit.compute(scores)
        assert result.k_competencies == 3


# ═══════════════════════════════════════════════════════════
# TESTS DNRE MASTER
# ═══════════════════════════════════════════════════════════

class TestDNREMaster:

    def test_compute_batch_returns_all_candidates(self, snapshot_strong, snapshot_high_risk, crew_snapshots):
        candidates = [
            {"snapshot": snapshot_strong,   "crew_profile_id": "A"},
            {"snapshot": snapshot_high_risk, "crew_profile_id": "B"},
        ]
        results = dnre.compute_batch(candidates, current_crew_snapshots=crew_snapshots)
        assert len(results) == 2

    def test_strong_beats_high_risk(self, snapshot_strong, snapshot_high_risk, crew_snapshots):
        candidates = [
            {"snapshot": snapshot_strong,   "crew_profile_id": "A"},
            {"snapshot": snapshot_high_risk, "crew_profile_id": "B"},
        ]
        results = dnre.compute_batch(candidates, current_crew_snapshots=crew_snapshots)
        strong = next(r for r in results if r.crew_profile_id == "A")
        risky  = next(r for r in results if r.crew_profile_id == "B")
        assert strong.g_fit > risky.g_fit

    def test_disqualified_g_fit_zero(self, snapshot_disqualified, snapshot_strong, crew_snapshots):
        candidates = [
            {"snapshot": snapshot_disqualified, "crew_profile_id": "DQ"},
            {"snapshot": snapshot_strong,        "crew_profile_id": "OK"},
        ]
        results = dnre.compute_batch(candidates)
        dq = next(r for r in results if r.crew_profile_id == "DQ")
        assert dq.g_fit == 0.0
        assert dq.fit_label == "DISQUALIFIED"
        assert dq.safety.safety_level == SafetyLevel.DISQUALIFIED

    def test_centile_computed_for_all(self, snapshot_strong, snapshot_high_risk):
        candidates = [
            {"snapshot": snapshot_strong,   "crew_profile_id": "A"},
            {"snapshot": snapshot_high_risk, "crew_profile_id": "B"},
            {"snapshot": {"big_five": {"agreeableness": {"score": 55.0}, "neuroticism": {"score": 50.0}}}, "crew_profile_id": "C"},
        ]
        results = dnre.compute_batch(candidates)
        for result in results:
            assert len(result.centile_ranks) == len(sme_score.ALL_COMPETENCIES)
            assert 0.0 <= result.overall_centile <= 100.0

    def test_batch_centile_ordering_coherent(self, snapshot_strong, snapshot_high_risk):
        """Le meilleur candidat doit avoir un centile plus élevé."""
        candidates = [
            {"snapshot": snapshot_strong,    "crew_profile_id": "STRONG"},
            {"snapshot": snapshot_high_risk,  "crew_profile_id": "WEAK"},
        ]
        results = dnre.compute_batch(candidates)
        strong = next(r for r in results if r.crew_profile_id == "STRONG")
        weak   = next(r for r in results if r.crew_profile_id == "WEAK")
        assert strong.overall_centile > weak.overall_centile

    def test_to_matching_row_structure(self, snapshot_strong, snapshot_high_risk):
        candidates = [
            {"snapshot": snapshot_strong, "crew_profile_id": "A"},
            {"snapshot": snapshot_high_risk, "crew_profile_id": "B"},
        ]
        results = dnre.compute_batch(candidates)
        row = results[0].to_matching_row()
        assert "g_fit" in row
        assert "overall_centile" in row
        assert "safety_level" in row
        assert "centile_by_competency" in row
        assert len(row["centile_by_competency"]) == 4

    def test_to_impact_report_structure(self, snapshot_strong, crew_snapshots):
        result = dnre.compute_single(
            snapshot_strong,
            current_crew_snapshots=crew_snapshots,
            crew_profile_id="test_crew",
        )
        report = result.to_impact_report()
        assert "g_fit" in report
        assert "competency_details" in report
        assert "safety" in report
        assert "team_impact" in report
        assert len(report["competency_details"]) == 4

    def test_f_team_delta_with_crew(self, snapshot_strong, crew_snapshots):
        result = dnre.compute_single(
            snapshot_strong,
            current_crew_snapshots=crew_snapshots,
            crew_profile_id="test",
        )
        assert result.f_team_detail is not None
        assert result.f_team_detail.delta is not None

    def test_to_event_snapshot_compact(self, snapshot_strong):
        result = dnre.compute_single(snapshot_strong)
        snap = result.to_event_snapshot()
        assert "g_fit" in snap
        assert "sme_scores" in snap
        assert len(snap["sme_scores"]) == 4
        assert "safety_level" in snap

    def test_single_without_pool_low_confidence(self, snapshot_strong):
        result = dnre.compute_single(snapshot_strong, pool_context=None)
        assert result.confidence == "LOW"
        assert any("Pool absent" in f for f in result.all_flags)

    def test_empty_candidates_batch(self):
        results = dnre.compute_batch([])
        assert results == []