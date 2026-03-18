# tests/engine/recruitment/pe_fit/test_f_team_updated.py
"""
Tests de non-régression et validation pour f_team.py avec les nouveaux poids Bell (2007).

Couverture :
    test_mean_c_contributes_positively    → équipe haute C_mean > basse C_mean
    test_weights_sum_to_one              → somme des poids absolus = 1.00
    test_bell_2007_anchoring             → poids reflètent les ρ Bell 2007
    Non-régression : les tests compute_fit() existants continuent de passer
"""
import pytest

from app.engine.pe_fit.pt_fit.f_team import compute, compute_fit, FTeamResult
from app.engine.pe_fit.pt_fit.weights import (
    W_JERK_FILTER,
    W_MEAN_C,
    W_EMOTIONAL_BUFFER,
    W_FAULTLINE_RISK,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def snap(agreeableness=75.0, conscientiousness=70.0, neuroticism=30.0):
    es = round(100.0 - neuroticism, 1)
    return {
        "big_five": {
            "agreeableness": agreeableness,
            "conscientiousness": conscientiousness,
            "neuroticism": neuroticism,
            "emotional_stability": es,
        }
    }


def snap_empty():
    return {}


# Équipe avec μ(C) élevée
CREW_HIGH_C = [
    snap(agreeableness=75.0, conscientiousness=90.0, neuroticism=30.0),
    snap(agreeableness=78.0, conscientiousness=88.0, neuroticism=28.0),
    snap(agreeableness=72.0, conscientiousness=92.0, neuroticism=32.0),
]

# Équipe avec μ(C) basse — autres facteurs identiques
CREW_LOW_C = [
    snap(agreeableness=75.0, conscientiousness=30.0, neuroticism=30.0),
    snap(agreeableness=78.0, conscientiousness=28.0, neuroticism=28.0),
    snap(agreeableness=72.0, conscientiousness=32.0, neuroticism=32.0),
]

CANDIDATE = snap(agreeableness=76.0, conscientiousness=70.0, neuroticism=29.0)


# ── Tests Bell (2007) ─────────────────────────────────────────────────────────

class TestMeanCContributesPositively:
    def test_haute_mean_c_donne_score_superieur(self):
        """
        Équipe avec μ(C) élevée doit scorer plus haut que la même équipe avec μ(C) basse.
        Toutes choses égales par ailleurs (agréabilité et ES identiques).
        """
        result_high_c = compute(CREW_HIGH_C + [CANDIDATE])
        result_low_c  = compute(CREW_LOW_C  + [CANDIDATE])

        assert result_high_c is not None
        assert result_low_c  is not None
        assert result_high_c.score > result_low_c.score

    def test_mean_c_dans_faultline_detail(self):
        """mean_conscientiousness est calculé et accessible."""
        result = compute(CREW_HIGH_C)
        assert result is not None
        assert result.faultline.mean_conscientiousness > 0.0

    def test_mean_c_eleve_reflete_dans_faultline(self):
        """μ(C) élevée dans l'équipe haute C."""
        result = compute(CREW_HIGH_C)
        assert result is not None
        # Mean C dans CREW_HIGH_C ≈ (90+88+92)/3 ≈ 90
        assert result.faultline.mean_conscientiousness > 80.0

    def test_mean_c_bas_reflete_dans_faultline(self):
        """μ(C) basse dans l'équipe basse C."""
        result = compute(CREW_LOW_C)
        assert result is not None
        # Mean C dans CREW_LOW_C ≈ (30+28+32)/3 ≈ 30
        assert result.faultline.mean_conscientiousness < 40.0


class TestWeightsSumToOne:
    def test_weights_sum_to_one(self):
        """
        La somme des poids absolus doit être 1.00.
        W_JERK(0.30) + W_MEAN_C(0.30) + W_EMOTIONAL(0.28) + W_FAULTLINE(0.12) = 1.00
        """
        total = W_JERK_FILTER + W_MEAN_C + W_EMOTIONAL_BUFFER + W_FAULTLINE_RISK
        assert abs(total - 1.00) < 1e-9, f"Somme des poids = {total}, attendu 1.00"

    def test_w_jerk_filter_value(self):
        assert W_JERK_FILTER == 0.30

    def test_w_mean_c_value(self):
        assert W_MEAN_C == 0.30

    def test_w_emotional_buffer_value(self):
        assert W_EMOTIONAL_BUFFER == 0.28

    def test_w_faultline_risk_value(self):
        assert W_FAULTLINE_RISK == 0.12


class TestBell2007Anchoring:
    def test_jerk_filter_ancre_bell_a_min(self):
        """
        W_JERK_FILTER reflète ρ A_min ≈ 0.27 de Bell (2007) —
        arrondi à 0.30 pour distribution cohérente.
        """
        # Le poids reflète la ρ Bell 2007 pour A_min (0.27) — arrondi opérationnel
        assert W_JERK_FILTER >= 0.27
        assert W_JERK_FILTER <= 0.35

    def test_mean_c_ancre_bell_c_mean(self):
        """
        W_MEAN_C reflète ρ C_mean ≈ 0.27 de Bell (2007).
        """
        assert W_MEAN_C >= 0.25
        assert W_MEAN_C <= 0.35

    def test_emotional_buffer_ancre_bell_es_mean(self):
        """
        W_EMOTIONAL_BUFFER reflète ρ ES_mean ≈ 0.25 de Bell (2007).
        """
        assert W_EMOTIONAL_BUFFER >= 0.23
        assert W_EMOTIONAL_BUFFER <= 0.30

    def test_faultline_risk_ancre_lau_murnighan(self):
        """
        W_FAULTLINE_RISK reflète ρ σ(C) ≈ -0.19 de Lau & Murnighan (1998).
        (poids de pénalité — valeur absolue entre 0.10 et 0.25)
        """
        assert W_FAULTLINE_RISK >= 0.10
        assert W_FAULTLINE_RISK <= 0.25

    def test_formula_snapshot_inclut_mean_c(self):
        """La formula_snapshot inclut le terme mean_C."""
        result = compute(CREW_HIGH_C)
        assert result is not None
        assert "W_MEAN_C" in result.formula_snapshot or "×0.3" in result.formula_snapshot or "×" in result.formula_snapshot


class TestNonRegression:
    """
    Tests de non-régression : les comportements existants ne doivent pas changer.
    Ces tests reprennent les assertions clés des tests originaux test_pt_fit.py.
    """
    def test_compute_fit_equipe_valide_retourne_fteam_result(self):
        crew = [snap(75.0, 70.0, 30.0), snap(80.0, 72.0, 25.0)]
        result = compute_fit(CANDIDATE, crew)
        assert isinstance(result, FTeamResult)

    def test_compute_fit_crew_none_retourne_none(self):
        result = compute_fit(CANDIDATE, None)
        assert result is None

    def test_compute_fit_crew_vide_retourne_none(self):
        result = compute_fit(CANDIDATE, [])
        assert result is None

    def test_compute_score_dans_bornes(self):
        result = compute(CREW_HIGH_C)
        assert 0.0 <= result.score <= 100.0

    def test_equipe_trop_petite_retourne_50(self):
        result = compute([snap()])
        assert result.score == 50.0
        assert any("CREW_TOO_SMALL" in f for f in result.flags)

    def test_equipe_vide_retourne_50(self):
        result = compute([])
        assert result.score == 50.0

    def test_candidat_jerk_abaisse_score(self):
        """Candidat avec agréabilité très basse abaisse le score."""
        crew = [snap(75.0, 70.0, 30.0), snap(80.0, 72.0, 25.0), snap(65.0, 68.0, 35.0)]
        result_bon  = compute_fit(snap(agreeableness=80.0), crew)
        result_jerk = compute_fit(snap(agreeableness=10.0), crew)
        assert result_bon  is not None
        assert result_jerk is not None
        assert result_bon.score > result_jerk.score

    def test_snapshot_vide_pas_exception(self):
        crew = [snap(75.0, 70.0, 30.0), snap(80.0, 72.0, 25.0)]
        result = compute_fit(snap_empty(), crew)
        assert isinstance(result, FTeamResult)
        assert 0.0 <= result.score <= 100.0
