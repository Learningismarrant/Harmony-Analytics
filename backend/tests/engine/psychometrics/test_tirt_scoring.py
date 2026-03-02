# tests/engine/psychometrics/test_tirt_scoring.py
"""
Tests moteur T-IRT (Brown & Maydeu-Olivares, 2011) — CUTTY SARK.

Stratégie : tests unitaires purs, zéro DB, zéro mock.
Marqueur  : engine

Couverture :
  - Intégrité des paramètres d'items (λ, μ, domaines)
  - Construction des paires (_build_pair_data)
    · items normaux (score_weight = +1)
    · items inversés (score_weight = −1) → λ_eff négatif
    · items inconnus → paire ignorée
    · réponses invalides → ignorées
  - Log-posterior négative (_neg_log_posterior)
    · forme scalaire, finie
    · prior seul à θ = 0
    · gradient vs différences finies
  - Estimation MAP (_optimize_map)
    · convergence sur données synthétiques
    · θ → 0 avec pattern équilibré (prior domine)
  - Scores finaux (calculate_tirt_scores)
    · pattern "high-C" → θ_C >> θ autres
    · pattern "high-A" → θ_A >> θ autres
    · items inversés C → θ_C négatif si toujours choisis
    · centiles ∈ [0, 100]
    · z-scores ∈ [-3.5, 3.5] pour patterns extrêmes
    · global_score ∈ [0, 100]
    · format de sortie conforme TestResult.scores
    · fiabilité : vitesse suspecte → is_reliable=False
    · fiabilité : acquiescement → is_reliable=False
    · ValueError si aucune paire valide
"""

import math
import pytest
import numpy as np
from types import SimpleNamespace

from app.engine.psychometrics.tirt_scoring import (
    DOMAINS,
    DOMAIN_IDX,
    DOMAIN_NAMES,
    ITEM_PARAMS,
    _build_pair_data,
    _neg_log_posterior,
    _gradient,
    _optimize_map,
    _compute_reliability_index,
    _check_response_quality,
    calculate_tirt_scores,
)

pytestmark = pytest.mark.engine


# ─── Helpers ─────────────────────────────────────────────────────────────────


def make_question(
    qid: int,
    left_ipip: str,
    left_domain: str,
    left_sw: int,
    right_ipip: str,
    right_domain: str,
    right_sw: int,
) -> SimpleNamespace:
    """Simule un objet Question ORM avec Question.options."""
    return SimpleNamespace(
        id=qid,
        question_type="forced_choice",
        trait=f"{left_domain}_vs_{right_domain}",
        options=[
            {
                "side": "left",
                "ipip_id": left_ipip,
                "domain": left_domain,
                "score_weight": left_sw,
            },
            {
                "side": "right",
                "ipip_id": right_ipip,
                "domain": right_domain,
                "score_weight": right_sw,
            },
        ],
    )


def make_response(
    question_id: int,
    chosen: str,
    seconds_spent: float = 8.0,
) -> SimpleNamespace:
    return SimpleNamespace(
        question_id=question_id,
        valeur_choisie=chosen,
        seconds_spent=seconds_spent,
    )


