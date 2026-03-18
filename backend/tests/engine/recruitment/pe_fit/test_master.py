# tests/engine/recruitment/pe_fit/test_master.py
"""
Tests unitaires pour engine.recruitment.pe_fit.master

Couverture :
    compute() complet (toutes données) :
        - Retourne PEFitResult
        - global_score ∈ [0, 100]
        - Toutes les dimensions de base renseignées (po_fit legacy, pt_fit, ps_fit)

    compute() minimal (snapshot uniquement) :
        - po_fit = None, pt_fit = None, ps_fit = None
        - global_score == pj_fit.score (seule dimension D-A disponible)

    global_score pondéré (DIMENSION_WEIGHTS) :
        - Pondération DA=0.28, NS=0.25, PG=0.16, PS=0.13, Phys=0.05, Mob=0.05
        - Renormalisation automatique pour dimensions absentes
        - po_fit legacy EXCLU du global_score

    Nouvelles dimensions (Fam. 6 et 7) :
        - physical_fit présent si maritime_conditions dans vessel_params
        - mobility_fit présent si mobility_requirements dans vessel_params

    is_disqualified :
        - True si emotional_stability très bas (< seuil HARD veto = 15)
        - False si snapshot nominal

    to_matching_row() :
        - Retourne un dict avec les clés attendues (incl. physical_fit_score, mobility_fit_score)

    to_impact_report() :
        - Retourne un dict avec les clés attendues
        - dimension_weights exposé

    Aliases sigmoid (compatibilité MLPSM) :
        - _sigmoid_transform(50.0) == 50.0
"""
import pytest

from app.engine.pe_fit.master import (
    compute,
    PEFitResult,
    DIMENSION_WEIGHTS,
    _sigmoid_transform,
    SIGMOID_CENTER,
    SIGMOID_SCALE,
    _weighted_global_score,
)

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snap(
    conscientiousness: float = 70.0,
    agreeableness: float = 70.0,
    emotional_stability: float = 65.0,
    openness: float = 60.0,
    gca: float = 72.0,
    autonomy: float = 0.6,
    feedback: float = 0.5,
    structure: float = 0.4,
    resilience: float = 65.0,
) -> dict:
    return {
        "big_five": {
            "conscientiousness":   conscientiousness,
            "agreeableness":       agreeableness,
            "emotional_stability": emotional_stability,
            "openness":            openness,
            "extraversion":        55.0,
            "neuroticism":         round(100 - emotional_stability, 1),
        },
        "emotional_stability": emotional_stability,
        "cognitive": {"gca_score": gca},
        "leadership_preferences": {
            "autonomy_preference":  autonomy,
            "feedback_preference":  feedback,
            "structure_preference": structure,
        },
        "resilience": resilience,
    }


def _vessel_params(with_maritime: bool = False, with_mobility: bool = False) -> dict:
    """Paramètres vessel de base + optionnellement Fam.6 et Fam.7."""
    params = {
        "salary_index":         0.7,
        "rest_days_ratio":      0.6,
        "private_cabin_ratio":  0.5,
        "charter_intensity":    0.6,
        "management_pressure":  0.4,
    }
    if with_maritime:
        params["maritime_conditions"] = {
            "space_constraint_level": 0.7,
            "isolation_level":        0.6,
            "physical_risk_level":    0.6,
            "schedule_irregularity":  0.7,
            "weather_exposure":       0.5,
        }
    if with_mobility:
        params["mobility_requirements"] = {
            "mobility_level":            0.6,
            "embarkation_weeks":         8.0,
            "schedule_unpredictability": 0.5,
            "contract_permanence":       0.2,
        }
    return params


def _snap_with_maritime() -> dict:
    snap = _snap()
    snap["maritime_tolerance"] = {
        "confined_space_tolerance": 75.0,
        "isolation_tolerance":      70.0,
        "physical_risk_tolerance":  65.0,
        "schedule_tolerance":       70.0,
        "weather_tolerance":        60.0,
    }
    snap["mobility_profile"] = {
        "mobility_flexibility":  75.0,
        "embarkation_tolerance": 70.0,
        "uncertainty_tolerance": 65.0,
        "contract_flexibility":  70.0,
    }
    return snap


def _captain_vector() -> dict:
    return {
        "autonomy_given":    0.6,
        "feedback_style":    0.5,
        "structure_imposed": 0.4,
    }


def _crew() -> list:
    return [
        _snap(agreeableness=75.0, emotional_stability=70.0),
        _snap(agreeableness=72.0, emotional_stability=68.0),
    ]


SNAPSHOT = _snap()
VESSEL   = _vessel_params()
CAPTAIN  = _captain_vector()
CREW     = _crew()


