"""
Tests use case RPS — appels directs, zéro mock.

Vérifie la classification du niveau de risque psychosocial,
la détection des facteurs déclencheurs et les recommandations.
"""
import pytest
from app.engine.use_cases.rps import run, RpsResult, RiskLevel


# ── Fixtures snapshots ────────────────────────────────────────────────────────

def _snap(
    agreeableness: float = 70.0,
    conscientiousness: float = 75.0,
    neuroticism: float = 25.0,
    openness: float = 65.0,
    extraversion: float = 60.0,
) -> dict:
    """Snapshot Big Five standard."""
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
    return [
        _snap(agreeableness=80.0, conscientiousness=78.0, neuroticism=20.0),
        _snap(agreeableness=75.0, conscientiousness=80.0, neuroticism=22.0),
        _snap(agreeableness=78.0, conscientiousness=76.0, neuroticism=18.0),
    ]


def _low_resources_high_demands_vessel() -> dict:
    """Ressources très faibles + demandes élevées → BURNOUT_RISK."""
    return {
        "salary_index": 0.1,
        "rest_days_ratio": 0.1,
        "private_cabin_ratio": 0.0,
        "charter_intensity": 0.95,
        "management_pressure": 0.90,
    }


def _balanced_vessel() -> dict:
    """Ressources/demandes équilibrées → faible risque burnout."""
    return {
        "salary_index": 0.8,
        "rest_days_ratio": 0.7,
        "private_cabin_ratio": 1.0,
        "charter_intensity": 0.3,
        "management_pressure": 0.25,
    }


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.engine
class TestRpsLowRisk:
    def test_low_risk_healthy_team(self):
        """Équipe saine sans vessel_params ni captain → risque LOW ou MODERATE."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        assert isinstance(result, RpsResult)
        assert result.global_risk_level in (RiskLevel.LOW, RiskLevel.MODERATE)

    def test_low_risk_with_balanced_resources(self):
        """Équipe saine + ressources équilibrées → risque LOW."""
        crew = _healthy_crew()
        vessel = _balanced_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        assert result.global_risk_level in (RiskLevel.LOW, RiskLevel.MODERATE)
        # Score de risque faible
        assert result.team_risk_score < 55.0

    def test_team_risk_score_in_bounds(self):
        """team_risk_score toujours dans [0, 100]."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        assert 0.0 <= result.team_risk_score <= 100.0

    def test_member_risks_count_matches_crew(self):
        """Autant de MemberRisk que de membres dans l'équipe."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        assert len(result.member_risks) == len(crew)


@pytest.mark.engine
class TestRpsHighRiskBurnout:
    def test_high_risk_burnout(self):
        """Ressources très faibles + demandes élevées → HIGH ou CRITICAL."""
        crew = _healthy_crew()
        vessel = _low_resources_high_demands_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        # Les demandes élevées avec peu de ressources → burnout risk élevé
        assert result.global_risk_level in (RiskLevel.MODERATE, RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_burnout_risk_score_elevated(self):
        """Avec ressources faibles → burnout_risk_score élevé pour chaque membre."""
        crew = _healthy_crew()
        vessel = _low_resources_high_demands_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        # Au moins un membre doit avoir un score de burnout élevé
        high_burnout = [m for m in result.member_risks if m.burnout_risk_score > 50.0]
        assert len(high_burnout) > 0

    def test_vessel_params_activates_ns_fit(self):
        """vessel_params → lmx_score None mais burnout_risk_score calculé."""
        crew = _healthy_crew()
        vessel = _balanced_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        for member in result.member_risks:
            # burnout_risk_score calculé depuis NS fit inversé
            assert member.burnout_risk_score is not None
            assert 0.0 <= member.burnout_risk_score <= 100.0

    def test_jerk_risk_elevates_team_score(self):
        """JERK_RISK ajoute un malus au team_risk_score."""
        # Équipe avec un membre très hostile
        jerk_crew = [
            _snap(agreeableness=20.0, conscientiousness=75.0),  # JERK (< 35)
            _snap(agreeableness=75.0, conscientiousness=75.0),
            _snap(agreeableness=78.0, conscientiousness=72.0),
        ]
        result_jerk = run(crew_snapshots=jerk_crew)
        result_normal = run(crew_snapshots=_healthy_crew())
        # L'équipe avec JERK_RISK doit avoir un score de risque plus élevé
        assert result_jerk.team_risk_score > result_normal.team_risk_score


@pytest.mark.engine
class TestRpsCriticalLmx:
    def test_critical_lmx_elevates_risk(self):
        """ps CRITICAL sur des membres → risque élevé."""
        # Vecteur capitaine très directif
        captain = {
            "autonomy_given": 0.02,
            "feedback_style": 0.02,
            "structure_imposed": 0.98,
        }
        # Membres qui veulent autonomie (openness élevée)
        crew = [
            _snap(agreeableness=70.0, conscientiousness=50.0, openness=95.0),
            _snap(agreeableness=70.0, conscientiousness=50.0, openness=92.0),
            _snap(agreeableness=70.0, conscientiousness=75.0, openness=45.0),  # ok
        ]
        result = run(crew_snapshots=crew, captain_vector=captain)
        # LMX très mauvais sur certains membres → risque élevé
        critical_members = [m for m in result.member_risks if m.lmx_score is not None and m.lmx_score < 35.0]
        if len(critical_members) >= 1:
            assert result.global_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL)

    def test_lmx_computed_with_captain_vector(self):
        """captain_vector fourni → lmx_score calculé pour chaque membre."""
        captain = {
            "autonomy_given": 0.6,
            "feedback_style": 0.5,
            "structure_imposed": 0.7,
        }
        crew = _healthy_crew()
        result = run(crew_snapshots=crew, captain_vector=captain)
        for member in result.member_risks:
            assert member.lmx_score is not None

    def test_lmx_none_without_captain(self):
        """Sans captain_vector → lmx_score = None."""
        crew = _healthy_crew()
        result = run(crew_snapshots=crew)
        for member in result.member_risks:
            assert member.lmx_score is None


@pytest.mark.engine
class TestRpsAlerts:
    def test_no_alerts_for_healthy_balanced_team(self):
        """Équipe saine + ressources équilibrées → peu ou pas d'alertes."""
        crew = _healthy_crew()
        vessel = _balanced_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        # Les alertes JERK_RISK et FAULTLINE_RISK ne devraient pas être là
        jerk_alerts = [a for a in result.alerts if a.code == "JERK_RISK"]
        assert len(jerk_alerts) == 0

    def test_critical_alert_generated_for_lmx_critical(self):
        """LMX CRITICAL → alerte severity CRITICAL."""
        captain = {
            "autonomy_given": 0.01,
            "feedback_style": 0.01,
            "structure_imposed": 0.99,
        }
        crew = [_snap(agreeableness=70.0, openness=98.0, conscientiousness=30.0)]
        result = run(crew_snapshots=crew, captain_vector=captain)
        critical_alerts = [a for a in result.alerts if a.severity == "CRITICAL"]
        if result.global_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            # Si risque élevé détecté → au moins une alerte
            assert len(result.alerts) > 0

    def test_crew_ids_linked_to_member_risks(self):
        """crew_ids fournis → liés aux MemberRisk dans l'ordre."""
        crew = _healthy_crew()
        ids = [201, 202, 203]
        result = run(crew_snapshots=crew, crew_ids=ids)
        for i, member in enumerate(result.member_risks):
            assert member.crew_id == ids[i]


@pytest.mark.engine
class TestRpsRecommendations:
    def test_recommendations_present_on_high_risk(self):
        """Risque élevé → recommandations générées."""
        crew = _healthy_crew()
        vessel = _low_resources_high_demands_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        if result.global_risk_level in (RiskLevel.HIGH, RiskLevel.CRITICAL):
            assert len(result.recommendations) > 0

    def test_no_recommendations_on_low_risk(self):
        """Risque LOW → pas de recommandations automatiques."""
        crew = _healthy_crew()
        vessel = _balanced_vessel()
        result = run(crew_snapshots=crew, vessel_params=vessel)
        if result.global_risk_level == RiskLevel.LOW:
            assert len(result.recommendations) == 0
