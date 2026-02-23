# tests/modules/vessel/test_service.py
"""
Tests unitaires pour modules.vessel.service — VesselService.

Couverture :
    create               → repo.create appelé avec employer_profile_id
    get_all_for_employer → repo.get_yachts_by_employer appelé
    get_secure           → repo.get_secure appelé
    update               → succès + PermissionError (yacht introuvable)
    delete               → succès + PermissionError
    update_environment   → succès (is_owner=True) + PermissionError
    refresh_boarding_token → succès + PermissionError
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock

from app.modules.vessel.service import VesselService
from tests.conftest import (
    make_employer_profile,
    make_yacht,
    make_async_db,
)

pytestmark = pytest.mark.service

service = VesselService()


def _env_payload(**kwargs):
    """Simule un YachtEnvironmentUpdateIn."""
    defaults = {
        "charter_intensity": 0.6,
        "management_pressure": 0.4,
        "salary_index": 0.7,
        "rest_days_ratio": 0.5,
    }
    defaults.update(kwargs)
    ns = SimpleNamespace(**defaults)
    ns.model_dump = lambda exclude_unset=False: {
        k: v for k, v in defaults.items() if v is not None
    }
    return ns


def _create_payload(**kwargs):
    """Simule un YachtCreateIn."""
    defaults = {"name": "Lady Aurora", "type": "Motor", "length": 45}
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── create ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_appelle_repo(mocker):
    yacht = make_yacht()
    mock_create = mocker.patch(
        "app.modules.vessel.service.repo.create",
        AsyncMock(return_value=yacht),
    )

    employer = make_employer_profile(id=1)
    result = await service.create(db=make_async_db(), payload=_create_payload(), employer=employer)

    mock_create.assert_awaited_once()
    assert result.name == yacht.name


# ── get_all_for_employer ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_all_for_employer_appelle_repo(mocker):
    yachts = [make_yacht(id=1), make_yacht(id=2)]
    mock_list = mocker.patch(
        "app.modules.vessel.service.repo.get_yachts_by_employer",
        AsyncMock(return_value=yachts),
    )

    employer = make_employer_profile(id=1)
    result = await service.get_all_for_employer(db=make_async_db(), employer=employer)

    mock_list.assert_awaited_once_with(mock_list.await_args[0][0], 1)
    assert len(result) == 2


# ── get_secure ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_secure_retourne_yacht(mocker):
    yacht = make_yacht(id=3)
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=yacht))

    employer = make_employer_profile(id=1)
    result = await service.get_secure(db=make_async_db(), yacht_id=3, employer=employer)

    assert result.id == 3


@pytest.mark.asyncio
async def test_get_secure_retourne_none(mocker):
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=None))

    employer = make_employer_profile(id=1)
    result = await service.get_secure(db=make_async_db(), yacht_id=999, employer=employer)

    assert result is None


# ── update ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_succes(mocker):
    yacht = make_yacht()
    updated = make_yacht(name="Nouveau Nom")
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=yacht))
    mocker.patch("app.modules.vessel.service.repo.update", AsyncMock(return_value=updated))

    employer = make_employer_profile(id=1)
    result = await service.update(
        db=make_async_db(), yacht_id=1,
        payload=SimpleNamespace(name="Nouveau Nom"),
        employer=employer,
    )

    assert result.name == "Nouveau Nom"


@pytest.mark.asyncio
async def test_update_permission_error(mocker):
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=None))

    employer = make_employer_profile(id=1)
    with pytest.raises(PermissionError, match="Yacht introuvable"):
        await service.update(
            db=make_async_db(), yacht_id=99,
            payload=SimpleNamespace(name="X"),
            employer=employer,
        )


# ── delete ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_succes(mocker):
    yacht = make_yacht()
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=yacht))
    mock_delete = mocker.patch("app.modules.vessel.service.repo.delete", AsyncMock(return_value=None))

    employer = make_employer_profile(id=1)
    await service.delete(db=make_async_db(), yacht_id=1, employer=employer)

    mock_delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_delete_permission_error(mocker):
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=None))

    employer = make_employer_profile(id=1)
    with pytest.raises(PermissionError):
        await service.delete(db=make_async_db(), yacht_id=99, employer=employer)


# ── update_environment ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_environment_succes(mocker):
    yacht = make_yacht()
    mocker.patch("app.modules.vessel.service.repo.is_owner", AsyncMock(return_value=True))
    mocker.patch("app.modules.vessel.service.repo.update_environment_params", AsyncMock(return_value=yacht))
    mocker.patch("app.modules.vessel.service.repo.get_crew_snapshots", AsyncMock(return_value=[]))

    employer = make_employer_profile(id=1)
    result = await service.update_environment(
        db=make_async_db(), yacht_id=1, payload=_env_payload(), employer=employer
    )

    assert result is not None


@pytest.mark.asyncio
async def test_update_environment_permission_error(mocker):
    mocker.patch("app.modules.vessel.service.repo.is_owner", AsyncMock(return_value=False))

    employer = make_employer_profile(id=1)
    with pytest.raises(PermissionError):
        await service.update_environment(
            db=make_async_db(), yacht_id=99, payload=_env_payload(), employer=employer
        )


# ── refresh_boarding_token ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_boarding_token_succes(mocker):
    yacht = make_yacht(id=1)
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=yacht))
    mocker.patch("app.modules.vessel.service.repo.rotate_boarding_token", AsyncMock(return_value="new-token-xyz"))

    employer = make_employer_profile(id=1)
    result = await service.refresh_boarding_token(db=make_async_db(), yacht_id=1, employer=employer)

    assert result["yacht_id"] == 1
    assert result["boarding_token"] == "new-token-xyz"


@pytest.mark.asyncio
async def test_refresh_boarding_token_permission_error(mocker):
    mocker.patch("app.modules.vessel.service.repo.get_secure", AsyncMock(return_value=None))

    employer = make_employer_profile(id=1)
    with pytest.raises(PermissionError):
        await service.refresh_boarding_token(db=make_async_db(), yacht_id=99, employer=employer)
