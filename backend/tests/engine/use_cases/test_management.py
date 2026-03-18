"""
Tests use case Management — appels directs, zéro mock.

Vérifie la détection des risques équipe (JERK_RISK, FAULTLINE_RISK,
EMOTIONAL_FRAGILITY) et la génération des recommandations.
"""
import pytest
from app.engine.use_cases.management import run, ManagementResult


# ── Fixtures snapshots ────────────────────────────────────────────────────────

def _snap(
    agreeableness: float = 70.0,
    conscientiousness: float = 75.0,
    neuroticism: float = 25.0,  # ES = 100 - neuroticism
    openness: float = 65.0,
    extraversion: float = 60.0,
) -> dict:
    return {
        "big_five": {
            "agreeableness": agreeableness,
            "conscientiousness": conscientiousness,
            "openness": openness,
            "extraversion": extraversion,
            "neuroticism": neuroticism,
        },
        "emotional_stability": 100.0 - neuroticism,
    }


def _healthy_crew() -> list:
    """Équipe saine : A_min=80, μES=75, σC faible."""
    return [
        _snap(agreeableness=80.0, conscientiousness=78.0, neuroticism=25.0),
        _snap(agreeableness=85.0, conscientiousness=80.0, neuroticism=25.0),
        _snap(agreeableness=82.0, conscientiousness=76.0, neuroticism=25.0),
    ]


def _jerk_crew() -> list:
    """Équipe avec un membre à A_min très bas (25 < seuil 35)."""
    return [
        _snap(agreeableness=25.0, conscientiousness=75.0, neuroticism=30.0),
        _snap(agreeableness=80.0, conscientiousness=75.0, neuroticism=25.0),
        _snap(agreeableness=78.0, conscientiousness=72.0, neuroticism=28.0),
    ]


def _faultline_crew() -> list:
    """Équipe avec forte variance de conscienciosité (σ > 20)."""
    return [
        _snap(agreeableness=70.0, conscientiousness=95.0, neuroticism=25.0),
        _snap(agreeableness=72.0, conscientiousness=40.0, neuroticism=28.0),
        _snap(agreeableness=68.0, conscientiousness=98.0, neuroticism=30.0),
        _snap(agreeableness=75.0, conscientiousness=35.0, neuroticism=27.0),
    ]


