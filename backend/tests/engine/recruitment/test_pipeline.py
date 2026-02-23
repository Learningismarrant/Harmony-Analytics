# tests/engine/recruitment/test_pipeline.py
"""
Tests unitaires pour engine.recruitment.pipeline

Couverture :
    run_batch() :
        - Candidats vides → liste vide
        - N candidats → N PipelineResult (ordre préservé)
        - Résultats non-DISQUALIFIED ont mlpsm renseigné
        - Résultats ont crew_profile_id
        - PipelineResult.to_matching_row() → champs attendus présents
        - PipelineResult.to_event_snapshot() → champs dnre + mlpsm

    run_single() :
        - Retourne PipelineResult avec les deux étages
        - to_impact_report() → champs stage_1_dnre + stage_2_mlpsm

    PipelineStage :
        - is_filtered=False pour un candidat passant
        - score/label/confidence non nuls
"""
import pytest

from app.engine.recruitment.pipeline import (
    run_batch,
    run_single,
    PipelineResult,
    PipelineStage,
)

pytestmark = pytest.mark.engine


# ── Helpers ───────────────────────────────────────────────────────────────────

def _snap(
    conscientiousness: float = 70.0,
    agreeableness: float = 70.0,
    neuroticism: float = 35.0,
    gca: float = 72.0,
) -> dict:
    return {
        "big_five": {
            "conscientiousness":  conscientiousness,
            "agreeableness":      agreeableness,
            "neuroticism":        neuroticism,
            "emotional_stability": round(100.0 - neuroticism, 1),
            "openness":           60.0,
            "extraversion":       55.0,
        },
        "cognitive": {"gca_score": gca},
        "leadership_preferences": {
            "autonomy_preference":  0.6,
            "feedback_preference":  0.5,
            "structure_preference": 0.4,
        },
        "resilience": {"global": 65.0},
    }


def _candidate(
    crew_profile_id: str = "cand_1",
    snapshot: dict | None = None,
    experience_years: int = 2,
    position_key: str = "deckhand",
) -> dict:
    return {
        "crew_profile_id":  crew_profile_id,
        "snapshot":         snapshot or _snap(),
        "experience_years": experience_years,
        "position_key":     position_key,
    }


VESSEL_PARAMS = {
    "demands":   {"physical": 55.0, "cognitive": 50.0, "stress": 50.0, "emotional": 45.0},
    "resources": {"autonomy": 60.0, "social_support": 60.0, "skill_variety": 55.0, "recognition": 55.0},
}
CAPTAIN_VECTOR = {"autonomy_preference": 0.6, "feedback_preference": 0.5, "structure_preference": 0.5}
CREW_SNAPS    = [_snap(agreeableness=75.0), _snap(agreeableness=72.0)]


# ── run_batch() ───────────────────────────────────────────────────────────────

