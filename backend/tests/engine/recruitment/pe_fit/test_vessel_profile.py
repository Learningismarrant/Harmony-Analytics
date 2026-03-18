# tests/engine/recruitment/pe_fit/test_vessel_profile.py
"""
Tests unitaires pour pe_fit/vessel_profile.py

Couverture :
    YachtStructuralProfile.to_vessel_params() — structure et valeurs par type
    Ajustement longueur < 25m → space_constraint +10%
    Override manuel via override()
    org_values et captain_vector transmis si fournis
    Tous les types YachtTypeAlpha ont des defaults
    Intégration : vessel_params généré → pe_fit.compute() ne lève pas d'exception
"""
import pytest
from app.engine.pe_fit.vessel_profile import YachtStructuralProfile, _STRUCTURAL_DEFAULTS
from app.engine.pe_fit.master import compute as pe_fit_compute
from app.shared.enums import YachtTypeAlpha

pytestmark = pytest.mark.engine


# ── Fixture snapshot minimal ──────────────────────────────────────────────────

def _snap() -> dict:
    return {
        "big_five": {
            "conscientiousness":   80.0,
            "agreeableness":       75.0,
            "emotional_stability": 70.0,
            "openness":            65.0,
            "extraversion":        60.0,
            "neuroticism":         30.0,
        },
        "emotional_stability": 70.0,
        "cognitive": {"gca_score": 72.0},
        "maritime_tolerance": {
            "confined_space_tolerance": 70.0,
            "isolation_tolerance":      65.0,
            "physical_risk_tolerance":  60.0,
            "schedule_tolerance":       70.0,
            "weather_tolerance":        65.0,
        },
        "mobility_profile": {
            "mobility_flexibility":  70.0,
            "embarkation_tolerance": 65.0,
            "uncertainty_tolerance": 60.0,
            "contract_flexibility":  70.0,
        },
    }


# ── Tests to_vessel_params() ─────────────────────────────────────────────────

class TestToVesselParams:
    def test_retourne_dict(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.SUPERYACHT)
        params = profile.to_vessel_params()
        assert isinstance(params, dict)

    def test_clés_base_presentes(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.MOTOR_CRUISER)
        params = profile.to_vessel_params()
        expected = {
            "salary_index", "rest_days_ratio", "private_cabin_ratio",
            "charter_intensity", "management_pressure",
        }
        assert expected.issubset(params.keys())

    def test_maritime_conditions_presentes(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.SAILING_CRUISER)
        params = profile.to_vessel_params()
        assert "maritime_conditions" in params
        mc = params["maritime_conditions"]
        expected_keys = {
            "space_constraint_level", "isolation_level", "physical_risk_level",
            "schedule_irregularity", "weather_exposure",
        }
        assert expected_keys == set(mc.keys())

    def test_mobility_requirements_presentes(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.EXPEDITION)
        params = profile.to_vessel_params()
        assert "mobility_requirements" in params
        mr = params["mobility_requirements"]
        expected_keys = {
            "mobility_level", "embarkation_weeks",
            "schedule_unpredictability", "contract_permanence",
        }
        assert expected_keys == set(mr.keys())

    def test_salary_index_transmis(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.MEGAYACHT)
        params = profile.to_vessel_params(salary_index=0.85)
        assert params["salary_index"] == 0.85

    def test_org_values_transmises_si_fournies(self):
        org = {"honesty": 0.9, "achievement": 0.8, "fairness": 0.7, "solidarity": 0.6}
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.CHARTER)
        params = profile.to_vessel_params(org_values=org)
        assert "org_values" in params
        assert params["org_values"] == org

    def test_org_values_absentes_si_non_fournies(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.CHARTER)
        params = profile.to_vessel_params()
        assert "org_values" not in params

    def test_captain_vector_transmis_si_fourni(self):
        cv = {"autonomy_given": 0.7, "feedback_style": 0.5, "structure_imposed": 0.4}
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.SUPERYACHT)
        params = profile.to_vessel_params(captain_vector=cv)
        assert "captain_vector" in params
        assert params["captain_vector"] == cv


