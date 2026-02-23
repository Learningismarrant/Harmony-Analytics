# tests/modules/identity/test_router.py
"""
Tests HTTP pour modules.identity.router

Couverture :
    GET  /identity/candidate/{id}            → 200 (UserDep) ou 403 accès refusé
    GET  /identity/candidate/{id}/identity   → 200 ou 403
    PATCH /identity/me                       → 200 (crew)
    POST  /identity/me/experiences           → 201 (crew)
    GET  /identity/candidate/{id}/reports    → 200 ou 403
"""
import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

pytestmark = pytest.mark.router


def _full_profile():
    return {
        "crew_profile_id": 1,
        "view_mode": "candidate",
        "context_label": "Mon profil",
        "is_active_crew": False,
        "identity": {
            "crew_profile_id": 1, "user_id": 1,
            "name": "Jean Marin", "email": "j@test.com",
            "avatar_url": None, "location": None,
            "phone": None, "bio": None,
            "is_harmony_verified": False,
            "position_targeted": "Deckhand",
            "availability_status": "available",
            "experience_years": 2,
            "nationality": None, "languages": [],
        },
        "experiences": [],
        "documents": [],
        "reports": {"has_data": False, "view_mode": "candidate", "message": "Aucun test."},
    }


def _identity():
    return {
        "crew_profile_id": 1, "user_id": 1,
        "name": "Jean Marin", "email": "j@test.com",
        "avatar_url": None, "location": None,
        "phone": None, "bio": None,
        "is_harmony_verified": False,
        "position_targeted": "Deckhand",
        "availability_status": "available",
        "experience_years": 2,
        "nationality": None, "languages": [],
    }


def _experience():
    return {
        "id": 1, "yacht_id": None, "role": "Deckhand",
        "start_date": "2024-01-01", "end_date": None,
        "is_active": True, "is_harmony_approved": False,
        "reference_comment": None,
    }


# ── GET /identity/candidate/{crew_profile_id} ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_full_profile_200(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.get_full_profile",
        AsyncMock(return_value=_full_profile()),
    )
    resp = await crew_client.get("/identity/candidate/1")
    assert resp.status_code == 200
    data = resp.json()
    assert "identity" in data


@pytest.mark.asyncio
async def test_get_full_profile_acces_refuse_403(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.get_full_profile",
        AsyncMock(return_value=None),
    )
    resp = await crew_client.get("/identity/candidate/99")
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_get_full_profile_sans_auth_401(client):
    resp = await client.get("/identity/candidate/1")
    assert resp.status_code in (401, 403)


# ── GET /identity/candidate/{id}/identity ────────────────────────────────────

@pytest.mark.asyncio
async def test_get_identity_200(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.get_identity",
        AsyncMock(return_value=_identity()),
    )
    resp = await crew_client.get("/identity/candidate/1/identity")
    assert resp.status_code == 200
    assert "name" in resp.json()


@pytest.mark.asyncio
async def test_get_identity_acces_refuse_403(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.get_identity",
        AsyncMock(return_value=None),
    )
    resp = await crew_client.get("/identity/candidate/99/identity")
    assert resp.status_code == 403


# ── PATCH /identity/me ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_patch_identity_me_200(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.update_identity",
        AsyncMock(return_value=None),
    )
    resp = await crew_client.patch("/identity/me", json={"name": "New Name"})
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_patch_identity_sans_auth_401(client):
    resp = await client.patch("/identity/me", json={"name": "X"})
    assert resp.status_code in (401, 403)


# ── POST /identity/me/experiences ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_experience_201(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.add_experience",
        AsyncMock(return_value=_experience()),
    )
    resp = await crew_client.post("/identity/me/experiences", json={
        "yacht_id": None,
        "role": "Deckhand",
        "start_date": "2024-01-01",
        "is_active": True,
    })
    assert resp.status_code == 201


# ── GET /identity/candidate/{id}/reports ─────────────────────────────────────

@pytest.mark.asyncio
async def test_get_reports_200(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.get_reports",
        AsyncMock(return_value={"has_data": False, "view_mode": "candidate"}),
    )
    resp = await crew_client.get("/identity/candidate/1/reports")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_reports_acces_refuse_403(crew_client, mocker):
    mocker.patch(
        "app.modules.identity.router.service.get_reports",
        AsyncMock(return_value=None),
    )
    resp = await crew_client.get("/identity/candidate/99/reports")
    assert resp.status_code == 403