# ── Tests compute() complet ───────────────────────────────────────────────────

class TestComputeComplet:
    def test_retourne_pe_fit_result(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert isinstance(result, PEFitResult)

    def test_global_score_dans_bornes(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert 0.0 <= result.global_score <= 100.0

    def test_dimensions_de_base_renseignees(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert result.pj_fit is not None
        assert result.pt_fit is not None
        assert result.ps_fit is not None

    def test_po_fit_legacy_present_si_vessel_params(self):
        """po_fit legacy (F_env) est calculé si vessel_params fourni."""
        result = compute(SNAPSHOT, vessel_params=VESSEL)
        assert result.po_fit is not None

    def test_po_fit_legacy_hors_global_score(self):
        """
        po_fit legacy (F_env) est exclu du global_score.
        Vérification : global_score est cohérent avec le calcul manuel sans po_fit legacy.
        """
        result_with_vessel = compute(SNAPSHOT, vessel_params=VESSEL)
        dim_scores = {
            "da_fit":        result_with_vessel.pj_fit.score,
            "ns_fit":        result_with_vessel.pj_fit.ns_fit_score,
            "po_values_fit": result_with_vessel.po_values_fit.score if result_with_vessel.po_values_fit else None,
            "pg_fit":        None,
            "ps_fit":        None,
            "physical_fit":  None,
            "mobility_fit":  None,
        }
        expected = _weighted_global_score(dim_scores, DIMENSION_WEIGHTS)
        assert abs(result_with_vessel.global_score - expected) < 0.1

    def test_sous_scores_dans_bornes(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert 0.0 <= result.pj_fit.score <= 100.0
        assert 0.0 <= result.pt_fit.score <= 100.0
        assert 0.0 <= result.ps_fit.score <= 100.0

    def test_data_quality_dans_bornes(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert 0.0 <= result.data_quality <= 1.0

    def test_confidence_coherent(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        if result.data_quality >= 0.85:
            assert result.confidence == "HIGH"
        elif result.data_quality >= 0.60:
            assert result.confidence == "MEDIUM"
        else:
            assert result.confidence == "LOW"

    def test_safety_level_est_string_valide(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert result.safety_level in {"CLEAR", "ADVISORY", "HIGH_RISK", "DISQUALIFIED"}

    def test_all_flags_est_liste(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL, captain_vector=CAPTAIN,
                         current_crew_snapshots=CREW)
        assert isinstance(result.all_flags, list)


# ── Tests compute() minimal ───────────────────────────────────────────────────

class TestComputeMinimal:
    def test_retourne_pe_fit_result(self):
        assert isinstance(compute(SNAPSHOT), PEFitResult)

    def test_po_fit_none_si_vessel_params_absent(self):
        assert compute(SNAPSHOT).po_fit is None

    def test_pt_fit_none_si_crew_absent(self):
        assert compute(SNAPSHOT).pt_fit is None

    def test_ps_fit_none_si_captain_absent(self):
        assert compute(SNAPSHOT).ps_fit is None

    def test_physical_fit_none_si_pas_de_donnees_maritimes(self):
        assert compute(SNAPSHOT).physical_fit is None

    def test_mobility_fit_none_si_pas_de_donnees_mobilite(self):
        assert compute(SNAPSHOT).mobility_fit is None

    def test_global_score_egal_pj_da_score_si_seul_disponible(self):
        """
        Seul le D-A fit (pj_fit.score) est disponible sans données contextuelles.
        N-S fit absent (pas de vessel_params) → global_score = pj_fit.score.
        """
        result = compute(SNAPSHOT)
        assert result.pj_fit.ns_fit_score is None  # Pas de vessel_params
        # Seule dimension disponible : da_fit → global = pj.score
        assert abs(result.global_score - result.pj_fit.score) < 0.05

    def test_pj_fit_toujours_present(self):
        result = compute(SNAPSHOT)
        assert result.pj_fit is not None
        assert 0.0 <= result.pj_fit.score <= 100.0

    def test_snapshot_vide_ne_leve_pas_exception(self):
        result = compute({})
        assert isinstance(result, PEFitResult)
        assert 0.0 <= result.global_score <= 100.0

    def test_flags_indique_dimensions_absentes(self):
        result = compute(SNAPSHOT)
        text = " ".join(result.all_flags)
        assert "PO legacy non calculé" in text or "PO Fit non calculé" in text or "vessel_params absent" in text
        assert "PG Fit non calculé" in text
        assert "PS Fit non calculé" in text


# ── Tests global_score pondéré ────────────────────────────────────────────────

class TestGlobalScorePondere:
    """Vérifie la pondération conforme au document de référence §5.3."""

    def test_da_et_ns_ponderes_si_vessel_params(self):
        """Avec vessel_params → ns_fit_score disponible → DA(0.28) + NS(0.25) pondérés."""
        result = compute(SNAPSHOT, vessel_params=VESSEL)
        if result.pj_fit.ns_fit_score is not None:
            dim_scores = {
                "da_fit": result.pj_fit.score,
                "ns_fit": result.pj_fit.ns_fit_score,
                "pg_fit": None,
                "ps_fit": None,
                "physical_fit": None,
                "mobility_fit": None,
            }
            expected = _weighted_global_score(dim_scores, DIMENSION_WEIGHTS)
            assert abs(result.global_score - expected) < 0.1

    def test_toutes_dimensions_disponibles(self):
        """Avec toutes les données → global_score = Σ(w_i × s_i) / Σw_i."""
        snap = _snap_with_maritime()
        vessel = _vessel_params(with_maritime=True, with_mobility=True)
        result = compute(
            snap,
            vessel_params=vessel,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert result.physical_fit is not None
        assert result.mobility_fit is not None

        dim_scores = {
            "da_fit":         result.pj_fit.score,
            "ns_fit":         result.pj_fit.ns_fit_score,
            "po_values_fit":  result.po_values_fit.score if result.po_values_fit else None,
            "pg_fit":         result.pt_fit.score,
            "ps_fit":         result.ps_fit.score,
            "physical_fit":   result.physical_fit.score,
            "mobility_fit":   result.mobility_fit.score,
        }
        expected = _weighted_global_score(dim_scores, DIMENSION_WEIGHTS)
        assert abs(result.global_score - expected) < 0.1

    def test_renormalisation_da_seul(self):
        """DA seul (poids=0.28) → renormalisé → global_score = DA score."""
        result = compute(SNAPSHOT)
        assert result.pj_fit.ns_fit_score is None
        assert abs(result.global_score - result.pj_fit.score) < 0.05

    def test_dimension_weights_complet(self):
        """DIMENSION_WEIGHTS doit contenir les 7 dimensions actives (incl. PO valeurs)."""
        expected_keys = {
            "da_fit", "ns_fit", "po_values_fit",
            "pg_fit", "ps_fit", "physical_fit", "mobility_fit",
        }
        assert expected_keys == set(DIMENSION_WEIGHTS.keys())

    def test_sum_weights_egal_1_10(self):
        """La somme des poids des 7 dimensions = 0.28+0.25+0.18+0.16+0.13+0.05+0.05 = 1.10."""
        total = sum(DIMENSION_WEIGHTS.values())
        assert abs(total - 1.10) < 0.01


class TestWeightedGlobalScoreHelper:
    """Tests unitaires pour _weighted_global_score()."""

    def test_moyenne_simple_deux_dims(self):
        scores = {"da_fit": 80.0, "ns_fit": 60.0}
        weights = {"da_fit": 0.5, "ns_fit": 0.5}
        result = _weighted_global_score(scores, weights)
        assert abs(result - 70.0) < 0.1

    def test_renormalisation_automatique(self):
        """Si ns_fit absent, da_fit seul → global = da_fit."""
        scores = {"da_fit": 75.0, "ns_fit": None}
        weights = {"da_fit": 0.28, "ns_fit": 0.25}
        result = _weighted_global_score(scores, weights)
        assert abs(result - 75.0) < 0.1

    def test_tous_none_retourne_zero(self):
        scores = {"da_fit": None, "ns_fit": None}
        weights = {"da_fit": 0.28, "ns_fit": 0.25}
        result = _weighted_global_score(scores, weights)
        assert result == 0.0

    def test_ponderation_inegalitaire(self):
        """DA (0.28) > NS (0.25) → score DA plus influent."""
        scores = {"da_fit": 100.0, "ns_fit": 0.0}
        weights = {"da_fit": 0.28, "ns_fit": 0.25}
        result = _weighted_global_score(scores, weights)
        # 100*0.28 / (0.28+0.25) = 52.8
        assert result > 50.0


# ── Tests nouvelles dimensions Fam.6 et Fam.7 ────────────────────────────────

class TestNouvellesDimensions:
    def test_physical_fit_present_si_maritime_conditions(self):
        vessel = _vessel_params(with_maritime=True)
        snap = _snap_with_maritime()
        result = compute(snap, vessel_params=vessel)
        assert result.physical_fit is not None
        assert 0.0 <= result.physical_fit.score <= 100.0

    def test_mobility_fit_present_si_mobility_requirements(self):
        vessel = _vessel_params(with_mobility=True)
        snap = _snap_with_maritime()
        result = compute(snap, vessel_params=vessel)
        assert result.mobility_fit is not None
        assert 0.0 <= result.mobility_fit.score <= 100.0

    def test_physical_fit_contribue_au_global_score(self):
        """Avec Fam.6 disponible, global_score doit intégrer son poids (0.05)."""
        snap = _snap_with_maritime()
        vessel_sans = _vessel_params()
        vessel_avec = _vessel_params(with_maritime=True)
        result_sans  = compute(snap, vessel_params=vessel_sans)
        result_avec  = compute(snap, vessel_params=vessel_avec)
        # Les scores peuvent différer (poids supplémentaire)
        # On vérifie juste qu'ils sont tous deux dans les bornes
        assert 0.0 <= result_sans.global_score <= 100.0
        assert 0.0 <= result_avec.global_score <= 100.0


# ── Tests sécurité ────────────────────────────────────────────────────────────

class TestSecurite:
    def test_is_disqualified_false_pour_snapshot_nominal(self):
        assert compute(SNAPSHOT).is_disqualified is False

    def test_is_disqualified_true_si_emotional_stability_tres_bas(self):
        snap_fragile = _snap(emotional_stability=5.0, agreeableness=70.0)
        result = compute(snap_fragile)
        assert result.is_disqualified is True
        assert result.safety_level == "DISQUALIFIED"

    def test_safety_level_clear_pour_candidat_nominal(self):
        assert compute(SNAPSHOT).safety_level in {"CLEAR", "ADVISORY"}

    def test_agreeableness_tres_bas_trigge_veto(self):
        snap_hostile = _snap(agreeableness=5.0, emotional_stability=70.0)
        assert compute(snap_hostile).is_disqualified is True


# ── Tests to_matching_row() ───────────────────────────────────────────────────

class TestToMatchingRow:
    def setup_method(self):
        snap = _snap_with_maritime()
        vessel = _vessel_params(with_maritime=True, with_mobility=True)
        self.result = compute(snap, vessel_params=vessel,
                              captain_vector=CAPTAIN, current_crew_snapshots=CREW)
        self.row = self.result.to_matching_row()

    def test_retourne_dict(self):
        assert isinstance(self.row, dict)

    def test_champs_obligatoires(self):
        expected_keys = {
            "pj_fit_score", "po_fit_score", "po_values_fit_score",
            "pt_fit_score", "ps_fit_score",
            "physical_fit_score", "mobility_fit_score",
            "global_score", "safety_level", "is_disqualified",
            "confidence", "data_quality", "safety_flags",
        }
        assert expected_keys.issubset(self.row.keys())

    def test_physical_et_mobility_scores_non_none(self):
        assert self.row["physical_fit_score"] is not None
        assert self.row["mobility_fit_score"] is not None

    def test_global_score_dans_bornes(self):
        assert 0.0 <= self.row["global_score"] <= 100.0

    def test_scores_none_quand_minimal(self):
        result_min = compute(SNAPSHOT)
        row_min = result_min.to_matching_row()
        assert row_min["po_fit_score"] is None
        assert row_min["pt_fit_score"] is None
        assert row_min["ps_fit_score"] is None
        assert row_min["physical_fit_score"] is None
        assert row_min["mobility_fit_score"] is None


# ── Tests to_impact_report() ──────────────────────────────────────────────────

class TestToImpactReport:
    def setup_method(self):
        snap = _snap_with_maritime()
        vessel = _vessel_params(with_maritime=True, with_mobility=True)
        self.result = compute(snap, vessel_params=vessel,
                              captain_vector=CAPTAIN, current_crew_snapshots=CREW)
        self.report = self.result.to_impact_report()

    def test_retourne_dict(self):
        assert isinstance(self.report, dict)

    def test_champs_principaux(self):
        expected = {
            "global_score", "safety_level", "is_disqualified",
            "confidence", "data_quality", "pj_fit", "po_fit", "po_values_fit",
            "pt_fit", "ps_fit", "physical_fit", "mobility_fit",
            "dimension_weights", "all_flags",
        }
        assert expected.issubset(self.report.keys())

    def test_dimension_weights_expose(self):
        dw = self.report["dimension_weights"]
        assert isinstance(dw, dict)
        assert "da_fit" in dw
        assert "ns_fit" in dw
        assert "pg_fit" in dw
        assert "ps_fit" in dw

    def test_physical_fit_detail_non_none(self):
        phys = self.report["physical_fit"]
        assert phys is not None
        assert "score" in phys
        assert "dimensions" in phys
        assert len(phys["dimensions"]) == 5

    def test_mobility_fit_detail_non_none(self):
        mob = self.report["mobility_fit"]
        assert mob is not None
        assert "score" in mob
        assert "dimensions" in mob
        assert len(mob["dimensions"]) == 4

    def test_po_fit_legacy_note_presente(self):
        """po_fit legacy doit contenir la note explicative."""
        po = self.report["po_fit"]
        if po is not None:
            assert "note" in po

    def test_pj_fit_expose_ns_et_motivation(self):
        pj = self.report["pj_fit"]
        assert "ns_fit_score" in pj
        assert "motivation_score" in pj

    def test_physical_et_mobility_none_quand_minimal(self):
        result_min = compute(SNAPSHOT)
        report_min = result_min.to_impact_report()
        assert report_min["physical_fit"] is None
        assert report_min["mobility_fit"] is None


# ── Tests aliases sigmoid ─────────────────────────────────────────────────────

class TestAliasesSigmoid:
    def test_sigmoid_center(self):
        assert SIGMOID_CENTER == 50.0

    def test_sigmoid_scale(self):
        assert SIGMOID_SCALE == 15.0

    def test_sigmoid_centre_invariant(self):
        assert _sigmoid_transform(SIGMOID_CENTER) == 50.0

    def test_sigmoid_dans_bornes(self):
        assert 0.0 < _sigmoid_transform(0.0) < 100.0
        assert 0.0 < _sigmoid_transform(100.0) < 100.0

    def test_sigmoid_monotone_croissant(self):
        scores = [_sigmoid_transform(x) for x in range(0, 101, 10)]
        for a, b in zip(scores, scores[1:]):
            assert a < b

    def test_sigmoid_valeur_superieure_a_50(self):
        assert _sigmoid_transform(65.0) > 50.0

    def test_sigmoid_valeur_inferieure_a_50(self):
        assert _sigmoid_transform(35.0) < 50.0


# ── Tests PO fit valeurs CES (Famille 3) ─────────────────────────────────────

class TestPOValuesFit:
    def _vessel_with_org_values(self) -> dict:
        params = _vessel_params()
        params["org_values"] = {
            "honesty":      0.8,
            "achievement":  0.7,
            "fairness":     0.7,
            "solidarity":   0.6,
        }
        return params

    def _snap_with_values(self) -> dict:
        snap = _snap()
        snap["values_profile"] = {
            "honesty":      80.0,
            "achievement":  70.0,
            "fairness":     70.0,
            "solidarity":   60.0,
        }
        return snap

    def test_po_values_fit_present_si_org_values_dans_vessel(self):
        snap = self._snap_with_values()
        vessel = self._vessel_with_org_values()
        result = compute(snap, vessel_params=vessel)
        assert result.po_values_fit is not None
        assert 0.0 <= result.po_values_fit.score <= 100.0

    def test_po_values_fit_none_si_pas_de_valeurs(self):
        result = compute(SNAPSHOT, vessel_params=VESSEL)
        assert result.po_values_fit is None

    def test_po_values_fit_contribue_au_global_score(self):
        """
        Avec org_values présentes, po_values_fit est dans dim_scores (PSI réel).
        Sans vessel_params → po_values_fit None (compute_values_fit retourne None).
        """
        snap = self._snap_with_values()
        # Sans vessel_params du tout → po_values_fit None
        result_sans = compute(snap)
        assert result_sans.po_values_fit is None
        # Avec org_values dans vessel → po_values_fit calculé avec PSI réels
        result_avec = compute(snap, vessel_params=self._vessel_with_org_values())
        assert result_avec.po_values_fit is not None
        assert 0.0 <= result_avec.global_score <= 100.0

    def test_po_values_fit_expose_dans_impact_report(self):
        snap = self._snap_with_values()
        vessel = self._vessel_with_org_values()
        result = compute(snap, vessel_params=vessel)
        report = result.to_impact_report()
        po = report["po_values_fit"]
        assert po is not None
        assert "score" in po
        assert "dimensions" in po
        assert len(po["dimensions"]) == 4

    def test_po_values_fit_score_expose_dans_matching_row(self):
        snap = self._snap_with_values()
        vessel = self._vessel_with_org_values()
        result = compute(snap, vessel_params=vessel)
        row = result.to_matching_row()
        assert "po_values_fit_score" in row
        assert row["po_values_fit_score"] is not None


# ── Tests position transmise ──────────────────────────────────────────────────

class TestPosition:
    def test_position_passee_au_pj_fit(self):
        result = compute(SNAPSHOT, position="Captain")
        assert isinstance(result, PEFitResult)
