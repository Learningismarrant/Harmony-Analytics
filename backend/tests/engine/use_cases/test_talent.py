"""
Tests use case Talent — appels directs, zéro mock.

Vérifie la détection du profil de talent (LEADER/SPECIALIST/GENERALIST),
le calcul de readiness par poste et le flag high_potential.
"""
import pytest
from app.engine.use_cases.talent import run, TalentResult, CAREER_PROGRESSIONS


# ── Fixtures snapshots ────────────────────────────────────────────────────────

def _snap_leader() -> dict:
    """C=80, E=70, GCA=75 → LEADER."""
    return {
        "big_five": {
            "conscientiousness": 80.0,
            "extraversion": 70.0,
            "agreeableness": 70.0,
            "openness": 65.0,
            "neuroticism": 20.0,
        },
        "cognitive": {
            "gca_score": 75.0,
            "logical": 75.0,
            "numerical": 75.0,
            "verbal": 75.0,
        },
        "motivation": {
            "intrinsic": 80.0,
            "identified": 80.0,
            "introjected": 25.0,
            "extrinsic_social": 55.0,
            "extrinsic_material": 50.0,
            "amotivation": 5.0,
        },
    }


def _snap_specialist() -> dict:
    """GCA=80, openness=75, E=45 → SPECIALIST."""
    return {
        "big_five": {
            "conscientiousness": 70.0,
            "extraversion": 45.0,
            "agreeableness": 65.0,
            "openness": 75.0,
            "neuroticism": 20.0,
        },
        "cognitive": {
            "gca_score": 80.0,
            "logical": 85.0,
            "numerical": 80.0,
            "verbal": 75.0,
        },
        "motivation": {
            "intrinsic": 90.0,
            "identified": 78.0,
            "introjected": 25.0,
            "extrinsic_social": 40.0,
            "extrinsic_material": 55.0,
            "amotivation": 5.0,
        },
    }


def _snap_generalist() -> dict:
    """Profil modéré sans caractéristiques LEADER ni SPECIALIST."""
    return {
        "big_five": {
            "conscientiousness": 60.0,
            "extraversion": 55.0,
            "agreeableness": 65.0,
            "openness": 55.0,
            "neuroticism": 35.0,
        },
        "cognitive": {
            "gca_score": 55.0,
        },
        "motivation": {
            "intrinsic": 55.0,
            "identified": 55.0,
            "introjected": 40.0,
            "extrinsic_social": 60.0,
            "extrinsic_material": 60.0,
            "amotivation": 20.0,
        },
    }


def _snap_high_potential_deckhand() -> dict:
    """Profil Deckhand avec scores élevés → high_potential sur Bosun."""
    return {
        "big_five": {
            "conscientiousness": 85.0,
            "extraversion": 65.0,
            "agreeableness": 80.0,
            "openness": 60.0,
            "neuroticism": 25.0,
        },
        "cognitive": {
            "gca_score": 72.0,
            "logical": 72.0,
            "numerical": 70.0,
            "verbal": 70.0,
        },
        "motivation": {
            "intrinsic": 80.0,
            "identified": 85.0,
            "introjected": 40.0,
            "extrinsic_social": 65.0,
            "extrinsic_material": 65.0,
            "amotivation": 0.0,
        },
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.engine
class TestTalentCareerProgression:
    def test_career_progression_deckhand(self):
        """Deckhand → postes cibles incluent Bosun et First Mate."""
        snap = _snap_generalist()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        assert isinstance(result, TalentResult)
        target_positions = [p.position for p in result.next_positions]
        assert "Bosun" in target_positions

    def test_career_progression_bosun(self):
        """Bosun → progression naturelle vers First Mate et Captain."""
        snap = _snap_generalist()
        result = run(
            candidate_snapshot=snap,
            current_position="Bosun",
        )
        target_positions = [p.position for p in result.next_positions]
        expected = CAREER_PROGRESSIONS["Bosun"]
        for pos in expected:
            assert pos in target_positions

    def test_career_progression_stewardess(self):
        """Stewardess → Chief Stewardess."""
        snap = _snap_generalist()
        result = run(
            candidate_snapshot=snap,
            current_position="Stewardess",
        )
        target_positions = [p.position for p in result.next_positions]
        assert "Chief Stewardess" in target_positions

    def test_explicit_target_positions_override(self):
        """target_positions explicite override la progression naturelle."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
            target_positions=["Captain", "Chief Engineer"],
        )
        target_positions = [p.position for p in result.next_positions]
        assert "Captain" in target_positions
        assert "Chief Engineer" in target_positions
        assert "Bosun" not in target_positions  # pas dans la liste explicite

    def test_position_without_progression_returns_empty(self):
        """Poste sans progression naturelle → next_positions vide."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Captain",  # pas dans CAREER_PROGRESSIONS
        )
        assert result.next_positions == []
        assert result.recommended_next is None


