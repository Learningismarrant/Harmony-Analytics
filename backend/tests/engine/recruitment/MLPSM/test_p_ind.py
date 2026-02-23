# tests/engine/recruitment/MLPSM/test_p_ind.py
"""
Tests unitaires pour engine.recruitment.MLPSM.p_ind.compute()

P_ind = (GCA × 0.60) + (C × 0.40)

Couverture :
    - Score nominal : formule vérifiée manuellement
    - GCA absent → fallback 50.0 + flag GCA_MISSING + data_quality -= 0.35
    - Big Five absent → fallback C=50.0 + flag BIG_FIVE_MISSING
    - Score clamped : jamais < 0 ou > 100
    - PIndResult structure complète
"""
import pytest

from app.engine.recruitment.MLPSM.p_ind import (
    compute,
    PIndResult,
    OMEGA_GCA,
    OMEGA_CONSCIENTIOUSNESS,
)

pytestmark = pytest.mark.engine


def snap_full(gca=72.0, conscientiousness=75.0):
    """Snapshot avec GCA pré-calculé et Conscienciosité."""
    return {
        "cognitive": {"gca_score": gca, "n_tests": 1},
        "big_five": {"conscientiousness": conscientiousness},
    }


def snap_no_cognitive(conscientiousness=75.0):
    return {"big_five": {"conscientiousness": conscientiousness}}


def snap_no_big_five(gca=72.0):
    return {"cognitive": {"gca_score": gca}}


def snap_empty():
    return {}


class TestPIndCompute:
    def test_retourne_pind_result(self):
        result = compute(snap_full())
        assert isinstance(result, PIndResult)

    def test_score_formule_nominale(self):
        """P_ind = GCA×0.60 + C×0.40 vérifié manuellement."""
        gca = 80.0
        c = 70.0
        expected = round((gca * OMEGA_GCA) + (c * OMEGA_CONSCIENTIOUSNESS), 1)
        result = compute(snap_full(gca=gca, conscientiousness=c))
        assert result.score == expected

    def test_score_dans_bornes(self):
        result = compute(snap_full())
        assert 0.0 <= result.score <= 100.0

    def test_data_quality_complete(self):
        """Données complètes → data_quality = 1.0."""
        result = compute(snap_full())
        assert result.data_quality == 1.0

    def test_gca_manquant_fallback(self):
        """Aucun test cognitif → GCA = 50.0, flag GCA_MISSING, data_quality -= 0.35."""
        result = compute(snap_no_cognitive(conscientiousness=80.0))
        assert any("GCA_MISSING" in f for f in result.flags)
        assert result.gca.gca_score == 50.0
        assert result.data_quality <= 0.65

    def test_big_five_manquant_fallback(self):
        """Pas de Big Five → C = 50.0, flag BIG_FIVE_MISSING."""
        result = compute(snap_no_big_five(gca=80.0))
        assert any("BIG_FIVE_MISSING" in f for f in result.flags)
        assert result.conscientiousness.c_score == 50.0

    def test_snapshot_vide_double_fallback(self):
        """Snapshot vide → GCA=50, C=50, P_ind = 50.0."""
        result = compute(snap_empty())
        expected = round((50.0 * OMEGA_GCA) + (50.0 * OMEGA_CONSCIENTIOUSNESS), 1)
        assert result.score == expected

    def test_score_clamp_max(self):
        """GCA=100, C=100 → P_ind ne dépasse pas 100."""
        result = compute(snap_full(gca=100.0, conscientiousness=100.0))
        assert result.score <= 100.0

    def test_score_clamp_min(self):
        """Score brut négatif impossible (GCA et C ≥ 0) mais le clamp est présent."""
        result = compute(snap_full(gca=0.0, conscientiousness=0.0))
        assert result.score >= 0.0

    def test_experience_years_transmis(self):
        """experience_years est enregistré dans ExperienceDetail."""
        result = compute(snap_full(), experience_years=5)
        assert result.experience.years == 5

    def test_experience_bonus_desactive_temps1(self):
        """En Temps 1, le bonus expérience ne doit pas modifier le score."""
        result_0yr = compute(snap_full(gca=72.0, conscientiousness=75.0), experience_years=0)
        result_10yr = compute(snap_full(gca=72.0, conscientiousness=75.0), experience_years=10)
        assert result_0yr.score == result_10yr.score

    def test_formula_snapshot(self):
        """formula_snapshot doit contenir la formule P_ind."""
        result = compute(snap_full(gca=80.0, conscientiousness=70.0))
        assert "P_ind" in result.formula_snapshot
        assert "0.60" in result.formula_snapshot or "OMEGA" in result.formula_snapshot or "0.6" in result.formula_snapshot

    def test_sous_scores_cognitifs_extraits(self):
        """Les sous-scores cognitifs sont disponibles dans GCADetail si fournis."""
        snap = {
            "cognitive": {
                "gca_score": 72.0,
                "logical_reasoning": 74.0,
                "numerical_reasoning": 70.0,
                "verbal_reasoning": 72.0,
            },
            "big_five": {"conscientiousness": 70.0},
        }
        result = compute(snap)
        assert result.gca.logical_reasoning == 74.0
        assert result.gca.numerical_reasoning == 70.0
        assert result.gca.verbal_reasoning == 72.0
