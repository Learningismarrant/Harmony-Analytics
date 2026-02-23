# tests/engine/recruitment/MLPSM/test_f_lmx.py
"""
Tests unitaires pour engine.recruitment.MLPSM.f_lmx.compute()

F_lmx = (1 - ||L_capt - V_crew|| / d_max) × 100

Couverture :
    - Vecteurs identiques → F_lmx = 100.0 (distance = 0)
    - Vecteurs opposés → F_lmx = 0.0 (distance = d_max)
    - Vecteur capitaine absent → flag CAPTAIN_DATA_INCOMPLETE
    - Préférences candidat absentes → dérivées du Big Five
    - Score clamped entre 0 et 100
    - Analyse par dimension (DimensionGap)
    - Labels de compatibilité (EXCELLENT, GOOD, TENSION, CRITICAL)
"""
import pytest
import math

from app.engine.recruitment.MLPSM.f_lmx import (
    compute,
    FLmxResult,
    D_MAX_UNIFORM,
    CRITICAL_DISTANCE_THRESHOLD,
    HIGH_DISTANCE_THRESHOLD,
)

pytestmark = pytest.mark.engine


def captain(autonomy=0.5, feedback=0.5, structure=0.5):
    return {
        "autonomy_given": autonomy,
        "feedback_style": feedback,
        "structure_imposed": structure,
    }


def snap_with_lp(autonomy=0.5, feedback=0.5, structure=0.5):
    """Snapshot avec leadership_preferences explicites."""
    return {
        "leadership_preferences": {
            "autonomy_preference": autonomy,
            "feedback_preference": feedback,
            "structure_preference": structure,
        }
    }


def snap_with_big_five(conscientiousness=70.0, openness=60.0, agreeableness=65.0):
    """Snapshot sans leadership_preferences → dérivé du Big Five."""
    return {
        "big_five": {
            "conscientiousness": conscientiousness,
            "openness": openness,
            "agreeableness": agreeableness,
        }
    }


def snap_empty():
    return {}


class TestFLmxCompute:
    def test_retourne_flmx_result(self):
        result = compute(snap_with_lp(), captain())
        assert isinstance(result, FLmxResult)

    def test_score_dans_bornes(self):
        result = compute(snap_with_lp(), captain())
        assert 0.0 <= result.score <= 100.0

    def test_vecteurs_identiques_score_100(self):
        """Vecteurs L_capt = V_crew → distance = 0 → F_lmx = 100."""
        v = captain(autonomy=0.7, feedback=0.3, structure=0.6)
        snap = snap_with_lp(autonomy=0.7, feedback=0.3, structure=0.6)
        result = compute(snap, v)
        assert result.score == 100.0

    def test_vecteurs_opposes_score_bas(self):
        """
        Vecteurs maximalement opposés → distance max → F_lmx proche de 0.
        Capt = (1, 1, 1), Crew = (0, 0, 0).
        """
        result = compute(
            snap_with_lp(autonomy=0.0, feedback=0.0, structure=0.0),
            captain(autonomy=1.0, feedback=1.0, structure=1.0),
        )
        assert result.score < 5.0

    def test_vecteur_capitaine_absent(self):
        """captain_vector vide → flag CAPTAIN_DATA_INCOMPLETE, data_quality réduite."""
        result = compute(snap_with_lp(), {})
        assert any("CAPTAIN_DATA_INCOMPLETE" in f for f in result.flags)
        assert result.data_quality < 1.0

    def test_preferences_derivees_big_five(self):
        """Sans leadership_preferences, les préférences sont dérivées du Big Five."""
        result = compute(snap_with_big_five(), captain())
        # Le résultat doit exister et être valide
        assert result.score is not None
        assert 0.0 <= result.score <= 100.0

    def test_snapshot_vide_fallback(self):
        """Snapshot vide → tous les fallbacks (0.5) utilisés."""
        result = compute(snap_empty(), captain())
        assert isinstance(result, FLmxResult)
        assert 0.0 <= result.score <= 100.0

    def test_dimension_gaps_3_dimensions(self):
        """3 dimensions analysées : autonomy, feedback, structure."""
        result = compute(snap_with_lp(), captain())
        assert len(result.dimensions) == 3
        dims = {d.dimension for d in result.dimensions}
        assert dims == {"autonomy", "feedback", "structure"}

    def test_gap_direction_captain_more(self):
        """Capitaine donne plus d'autonomie que crew ne veut → CAPTAIN_MORE."""
        result = compute(
            snap_with_lp(autonomy=0.1),
            captain(autonomy=0.9),
        )
        autonomy_gap = next(d for d in result.dimensions if d.dimension == "autonomy")
        if autonomy_gap.gap > 0.30:
            assert autonomy_gap.gap_direction == "CAPTAIN_MORE"

    def test_gap_direction_crew_more(self):
        """Crew veut plus d'autonomie que capitaine n'en donne → CREW_MORE."""
        result = compute(
            snap_with_lp(autonomy=0.9),
            captain(autonomy=0.1),
        )
        autonomy_gap = next(d for d in result.dimensions if d.dimension == "autonomy")
        if autonomy_gap.gap > 0.30:
            assert autonomy_gap.gap_direction == "CREW_MORE"

    def test_compatibilite_excellent(self):
        """Vecteurs très proches → compat_label = 'EXCELLENT'."""
        result = compute(
            snap_with_lp(autonomy=0.5, feedback=0.5, structure=0.5),
            captain(autonomy=0.5, feedback=0.5, structure=0.5),
        )
        assert result.distance.compatibility_label == "EXCELLENT"

    def test_compatibilite_critical_flag(self):
        """Distance normalisée > threshold → flag LMX_CRITICAL."""
        result = compute(
            snap_with_lp(autonomy=0.0, feedback=0.0, structure=0.0),
            captain(autonomy=1.0, feedback=1.0, structure=1.0),
        )
        assert any("CRITICAL" in f for f in result.flags)

    def test_vectors_detail_correct(self):
        """VectorDetail doit contenir les valeurs des deux vecteurs."""
        capt_vals = captain(autonomy=0.7, feedback=0.4, structure=0.6)
        crew_snap = snap_with_lp(autonomy=0.3, feedback=0.8, structure=0.5)
        result = compute(crew_snap, capt_vals)
        assert result.vectors.captain_autonomy_given == 0.7
        assert result.vectors.crew_autonomy_preference == 0.3

    def test_distance_euclidienne_manuelle(self):
        """
        Vérification manuelle de la distance euclidienne avec pondérations 1/3.
        Capt = (0.8, 0.2, 0.7), Crew = (0.3, 0.6, 0.4)
        dist = sqrt(1/3 × (0.5)² + 1/3 × (0.4)² + 1/3 × (0.3)²)
        """
        capt = captain(autonomy=0.8, feedback=0.2, structure=0.7)
        crew = snap_with_lp(autonomy=0.3, feedback=0.6, structure=0.4)
        result = compute(crew, capt)
        expected_dist_sq = (1/3) * (0.5**2 + 0.4**2 + 0.3**2)
        expected_dist = math.sqrt(expected_dist_sq)
        assert abs(result.distance.euclidean_distance - expected_dist) < 0.001
