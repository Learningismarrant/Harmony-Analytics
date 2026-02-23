# tests/engine/recruitment/MLPSM/test_f_env.py
"""
Tests unitaires pour engine.recruitment.MLPSM.f_env.compute()

F_env = (R_yacht / D_yacht) × Resilience_ind × 100  (cappé à 100)

Couverture :
    - Score nominal JDR équilibré (R ≈ D) → score ~50
    - Ressources > demandes → score > 50
    - Ressources nulles → score = 0
    - Résilience = 0 → score = 0 (multiplicateur)
    - vessel_params absent → flag NO_VESSEL_PARAMS, data_quality -= 0.40
    - Résilience basse → flag LOW_RESILIENCE
    - BURNOUT_RISK flag quand ratio < 0.40
    - Sources de résilience : snapshot.resilience, big_five.ES, fallback
"""
import pytest

from app.engine.recruitment.MLPSM.f_env import (
    compute,
    FEnvResult,
    BURNOUT_RISK_THRESHOLD,
    COMFORT_THRESHOLD,
    RESILIENCE_LOW_THRESHOLD,
    JDR_RATIO_CAP,
)

pytestmark = pytest.mark.engine


def vessel_nominal():
    """JDR équilibré : R ≈ D ≈ 0.5."""
    return {
        "salary_index": 0.5,
        "rest_days_ratio": 0.5,
        "private_cabin_ratio": 0.5,
        "charter_intensity": 0.5,
        "management_pressure": 0.5,
    }


def vessel_high_resources():
    """Ressources très élevées, demandes faibles."""
    return {
        "salary_index": 0.9,
        "rest_days_ratio": 0.9,
        "private_cabin_ratio": 0.8,
        "charter_intensity": 0.2,
        "management_pressure": 0.2,
    }


def vessel_high_demands():
    """Demandes très élevées, ressources faibles → burnout risk."""
    return {
        "salary_index": 0.1,
        "rest_days_ratio": 0.1,
        "private_cabin_ratio": 0.1,
        "charter_intensity": 0.9,
        "management_pressure": 0.9,
    }


def snap_with_resilience(value=70.0):
    return {"resilience": value}


def snap_with_es(es=70.0):
    return {"big_five": {"emotional_stability": es}}


def snap_with_neuroticism(neuroticism=30.0):
    return {"big_five": {"neuroticism": neuroticism}}


def snap_empty():
    return {}


class TestFEnvCompute:
    def test_retourne_fenv_result(self):
        result = compute(snap_with_resilience(), vessel_nominal())
        assert isinstance(result, FEnvResult)

    def test_score_dans_bornes(self):
        result = compute(snap_with_resilience(), vessel_nominal())
        assert 0.0 <= result.score <= 100.0

    def test_ressources_elevees_score_eleve(self):
        """Ressources >> Demandes → score élevé."""
        result = compute(snap_with_resilience(80.0), vessel_high_resources())
        assert result.score > 60.0

    def test_demandes_elevees_score_faible(self):
        """Demandes >> Ressources → score faible."""
        result = compute(snap_with_resilience(70.0), vessel_high_demands())
        assert result.score < 40.0

    def test_resilience_zero_donne_score_zero(self):
        """Résilience = 0 → F_env = 0 (multiplicateur)."""
        result = compute(snap_with_resilience(0.0), vessel_nominal())
        assert result.score == 0.0

    def test_vessel_params_absent(self):
        """vessel_params vide → flag NO_VESSEL_PARAMS, data_quality réduite."""
        result = compute(snap_with_resilience(), {})
        assert any("NO_VESSEL_PARAMS" in f for f in result.flags)
        assert result.data_quality < 1.0

    def test_vessel_params_none_traite_comme_vide(self):
        """None est traité comme dict vide → pas d'exception."""
        result = compute(snap_empty(), {})
        assert isinstance(result, FEnvResult)

    def test_burnout_risk_flag(self):
        """Ratio < BURNOUT_RISK_THRESHOLD → flag BURNOUT_RISK."""
        result = compute(snap_with_resilience(70.0), vessel_high_demands())
        if result.jdr_ratio.raw_ratio < BURNOUT_RISK_THRESHOLD:
            assert result.jdr_ratio.equilibrium_status == "BURNOUT_RISK"
            assert any("BURNOUT_RISK" in f for f in result.flags)

    def test_resilience_basse_flag(self):
        """Résilience < RESILIENCE_LOW_THRESHOLD → flag LOW_RESILIENCE."""
        result = compute(snap_with_resilience(30.0), vessel_nominal())
        assert any("LOW_RESILIENCE" in f for f in result.flags)
        assert result.resilience.is_low is True

    def test_source_resilience_directe(self):
        """snapshot.resilience → source='snapshot.resilience'."""
        result = compute(snap_with_resilience(70.0), vessel_nominal())
        assert result.resilience.source == "snapshot.resilience"

    def test_source_resilience_big_five_es(self):
        """snapshot.big_five.emotional_stability → source='big_five.emotional_stability'."""
        result = compute(snap_with_es(70.0), vessel_nominal())
        assert result.resilience.source == "big_five.emotional_stability"

    def test_source_resilience_neuroticism(self):
        """snapshot.big_five.neuroticism → source='big_five.emotional_stability' (dérivé)."""
        result = compute(snap_with_neuroticism(30.0), vessel_nominal())
        assert result.resilience.source == "big_five.emotional_stability"

    def test_source_resilience_fallback(self):
        """Aucune source disponible → source='fallback_median', resilience=50."""
        result = compute(snap_empty(), vessel_nominal())
        assert result.resilience.source == "fallback_median"
        assert result.resilience.resilience_raw == 50.0

    def test_jdr_cap_applique(self):
        """Ratio > JDR_RATIO_CAP (2.0) → capped_ratio = 2.0."""
        result = compute(snap_with_resilience(80.0), vessel_high_resources())
        assert result.jdr_ratio.capped_ratio <= JDR_RATIO_CAP

    def test_equilibrium_comfortable(self):
        """Ratio élevé → equilibrium_status='COMFORTABLE'."""
        result = compute(snap_with_resilience(80.0), vessel_high_resources())
        if result.jdr_ratio.raw_ratio >= COMFORT_THRESHOLD:
            assert result.jdr_ratio.equilibrium_status == "COMFORTABLE"

    def test_details_resources_presents(self):
        """ResourcesDetail et DemandsDetail doivent être correctement remplis."""
        result = compute(snap_with_resilience(), vessel_nominal())
        assert result.resources.salary_index == 0.5
        assert result.demands.charter_intensity == 0.5
