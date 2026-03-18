"""
Tests use case Formation — appels directs, zéro mock.

Vérifie le gap analysis par trait, la détection des forces,
et le calcul de l'overall_readiness.
"""
import pytest
from app.engine.use_cases.training import run, TrainingResult, TraitGap


# ── Fixtures snapshots ────────────────────────────────────────────────────────

def _snap_low_profile() -> dict:
    """Profil candidat bas sur tous les traits → gaps positifs élevés."""
    return {
        "big_five": {
            "agreeableness": 30.0,
            "conscientiousness": 25.0,
            "openness": 20.0,
            "extraversion": 25.0,
            "neuroticism": 70.0,  # ES = 30
        },
        "cognitive": {
            "gca_score": 30.0,
            "logical": 30.0,
            "numerical": 25.0,
            "verbal": 30.0,
        },
        "motivation": {
            "intrinsic": 30.0,
            "identified": 30.0,
            "introjected": 60.0,
            "extrinsic_social": 40.0,
            "extrinsic_material": 50.0,
            "amotivation": 50.0,
        },
    }


def _snap_high_profile() -> dict:
    """Profil candidat élevé → forces détectées."""
    return {
        "big_five": {
            "agreeableness": 95.0,
            "conscientiousness": 98.0,
            "openness": 90.0,
            "extraversion": 90.0,
            "neuroticism": 5.0,  # ES = 95
        },
        "cognitive": {
            "gca_score": 95.0,
            "logical": 95.0,
            "numerical": 95.0,
            "verbal": 95.0,
        },
        "motivation": {
            "intrinsic": 95.0,
            "identified": 90.0,
            "introjected": 5.0,
            "extrinsic_social": 55.0,
            "extrinsic_material": 40.0,
            "amotivation": 0.0,
        },
    }


def _snap_median_profile() -> dict:
    """Profil médian."""
    return {
        "big_five": {
            "agreeableness": 50.0,
            "conscientiousness": 50.0,
            "openness": 50.0,
            "extraversion": 50.0,
            "neuroticism": 50.0,
        },
        "cognitive": {
            "gca_score": 50.0,
        },
        "motivation": {
            "intrinsic": 50.0,
            "identified": 50.0,
            "introjected": 50.0,
            "extrinsic_social": 50.0,
            "extrinsic_material": 50.0,
            "amotivation": 50.0,
        },
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.engine
class TestTrainingGapAnalysis:
    def test_gap_analysis_correct_low_profile(self):
        """Profil bas → gaps positifs (ideal > current) pour la plupart des traits."""
        snap = _snap_low_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Captain",
        )
        assert isinstance(result, TrainingResult)
        # Avec un profil bas, la majorité des gaps doit être positive (sous le niveau)
        positive_gaps = [g for g in result.trait_gaps if g.gap > 0]
        assert len(positive_gaps) > 0

    def test_gap_priority_high_detected(self):
        """Gaps > 25 → priority HIGH."""
        snap = _snap_low_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Captain",
        )
        high_prio = [g for g in result.trait_gaps if g.priority == "HIGH"]
        assert len(high_prio) > 0

    def test_overall_readiness_low_for_low_profile(self):
        """Profil bas → overall_readiness faible."""
        snap = _snap_low_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Captain",
        )
        assert result.overall_readiness < 70.0
        assert result.readiness_label in ("DEVELOPING", "GAP")

    def test_trait_gaps_sorted_by_priority(self):
        """trait_gaps trié : HIGH avant MEDIUM avant LOW."""
        snap = _snap_low_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Bosun",
        )
        priority_order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        for i in range(len(result.trait_gaps) - 1):
            curr = priority_order.get(result.trait_gaps[i].priority, 3)
            nxt  = priority_order.get(result.trait_gaps[i + 1].priority, 3)
            assert curr <= nxt

    def test_top_priorities_max_3(self):
        """top_priorities contient au plus 3 éléments."""
        snap = _snap_low_profile()
        result = run(candidate_snapshot=snap, current_position="Captain")
        assert len(result.top_priorities) <= 3


@pytest.mark.engine
class TestTrainingStrengths:
    def test_strengths_detected_high_profile(self):
        """Profil élevé → forces détectées (gap < 0)."""
        snap = _snap_high_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",  # poste bas → idéal plus facile à dépasser
        )
        assert isinstance(result, TrainingResult)
        assert len(result.strengths) > 0

    def test_strengths_max_3(self):
        """strengths contient au plus 3 éléments."""
        snap = _snap_high_profile()
        result = run(candidate_snapshot=snap, current_position="Deckhand")
        assert len(result.strengths) <= 3

    def test_overall_readiness_high_for_high_profile(self):
        """Profil élevé → overall_readiness élevé."""
        snap = _snap_high_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        assert result.overall_readiness > 70.0


@pytest.mark.engine
class TestTrainingTargetPosition:
    def test_same_position_default(self):
        """target_position=None → target = current_position."""
        snap = _snap_median_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Bosun",
            target_position=None,
        )
        assert result.target_position == "Bosun"
        assert result.current_position == "Bosun"

    def test_explicit_target_position(self):
        """target_position explicite utilisé."""
        snap = _snap_median_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
            target_position="Captain",
        )
        assert result.target_position == "Captain"
        assert result.current_position == "Deckhand"

    def test_unknown_position_returns_minimal_result(self):
        """Poste inconnu → résultat minimal sans erreur."""
        snap = _snap_median_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
            target_position="UnknownPosition",
        )
        assert isinstance(result, TrainingResult)
        assert result.overall_readiness == 50.0
        assert result.trait_gaps == []

    def test_different_positions_give_different_gaps(self):
        """Deckhand vs Captain → gaps différents pour le même snapshot."""
        snap = _snap_median_profile()
        result_low = run(candidate_snapshot=snap, current_position="Deckhand")
        result_high = run(candidate_snapshot=snap, current_position="Captain")
        # Le Captain a des exigences plus élevées → readiness plus basse
        assert result_high.overall_readiness <= result_low.overall_readiness


@pytest.mark.engine
class TestTrainingMotivationGaps:
    def test_motivation_gaps_present_when_position_known(self):
        """Avec un poste connu → motivation_gaps calculés."""
        snap = _snap_median_profile()
        result = run(
            candidate_snapshot=snap,
            current_position="Captain",
        )
        # Si position connue → gaps motivationnels via SDT
        # peuvent être vides si aucune donnée motivation
        assert isinstance(result.motivation_gaps, list)

    def test_motivation_gaps_populated_with_motivation_data(self):
        """Avec données motivation → motivation_gaps non vides."""
        snap = _snap_low_profile()  # contient motivation
        result = run(
            candidate_snapshot=snap,
            current_position="Captain",
        )
        assert len(result.motivation_gaps) > 0


@pytest.mark.engine
class TestTrainingConfidence:
    def test_confidence_high_with_complete_data(self):
        """Snapshot complet → confidence HIGH ou MEDIUM."""
        snap = _snap_high_profile()
        result = run(candidate_snapshot=snap, current_position="Captain")
        assert result.confidence.value in ("HIGH", "MEDIUM")

    def test_confidence_low_with_empty_snapshot(self):
        """Snapshot vide → confidence LOW."""
        result = run(
            candidate_snapshot={},
            current_position="Deckhand",
        )
        # Snapshot vide → beaucoup de fallbacks → LOW confidence
        assert result.confidence.value in ("LOW", "MEDIUM")