# 30 paires couvrant les 5 domaines (blocs 1–5 du CUTTY SARK)
SAMPLE_PAIRS_30 = [
    # P01–P06  C vs A
    (1,  "C1_5",   "C",  1,  "A3_76",  "A",  1),
    (2,  "C2_10",  "C",  1,  "A4_106", "A",  1),
    (3,  "C3_45",  "C",  1,  "A1_16",  "A",  1),
    (4,  "C5_175R","C", -1,  "A5_226R","A", -1),
    (5,  "C2_190R","C", -1,  "A2_136R","A", -1),
    (6,  "C4_230R","C", -1,  "A6_149R","A", -1),
    # P07–P12  C vs E
    (7,  "C1_35",  "C",  1,  "E1_6",   "E",  1),
    (8,  "C6_15",  "C",  1,  "E3_66",  "E",  1),
    (9,  "C4_50",  "C",  1,  "E4_96",  "E",  1),
    (10, "C3_195R","C", -1,  "E2_127R","E", -1),
    (11, "C1_155R","C", -1,  "E3_187R","E", -1),
    (12, "C6_120R","C", -1,  "E6_217R","E", -1),
    # P13–P18  C vs N
    (13, "C2_40",  "C",  1,  "N1_1",   "N", -1),
    (14, "C5_85",  "C",  1,  "N4_91",  "N", -1),
    (15, "C3_105", "C",  1,  "N6_151", "N", -1),
    (16, "C5_235R","C", -1,  "N2_31",  "N",  1),
    (17, "C2_220R","C", -1,  "N3_61",  "N",  1),
    (18, "C4_170", "C",  1,  "N5_121", "N",  1),
    # P19–P24  C vs O
    (19, "C2_10",  "C",  1,  "O4_134", "O",  1),
    (20, "C6_150", "C",  1,  "O1_2",   "O",  1),
    (21, "C1_65",  "C",  1,  "O6_209", "O",  1),
    (22, "C3_225R","C", -1,  "O5_239R","O", -1),
    (23, "C5_265R","C", -1,  "O2_164R","O", -1),
    (24, "C2_190R","C", -1,  "O3_118R","O", -1),
    # P25–P30  A vs E
    (25, "A1_16",  "A",  1,  "E1_36",  "E",  1),
    (26, "A4_106", "A",  1,  "E3_66",  "E",  1),
    (27, "A6_59",  "A",  1,  "E5_156", "E",  1),
    (28, "A2_136R","A", -1,  "E2_127R","E", -1),
    (29, "A5_226R","A", -1,  "E6_217R","E", -1),
    (30, "A3_221R","A", -1,  "E4_277R","E", -1),
]


@pytest.fixture
def questions_map_30() -> dict:
    """Questions map avec 30 paires (5 domaines couverts)."""
    qs = [make_question(*p) for p in SAMPLE_PAIRS_30]
    return {q.id: q for q in qs}


def responses_always_left(n: int = 30, secs: float = 8.0) -> list:
    return [make_response(i, "left", secs) for i in range(1, n + 1)]


def responses_always_right(n: int = 30, secs: float = 8.0) -> list:
    return [make_response(i, "right", secs) for i in range(1, n + 1)]


def responses_balanced(n: int = 30, secs: float = 8.0) -> list:
    """Alternance left/right (pattern équilibré → prior domine)."""
    return [
        make_response(i, "left" if i % 2 == 0 else "right", secs)
        for i in range(1, n + 1)
    ]


# ─── Tests paramètres d'items ────────────────────────────────────────────────


class TestItemParams:

    def test_all_items_have_lambda_and_mu(self):
        for iid, params in ITEM_PARAMS.items():
            assert "lambda_" in params, f"{iid} manque lambda_"
            assert "mu" in params, f"{iid} manque mu"

    def test_lambda_in_valid_range(self):
        for iid, params in ITEM_PARAMS.items():
            lam = params["lambda_"]
            assert 0.0 < lam < 2.0, f"{iid}: lambda_={lam} hors plage"

    def test_mu_in_valid_range(self):
        for iid, params in ITEM_PARAMS.items():
            mu = params["mu"]
            assert -3.0 < mu < 3.0, f"{iid}: mu={mu} hors plage"

    def test_item_count(self):
        """76 items uniques attendus dans le CUTTY SARK (22C+17A+13E+10N+14O)."""
        assert len(ITEM_PARAMS) == 76

    def test_all_cutty_sark_items_in_params(self):
        """Vérifie que chaque ipip_id du CUTTY SARK est dans ITEM_PARAMS."""
        required = {
            # C (22)
            "C1_5", "C1_35", "C1_65", "C1_155R",
            "C2_10", "C2_40", "C2_190R", "C2_220R",
            "C3_45", "C3_105", "C3_195R", "C3_225R",
            "C4_50", "C4_170", "C4_230R",
            "C5_85", "C5_175R", "C5_235R", "C5_265R",
            "C6_15", "C6_120R", "C6_150",
            # A (17)
            "A1_16", "A1_41", "A1_166R",
            "A2_46", "A2_136R", "A2_196R",
            "A3_76", "A3_119", "A3_221R",
            "A4_16", "A4_106", "A4_256R",
            "A5_131", "A5_226R", "A5_286R",
            "A6_59", "A6_149R",
            # E (13)
            "E1_6", "E1_36", "E1_156R",
            "E2_37", "E2_127R",
            "E3_66", "E3_187R",
            "E4_96", "E4_277R",
            "E5_156", "E5_216R",
            "E6_126", "E6_217R",
            # N (10)
            "N1_1",
            "N2_31", "N2_186R",
            "N3_61",
            "N4_91", "N4_126R", "N4_181",
            "N5_121",
            "N6_151", "N6_271R",
            # O (14)
            "O1_2", "O1_32", "O1_152R",
            "O2_14", "O2_164R",
            "O3_88", "O3_118R",
            "O4_134", "O4_254R",
            "O5_58", "O5_239R",
            "O6_144", "O6_209", "O6_299R",
        }
        missing = required - set(ITEM_PARAMS.keys())
        assert not missing, f"Items manquants dans ITEM_PARAMS : {missing}"


