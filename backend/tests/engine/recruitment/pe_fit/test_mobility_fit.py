# tests/engine/recruitment/pe_fit/test_mobility_fit.py
"""
Tests unitaires pour engine.pe_fit.mobility_fit.f_mobility

Couverture :
    PSI par dimension (7.1–7.4)
    Score global ∈ [0, 100]
    Normalisation durée embarquement (breakpoints semaines)
    Inversion contract_permanence
    Données absentes → médiane
    compute_fit() → None si pas de données mobilité
    Alertes LOW_FLEXIBILITY
"""
import pytest
from app.engine.pe_fit.mobility_fit.f_mobility import (
    compute,
    compute_fit,
    FMobilityResult,
    _normalize_embarkation_weeks,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _snapshot_full(
    mobility: float = 80.0,
    embarkation: float = 75.0,
    uncertainty: float = 65.0,
    contract: float = 70.0,
) -> dict:
    return {
        "mobility_profile": {
            "mobility_flexibility":  mobility,
            "embarkation_tolerance": embarkation,
            "uncertainty_tolerance": uncertainty,
            "contract_flexibility":  contract,
        }
    }


def _vessel_full(
    mobility_level: float = 0.6,
    embarkation_weeks: float = 8.0,
    unpredictability: float = 0.5,
    contract_permanence: float = 0.2,
) -> dict:
    return {
        "mobility_requirements": {
            "mobility_level":            mobility_level,
            "embarkation_weeks":         embarkation_weeks,
            "schedule_unpredictability": unpredictability,
            "contract_permanence":       contract_permanence,
        }
    }


SNAP   = _snapshot_full()
VESSEL = _vessel_full()


# ── Tests _normalize_embarkation_weeks() ─────────────────────────────────────

class TestNormalizeEmbarkation:
    def test_court_moins_4_semaines(self):
        assert _normalize_embarkation_weeks(2.0) == 0.25

    def test_moyen_4_a_12_semaines(self):
        assert _normalize_embarkation_weeks(8.0) == 0.50

    def test_long_12_a_26_semaines(self):
        assert _normalize_embarkation_weeks(20.0) == 0.75

    def test_tres_long_26_plus(self):
        assert _normalize_embarkation_weeks(30.0) == 1.00

    def test_exactement_4_semaines(self):
        assert _normalize_embarkation_weeks(4.0) == 0.50

    def test_exactement_12_semaines(self):
        assert _normalize_embarkation_weeks(12.0) == 0.75

    def test_exactement_26_semaines(self):
        assert _normalize_embarkation_weeks(26.0) == 1.00

    def test_none_retourne_none(self):
        assert _normalize_embarkation_weeks(None) is None


# ── Tests compute() ───────────────────────────────────────────────────────────

class TestComputeBase:
    def test_retourne_f_mobility_result(self):
        result = compute(SNAP, VESSEL)
        assert isinstance(result, FMobilityResult)

    def test_score_dans_bornes(self):
        result = compute(SNAP, VESSEL)
        assert 0.0 <= result.score <= 100.0

    def test_4_dimensions_presentes(self):
        result = compute(SNAP, VESSEL)
        assert len(result.dimensions) == 4

    def test_data_quality_pleine_si_donnees_completes(self):
        result = compute(SNAP, VESSEL)
        assert result.data_quality == 1.0

    def test_flags_vide_si_candidat_flexible(self):
        result = compute(_snapshot_full(80, 80, 80, 80), VESSEL)
        assert result.flags == []


class TestPSIMobilite:
    def test_psi_parfait_7_1(self):
        """P = 60/100 = 0.6, E = 0.6 → PSI = 1.0."""
        snap = _snapshot_full(mobility=60.0)
        vessel = _vessel_full(mobility_level=0.6)
        result = compute(snap, vessel)
        dim_71 = next(d for d in result.dimensions if d.dimension == "mobility_situation_7.1")
        assert abs(dim_71.score - 1.0) < 0.01

    def test_sous_fit_mobilite(self):
        """Candidat peu mobile (20) sur poste très mobile (E=0.9)."""
        snap = _snapshot_full(mobility=20.0)
        vessel = _vessel_full(mobility_level=0.9)
        result = compute(snap, vessel)
        dim_71 = next(d for d in result.dimensions if d.dimension == "mobility_situation_7.1")
        assert dim_71.score < 0.5

    def test_psi_embarquement_court_et_candidat_flexible(self):
        """Contrat 2 semaines (E=0.25), candidat tolérant longues durées (P=80) → sous-fit."""
        snap = _snapshot_full(embarkation=80.0)
        vessel = _vessel_full(embarkation_weeks=2.0)
        result = compute(snap, vessel)
        dim_72 = next(d for d in result.dimensions if d.dimension == "embarkation_duration_7.2")
        # P_norm=0.80 vs E=0.25 → gap = 0.55 → score = 0.45
        assert dim_72.score < 0.6


class TestContractInversion:
    def test_poste_saisonnier_requiert_flexibilite(self):
        """
        contract_permanence = 0.0 (saisonnier) → E_contract = 1.0 (haute flexibilité requise).
        Candidat flexible (P=90/100=0.9) → PSI proche 1.
        """
        snap = _snapshot_full(contract=90.0)
        vessel = _vessel_full(contract_permanence=0.0)
        result = compute(snap, vessel)
        dim_74 = next(d for d in result.dimensions if d.dimension == "contract_flexibility_7.4")
        assert dim_74.score >= 0.85

    def test_poste_permanent_et_candidat_rigide(self):
        """
        contract_permanence = 1.0 (permanent) → E_contract = 0.0.
        Candidat peu flexible (P=20/100=0.2) → PSI ≈ 1.0 (ok pour poste permanent).
        """
        snap = _snapshot_full(contract=20.0)
        vessel = _vessel_full(contract_permanence=1.0)
        result = compute(snap, vessel)
        dim_74 = next(d for d in result.dimensions if d.dimension == "contract_flexibility_7.4")
        assert dim_74.score >= 0.80


class TestDonneesMissing:
    def test_snapshot_vide_ne_leve_pas_exception(self):
        result = compute({}, VESSEL)
        assert isinstance(result, FMobilityResult)

    def test_data_quality_degradee_si_partiels(self):
        snap_partiel = {"mobility_profile": {"mobility_flexibility": 70.0}}
        result = compute(snap_partiel, VESSEL)
        assert result.data_quality < 1.0

    def test_vessel_vide_ne_leve_pas_exception(self):
        result = compute(SNAP, {})
        assert isinstance(result, FMobilityResult)


class TestAlertesFlexibilite:
    def test_alerte_mobilite_basse_sur_poste_exigeant(self):
        snap = _snapshot_full(mobility=20.0)
        vessel = _vessel_full(mobility_level=0.8)
        result = compute(snap, vessel)
        assert any("LOW_MOBILITY" in f for f in result.flags)

    def test_alerte_embarquement_bas_sur_longue_mission(self):
        snap = _snapshot_full(embarkation=20.0)
        vessel = _vessel_full(embarkation_weeks=20.0)
        result = compute(snap, vessel)
        assert any("LOW_EMBARKATION" in f for f in result.flags)


# ── Tests compute_fit() ───────────────────────────────────────────────────────

class TestComputeFit:
    def test_none_si_vessel_params_absent(self):
        assert compute_fit(SNAP, None) is None

    def test_none_si_vessel_vide_et_snap_vide(self):
        assert compute_fit({}, {}) is None

    def test_retourne_result_si_donnees_mobilite_dans_vessel(self):
        result = compute_fit(SNAP, VESSEL)
        assert result is not None

    def test_retourne_result_si_donnees_mobilite_dans_snap_uniquement(self):
        result = compute_fit(SNAP, {"salary_index": 0.7})
        assert result is not None

    def test_none_si_ni_snap_ni_vessel_ont_donnees_mobilite(self):
        result = compute_fit({"big_five": {}}, {"salary_index": 0.7})
        assert result is None
