# tests/engine/recruitment/pe_fit/test_pt_fit.py
"""
Tests unitaires pour engine.recruitment.pe_fit.pt_fit.f_team

Couverture :
    compute_fit() avec équipe de 2+ membres     → FTeamResult, score [0, 100]
    compute_fit() sans équipe (None)             → None
    compute_fit() équipe vide []                 → None
    compute() existant (2-3 snapshots)           → score [0, 100] rétrocompatibilité
"""
import pytest

from app.engine.pe_fit.pt_fit.f_team import (
    compute,
    compute_fit,
    FTeamResult,
)

pytestmark = pytest.mark.engine


# ── Fixtures ──────────────────────────────────────────────────────────────────

def snap(agreeableness=75.0, conscientiousness=70.0, neuroticism=30.0):
    es = round(100.0 - neuroticism, 1)
    return {
        "big_five": {
            "agreeableness": agreeableness,
            "conscientiousness": conscientiousness,
            "neuroticism": neuroticism,
            "emotional_stability": es,
        }
    }


def snap_empty():
    return {}


CREW_2 = [
    snap(agreeableness=75.0, conscientiousness=70.0, neuroticism=30.0),
    snap(agreeableness=80.0, conscientiousness=72.0, neuroticism=25.0),
]

CREW_3 = [
    snap(agreeableness=75.0, conscientiousness=70.0, neuroticism=30.0),
    snap(agreeableness=80.0, conscientiousness=75.0, neuroticism=25.0),
    snap(agreeableness=65.0, conscientiousness=68.0, neuroticism=35.0),
]

CANDIDATE = snap(agreeableness=78.0, conscientiousness=72.0, neuroticism=28.0)


# ── Tests compute_fit() ───────────────────────────────────────────────────────

class TestComputeFit:
    def test_equipe_deux_membres_retourne_fteam_result(self):
        result = compute_fit(CANDIDATE, CREW_2)
        assert isinstance(result, FTeamResult)

    def test_equipe_trois_membres_score_dans_bornes(self):
        result = compute_fit(CANDIDATE, CREW_3)
        assert result is not None
        assert 0.0 <= result.score <= 100.0

    def test_current_crew_none_retourne_none(self):
        result = compute_fit(CANDIDATE, None)
        assert result is None

    def test_current_crew_vide_retourne_none(self):
        result = compute_fit(CANDIDATE, [])
        assert result is None

    def test_snapshot_vide_pas_exception(self):
        """snapshot candidat sans données → pas d'exception, FTeamResult retourné."""
        result = compute_fit(snap_empty(), CREW_2)
        assert isinstance(result, FTeamResult)
        assert 0.0 <= result.score <= 100.0

    def test_taille_equipe_inclut_candidat(self):
        """crew_size = len(current_crew) + 1 (candidat inclus)."""
        result = compute_fit(CANDIDATE, CREW_2)
        assert result is not None
        assert result.crew_size == 3

    def test_jerk_filter_present(self):
        result = compute_fit(CANDIDATE, CREW_2)
        assert result is not None
        assert result.jerk_filter is not None
        assert result.jerk_filter.min_agreeableness > 0

    def test_faultline_present(self):
        result = compute_fit(CANDIDATE, CREW_2)
        assert result is not None
        assert result.faultline is not None

    def test_emotional_buffer_present(self):
        result = compute_fit(CANDIDATE, CREW_2)
        assert result is not None
        assert result.emotional is not None

    def test_candidat_jerk_abaisse_score(self):
        """Candidat avec agréabilité très basse abaisse le score vs candidat normal."""
        result_bon = compute_fit(snap(agreeableness=80.0), CREW_3)
        result_jerk = compute_fit(snap(agreeableness=10.0), CREW_3)
        assert result_bon is not None
        assert result_jerk is not None
        assert result_bon.score > result_jerk.score

    def test_equipe_un_membre_puis_candidat_retourne_result(self):
        """Équipe d'1 membre + candidat = 2 → compute() peut calculer."""
        crew_solo = [snap()]
        result = compute_fit(CANDIDATE, crew_solo)
        assert isinstance(result, FTeamResult)
        assert 0.0 <= result.score <= 100.0


# ── Tests compute() rétrocompatibilité ────────────────────────────────────────

class TestComputeRetrocompat:
    def test_equipe_nominale_retourne_fteam_result(self):
        result = compute(CREW_3)
        assert isinstance(result, FTeamResult)

    def test_score_dans_bornes(self):
        result = compute(CREW_3)
        assert 0.0 <= result.score <= 100.0

    def test_deux_membres(self):
        result = compute(CREW_2)
        assert isinstance(result, FTeamResult)
        assert 0.0 <= result.score <= 100.0

    def test_equipe_trop_petite_retourne_50(self):
        result = compute([snap()])
        assert result.score == 50.0
        assert any("CREW_TOO_SMALL" in f for f in result.flags)

    def test_equipe_vide_retourne_50(self):
        result = compute([])
        assert result.score == 50.0

    def test_crew_size_correct(self):
        result = compute(CREW_3)
        assert result.crew_size == 3

    def test_formula_snapshot_non_vide(self):
        result = compute(CREW_3)
        assert isinstance(result.formula_snapshot, str)
        assert len(result.formula_snapshot) > 0