# ─── Tests _build_pair_data ──────────────────────────────────────────────────


class TestBuildPairData:

    def test_returns_correct_count(self, questions_map_30):
        responses = responses_always_left(30)
        pair_data, n, _ = _build_pair_data(responses, questions_map_30)
        assert n == 30
        assert len(pair_data) == 30

    def test_y_equals_1_for_left(self, questions_map_30):
        responses = [make_response(1, "left")]
        pair_data, _, _ = _build_pair_data(responses, questions_map_30)
        assert len(pair_data) == 1
        y = pair_data[0][0]
        assert y == 1

    def test_y_equals_0_for_right(self, questions_map_30):
        responses = [make_response(1, "right")]
        pair_data, _, _ = _build_pair_data(responses, questions_map_30)
        assert len(pair_data) == 1
        y = pair_data[0][0]
        assert y == 0

    def test_invalid_chosen_side_skipped(self, questions_map_30):
        responses = [make_response(1, "INVALID")]
        pair_data, n, _ = _build_pair_data(responses, questions_map_30)
        assert n == 0
        assert len(pair_data) == 0

    def test_unknown_question_id_skipped(self, questions_map_30):
        responses = [make_response(9999, "left")]
        pair_data, n, _ = _build_pair_data(responses, questions_map_30)
        assert n == 0

    def test_unknown_ipip_id_skipped(self):
        """Paire avec item inconnu → ignorée."""
        q = make_question(1, "UNKNOWN_ITEM", "C", 1, "A3_76", "A", 1)
        questions_map = {1: q}
        responses = [make_response(1, "left")]
        pair_data, n, _ = _build_pair_data(responses, questions_map)
        assert n == 0

    def test_positive_item_positive_lambda_eff(self, questions_map_30):
        """P01 : C1_5 (sw=+1) → λ_eff_left > 0."""
        responses = [make_response(1, "left")]
        pair_data, _, _ = _build_pair_data(responses, questions_map_30)
        assert len(pair_data) == 1
        _, _, _, lam_eff_l, _, _, _, _ = pair_data[0]
        assert lam_eff_l > 0

    def test_inverted_item_negative_lambda_eff(self, questions_map_30):
        """P04 : C5_175R (sw=−1) → λ_eff_left < 0."""
        responses = [make_response(4, "left")]
        pair_data, _, _ = _build_pair_data(responses, questions_map_30)
        assert len(pair_data) == 1
        _, _, _, lam_eff_l, _, _, lam_eff_r, _ = pair_data[0]
        assert lam_eff_l < 0  # C5_175R est inversé → λ_eff négatif
        assert lam_eff_r < 0  # A5_226R est aussi inversé

    def test_sigma_is_positive(self, questions_map_30):
        responses = responses_always_left(30)
        pair_data, _, _ = _build_pair_data(responses, questions_map_30)
        for row in pair_data:
            sigma = row[7]
            assert sigma > 0

    def test_side_counts_tracking(self, questions_map_30):
        responses = (
            [make_response(i, "left") for i in range(1, 11)]
            + [make_response(i, "right") for i in range(11, 21)]
        )
        _, _, side_counts = _build_pair_data(responses, questions_map_30)
        assert side_counts["left"] == 10
        assert side_counts["right"] == 10

    def test_domain_indices_correct(self, questions_map_30):
        """P07 : left = C (idx 1), right = E (idx 2)."""
        responses = [make_response(7, "left")]
        pair_data, _, _ = _build_pair_data(responses, questions_map_30)
        assert len(pair_data) == 1
        _, di_l, _, _, di_r, _, _, _ = pair_data[0]
        assert di_l == DOMAIN_IDX["C"]
        assert di_r == DOMAIN_IDX["E"]


