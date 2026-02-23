# tests/modules/crew/test_service.py
"""
Tests unitaires pour modules.crew.service.CrewService

Couverture :
    assign_member() :
        - Employer n'est pas propriétaire → PermissionError
        - Marin déjà actif sur le yacht → ValueError
        - Succès → retourne l'assignment

    remove_member() :
        - Employer n'est pas propriétaire → PermissionError
        - Membre introuvable → KeyError
        - Succès → deactivate_assignment appelé

    submit_daily_pulse() :
        - Pas d'assignation active → ValueError "NO_ACTIVE_ASSIGNMENT"
        - Pulse déjà soumis aujourd'hui → ValueError "ALREADY_SUBMITTED_TODAY"
        - Succès → retourne le pulse créé

    get_full_dashboard() :
        - Employer n'est pas propriétaire → retourne None
        - Équipage < 2 membres → _empty_dashboard
        - Succès → retourne dict avec harmony_metrics, weather_trend, full_diagnosis

    _compute_weather_trend() :
        - Pulses vides → no_data
        - Moyenne ≥ 4.5 → "excellent"
        - Moyenne < 2.5 → "critical"
"""
import pytest
from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from app.modules.crew.service import CrewService, _to_harmony_metrics
from tests.conftest import (
    make_crew_profile, make_employer_profile, make_crew_assignment,
    make_daily_pulse, make_yacht, snapshot_full
)

pytestmark = pytest.mark.service

service = CrewService()


def _snap():
    return snapshot_full()


def _pulse(score: float = 4.0, days_ago: int = 0):
    from datetime import datetime, timedelta
    p = make_daily_pulse(score=score)
    p.created_at = datetime.utcnow() - timedelta(days=days_ago)
    return p


# ── assign_member() ────────────────────────────────────────────────────────────

class TestAssignMember:
    @pytest.mark.asyncio
    async def test_employer_pas_proprietaire_leve_permission_error(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile(id=99)
        mocker.patch(
            "app.modules.crew.service.vessel_repo.is_owner",
            AsyncMock(return_value=False),
        )
        with pytest.raises(PermissionError):
            await service.assign_member(db, yacht_id=1, payload=MagicMock(), employer=employer)

    @pytest.mark.asyncio
    async def test_marin_deja_actif_leve_value_error(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile(id=1)
        existing = make_crew_assignment(is_active=True)

        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=True))
        mocker.patch("app.modules.crew.service.crew_repo.get_assignment", AsyncMock(return_value=existing))

        payload = MagicMock()
        payload.crew_profile_id = 1

        with pytest.raises(ValueError, match="déjà assigné"):
            await service.assign_member(db, yacht_id=1, payload=payload, employer=employer)

    @pytest.mark.asyncio
    async def test_succes_retourne_assignment(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile(id=1)
        new_assignment = make_crew_assignment()

        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=True))
        mocker.patch("app.modules.crew.service.crew_repo.get_assignment", AsyncMock(return_value=None))
        mocker.patch("app.modules.crew.service.crew_repo.create_assignment", AsyncMock(return_value=new_assignment))
        mocker.patch("app.modules.crew.service.vessel_repo.get_crew_snapshots", AsyncMock(return_value=[_snap(), _snap()]))
        mocker.patch("app.modules.crew.service.vessel_repo.update_vessel_snapshot", AsyncMock())

        payload = MagicMock()
        payload.crew_profile_id = 1

        result = await service.assign_member(db, yacht_id=1, payload=payload, employer=employer)
        assert result == new_assignment


# ── remove_member() ────────────────────────────────────────────────────────────

class TestRemoveMember:
    @pytest.mark.asyncio
    async def test_employer_pas_proprietaire(self, mocker):
        db = AsyncMock()
        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=False))

        with pytest.raises(PermissionError):
            await service.remove_member(db, yacht_id=1, crew_profile_id=1, employer=make_employer_profile())

    @pytest.mark.asyncio
    async def test_membre_introuvable_leve_key_error(self, mocker):
        db = AsyncMock()
        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=True))
        mocker.patch("app.modules.crew.service.crew_repo.deactivate_assignment", AsyncMock(return_value=False))

        with pytest.raises(KeyError):
            await service.remove_member(db, yacht_id=1, crew_profile_id=99, employer=make_employer_profile())

    @pytest.mark.asyncio
    async def test_succes_appelle_deactivate(self, mocker):
        db = AsyncMock()
        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=True))
        mock_deactivate = mocker.patch(
            "app.modules.crew.service.crew_repo.deactivate_assignment",
            AsyncMock(return_value=True),
        )
        mocker.patch("app.modules.crew.service.vessel_repo.get_crew_snapshots", AsyncMock(return_value=[]))

        await service.remove_member(db, yacht_id=1, crew_profile_id=1, employer=make_employer_profile())
        mock_deactivate.assert_called_once_with(db, 1, 1)


