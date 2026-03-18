# tests/engine/recruitment/pe_fit/test_jdr.py
"""
Tests unitaires pour engine.pe_fit.pj_fit.needs_supplies.jdr

Couverture :
    compute() sans vessel_params           → None
    compute() environnement confortable    → score élevé, COMFORTABLE
    compute() risque burnout               → score bas, BURNOUT_RISK
    buffer effect : haute résilience mitige demandes élevées
    fallback vessel_params partiels        → data_quality < 1.0
"""
import pytest

from app.engine.pe_fit.pj_fit.needs_supplies.jdr import compute, JDRResult

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def vessel_comfortable():
    """Ressources élevées, demandes faibles."""
    return {
        "salary_index": 0.85,
        "rest_days_ratio": 0.80,
        "private_cabin_ratio": 0.90,
        "charter_intensity": 0.15,
        "management_pressure": 0.10,
    }


def vessel_high_demands():
    """Ressources faibles, demandes très élevées."""
    return {
        "salary_index": 0.10,
        "rest_days_ratio": 0.10,
        "private_cabin_ratio": 0.10,
        "charter_intensity": 0.95,
        "management_pressure": 0.95,
    }


def snap_resilient(resilience=80.0):
    return {"resilience": resilience}


def snap_low_resilience():
    return {"resilience": 25.0}


def snap_empty():
    return {}


def vessel_partial():
    """Seulement 2 paramètres renseignés sur 5."""
    return {
        "charter_intensity": 0.5,
        "management_pressure": 0.5,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

class TestComputeWithoutVesselParams:
    def test_returns_none_without_vessel_params(self):
        result = compute(snap_resilient(), vessel_params=None)
        assert result is None

    def test_returns_none_with_empty_vessel_params(self):
        result = compute(snap_resilient(), vessel_params={})
        assert result is None


class TestComfortableEnvironment:
    def test_comfortable_environment_score_eleve(self):
        """Ressources élevées, demandes faibles, résilience forte → score élevé."""
        result = compute(snap_resilient(80.0), vessel_comfortable())
        assert result is not None
        assert result.score > 50.0

    def test_comfortable_environment_statut(self):
        """Overload faible → COMFORTABLE."""
        result = compute(snap_resilient(80.0), vessel_comfortable())
        assert result is not None
        assert result.buffer.equilibrium_status == "COMFORTABLE"

    def test_comfortable_returns_jdr_result(self):
        result = compute(snap_resilient(70.0), vessel_comfortable())
        assert isinstance(result, JDRResult)

    def test_comfortable_score_dans_bornes(self):
        result = compute(snap_resilient(70.0), vessel_comfortable())
        assert result is not None
        assert 0.0 <= result.score <= 100.0

    def test_comfortable_data_quality_un(self):
        """Tous les paramètres présents → data_quality = 1.0."""
        result = compute(snap_resilient(70.0), vessel_comfortable())
        assert result is not None
        assert result.data_quality == 1.0


class TestBurnoutRisk:
    def test_burnout_risk_score_bas(self):
        """Demandes très élevées, résilience basse → score bas."""
        result = compute(snap_low_resilience(), vessel_high_demands())
        assert result is not None
        assert result.score < 30.0

    def test_burnout_risk_statut(self):
        """Overload élevé → BURNOUT_RISK."""
        result = compute(snap_low_resilience(), vessel_high_demands())
        assert result is not None
        assert result.buffer.equilibrium_status == "BURNOUT_RISK"

    def test_burnout_risk_flag_present(self):
        """Flag BURNOUT_RISK dans les flags."""
        result = compute(snap_low_resilience(), vessel_high_demands())
        assert result is not None
        assert any("BURNOUT_RISK" in f for f in result.flags)

    def test_resilience_zero_donne_score_zero(self):
        """Résilience = 0 → score = 0 (multiplicateur modulator = 0)."""
        result = compute({"resilience": 0.0}, vessel_comfortable())
        assert result is not None
        assert result.score == 0.0


class TestBufferEffectHighResilience:
    def test_haute_resilience_mitige_demandes_elevees(self):
        """
        Même demandes élevées : ES=80 doit produire un score plus élevé qu'ES=30.
        Le buffer est centré sur la résilience individuelle.
        """
        snap_high_es = {"resilience": 80.0}
        snap_low_es  = {"resilience": 30.0}

        result_high = compute(snap_high_es, vessel_high_demands())
        result_low  = compute(snap_low_es,  vessel_high_demands())

        assert result_high is not None
        assert result_low  is not None
        assert result_high.score > result_low.score

    def test_resilience_source_directe(self):
        result = compute({"resilience": 70.0}, vessel_comfortable())
        assert result is not None
        assert result.resilience_source == "snapshot.resilience"

    def test_resilience_depuis_big_five_neuroticism(self):
        """Neuroticism=20 → résilience dérivée = 80."""
        snap = {"big_five": {"neuroticism": 20.0}}
        result = compute(snap, vessel_comfortable())
        assert result is not None
        assert result.resilience_source == "big_five.neuroticism_derived"
        assert abs(result.resilience_raw - 80.0) < 0.1

    def test_resilience_fallback_si_aucune_donnee(self):
        result = compute(snap_empty(), vessel_comfortable())
        assert result is not None
        assert result.resilience_source == "fallback_median"
        assert result.resilience_raw == 50.0


class TestFallbackVesselParams:
    def test_partial_vessel_params_data_quality_inferieure_a_un(self):
        """Paramètres manquants → data_quality < 1.0."""
        result = compute(snap_resilient(70.0), vessel_partial())
        assert result is not None
        assert result.data_quality < 1.0

    def test_partial_vessel_params_flags_fallback(self):
        """Paramètres manquants → flags FALLBACK_*."""
        result = compute(snap_resilient(70.0), vessel_partial())
        assert result is not None
        fallback_flags = [f for f in result.flags if "FALLBACK_" in f]
        assert len(fallback_flags) >= 3  # salary, rest, cabin manquants

    def test_partial_vessel_params_score_quand_meme_calcule(self):
        """Même avec des fallbacks, un score est toujours retourné."""
        result = compute(snap_resilient(70.0), vessel_partial())
        assert result is not None
        assert 0.0 <= result.score <= 100.0

    def test_formula_snapshot_non_vide(self):
        result = compute(snap_resilient(70.0), vessel_comfortable())
        assert result is not None
        assert isinstance(result.formula_snapshot, str)
        assert len(result.formula_snapshot) > 0

    def test_resources_detail_correct(self):
        result = compute(snap_resilient(70.0), vessel_comfortable())
        assert result is not None
        assert result.resources.raw > 0
        assert result.demands.raw > 0
