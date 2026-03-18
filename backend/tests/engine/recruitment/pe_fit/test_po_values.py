# tests/engine/recruitment/pe_fit/test_po_values.py
"""
Tests unitaires pour engine.pe_fit.po_fit.f_values

Couverture :
    PSI par dimension (3.1a–3.1d)
    Score global ∈ [0, 100]
    Équipondération (w=0.25 chacun)
    Données absentes → médiane (default_score=0.5)
    compute_values_fit() → None si pas de données valeurs
    Alertes VALUES_MISALIGNMENT
    data_quality dégradée si données partielles
"""
import pytest
from app.engine.pe_fit.po_fit.f_values import (
    compute,
    compute_values_fit,
    POValuesResult,
    POValuesDimScore,
    _psi_dim,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def _snapshot_full(
    honesty: float = 80.0,
    achievement: float = 75.0,
    fairness: float = 70.0,
    solidarity: float = 65.0,
) -> dict:
    return {
        "values_profile": {
            "honesty":      honesty,
            "achievement":  achievement,
            "fairness":     fairness,
            "solidarity":   solidarity,
        }
    }


def _vessel_full(
    honesty: float = 0.8,
    achievement: float = 0.7,
    fairness: float = 0.7,
    solidarity: float = 0.6,
) -> dict:
    return {
        "org_values": {
            "honesty":      honesty,
            "achievement":  achievement,
            "fairness":     fairness,
            "solidarity":   solidarity,
        }
    }


SNAP   = _snapshot_full()
VESSEL = _vessel_full()


# ── Tests _psi_dim() ──────────────────────────────────────────────────────────

class TestPsiDim:
    def test_alignement_parfait(self):
        """P = 80/100 = 0.8, E = 0.8 → PSI = 1.0."""
        assert _psi_dim(80.0, 0.8) == 1.0

    def test_desalignement_total(self):
        """P = 0/100 = 0.0, E = 1.0 → PSI = 0.0."""
        assert _psi_dim(0.0, 1.0) == 0.0

    def test_ecart_partiel(self):
        """P = 60/100 = 0.6, E = 0.2 → PSI = 1 − |0.6 − 0.2| = 0.6."""
        assert abs(_psi_dim(60.0, 0.2) - 0.6) < 0.001

    def test_p_none_retourne_default(self):
        assert _psi_dim(None, 0.5) == 0.5

    def test_e_none_retourne_default(self):
        assert _psi_dim(70.0, None) == 0.5

    def test_les_deux_none_retourne_default(self):
        assert _psi_dim(None, None) == 0.5

    def test_resultat_borne_entre_0_et_1(self):
        """Vérification du clamping — ne peut pas dépasser 1."""
        score = _psi_dim(100.0, 1.0)
        assert 0.0 <= score <= 1.0


# ── Tests compute() ───────────────────────────────────────────────────────────

class TestComputeBase:
    def test_retourne_po_values_result(self):
        result = compute(SNAP, VESSEL)
        assert isinstance(result, POValuesResult)

    def test_score_dans_bornes(self):
        result = compute(SNAP, VESSEL)
        assert 0.0 <= result.score <= 100.0

    def test_4_dimensions_presentes(self):
        result = compute(SNAP, VESSEL)
        assert len(result.dimensions) == 4

    def test_data_quality_pleine_si_completes(self):
        result = compute(SNAP, VESSEL)
        assert result.data_quality == 1.0

    def test_flags_vide_si_aligne(self):
        """Candidat très aligné → pas de flag VALUES_MISALIGNMENT."""
        snap = _snapshot_full(80, 80, 80, 80)
        vessel = _vessel_full(0.8, 0.8, 0.8, 0.8)
        result = compute(snap, vessel)
        assert result.flags == []


class TestPsiParDimension:
    def test_psi_parfait_honesty(self):
        """P=80 → P_norm=0.8, E=0.8 → PSI=1.0."""
        snap = _snapshot_full(honesty=80.0)
        vessel = _vessel_full(honesty=0.8)
        result = compute(snap, vessel)
        dim = next(d for d in result.dimensions if d.dimension == "honesty_3.1a")
        assert abs(dim.score - 1.0) < 0.01

    def test_psi_parfait_achievement(self):
        snap = _snapshot_full(achievement=50.0)
        vessel = _vessel_full(achievement=0.5)
        result = compute(snap, vessel)
        dim = next(d for d in result.dimensions if d.dimension == "achievement_3.1b")
        assert abs(dim.score - 1.0) < 0.01

    def test_psi_faible_fairness(self):
        """Candidat faible (P=10) sur org exigeante (E=0.9)."""
        snap = _snapshot_full(fairness=10.0)
        vessel = _vessel_full(fairness=0.9)
        result = compute(snap, vessel)
        dim = next(d for d in result.dimensions if d.dimension == "fairness_3.1c")
        assert dim.score < 0.3

    def test_psi_solidarity_median(self):
        """P=50 → P_norm=0.5, E=0.5 → PSI=1.0."""
        snap = _snapshot_full(solidarity=50.0)
        vessel = _vessel_full(solidarity=0.5)
        result = compute(snap, vessel)
        dim = next(d for d in result.dimensions if d.dimension == "solidarity_3.1d")
        assert abs(dim.score - 1.0) < 0.01


class TestEquiponderee:
    def test_poids_sont_0_25_chacun(self):
        result = compute(SNAP, VESSEL)
        for dim in result.dimensions:
            assert abs(dim.weight - 0.25) < 0.001

    def test_score_global_est_moyenne_dimensions(self):
        """Score global = moyenne des 4 PSI × 100."""
        snap = _snapshot_full(80, 80, 80, 80)
        vessel = _vessel_full(0.8, 0.8, 0.8, 0.8)
        result = compute(snap, vessel)
        # Tous PSI = 1.0 → score = 100.0
        assert abs(result.score - 100.0) < 0.5


# ── Tests données absentes ────────────────────────────────────────────────────

class TestDonneesMissing:
    def test_snapshot_vide_ne_leve_pas_exception(self):
        result = compute({}, VESSEL)
        assert isinstance(result, POValuesResult)

    def test_vessel_vide_ne_leve_pas_exception(self):
        result = compute(SNAP, {})
        assert isinstance(result, POValuesResult)

    def test_data_quality_degradee_si_candidat_partiel(self):
        snap_partiel = {"values_profile": {"honesty": 80.0}}
        result = compute(snap_partiel, VESSEL)
        assert result.data_quality < 1.0
        assert any("VALUES_PROFILE_PARTIAL" in f for f in result.flags)

    def test_data_quality_degradee_si_org_partiel(self):
        vessel_partiel = {"org_values": {"honesty": 0.8}}
        result = compute(SNAP, vessel_partiel)
        assert result.data_quality < 1.0
        assert any("ORG_VALUES_PARTIAL" in f for f in result.flags)

    def test_score_par_defaut_si_deux_absentes(self):
        """Sans données → PSI = 0.5 (médiane) → score ~ 50."""
        result = compute({}, {})
        assert abs(result.score - 50.0) < 1.0


# ── Tests alertes désalignement ───────────────────────────────────────────────

class TestAlertesDesalignement:
    def test_alerte_honesty_misalignment(self):
        """P=10, E=0.9 → PSI < 0.4 → flag VALUES_MISALIGNMENT_HONESTY."""
        snap = _snapshot_full(honesty=10.0)
        vessel = _vessel_full(honesty=0.9)
        result = compute(snap, vessel)
        assert any("VALUES_MISALIGNMENT_HONESTY" in f for f in result.flags)

    def test_alerte_achievement_misalignment(self):
        snap = _snapshot_full(achievement=5.0)
        vessel = _vessel_full(achievement=0.95)
        result = compute(snap, vessel)
        assert any("VALUES_MISALIGNMENT_ACHIEVEMENT" in f for f in result.flags)

    def test_pas_alerte_si_psi_au_dessus_seuil(self):
        """PSI ≥ 0.40 → pas de flag."""
        snap = _snapshot_full(honesty=60.0)
        vessel = _vessel_full(honesty=0.6)
        result = compute(snap, vessel)
        assert not any("VALUES_MISALIGNMENT_HONESTY" in f for f in result.flags)


# ── Tests compute_values_fit() ────────────────────────────────────────────────

class TestComputeValuesFit:
    def test_none_si_vessel_params_absent(self):
        assert compute_values_fit(SNAP, None) is None

    def test_none_si_vessel_vide_et_snap_sans_values(self):
        assert compute_values_fit({"big_five": {}}, {}) is None

    def test_none_si_ni_snap_ni_vessel_ont_values(self):
        assert compute_values_fit(
            {"big_five": {}},
            {"salary_index": 0.7}
        ) is None

    def test_retourne_result_si_org_values_presents(self):
        result = compute_values_fit(SNAP, VESSEL)
        assert result is not None
        assert isinstance(result, POValuesResult)

    def test_retourne_result_si_values_profile_seulement(self):
        """org_values absentes, mais values_profile présent → on calcule quand même."""
        result = compute_values_fit(SNAP, {"salary_index": 0.7})
        assert result is not None

    def test_retourne_result_si_org_values_seulement(self):
        """values_profile absent, mais org_values présentes → on calcule."""
        result = compute_values_fit({"big_five": {}}, VESSEL)
        assert result is not None