# ── submit_daily_pulse() ──────────────────────────────────────────────────────

class TestSubmitDailyPulse:
    @pytest.mark.asyncio
    async def test_pas_assignation_active(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        mocker.patch("app.modules.crew.service.crew_repo.get_active_assignment", AsyncMock(return_value=None))

        with pytest.raises(ValueError, match="NO_ACTIVE_ASSIGNMENT"):
            await service.submit_daily_pulse(db, crew, MagicMock(score=4, comment=None))

    @pytest.mark.asyncio
    async def test_pulse_deja_soumis(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        assignment = make_crew_assignment()

        mocker.patch("app.modules.crew.service.crew_repo.get_active_assignment", AsyncMock(return_value=assignment))
        mocker.patch("app.modules.crew.service.crew_repo.has_pulse_today", AsyncMock(return_value=True))

        with pytest.raises(ValueError, match="ALREADY_SUBMITTED_TODAY"):
            await service.submit_daily_pulse(db, crew, MagicMock(score=4, comment=None))

    @pytest.mark.asyncio
    async def test_succes_retourne_pulse(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        assignment = make_crew_assignment(yacht_id=5)
        pulse = make_daily_pulse(score=4)

        mocker.patch("app.modules.crew.service.crew_repo.get_active_assignment", AsyncMock(return_value=assignment))
        mocker.patch("app.modules.crew.service.crew_repo.has_pulse_today", AsyncMock(return_value=False))
        mocker.patch("app.modules.crew.service.crew_repo.create_pulse", AsyncMock(return_value=pulse))

        result = await service.submit_daily_pulse(db, crew, MagicMock(score=4, comment=None))
        assert result == pulse


# ── get_full_dashboard() ──────────────────────────────────────────────────────

class TestGetFullDashboard:
    @pytest.mark.asyncio
    async def test_employer_pas_proprietaire_retourne_none(self, mocker):
        db = AsyncMock()
        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=False))

        result = await service.get_full_dashboard(db, yacht_id=1, employer=make_employer_profile())
        assert result is None

    @pytest.mark.asyncio
    async def test_equipage_insuffisant_retourne_empty(self, mocker):
        db = AsyncMock()
        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=True))
        mocker.patch("app.modules.crew.service.vessel_repo.get_vessel_snapshot", AsyncMock(return_value=None))
        mocker.patch("app.modules.crew.service.vessel_repo.get_crew_snapshots", AsyncMock(return_value=[_snap()]))
        mocker.patch("app.modules.crew.service.crew_repo.get_recent_pulse_data", AsyncMock(return_value=[]))

        result = await service.get_full_dashboard(db, yacht_id=1, employer=make_employer_profile())
        assert result is not None
        assert result["yacht_id"] == 1

    @pytest.mark.asyncio
    async def test_succes_retourne_dashboard_complet(self, mocker):
        db = AsyncMock()
        pulses = [_pulse(score=4.0, days_ago=i) for i in range(5)]
        harmony_metrics = {
            "performance": 65.0,
            "cohesion": 60.0,
            "risk_factors": {"conscientiousness_divergence": 10.0, "weakest_link_stability": 55.0},
        }

        mocker.patch("app.modules.crew.service.vessel_repo.is_owner", AsyncMock(return_value=True))
        mocker.patch("app.modules.crew.service.vessel_repo.get_vessel_snapshot", AsyncMock(
            return_value={"harmony_result": harmony_metrics}
        ))
        mocker.patch("app.modules.crew.service.crew_repo.get_recent_pulse_data", AsyncMock(return_value=pulses))

        result = await service.get_full_dashboard(db, yacht_id=1, employer=make_employer_profile())

        assert "yacht_id" in result
        assert "harmony_metrics" in result
        assert "weather_trend" in result
        assert "full_diagnosis" in result


# ── _compute_weather_trend() ──────────────────────────────────────────────────

class TestComputeWeatherTrend:
    def test_pulses_vides_retourne_no_data(self):
        result = service._compute_weather_trend([])
        assert result["status"] == "no_data"
        assert result["response_count"] == 0

    def test_pulses_excellent(self):
        pulses = [_pulse(score=5.0) for _ in range(3)]
        result = service._compute_weather_trend(pulses)
        assert result["status"] == "excellent"

    def test_pulses_critical(self):
        pulses = [_pulse(score=2.0) for _ in range(3)]
        result = service._compute_weather_trend(pulses)
        assert result["status"] == "critical"

    def test_retourne_champs_requis(self):
        pulses = [_pulse(score=3.5)]
        result = service._compute_weather_trend(pulses)
        for key in ("average", "std", "response_count", "days_observed", "status"):
            assert key in result, f"Clé manquante : {key}"