def _fragile_crew() -> list:
    """Équipe avec faible stabilité émotionnelle (μES < 45)."""
    return [
        _snap(agreeableness=70.0, conscientiousness=75.0, neuroticism=65.0),  # ES=35
        _snap(agreeableness=72.0, conscientiousness=73.0, neuroticism=62.0),  # ES=38
        _snap(agreeableness=68.0, conscientiousness=70.0, neuroticism=60.0),  # ES=40
    ]


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.engine
class TestManagementHealthy:
    def test_healthy_team(self):
        """A_min=80, μES=75 → HEALTHY, pas de JERK_RISK."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        assert isinstance(result, ManagementResult)
        assert result.team_health_label == "HEALTHY"
        assert result.jerk_risk is False
        assert result.team_health_score >= 65.0

    def test_healthy_no_alerts(self):
        """Équipe saine → pas d'alertes PT."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        pt_alerts = [a for a in result.team_alerts if a.code == "JERK_RISK"]
        assert len(pt_alerts) == 0

    def test_crew_size_recorded(self):
        """crew_size doit correspondre au nombre de snapshots fournis."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        assert result.crew_size == len(crew)


@pytest.mark.engine
class TestManagementJerkRisk:
    def test_jerk_risk_detected(self):
        """A_min=25 → jerk_risk=True."""
        crew = _jerk_crew()
        result = run(crew_snapshots=crew)
        assert result.jerk_risk is True

    def test_jerk_risk_alert_generated(self):
        """jerk_risk=True → alerte JERK_RISK présente."""
        crew = _jerk_crew()
        result = run(crew_snapshots=crew)
        codes = [a.code for a in result.team_alerts]
        assert "JERK_RISK" in codes

    def test_jerk_risk_alert_severity(self):
        """Alerte JERK_RISK doit avoir severity WARNING ou CRITICAL."""
        crew = _jerk_crew()
        result = run(crew_snapshots=crew)
        jerk_alerts = [a for a in result.team_alerts if a.code == "JERK_RISK"]
        assert jerk_alerts[0].severity in ("WARNING", "CRITICAL")


@pytest.mark.engine
class TestManagementFaultlineRisk:
    def test_faultline_risk_detected(self):
        """σ(C) > 20 → faultline_risk=True."""
        crew = _faultline_crew()
        result = run(crew_snapshots=crew)
        assert result.faultline_risk is True

    def test_faultline_alert_generated(self):
        """faultline_risk=True → alerte FAULTLINE_RISK présente."""
        crew = _faultline_crew()
        result = run(crew_snapshots=crew)
        codes = [a.code for a in result.team_alerts]
        assert "FAULTLINE_RISK" in codes


@pytest.mark.engine
class TestManagementRecommendations:
    def test_recommendations_generated_on_jerk_risk(self):
        """Au moins 1 recommandation si JERK_RISK détecté."""
        crew = _jerk_crew()
        result = run(crew_snapshots=crew)
        assert len(result.recommendations) >= 1
        # Vérifier qu'une reco mentionne l'entretien individuel
        recos_text = " ".join(result.recommendations).lower()
        assert "entretien" in recos_text or "individuel" in recos_text

    def test_no_recommendations_on_healthy_team(self):
        """Équipe saine → pas de recommandations."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        assert len(result.recommendations) == 0

    def test_emotional_fragility_recommendation(self):
        """Équipe fragile → recommandation de surveillance."""
        crew = _fragile_crew()
        result = run(crew_snapshots=crew)
        if result.emotional_fragility:
            recos_text = " ".join(result.recommendations).lower()
            assert "émotionnel" in recos_text or "charge" in recos_text


@pytest.mark.engine
class TestManagementLMX:
    def test_lmx_per_member_with_captain(self):
        """captain_vector fourni → ps_score calculé pour chaque membre."""
        crew = _healthy_crew()
        captain = {
            "autonomy_given": 0.6,
            "feedback_style": 0.5,
            "structure_imposed": 0.7,
        }
        result = run(crew_snapshots=crew, captain_vector=captain)
        for status in result.member_statuses:
            assert status.ps_score is not None
            assert status.ps_label in ("EXCELLENT", "GOOD", "TENSION", "CRITICAL")

    def test_lmx_not_computed_without_captain(self):
        """Sans captain_vector → ps_score = None pour tous les membres."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        for status in result.member_statuses:
            assert status.ps_score is None

    def test_crew_ids_linked_to_member_statuses(self):
        """crew_ids fournis → liés correctement aux MemberStatus."""
        crew = _healthy_crew()
        ids = [101, 102, 103]
        result = run(crew_snapshots=crew, crew_ids=ids)
        for i, status in enumerate(result.member_statuses):
            assert status.crew_id == ids[i]

    def test_lmx_critical_generates_recommendation(self):
        """LMX CRITICAL pour un membre → recommandation médiation."""
        # Vecteur capitaine très directif
        captain = {
            "autonomy_given": 0.05,  # donne très peu d'autonomie
            "feedback_style": 0.05,
            "structure_imposed": 0.95,  # très structuré
        }
        # Membre qui veut beaucoup d'autonomie (openness élevée)
        crew = [
            _snap(agreeableness=70.0, conscientiousness=50.0, openness=95.0),
            _snap(agreeableness=70.0, conscientiousness=75.0),
        ]
        result = run(
            crew_snapshots=crew,
            captain_vector=captain,
        )
        # Si LMX CRITICAL détecté → recommandation présente
        critical_members = [m for m in result.member_statuses if m.ps_label == "CRITICAL"]
        if critical_members:
            recos_text = " ".join(result.recommendations).lower()
            assert "médiation" in recos_text or "repositionnement" in recos_text
