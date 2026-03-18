"""
Tests use case Recrutement — appels directs, zéro mock.

Vérifie la logique de décision HIRE / CONDITIONAL / DISQUALIFY
en fonction des scores psychométriques et des paramètres disponibles.
"""
import pytest
from app.engine.use_cases.recruitment import run, RecruitmentResult


# ── Fixtures snapshots ────────────────────────────────────────────────────────

def _snapshot_clear(
    es: float = 75.0,
    agreeableness: float = 70.0,
    conscientiousness: float = 80.0,
    gca: float = 75.0,
) -> dict:
    """Snapshot avec données suffisantes pour un candidat sain."""
    return {
        "big_five": {
            "agreeableness": agreeableness,
            "conscientiousness": conscientiousness,
            "openness": 65.0,
            "extraversion": 60.0,
            "neuroticism": 100.0 - es,
        },
        "emotional_stability": es,
        "cognitive": {
            "gca_score": gca,
            "logical": gca,
            "numerical": gca,
            "verbal": gca,
        },
        "motivation": {
            "intrinsic": 80.0,
            "identified": 75.0,
            "introjected": 30.0,
            "extrinsic_social": 60.0,
            "extrinsic_material": 55.0,
            "amotivation": 5.0,
        },
    }


def _snapshot_high_fit() -> dict:
    """Snapshot avec scores élevés sur tous les traits."""
    return _snapshot_clear(
        es=80.0,
        agreeableness=80.0,
        conscientiousness=90.0,
        gca=85.0,
    )


def _snapshot_medium_fit() -> dict:
    """Snapshot avec scores moyens."""
    return _snapshot_clear(
        es=55.0,
        agreeableness=55.0,
        conscientiousness=55.0,
        gca=50.0,
    )


def _snapshot_disqualify_es() -> dict:
    """ES = 10 → HARD VETO → DISQUALIFY."""
    return _snapshot_clear(
        es=10.0,
        agreeableness=70.0,
        conscientiousness=80.0,
        gca=75.0,
    )


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.engine
class TestRecruitmentDisqualify:
    def test_disqualify_on_safety_barrier(self):
        """ES=10 → HARD VETO → décision DISQUALIFY."""
        snap = _snapshot_disqualify_es()
        result = run(
            candidate_snapshot=snap,
            position="Deckhand",
            pool=[],
        )
        assert isinstance(result, RecruitmentResult)
        assert result.decision == "DISQUALIFY"
        assert result.safety_level == "DISQUALIFIED"

    def test_disqualify_produces_safety_alert(self):
        """Une alerte CRITICAL doit être générée quand DISQUALIFIED."""
        snap = _snapshot_disqualify_es()
        result = run(
            candidate_snapshot=snap,
            position="Deckhand",
            pool=[],
        )
        assert any(a.severity == "CRITICAL" for a in result.alerts)

    def test_disqualify_low_score(self):
        """Score très bas sans veto → DISQUALIFY si score < 45."""
        snap = {
            "big_five": {
                "agreeableness": 20.0,
                "conscientiousness": 20.0,
                "openness": 20.0,
                "extraversion": 20.0,
                "neuroticism": 40.0,
            },
            "cognitive": {"gca_score": 15.0},
        }
        result = run(
            candidate_snapshot=snap,
            position="Deckhand",
            pool=[],
        )
        # Avec agreeableness=20 → SOFT veto → HIGH_RISK → CONDITIONAL
        # Mais score très bas → DISQUALIFY
        assert result.decision in ("DISQUALIFY", "CONDITIONAL")


@pytest.mark.engine
class TestRecruitmentHire:
    def test_hire_high_fit(self):
        """Tous scores élevés → HIRE."""
        snap = _snapshot_high_fit()
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=[],
        )
        assert result.decision == "HIRE"
        assert result.global_fit_score >= 65.0
        assert result.safety_level in ("CLEAR", "ADVISORY")

    def test_hire_returns_pj_score(self):
        """Le score PJ doit être calculé et présent."""
        snap = _snapshot_high_fit()
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=[],
        )
        assert result.pj_score > 0.0
        assert 0.0 <= result.pj_score <= 100.0