class TestAjustementLongueur:
    def test_longueur_inferieure_25m_augmente_space_constraint(self):
        """< 25m → space_constraint_level += 0.10 (clamped à 1.0)."""
        profile_court = YachtStructuralProfile(
            yacht_type=YachtTypeAlpha.SAILING_CRUISER, length_m=20.0
        )
        profile_normal = YachtStructuralProfile(
            yacht_type=YachtTypeAlpha.SAILING_CRUISER, length_m=35.0
        )
        params_court  = profile_court.to_vessel_params()
        params_normal = profile_normal.to_vessel_params()
        sc_court  = params_court["maritime_conditions"]["space_constraint_level"]
        sc_normal = params_normal["maritime_conditions"]["space_constraint_level"]
        assert sc_court > sc_normal

    def test_longueur_superieure_25m_pas_ajustement(self):
        default_sc = _STRUCTURAL_DEFAULTS[YachtTypeAlpha.MOTOR_CRUISER.value][
            "maritime_conditions"
        ]["space_constraint_level"]
        profile = YachtStructuralProfile(
            yacht_type=YachtTypeAlpha.MOTOR_CRUISER, length_m=30.0
        )
        params = profile.to_vessel_params()
        assert params["maritime_conditions"]["space_constraint_level"] == default_sc

    def test_space_constraint_clampe_a_1(self):
        """Cas limite : space_constraint + 0.10 ne dépasse pas 1.0."""
        profile = YachtStructuralProfile(
            yacht_type=YachtTypeAlpha.SAILING_RACING, length_m=10.0
        )
        params = profile.to_vessel_params()
        assert params["maritime_conditions"]["space_constraint_level"] <= 1.0


class TestOverride:
    def test_override_retourne_nouveau_profil(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.SUPERYACHT)
        new_profile = profile.override(management_pressure=0.9)
        # Le profil d'origine est inchangé
        original_params = profile.to_vessel_params()
        new_params = new_profile.to_vessel_params()
        assert original_params["management_pressure"] != 0.9
        assert new_params["management_pressure"] == 0.9

    def test_override_peut_empiler(self):
        profile = YachtStructuralProfile(yacht_type=YachtTypeAlpha.CHARTER)
        new_profile = (
            profile
            .override(salary_index=0.9)
            .override(management_pressure=0.8)
        )
        params = new_profile.to_vessel_params()
        assert params["salary_index"] == 0.9
        assert params["management_pressure"] == 0.8


class TestTousLesTypes:
    @pytest.mark.parametrize("yacht_type", list(YachtTypeAlpha))
    def test_to_vessel_params_ne_leve_pas_exception(self, yacht_type: YachtTypeAlpha):
        profile = YachtStructuralProfile(yacht_type=yacht_type, length_m=35.0)
        params = profile.to_vessel_params()
        assert isinstance(params, dict)

    @pytest.mark.parametrize("yacht_type", list(YachtTypeAlpha))
    def test_defaults_existent_pour_chaque_type(self, yacht_type: YachtTypeAlpha):
        assert yacht_type.value in _STRUCTURAL_DEFAULTS


class TestIntegrationPEFit:
    def test_vessel_params_genere_compatible_avec_pe_fit(self):
        """
        vessel_params généré par to_vessel_params() est accepté par pe_fit.compute()
        sans lever d'exception.
        """
        profile = YachtStructuralProfile(
            yacht_type=YachtTypeAlpha.SUPERYACHT,
            length_m=45.0,
            crew_size=12,
        )
        params = profile.to_vessel_params(
            salary_index=0.75,
            org_values={"honesty": 0.8, "achievement": 0.7, "fairness": 0.7, "solidarity": 0.6},
        )
        snap = _snap()
        result = pe_fit_compute(snap, vessel_params=params, position="Captain")
        assert 0.0 <= result.global_score <= 100.0
        assert result.physical_fit is not None
        assert result.mobility_fit is not None

    @pytest.mark.parametrize("yacht_type", list(YachtTypeAlpha))
    def test_integration_tous_types(self, yacht_type: YachtTypeAlpha):
        profile = YachtStructuralProfile(yacht_type=yacht_type, length_m=40.0)
        params = profile.to_vessel_params()
        snap = _snap()
        result = pe_fit_compute(snap, vessel_params=params)
        assert 0.0 <= result.global_score <= 100.0