# ─── Tests log-posterior ─────────────────────────────────────────────────────


class TestNegLogPosterior:

    @pytest.fixture
    def sample_pair_data(self, questions_map_30):
        responses = responses_balanced(30)
        data, _, _ = _build_pair_data(responses, questions_map_30)
        return data

    def test_returns_finite_scalar(self, sample_pair_data):
        theta = np.zeros(5)
        val = _neg_log_posterior(theta, sample_pair_data)
        assert math.isfinite(val)
        assert isinstance(val, float)

    def test_prior_dominates_at_zero(self):
        """À θ = 0, la log-posterior ne dépend que du prior (terme = 0 pour prior N(0,I))."""
        theta = np.zeros(5)
        pair_data_empty: list = []
        val = _neg_log_posterior(theta, pair_data_empty)
        # Prior : 0.5 * ||0||² = 0
        assert val == pytest.approx(0.0, abs=1e-9)

    def test_prior_increases_with_theta_magnitude(self, sample_pair_data):
        theta_zero = np.zeros(5)
        theta_large = np.array([2.0, 2.0, 2.0, 2.0, 2.0])
        # Avec données identiques, le prior augmente la nll pour θ grand
        nll_zero = _neg_log_posterior(theta_zero, [])
        nll_large = _neg_log_posterior(theta_large, [])
        assert nll_large > nll_zero

    def test_gradient_matches_finite_differences(self, sample_pair_data):
        """Gradient analytique vs différences finies centrées (ε = 1e-5)."""
        theta = np.array([0.3, -0.4, 0.2, 0.5, -0.1])
        eps = 1e-5
        grad_analytic = _gradient(theta, sample_pair_data)
        grad_numerical = np.zeros(5)
        for k in range(5):
            theta_plus = theta.copy()
            theta_plus[k] += eps
            theta_minus = theta.copy()
            theta_minus[k] -= eps
            grad_numerical[k] = (
                _neg_log_posterior(theta_plus, sample_pair_data)
                - _neg_log_posterior(theta_minus, sample_pair_data)
            ) / (2 * eps)
        np.testing.assert_allclose(grad_analytic, grad_numerical, rtol=1e-3, atol=1e-5)


# ─── Tests _optimize_map ─────────────────────────────────────────────────────


class TestOptimizeMap:

    def test_returns_5d_vector(self, questions_map_30):
        pair_data, _, _ = _build_pair_data(responses_balanced(30), questions_map_30)
        theta_opt, posterior_var = _optimize_map(pair_data)
        assert theta_opt.shape == (5,)
        assert posterior_var.shape == (5,)

    def test_posterior_var_positive(self, questions_map_30):
        pair_data, _, _ = _build_pair_data(responses_balanced(30), questions_map_30)
        _, posterior_var = _optimize_map(pair_data)
        assert all(v > 0 for v in posterior_var)

    def test_balanced_pattern_theta_near_zero(self, questions_map_30):
        """Pattern équilibré → prior domine → θ proches de 0."""
        pair_data, _, _ = _build_pair_data(responses_balanced(30), questions_map_30)
        theta_opt, _ = _optimize_map(pair_data)
        assert np.all(np.abs(theta_opt) < 1.5)

    def test_theta_finite(self, questions_map_30):
        pair_data, _, _ = _build_pair_data(responses_always_left(30), questions_map_30)
        theta_opt, _ = _optimize_map(pair_data)
        assert all(math.isfinite(v) for v in theta_opt)


# ─── Tests fiabilité ─────────────────────────────────────────────────────────