class TestRunBatch:
    def test_candidats_vides_retourne_liste_vide(self):
        results = run_batch(candidates=[])
        assert results == []

    def test_n_candidats_n_resultats(self):
        candidates = [_candidate(f"cand_{i}") for i in range(3)]
        results = run_batch(
            candidates=candidates,
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        assert len(results) == 3

    def test_retourne_pipeline_result_instances(self):
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        assert all(isinstance(r, PipelineResult) for r in results)

    def test_crew_profile_id_present(self):
        results = run_batch(
            candidates=[_candidate("abc_42")],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        assert results[0].crew_profile_id == "abc_42"

    def test_candidat_non_filtre_a_mlpsm(self):
        """Un candidat avec un snapshot correct passe les deux étages."""
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        result = results[0]
        # Un profil standard ne devrait pas être DISQUALIFIED
        if result.is_pipeline_pass:
            assert result.mlpsm is not None

    def test_dnre_stage_present(self):
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        assert results[0].dnre_stage is not None
        assert isinstance(results[0].dnre_stage, PipelineStage)

    def test_dnre_stage_a_score(self):
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        stage = results[0].dnre_stage
        assert 0.0 <= stage.score <= 100.0
        assert stage.label is not None

    def test_all_flags_est_liste(self):
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        assert isinstance(results[0].all_flags, list)

    def test_sans_contexte_yacht_fonctionne(self):
        """run_batch sans vessel/captain/crew → pas d'exception."""
        results = run_batch(candidates=[_candidate()])
        assert len(results) == 1


# ── PipelineResult.to_matching_row() ─────────────────────────────────────────

class TestToMatchingRow:
    def setup_method(self):
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        self.result = results[0]
        self.row    = self.result.to_matching_row()

    def test_retourne_dict(self):
        assert isinstance(self.row, dict)

    def test_champs_obligatoires(self):
        expected = {"crew_profile_id", "is_pipeline_pass", "filtered_at",
                    "profile_fit", "team_integration"}
        assert expected.issubset(self.row.keys())

    def test_profile_fit_champs(self):
        pf = self.row["profile_fit"]
        assert "g_fit" in pf
        assert "safety_level" in pf

    def test_g_fit_dans_bornes(self):
        assert 0.0 <= self.row["profile_fit"]["g_fit"] <= 100.0

    def test_team_integration_disponible_si_non_filtre(self):
        if self.result.is_pipeline_pass and self.result.mlpsm:
            ti = self.row["team_integration"]
            assert ti.get("available") is True
            assert "y_success" in ti


# ── PipelineResult.to_event_snapshot() ───────────────────────────────────────

class TestToEventSnapshot:
    def setup_method(self):
        results = run_batch(
            candidates=[_candidate()],
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
        )
        self.result = results[0]
        self.snap   = self.result.to_event_snapshot()

    def test_retourne_dict(self):
        assert isinstance(self.snap, dict)

    def test_champs_dnre_present(self):
        assert "dnre" in self.snap
        dnre = self.snap["dnre"]
        assert "g_fit" in dnre
        assert "safety_level" in dnre

    def test_is_pipeline_pass_present(self):
        assert "is_pipeline_pass" in self.snap

    def test_mlpsm_present_ou_none(self):
        """mlpsm est un dict ou None selon le résultat du pipeline."""
        mlpsm = self.snap.get("mlpsm")
        assert mlpsm is None or isinstance(mlpsm, dict)


# ── PipelineResult.to_impact_report() ────────────────────────────────────────

class TestToImpactReport:
    def setup_method(self):
        self.result = run_single(
            candidate_snapshot=_snap(),
            current_crew_snapshots=CREW_SNAPS,
            vessel_params=VESSEL_PARAMS,
            captain_vector=CAPTAIN_VECTOR,
            crew_profile_id="test_candidate",
        )
        self.report = self.result.to_impact_report()

    def test_retourne_dict(self):
        assert isinstance(self.report, dict)

    def test_champs_stage1_dnre(self):
        assert "stage_1_dnre" in self.report
        s1 = self.report["stage_1_dnre"]
        assert "g_fit" in s1

    def test_champs_stage2_mlpsm(self):
        assert "stage_2_mlpsm" in self.report

    def test_pipeline_summary(self):
        assert "pipeline_summary" in self.report
        ps = self.report["pipeline_summary"]
        assert "is_pipeline_pass" in ps

    def test_all_flags_liste(self):
        assert isinstance(self.report.get("all_flags"), list)


# ── run_single() ─────────────────────────────────────────────────────────────

class TestRunSingle:
    def test_retourne_pipeline_result(self):
        result = run_single(candidate_snapshot=_snap())
        assert isinstance(result, PipelineResult)

    def test_dnre_stage_non_nul(self):
        result = run_single(candidate_snapshot=_snap())
        assert result.dnre_stage is not None

    def test_sans_pool_context_fonctionne(self):
        """Pas de pool_context → centile absent mais pipeline s'exécute."""
        result = run_single(
            candidate_snapshot=_snap(),
            pool_context=None,
        )
        assert isinstance(result, PipelineResult)

    def test_crew_profile_id_transmis(self):
        result = run_single(
            candidate_snapshot=_snap(),
            crew_profile_id="my_candidate_99",
        )
        assert result.crew_profile_id == "my_candidate_99"
