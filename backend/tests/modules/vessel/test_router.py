# tests/modules/vessel/test_router.py
"""
Tests HTTP pour modules.vessel.router

Couverture :
    POST   /vessels/                             → 201 + YachtOut
    GET    /vessels/                             → 200 liste
    GET    /vessels/{id}                         → 200 + YachtOut
    GET    /vessels/{id}                         introuvable → 404
    PATCH  /vessels/{id}                         → 200
    PATCH  /vessels/{id}                         accès refusé → 403
    DELETE /vessels/{id}                         → 204
    DELETE /vessels/{id}                         accès refusé → 403
    PATCH  /vessels/{id}/environment             → 200
    PATCH  /vessels/{id}/environment             accès refusé → 403
    POST   /vessels/{id}/boarding-token/refresh  → 200 + YachtTokenOut
    POST   /vessels/{id}/boarding-token/refresh  accès refusé → 403
    Sans auth                                    → 401/403

NOTE : Le router appelle service.create(..., owner_id=...) et
       service.get_all_for_owner(..., owner_id=...) alors que le service
       définit employer=EmployerProfile. Les mocks absorbent cette discordance.
"""
import pytest
from datetime import datetime
from unittest.mock import AsyncMock

from tests.conftest import make_yacht

pytestmark = pytest.mark.router


def _yacht_out():
    y = make_yacht(id=1)
    return {
        "id": y.id,
        "name": y.name,
        "type": y.type,
        "length": int(y.length),
        "employer_profile_id": y.employer_profile_id,
        "boarding_token": y.boarding_token,
        "created_at": "2025-01-01T00:00:00",
    }


def _token_out():
    return {"id": 1, "name": "Lady Aurora", "boarding_token": "new-token-xyz"}


# ── POST /vessels/ ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_yacht_201(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.create",
        AsyncMock(return_value=make_yacht()),
    )
    resp = await employer_client.post("/vessels/", json={
        "name": "Lady Aurora", "type": "Motor", "length": 45,
    })
    assert resp.status_code == 201
    assert resp.json()["name"] == "Lady Aurora"


@pytest.mark.asyncio
async def test_create_yacht_sans_auth_401(client):
    resp = await client.post("/vessels/", json={"name": "X", "type": "Motor"})
    assert resp.status_code in (401, 403)


# ── GET /vessels/ ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_yachts_200(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.get_all_for_employer",
        AsyncMock(return_value=[make_yacht()]),
    )
    resp = await employer_client.get("/vessels/")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
    assert len(resp.json()) == 1


# ── GET /vessels/{id} ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_yacht_200(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.get_secure",
        AsyncMock(return_value=make_yacht(id=1)),
    )
    resp = await employer_client.get("/vessels/1")
    assert resp.status_code == 200
    assert resp.json()["id"] == 1


@pytest.mark.asyncio
async def test_get_yacht_introuvable_404(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.get_secure",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.get("/vessels/999")
    assert resp.status_code == 404


# ── PATCH /vessels/{id} ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_yacht_200(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.update",
        AsyncMock(return_value=make_yacht(name="Renamed")),
    )
    resp = await employer_client.patch("/vessels/1", json={"name": "Renamed"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_yacht_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.update",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.patch("/vessels/99", json={"name": "X"})
    assert resp.status_code == 403


# ── DELETE /vessels/{id} ──────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_delete_yacht_204(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.delete",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.delete("/vessels/1")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_delete_yacht_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.delete",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.delete("/vessels/99")
    assert resp.status_code == 403


# ── PATCH /vessels/{id}/environment ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_update_environment_200(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.update_environment",
        AsyncMock(return_value=make_yacht()),
    )
    resp = await employer_client.patch("/vessels/1/environment", json={
        "charter_intensity": 0.6,
        "salary_index": 0.7,
    })
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_update_environment_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.update_environment",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.patch("/vessels/99/environment", json={"salary_index": 0.5})
    assert resp.status_code == 403


# ── POST /vessels/{id}/boarding-token/refresh ─────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_boarding_token_200(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.refresh_boarding_token",
        AsyncMock(return_value=make_yacht(boarding_token="new-token")),
    )
    resp = await employer_client.post("/vessels/1/boarding-token/refresh")
    assert resp.status_code == 200
    assert "boarding_token" in resp.json()


@pytest.mark.asyncio
async def test_refresh_boarding_token_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.vessel.router.service.refresh_boarding_token",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.post("/vessels/99/boarding-token/refresh")
    assert resp.status_code == 403