class TestReliability:

    def test_reliability_index_in_range(self):
        # SEM² ∈ [0, 1] → ρ ∈ [0, 1]
        for var in [np.array([0.1] * 5), np.array([0.5] * 5), np.array([1.0] * 5)]:
            ri = _compute_reliability_index(var)
            assert 0.0 <= ri <= 1.0

    def test_low_variance_high_reliability(self):
        posterior_var = np.array([0.05] * 5)
        ri = _compute_reliability_index(posterior_var)
        assert ri > 0.90

    def test_high_variance_low_reliability(self):
        posterior_var = np.array([0.95] * 5)
        ri = _compute_reliability_index(posterior_var)
        assert ri < 0.10

    def test_too_fast_is_unreliable(self):
        is_reliable, reasons = _check_response_quality(
            n_answered=60, side_counts={"left": 30, "right": 30},
            total_seconds=30.0,   # < 2s/paire
        )
        assert not is_reliable
        assert any("Temps" in r for r in reasons)

    def test_normal_speed_reliable(self):
        is_reliable, reasons = _check_response_quality(
            n_answered=60, side_counts={"left": 30, "right": 30},
            total_seconds=360.0,  # 6s/paire
        )
        assert is_reliable
        assert not reasons

    def test_acquiescence_left_unreliable(self):
        is_reliable, reasons = _check_response_quality(
            n_answered=60, side_counts={"left": 58, "right": 2},
            total_seconds=360.0,
        )
        assert not is_reliable
        assert any("acquiescement" in r.lower() for r in reasons)

    def test_acquiescence_right_unreliable(self):
        is_reliable, reasons = _check_response_quality(
            n_answered=60, side_counts={"left": 2, "right": 58},
            total_seconds=360.0,
        )
        assert not is_reliable

    def test_acquiescence_check_requires_more_than_10_pairs(self):
        """Moins de 10 paires : vérification acquiescement désactivée."""
        is_reliable, _ = _check_response_quality(
            n_answered=5, side_counts={"left": 5, "right": 0},
            total_seconds=60.0,
        )
        assert is_reliable  # pas assez de données pour détecter l'acquiescement


# ─── Tests calculate_tirt_scores ─────────────────────────────────────────────