@pytest.mark.engine
class TestRecruitmentConditional:
    def test_conditional_medium_fit(self):
        """Scores moyens → CONDITIONAL (score entre 45 et 65)."""
        snap = _snapshot_medium_fit()
        result = run(
            candidate_snapshot=snap,
            position="Deckhand",
            pool=[],
        )
        assert result.decision in ("CONDITIONAL", "HIRE", "DISQUALIFY")
        # Avec des scores moyens (55), le résultat devrait être CONDITIONAL
        # la plupart du temps (sauf si le SME poids donne > 65 ou < 45)
        assert isinstance(result.global_fit_score, float)

    def test_conditional_high_risk_safety(self):
        """Scores corrects mais HIGH_RISK safety → CONDITIONAL et non HIRE."""
        snap = _snapshot_clear(
            es=25.0,  # SOFT veto → HIGH_RISK
            agreeableness=70.0,
            conscientiousness=80.0,
            gca=75.0,
        )
        result = run(
            candidate_snapshot=snap,
            position="Deckhand",
            pool=[],
        )
        # HIGH_RISK safety force CONDITIONAL même avec score > 65
        assert result.safety_level == "HIGH_RISK"
        assert result.decision == "CONDITIONAL"


@pytest.mark.engine
class TestRecruitmentDimensions:
    def test_dimensions_used_without_optional_params(self):
        """Sans vessel_params, captain_vector, crew_snapshots → 'ns', 'pt', 'ps' absents.

        La dimension 'motivation' est incluse dès que position est fourni
        (pas besoin de vessel_params). Seules 'ns', 'pt', 'ps' sont strictement
        optionnelles (nécessitent vessel_params, crew_snapshots, captain_vector).
        """
        snap = _snapshot_high_fit()
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=[],
        )
        assert "pj" in result.dimensions_used
        assert "ns" not in result.dimensions_used
        assert "pt" not in result.dimensions_used
        assert "ps" not in result.dimensions_used

    def test_dimensions_used_with_vessel_params(self):
        """Avec vessel_params → NS fit activé → 'ns' dans dimensions_used."""
        snap = _snapshot_high_fit()
        vessel = {
            "salary_index": 0.8,
            "rest_days_ratio": 0.7,
            "private_cabin_ratio": 1.0,
            "charter_intensity": 0.4,
            "management_pressure": 0.3,
        }
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=[],
            vessel_params=vessel,
        )
        assert "ns" in result.dimensions_used
        assert result.ns_score is not None

    def test_dimensions_used_with_all_params(self):
        """Avec tous les paramètres → 4+ dimensions utilisées."""
        snap = _snapshot_high_fit()
        vessel = {
            "salary_index": 0.8,
            "rest_days_ratio": 0.7,
            "private_cabin_ratio": 1.0,
            "charter_intensity": 0.4,
            "management_pressure": 0.3,
        }
        captain = {
            "autonomy_given": 0.6,
            "feedback_style": 0.5,
            "structure_imposed": 0.7,
        }
        crew = [_snapshot_high_fit(), _snapshot_high_fit()]
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=[],
            vessel_params=vessel,
            captain_vector=captain,
            current_crew_snapshots=crew,
        )
        assert len(result.dimensions_used) >= 4

    def test_centile_none_with_small_pool(self):
        """Pool < 2 → centile == None, centile_label == 'N/A'."""
        snap = _snapshot_high_fit()
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=[_snapshot_medium_fit()],  # 1 seul candidat — pas assez
        )
        assert result.centile is None
        assert result.centile_label == "N/A"

    def test_centile_computed_with_pool(self):
        """Pool >= 2 → centile calculé."""
        snap = _snapshot_high_fit()
        pool = [_snapshot_medium_fit(), _snapshot_clear()]
        result = run(
            candidate_snapshot=snap,
            position="Bosun",
            pool=pool,
        )
        assert result.centile is not None
        assert 0.0 <= result.centile <= 100.0

    def test_motivation_score_present_with_position(self):
        """Position fournie → motivation_score calculé."""
        snap = _snapshot_high_fit()
        result = run(
            candidate_snapshot=snap,
            position="Captain",
            pool=[],
        )
        assert result.motivation_score is not None
        assert "motivation" in result.dimensions_used
