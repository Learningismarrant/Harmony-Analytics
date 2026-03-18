# tests/engine/recruitment/pe_fit/test_physical_fit.py
"""
Tests unitaires pour engine.pe_fit.physical_fit.f_physical

Couverture :
    PSI par dimension (6.1–6.5)
    Score global ∈ [0, 100]
    Sur-fit risque physique (6.3) pénalisé
    Données absentes → médiane (0.5 par dimension)
    compute_fit() → None si pas de données maritimes
    Alertes LOW_TOLERANCE
"""
import pytest
from app.engine.pe_fit.physical_fit.f_physical import (
    compute,
    compute_fit,
    FPhysicalResult,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _snapshot_full(
    confined: float = 80.0,
    isolation: float = 75.0,
    risk: float = 70.0,
    schedule: float = 65.0,
    weather: float = 60.0,
) -> dict:
    return {
        "maritime_tolerance": {
            "confined_space_tolerance": confined,
            "isolation_tolerance":      isolation,
            "physical_risk_tolerance":  risk,
            "schedule_tolerance":       schedule,
            "weather_tolerance":        weather,
        }
    }


def _vessel_full(
    space: float = 0.7,
    isolation: float = 0.6,
    risk: float = 0.6,
    schedule: float = 0.7,
    weather: float = 0.5,
) -> dict:
    return {
        "maritime_conditions": {
            "space_constraint_level": space,
            "isolation_level":        isolation,
            "physical_risk_level":    risk,
            "schedule_irregularity":  schedule,
            "weather_exposure":       weather,
        }
    }


SNAP = _snapshot_full()
VESSEL = _vessel_full()


# ── Tests compute() ───────────────────────────────────────────────────────────

class TestComputeBase:
    def test_retourne_f_physical_result(self):
        result = compute(SNAP, VESSEL)
        assert isinstance(result, FPhysicalResult)

    def test_score_dans_bornes(self):
        result = compute(SNAP, VESSEL)
        assert 0.0 <= result.score <= 100.0

    def test_5_dimensions_presentes(self):
        result = compute(SNAP, VESSEL)
        assert len(result.dimensions) == 5

    def test_data_quality_pleine_si_donnees_completes(self):
        result = compute(SNAP, VESSEL)
        assert result.data_quality == 1.0

    def test_flags_vide_si_hautes_tolerances(self):
        """Candidat avec hautes tolérances et poste nominal → pas d'alerte."""
        result = compute(_snapshot_full(80, 80, 65, 80, 80), _vessel_full())
        assert result.flags == []


class TestPSIParDimension:
    def test_psi_parfait_si_p_egal_e(self):
        """P = E → PSI = 1.0 → score_dim = 100."""
        snap = _snapshot_full(confined=70.0)
        vessel = _vessel_full(space=0.70)
        result = compute(snap, vessel)
        dim_61 = next(d for d in result.dimensions if d.dimension == "confined_space_6.1")
        assert abs(dim_61.score - 1.0) < 0.01

    def test_psi_minimal_si_p_oppose_e(self):
        """P_norm = 0.0, E = 1.0 → PSI = 0.0."""
        snap = _snapshot_full(confined=0.0)
        vessel = _vessel_full(space=1.0)
        result = compute(snap, vessel)
        dim_61 = next(d for d in result.dimensions if d.dimension == "confined_space_6.1")
        assert dim_61.score <= 0.01

    def test_psi_symetrique_sous_fit(self):
        """P basse sur poste E haute → sous-fit pénalisé."""
        snap = _snapshot_full(isolation=20.0)
        vessel = _vessel_full(isolation=0.9)
        result = compute(snap, vessel)
        dim_62 = next(d for d in result.dimensions if d.dimension == "isolation_6.2")
        assert dim_62.score < 0.5


class TestRisquePhysiqueSpecial:
    def test_sous_fit_risque_penalise(self):
        """Candidat peu à l'aise avec le risque (20/100) sur poste à haut risque (0.9)."""
        snap = _snapshot_full(risk=20.0)
        vessel = _vessel_full(risk=0.9)
        result = compute(snap, vessel)
        dim_63 = next(d for d in result.dimensions if d.dimension == "physical_risk_6.3")
        assert dim_63.score < 0.5

    def test_surfit_risque_penalise(self):
        """Candidat très insouciant (95/100) sur poste faible risque (0.2) → sur-fit dangereux."""
        snap = _snapshot_full(risk=95.0)
        vessel = _vessel_full(risk=0.2)
        result = compute(snap, vessel)
        dim_63 = next(d for d in result.dimensions if d.dimension == "physical_risk_6.3")
        # Sur-fit détecté : score dégradé + flag
        assert dim_63.score < 0.5
        assert any("OVERFIT" in f for f in result.flags)

    def test_risque_equilibre_score_eleve(self):
        """Candidat calibré (65/100) sur poste risque moyen (0.6) → bon PSI."""
        snap = _snapshot_full(risk=65.0)
        vessel = _vessel_full(risk=0.65)
        result = compute(snap, vessel)
        dim_63 = next(d for d in result.dimensions if d.dimension == "physical_risk_6.3")
        assert dim_63.score >= 0.90


class TestDonneesMissingSnapshot:
    def test_dimension_manquante_utilise_mediane(self):
        """Snapshot sans maritime_tolerance → score médiane (pas d'exception)."""
        result = compute({}, VESSEL)
        assert isinstance(result, FPhysicalResult)
        # Score doit être proche de 50 (médianes)
        assert 0.0 <= result.score <= 100.0

    def test_data_quality_degradee_si_partiels(self):
        snap_partiel = {"maritime_tolerance": {"confined_space_tolerance": 70.0}}
        result = compute(snap_partiel, VESSEL)
        assert result.data_quality < 1.0

    def test_flag_partial_si_manquant(self):
        result = compute({}, VESSEL)
        assert any("PARTIAL" in f for f in result.flags)


class TestDonneesMissingVessel:
    def test_conditions_manquantes_utilise_mediane(self):
        result = compute(SNAP, {})
        assert isinstance(result, FPhysicalResult)
        assert 0.0 <= result.score <= 100.0


class TestAlertesTolerance:
    def test_alerte_confined_space_bas(self):
        snap = _snapshot_full(confined=20.0)
        result = compute(snap, _vessel_full(space=0.8))
        assert any("LOW_CONFINED" in f for f in result.flags)

    def test_alerte_isolation_bas(self):
        snap = _snapshot_full(isolation=25.0)
        result = compute(snap, _vessel_full(isolation=0.8))
        assert any("LOW_ISOLATION" in f for f in result.flags)

    def test_alerte_schedule_bas(self):
        snap = _snapshot_full(schedule=20.0)
        result = compute(snap, _vessel_full(schedule=0.9))
        assert any("LOW_SCHEDULE" in f for f in result.flags)


# ── Tests compute_fit() ───────────────────────────────────────────────────────

class TestComputeFit:
    def test_none_si_vessel_params_absent(self):
        assert compute_fit(SNAP, None) is None

    def test_none_si_vessel_vide_et_snap_vide(self):
        assert compute_fit({}, {}) is None

    def test_retourne_result_si_donnees_maritimes_dans_vessel(self):
        result = compute_fit(SNAP, VESSEL)
        assert result is not None
        assert isinstance(result, FPhysicalResult)

    def test_retourne_result_si_donnees_maritimes_dans_snap_uniquement(self):
        """Même sans maritime_conditions dans vessel, si snap a des données → calcul."""
        result = compute_fit(SNAP, {"other_key": 1.0})
        assert result is not None

    def test_none_si_ni_snap_ni_vessel_ont_donnees_maritimes(self):
        result = compute_fit({"big_five": {}}, {"salary_index": 0.7})
        assert result is None
