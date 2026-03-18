# tests/engine/recruitment/pe_fit/test_master.py
"""
Tests unitaires pour engine.recruitment.pe_fit.master

Couverture :
    compute() complet (toutes données) :
        - Retourne PEFitResult
        - global_score ∈ [0, 100]
        - Toutes les dimensions renseignées (po_fit, pt_fit, ps_fit non None)

    compute() minimal (snapshot uniquement) :
        - po_fit = None, pt_fit = None, ps_fit = None
        - global_score == pj_fit.score

    is_disqualified :
        - True si emotional_stability très bas (< seuil HARD veto = 15)
        - False si snapshot nominal

    to_matching_row() :
        - Retourne un dict avec les clés attendues

    to_impact_report() :
        - Retourne un dict avec les clés attendues

    Aliases sigmoid (compatibilité MLPSM) :
        - _sigmoid_transform(50.0) == 50.0
        - SIGMOID_CENTER == 50.0
        - SIGMOID_SCALE == 15.0
"""
import pytest

from app.engine.pe_fit.master import (
    compute,
    PEFitResult,
    _sigmoid_transform,
    SIGMOID_CENTER,
    SIGMOID_SCALE,
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
    """Snapshot psychométrique minimal valide pour les tests PE Fit."""
    return {
        "big_five": {
            "conscientiousness": conscientiousness,
            "agreeableness":     agreeableness,
            "emotional_stability": emotional_stability,
            "openness":          openness,
            "extraversion":      55.0,
            "neuroticism":       round(100 - emotional_stability, 1),
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


def _vessel_params() -> dict:
    """Paramètres JD-R du yacht pour le PO Fit."""
    return {
        "salary_index":         0.7,
        "rest_days_ratio":      0.6,
        "private_cabin_ratio":  0.5,
        "charter_intensity":    0.6,
        "management_pressure":  0.4,
    }


def _captain_vector() -> dict:
    """Vecteur de style capitaine pour le PS Fit."""
    return {
        "autonomy_given":    0.6,
        "feedback_style":    0.5,
        "structure_imposed": 0.4,
    }


def _crew() -> list:
    """Équipe de base pour le PT Fit."""
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
    """compute() avec toutes les données disponibles."""

    def test_retourne_pe_fit_result(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert isinstance(result, PEFitResult)

    def test_global_score_dans_bornes(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert 0.0 <= result.global_score <= 100.0

    def test_toutes_dimensions_renseignees(self):
        """Avec toutes les données, po_fit / pt_fit / ps_fit non None."""
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert result.pj_fit is not None
        assert result.po_fit is not None
        assert result.pt_fit is not None
        assert result.ps_fit is not None

    def test_sous_scores_dans_bornes(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert 0.0 <= result.pj_fit.score <= 100.0
        assert 0.0 <= result.po_fit.score <= 100.0
        assert 0.0 <= result.pt_fit.score <= 100.0
        assert 0.0 <= result.ps_fit.score <= 100.0

    def test_global_score_est_moyenne_des_4_dimensions(self):
        """global_score == moyenne de pj, po, pt, ps quand les 4 sont présents."""
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        expected = round(
            (result.pj_fit.score + result.po_fit.score
             + result.pt_fit.score + result.ps_fit.score) / 4,
            1,
        )
        assert abs(result.global_score - expected) < 0.05

    def test_data_quality_dans_bornes(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert 0.0 <= result.data_quality <= 1.0

    def test_confidence_coherent(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        if result.data_quality >= 0.85:
            assert result.confidence == "HIGH"
        elif result.data_quality >= 0.60:
            assert result.confidence == "MEDIUM"
        else:
            assert result.confidence == "LOW"

    def test_safety_level_est_string(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert isinstance(result.safety_level, str)
        assert result.safety_level in {"CLEAR", "ADVISORY", "HIGH_RISK", "DISQUALIFIED"}

    def test_all_flags_est_liste(self):
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        assert isinstance(result.all_flags, list)


# ── Tests compute() minimal ───────────────────────────────────────────────────

class TestComputeMinimal:
    """compute() avec snapshot uniquement (aucun contexte environnemental)."""

    def test_retourne_pe_fit_result(self):
        result = compute(SNAPSHOT)
        assert isinstance(result, PEFitResult)

    def test_po_fit_none_si_vessel_params_absent(self):
        result = compute(SNAPSHOT)
        assert result.po_fit is None

    def test_pt_fit_none_si_crew_absent(self):
        result = compute(SNAPSHOT)
        assert result.pt_fit is None

    def test_ps_fit_none_si_captain_absent(self):
        result = compute(SNAPSHOT)
        assert result.ps_fit is None

    def test_global_score_egal_pj_fit_score(self):
        """Quand seul PJ Fit est disponible, global_score == pj_fit.score."""
        result = compute(SNAPSHOT)
        assert abs(result.global_score - result.pj_fit.score) < 0.05

    def test_pj_fit_toujours_present(self):
        result = compute(SNAPSHOT)
        assert result.pj_fit is not None
        assert 0.0 <= result.pj_fit.score <= 100.0

    def test_snapshot_vide_ne_leve_pas_exception(self):
        """Snapshot candidat vide → résultat avec fallbacks, pas d'exception."""
        result = compute({})
        assert isinstance(result, PEFitResult)
        assert 0.0 <= result.global_score <= 100.0

    def test_flags_indique_dimensions_absentes(self):
        result = compute(SNAPSHOT)
        text = " ".join(result.all_flags)
        assert "PO Fit non calculé" in text
        assert "PT Fit non calculé" in text
        assert "PS Fit non calculé" in text


# ── Tests sécurité / disqualification ─────────────────────────────────────────

class TestSecurite:
    """Tests de la barrière de sécurité propagée depuis PJ Fit."""

    def test_is_disqualified_false_pour_snapshot_nominal(self):
        """Snapshot normal → is_disqualified = False."""
        result = compute(SNAPSHOT)
        assert result.is_disqualified is False

    def test_is_disqualified_true_si_emotional_stability_tres_bas(self):
        """
        Emotional stability < 15 → veto HARD → DISQUALIFIED.
        Le seuil HARD veto de la safety_barrier est ES < 15.
        """
        snap_fragile = _snap(emotional_stability=5.0, agreeableness=70.0)
        result = compute(snap_fragile)
        assert result.is_disqualified is True
        assert result.safety_level == "DISQUALIFIED"

    def test_safety_level_clear_pour_candidat_nominal(self):
        result = compute(SNAPSHOT)
        # Snapshot nominal sans veto → CLEAR ou ADVISORY (pas de HARD/SOFT)
        assert result.safety_level in {"CLEAR", "ADVISORY"}

    def test_disqualified_propagee_dans_matching_row(self):
        snap_fragile = _snap(emotional_stability=5.0)
        result = compute(snap_fragile)
        row = result.to_matching_row()
        assert row["is_disqualified"] is True
        assert row["safety_level"] == "DISQUALIFIED"

    def test_disqualified_propagee_dans_impact_report(self):
        snap_fragile = _snap(emotional_stability=5.0)
        result = compute(snap_fragile)
        report = result.to_impact_report()
        assert report["is_disqualified"] is True

    def test_agreeableness_tres_bas_trigge_veto(self):
        """Agreeableness < 15 → veto HARD → DISQUALIFIED."""
        snap_hostile = _snap(agreeableness=5.0, emotional_stability=70.0)
        result = compute(snap_hostile)
        assert result.is_disqualified is True


# ── Tests to_matching_row() ───────────────────────────────────────────────────

class TestToMatchingRow:
    def setup_method(self):
        self.result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        self.row = self.result.to_matching_row()

    def test_retourne_dict(self):
        assert isinstance(self.row, dict)

    def test_champs_obligatoires(self):
        expected_keys = {
            "pj_fit_score", "po_fit_score", "pt_fit_score", "ps_fit_score",
            "global_score", "safety_level", "is_disqualified",
            "confidence", "data_quality", "safety_flags",
        }
        assert expected_keys.issubset(self.row.keys())

    def test_global_score_dans_bornes(self):
        assert 0.0 <= self.row["global_score"] <= 100.0

    def test_sous_scores_non_none_quand_donnees_presentes(self):
        assert self.row["pj_fit_score"] is not None
        assert self.row["po_fit_score"] is not None
        assert self.row["pt_fit_score"] is not None
        assert self.row["ps_fit_score"] is not None

    def test_sous_scores_none_quand_minimal(self):
        result_min = compute(SNAPSHOT)
        row_min = result_min.to_matching_row()
        assert row_min["po_fit_score"] is None
        assert row_min["pt_fit_score"] is None
        assert row_min["ps_fit_score"] is None

    def test_safety_flags_est_liste(self):
        assert isinstance(self.row["safety_flags"], list)


# ── Tests to_impact_report() ──────────────────────────────────────────────────

class TestToImpactReport:
    def setup_method(self):
        self.result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            captain_vector=CAPTAIN,
            current_crew_snapshots=CREW,
        )
        self.report = self.result.to_impact_report()

    def test_retourne_dict(self):
        assert isinstance(self.report, dict)

    def test_champs_principaux(self):
        expected = {
            "global_score", "safety_level", "is_disqualified",
            "confidence", "data_quality", "pj_fit", "po_fit",
            "pt_fit", "ps_fit", "all_flags",
        }
        assert expected.issubset(self.report.keys())

    def test_pj_fit_detail(self):
        pj = self.report["pj_fit"]
        assert "score" in pj
        assert "p_ind_score" in pj
        assert "fit_label" in pj
        assert "safety" in pj
        assert "flags" in pj

    def test_po_fit_detail_non_none(self):
        po = self.report["po_fit"]
        assert po is not None
        assert "score" in po
        assert "jdr_ratio" in po
        assert "jdr_status" in po
        assert "resilience" in po

    def test_pt_fit_detail_non_none(self):
        pt = self.report["pt_fit"]
        assert pt is not None
        assert "score" in pt
        assert "min_agreeableness" in pt
        assert "mean_es" in pt
        assert "crew_size" in pt

    def test_ps_fit_detail_non_none(self):
        ps = self.report["ps_fit"]
        assert ps is not None
        assert "score" in ps
        assert "compatibility_label" in ps
        assert "normalized_distance" in ps
        assert "dimension_gaps" in ps

    def test_po_fit_none_quand_minimal(self):
        result_min = compute(SNAPSHOT)
        report_min = result_min.to_impact_report()
        assert report_min["po_fit"] is None

    def test_pt_fit_none_quand_minimal(self):
        result_min = compute(SNAPSHOT)
        report_min = result_min.to_impact_report()
        assert report_min["pt_fit"] is None

    def test_ps_fit_none_quand_minimal(self):
        result_min = compute(SNAPSHOT)
        report_min = result_min.to_impact_report()
        assert report_min["ps_fit"] is None

    def test_all_flags_est_liste(self):
        assert isinstance(self.report["all_flags"], list)


# ── Tests aliases sigmoid (compatibilité MLPSM) ───────────────────────────────

class TestAliasesSigmoid:
    """Vérifie que les aliases MLPSM sont correctement exposés."""

    def test_sigmoid_center(self):
        assert SIGMOID_CENTER == 50.0

    def test_sigmoid_scale(self):
        assert SIGMOID_SCALE == 15.0

    def test_sigmoid_centre_invariant(self):
        """sigmoid(50.0) doit retourner exactement 50.0."""
        assert _sigmoid_transform(SIGMOID_CENTER) == 50.0

    def test_sigmoid_dans_bornes(self):
        assert 0.0 < _sigmoid_transform(0.0) < 100.0
        assert 0.0 < _sigmoid_transform(100.0) < 100.0

    def test_sigmoid_monotone_croissant(self):
        scores = [_sigmoid_transform(x) for x in range(0, 101, 10)]
        for a, b in zip(scores, scores[1:]):
            assert a < b, f"Non monotone: {a} >= {b}"

    def test_sigmoid_valeur_superieure_a_50(self):
        assert _sigmoid_transform(65.0) > 50.0

    def test_sigmoid_valeur_inferieure_a_50(self):
        assert _sigmoid_transform(35.0) < 50.0


# ── Tests calcul global_score avec dimensions partielles ─────────────────────

class TestGlobalScorePartiel:
    """Vérifie la moyenne avec différentes combinaisons de dimensions."""

    def test_2_dimensions_pj_po(self):
        """Avec PJ + PO seulement → global = moyenne(pj, po)."""
        result = compute(SNAPSHOT, vessel_params=VESSEL)
        assert result.pt_fit is None
        assert result.ps_fit is None
        expected = round((result.pj_fit.score + result.po_fit.score) / 2, 1)
        assert abs(result.global_score - expected) < 0.05

    def test_2_dimensions_pj_ps(self):
        """Avec PJ + PS seulement → global = moyenne(pj, ps)."""
        result = compute(SNAPSHOT, captain_vector=CAPTAIN)
        assert result.po_fit is None
        assert result.pt_fit is None
        expected = round((result.pj_fit.score + result.ps_fit.score) / 2, 1)
        assert abs(result.global_score - expected) < 0.05

    def test_3_dimensions_pj_po_pt(self):
        """Avec PJ + PO + PT → global = moyenne(pj, po, pt)."""
        result = compute(
            SNAPSHOT,
            vessel_params=VESSEL,
            current_crew_snapshots=CREW,
        )
        assert result.ps_fit is None
        expected = round(
            (result.pj_fit.score + result.po_fit.score + result.pt_fit.score) / 3,
            1,
        )
        assert abs(result.global_score - expected) < 0.05

    def test_position_passee_au_pj_fit(self):
        """position transmis sans lever d'exception."""
        result = compute(SNAPSHOT, position="Captain")
        assert isinstance(result, PEFitResult)