@pytest.mark.engine
class TestTalentHighPotential:
    def test_high_potential_flag_high_readiness(self):
        """Readiness ≥ 70 sur au moins un poste → high_potential=True."""
        snap = _snap_high_potential_deckhand()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        # Vérifier que le flag est cohérent avec les scores
        has_ready = any(p.readiness_score >= 70.0 for p in result.next_positions)
        assert result.high_potential == has_ready

    def test_high_potential_false_for_generalist(self):
        """Profil modéré → high_potential probablement False sur poste Captain."""
        snap = _snap_generalist()
        result = run(
            candidate_snapshot=snap,
            current_position="Bosun",
            target_positions=["Captain"],
        )
        if result.next_positions:
            captain_readiness = result.next_positions[0].readiness_score
            expected_hp = captain_readiness >= 70.0
            assert result.high_potential == expected_hp


@pytest.mark.engine
class TestTalentProfile:
    def test_leader_profile_detection(self):
        """C=80, E=70, GCA=75 → LEADER."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
            target_positions=["Bosun"],
        )
        assert result.talent_profile == "LEADER"

    def test_specialist_profile_detection(self):
        """GCA=80, openness=75, E=45 → SPECIALIST."""
        snap = _snap_specialist()
        result = run(
            candidate_snapshot=snap,
            current_position="2nd Engineer",
            target_positions=["Chief Engineer"],
        )
        assert result.talent_profile == "SPECIALIST"

    def test_generalist_profile_detection(self):
        """Profil modéré → GENERALIST."""
        snap = _snap_generalist()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
            target_positions=["Bosun"],
        )
        assert result.talent_profile == "GENERALIST"


@pytest.mark.engine
class TestTalentPositionReadiness:
    def test_readiness_score_in_bounds(self):
        """readiness_score doit être entre 0 et 100."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        for pos_r in result.next_positions:
            assert 0.0 <= pos_r.readiness_score <= 100.0

    def test_readiness_label_coherent(self):
        """readiness_label cohérent avec readiness_score."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        for pos_r in result.next_positions:
            if pos_r.readiness_score >= 70.0:
                assert pos_r.readiness_label == "READY"
            elif pos_r.readiness_score >= 50.0:
                assert pos_r.readiness_label == "DEVELOPING"
            else:
                assert pos_r.readiness_label == "NOT_READY"

    def test_development_time_coherent(self):
        """estimated_development_time cohérent avec readiness_score."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        for pos_r in result.next_positions:
            if pos_r.readiness_score >= 70.0:
                assert pos_r.estimated_development_time == "< 6 mois"
            elif pos_r.readiness_score >= 50.0:
                assert pos_r.estimated_development_time == "6-18 mois"
            else:
                assert pos_r.estimated_development_time == "> 18 mois"

    def test_key_gaps_max_3(self):
        """key_gaps contient au plus 3 éléments par poste."""
        snap = _snap_generalist()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        for pos_r in result.next_positions:
            assert len(pos_r.key_gaps) <= 3

    def test_recommended_next_is_best_position(self):
        """recommended_next = poste avec le meilleur readiness_score."""
        snap = _snap_leader()
        result = run(
            candidate_snapshot=snap,
            current_position="Deckhand",
        )
        if result.next_positions and result.recommended_next:
            best_score = max(p.readiness_score for p in result.next_positions)
            recommended = next(
                p for p in result.next_positions
                if p.position == result.recommended_next
            )
            assert recommended.readiness_score == best_score
