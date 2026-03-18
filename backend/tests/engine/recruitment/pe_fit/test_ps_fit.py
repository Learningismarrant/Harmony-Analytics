# tests/engine/recruitment/pe_fit/test_ps_fit.py
"""
Tests unitaires pour engine.recruitment.pe_fit.ps_fit.f_lmx

Couverture :
    compute_fit() avec captain_vector complet    → FLmxResult, score [0, 100]
    compute_fit() avec captain_vector=None       → None
    compute_fit() snapshot vide                  → pas d'exception, FLmxResult
    compute() rétrocompatibilité                 → FLmxResult identique à MLPSM
"""
import pytest

from app.engine.pe_fit.ps_fit.f_lmx import (
    compute,
    compute_fit,
    FLmxResult,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def captain_nominal():
    return {
        "autonomy_given": 0.6,
        "feedback_style": 0.4,
        "structure_imposed": 0.5,
    }


def captain_directive():
    """Capitaine très directif : peu d'autonomie, structure rigide."""
    return {
        "autonomy_given": 0.1,
        "feedback_style": 0.2,
        "structure_imposed": 0.9,
    }


def snap_autonome():
    """Candidat préférant beaucoup d'autonomie — via Big Five openness élevé."""
    return {
        "big_five": {
            "openness": 90.0,
            "agreeableness": 50.0,
            "conscientiousness": 40.0,
        }
    }


def snap_with_lp():
    """Candidat avec leadership_preferences explicites."""
    return {
        "leadership_preferences": {
            "autonomy_preference": 0.6,
            "feedback_preference": 0.4,
            "structure_preference": 0.5,
        }
    }


def snap_empty():
    return {}


# ── Tests compute_fit() ───────────────────────────────────────────────────────

class TestComputeFit:
    def test_captain_vector_complet_retourne_flmx_result(self):
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert isinstance(result, FLmxResult)

    def test_score_dans_bornes(self):
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert result is not None
        assert 0.0 <= result.score <= 100.0

    def test_captain_vector_none_retourne_none(self):
        result = compute_fit(snap_with_lp(), None)
        assert result is None

    def test_captain_vector_vide_retourne_none(self):
        result = compute_fit(snap_with_lp(), {})
        assert result is None

    def test_snapshot_vide_pas_exception(self):
        """snapshot sans données → compute_fit retourne FLmxResult sans exception."""
        result = compute_fit(snap_empty(), captain_nominal())
        assert isinstance(result, FLmxResult)
        assert 0.0 <= result.score <= 100.0

    def test_alignement_parfait_score_eleve(self):
        """Préférences candidat = style capitaine → score proche de 100."""
        snap_aligned = {
            "leadership_preferences": {
                "autonomy_preference": 0.6,
                "feedback_preference": 0.4,
                "structure_preference": 0.5,
            }
        }
        result = compute_fit(snap_aligned, captain_nominal())
        assert result is not None
        assert result.score > 90.0

    def test_incompatibilite_maximale_score_bas(self):
        """Candidat veut autonomie max, capitaine est directif → score bas."""
        snap_max_autonomy = {
            "leadership_preferences": {
                "autonomy_preference": 1.0,
                "feedback_preference": 1.0,
                "structure_preference": 0.0,
            }
        }
        result = compute_fit(snap_max_autonomy, captain_directive())
        assert result is not None
        assert result.score < 50.0

    def test_vectors_remplis(self):
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert result is not None
        assert result.vectors.captain_autonomy_given == 0.6
        assert result.vectors.crew_autonomy_preference == 0.6

    def test_dimensions_trois_elements(self):
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert result is not None
        assert len(result.dimensions) == 3
        dims = {d.dimension for d in result.dimensions}
        assert dims == {"autonomy", "feedback", "structure"}

    def test_distance_normalisee_dans_bornes(self):
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert result is not None
        assert 0.0 <= result.distance.normalized_distance <= 1.0

    def test_compatibility_inverse_distance(self):
        """compatibility = 1 - normalized_distance."""
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert result is not None
        assert abs(result.distance.compatibility - (1.0 - result.distance.normalized_distance)) < 1e-6

    def test_source_leadership_preferences_direct(self):
        """Quand leadership_preferences est fourni → data_quality élevée."""
        result = compute_fit(snap_with_lp(), captain_nominal())
        assert result is not None
        assert result.vectors.crew_data_completeness == 1.0

    def test_source_big_five_fallback(self):
        """Sans leadership_preferences, dérivation depuis Big Five."""
        result = compute_fit(snap_autonome(), captain_nominal())
        assert result is not None
        assert isinstance(result, FLmxResult)


# ── Tests compute() rétrocompatibilité ────────────────────────────────────────

class TestComputeRetrocompat:
    def test_compute_retourne_flmx_result(self):
        result = compute(snap_with_lp(), captain_nominal())
        assert isinstance(result, FLmxResult)

    def test_compute_score_dans_bornes(self):
        result = compute(snap_with_lp(), captain_nominal())
        assert 0.0 <= result.score <= 100.0

    def test_compute_captain_incomplet_flag(self):
        result = compute(snap_with_lp(), {})
        assert any("CAPTAIN_DATA_INCOMPLETE" in f for f in result.flags)
        assert result.data_quality < 1.0

    def test_compute_formula_snapshot_non_vide(self):
        result = compute(snap_with_lp(), captain_nominal())
        assert isinstance(result.formula_snapshot, str)
        assert len(result.formula_snapshot) > 0