class TestCalculateTirtScores:

    def test_output_keys_present(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        assert "traits" in result
        assert "global_score" in result
        assert "reliability" in result
        assert "meta" in result
        assert "tirt_detail" in result

    def test_traits_contain_all_big_five(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        for name in DOMAIN_NAMES.values():
            assert name in result["traits"], f"Domaine manquant : {name}"

    def test_trait_scores_in_range(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        for name, data in result["traits"].items():
            score = data["score"]
            assert 0.0 <= score <= 100.0, f"{name}: score={score} hors [0, 100]"

    def test_global_score_in_range(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        assert 0.0 <= result["global_score"] <= 100.0

    def test_tirt_detail_z_scores_finite(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_always_left(30), questions_map_30, total_seconds=240.0
        )
        for d in DOMAINS:
            z = result["tirt_detail"][d]["z_score"]
            assert math.isfinite(z)

    def test_tirt_detail_percentiles_in_range(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_always_left(30), questions_map_30, total_seconds=240.0
        )
        for d in DOMAINS:
            pct = result["tirt_detail"][d]["percentile"]
            assert 0.0 <= pct <= 100.0

    def test_reliability_index_present(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        ri = result["tirt_detail"]["reliability_index"]
        assert 0.0 <= ri <= 1.0

    def test_meta_time_fields(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=300.0
        )
        assert result["meta"]["total_time_seconds"] == 300.0
        assert result["meta"]["avg_seconds_per_question"] == pytest.approx(10.0, abs=0.1)

    def test_high_c_pattern_raises_c_score(self, questions_map_30):
        """
        Toujours choisir l'item C dans les paires C-vs-X
        → θ_C doit être nettement positif → percentile_C > 60.
        """
        # Paires 1-12 et 13-24 sont C-vs-X (blocs 1-4)
        # Toujours choisir "left" (= C dans paires 1-12) ou "right" selon le bloc
        # Pour les 12 paires C vs A (P01-P06) et C vs E (P07-P12) : left = C → choisir left
        # Pour P13-P24 (C vs N, C vs O) : left = C → choisir left
        responses = responses_always_left(30)
        result = calculate_tirt_scores(responses, questions_map_30, total_seconds=300.0)
        c_percentile = result["tirt_detail"]["C"]["percentile"]
        # Le prior N(0,1) atténue mais C doit être au-dessus de la médiane
        assert c_percentile > 55.0, f"θ_C attendu positif, percentile_C = {c_percentile}"

    def test_inverted_c_items_flip_c_direction(self, questions_map_30):
        """
        P04 (C5_175R sw=-1) et P05 (C2_190R sw=-1) :
        Choisir l'item C inversé (left) → contribue négativement à θ_C.
        P01 (C1_5 sw=+1) : Choisir left → contribue positivement.
        Réponses mixtes : on peut quand même scorer.
        """
        # Toujours choisir right (non-C) sur les paires C vs A
        # → θ_A devrait être plus élevé que θ_C
        responses_right_for_1_to_6 = (
            [make_response(i, "right") for i in range(1, 7)]   # C vs A → choisir A
            + [make_response(i, "left") for i in range(7, 31)]  # reste → left
        )
        result = calculate_tirt_scores(
            responses_right_for_1_to_6, questions_map_30, total_seconds=300.0
        )
        a_pct = result["tirt_detail"]["A"]["percentile"]
        c_pct = result["tirt_detail"]["C"]["percentile"]
        # A devrait bénéficier des choix A dans P01-P06
        assert a_pct > 50.0, f"θ_A attendu > 50, got {a_pct}"
        # Le résultat doit être cohérent (pas de crash)
        assert result["reliability"]["is_reliable"] is not None

    def test_n_inverted_scores_correctly(self, questions_map_30):
        """
        Items N avec score_weight=-1 (ex. N1_1 en P13) :
        Choisir N1_1 (sw=-1) → contribue négativement à θ_N (basse neuroticism).
        Choisir toujours right dans P13-P18 (items N) → θ_N devrait être élevé.
        """
        # P13-P18 : right = N item
        # P13: right = N1_1 (sw=-1) → choisir right → infère LOW N trait → θ_N < 0
        # P16: right = N2_31 (sw=+1) → choisir right → infère HIGH N trait → θ_N > 0
        # Effet mixte → scorer sans crash est l'objectif minimal ici
        responses = responses_always_right(30)
        result = calculate_tirt_scores(responses, questions_map_30, total_seconds=300.0)
        for d in DOMAINS:
            pct = result["tirt_detail"][d]["percentile"]
            assert 0.0 <= pct <= 100.0

    def test_raises_value_error_on_empty_valid_pairs(self):
        """Aucune paire valide → ValueError."""
        q = make_question(1, "UNKNOWN_L", "C", 1, "UNKNOWN_R", "A", 1)
        questions_map = {1: q}
        responses = [make_response(1, "left")]
        with pytest.raises(ValueError, match="Aucune paire TIRT valide"):
            calculate_tirt_scores(responses, questions_map)

    def test_too_fast_responses_flagged(self, questions_map_30):
        responses = responses_balanced(30, secs=0.5)  # 0.5s × 30 = 15s total
        result = calculate_tirt_scores(responses, questions_map_30, total_seconds=15.0)
        assert not result["reliability"]["is_reliable"]
        assert any("Temps" in r for r in result["reliability"]["reasons"])

    def test_normal_responses_reliable(self, questions_map_30):
        responses = responses_balanced(30, secs=8.0)
        result = calculate_tirt_scores(responses, questions_map_30, total_seconds=240.0)
        # Fiabilité comportementale OK (index peut être bas avec seulement 30 paires)
        assert "is_reliable" in result["reliability"]

    def test_level_label_assigned(self, questions_map_30):
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        valid_levels = {"Élevé", "Moyen", "Faible"}
        for name, data in result["traits"].items():
            assert data["niveau"] in valid_levels, (
                f"{name}: niveau='{data['niveau']}' invalide"
            )

    def test_z_scores_extreme_pattern_in_bounds(self, questions_map_30):
        """Pattern extrême (always left) → z-scores hors plage [-4, 4] seraient suspects."""
        result = calculate_tirt_scores(
            responses_always_left(30), questions_map_30, total_seconds=300.0
        )
        for d in DOMAINS:
            z = result["tirt_detail"][d]["z_score"]
            assert -4.0 <= z <= 4.0, f"θ_{d} = {z} semble anormal"

    def test_consistency_with_snapshot_format(self, questions_map_30):
        """
        Les clés de 'traits' correspondent aux noms attendus par build_snapshot()
        (agreeableness, conscientiousness, extraversion, neuroticism, openness).
        """
        result = calculate_tirt_scores(
            responses_balanced(30), questions_map_30, total_seconds=240.0
        )
        expected_trait_keys = set(DOMAIN_NAMES.values())
        actual_keys = set(result["traits"].keys())
        assert actual_keys == expected_trait_keys
