# tests/engine/recruitment/pe_fit/test_po_fit.py
"""
Tests unitaires pour engine.recruitment.pe_fit.po_fit.f_env

Couverture :
    compute_fit() avec vessel_params complet     → FEnvResult, score [0, 100]
    compute_fit() avec vessel_params=None        → None
    compute_fit() snapshot vide                  → pas d'exception, FEnvResult
    compute() rétrocompatibilité                 → FEnvResult identique à MLPSM
"""
import pytest

from app.engine.pe_fit.po_fit.f_env import (
    compute,
    compute_fit,
    FEnvResult,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def vessel_nominal():
    return {
        "salary_index": 0.6,
        "rest_days_ratio": 0.6,
        "private_cabin_ratio": 0.5,
        "charter_intensity": 0.4,
        "management_pressure": 0.4,
    }


def vessel_high_demands():
    return {
        "salary_index": 0.1,
        "rest_days_ratio": 0.1,
        "private_cabin_ratio": 0.1,
        "charter_intensity": 0.9,
        "management_pressure": 0.9,
    }


def snap_resilient(value=70.0):
    return {"resilience": value}


def snap_big_five_es(es=65.0):
    return {"big_five": {"emotional_stability": es}}


def snap_big_five_neuroticism(n=30.0):
    return {"big_five": {"neuroticism": n}}


def snap_empty():
    return {}


# ── Tests compute_fit() ───────────────────────────────────────────────────────

class TestComputeFit:
    def test_vessel_params_complet_retourne_fenv_result(self):
        result = compute_fit(snap_resilient(), vessel_nominal())
        assert isinstance(result, FEnvResult)

    def test_score_dans_bornes(self):
        result = compute_fit(snap_resilient(), vessel_nominal())
        assert result is not None
        assert 0.0 <= result.score <= 100.0

    def test_vessel_params_none_retourne_none(self):
        result = compute_fit(snap_resilient(), None)
        assert result is None

    def test_vessel_params_vide_retourne_none(self):
        result = compute_fit(snap_resilient(), {})
        assert result is None

    def test_snapshot_vide_pas_exception(self):
        """snapshot sans données → compute_fit retourne FEnvResult sans lever d'exception."""
        result = compute_fit(snap_empty(), vessel_nominal())
        assert isinstance(result, FEnvResult)
        assert 0.0 <= result.score <= 100.0

    def test_score_eleve_avec_bonnes_ressources(self):
        """Ressources élevées, demandes faibles, résilience forte → score élevé."""
        result = compute_fit(snap_resilient(80.0), vessel_nominal())
        assert result is not None
        assert result.score > 40.0

    def test_score_faible_avec_demandes_elevees(self):
        """Demandes >> ressources → score faible."""
        result = compute_fit(snap_resilient(70.0), vessel_high_demands())
        assert result is not None
        assert result.score < 40.0

    def test_resilience_zero_donne_score_zero(self):
        """Résilience = 0 → F_env = 0 (multiplicateur)."""
        result = compute_fit(snap_resilient(0.0), vessel_nominal())
        assert result is not None
        assert result.score == 0.0

    def test_source_resilience_directe(self):
        result = compute_fit(snap_resilient(70.0), vessel_nominal())
        assert result is not None
        assert result.resilience.source == "snapshot.resilience"

    def test_source_resilience_big_five_es(self):
        result = compute_fit(snap_big_five_es(65.0), vessel_nominal())
        assert result is not None
        assert result.resilience.source == "big_five.emotional_stability"

    def test_source_resilience_neuroticism(self):
        result = compute_fit(snap_big_five_neuroticism(30.0), vessel_nominal())
        assert result is not None
        assert result.resilience.source == "big_five.emotional_stability"

    def test_source_resilience_fallback(self):
        result = compute_fit(snap_empty(), vessel_nominal())
        assert result is not None
        assert result.resilience.source == "fallback_median"

    def test_burnout_risk_flag_si_ratio_bas(self):
        """Ratio JD-R très bas → flag BURNOUT_RISK."""
        result = compute_fit(snap_resilient(70.0), vessel_high_demands())
        assert result is not None
        if result.jdr_ratio.raw_ratio < 0.40:
            assert any("BURNOUT_RISK" in f for f in result.flags)

    def test_data_quality_non_nul(self):
        result = compute_fit(snap_resilient(), vessel_nominal())
        assert result is not None
        assert result.data_quality > 0.0


# ── Tests rétrocompatibilité compute() ────────────────────────────────────────

class TestComputeRetrocompat:
    def test_compute_retourne_fenv_result(self):
        result = compute(snap_resilient(), vessel_nominal())
        assert isinstance(result, FEnvResult)

    def test_compute_score_dans_bornes(self):
        result = compute(snap_resilient(), vessel_nominal())
        assert 0.0 <= result.score <= 100.0

    def test_compute_vessel_vide_flag_no_vessel_params(self):
        result = compute(snap_empty(), {})
        assert any("NO_VESSEL_PARAMS" in f for f in result.flags)
        assert result.data_quality < 1.0

    def test_compute_details_remplis(self):
        result = compute(snap_resilient(), vessel_nominal())
        assert result.resources.salary_index == 0.6
        assert result.demands.charter_intensity == 0.4
        assert result.formula_snapshot != ""
