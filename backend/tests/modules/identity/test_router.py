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

pytestmark = pytest.mark.router


def _identity():
    """UserIdentityOut — champs obligatoires : id, name, email, is_harmony_verified, is_active, created_at."""
    return {
        "id": 1,
        "name": "Jean Marin",
        "email": "j@test.com",
        "phone": None,
        "avatar_url": None,
        "location": None,
        "is_harmony_verified": False,
        "is_active": True,
        "created_at": "2025-01-01T00:00:00",
    }


def _full_profile():
    """FullCrewProfileOut — context + identity + crew + experiences + documents + reports."""
    return {
        "context": {
            "view_mode": "candidate",
            "label": "Mon profil",
            "context_position": None,
            "is_active_crew": False,
        },
        "identity": _identity(),
        "crew": {
            "id": 1,
            "user_id": 1,
            "position_targeted": "Deckhand",
            "experience_years": 2,
            "availability_status": "available",
        },
        "experiences": [],
        "documents": [],
        "reports": [],
    }


def _experience():
    """ExperienceOut — yacht_name (str), role (str), start_date (datetime), is_harmony_approved."""
    return {
        "id": 1,
        "yacht_name": "Lady Aurora",
        "role": "bosun",
        "start_date": "2024-01-01T00:00:00",
        "end_date": None,
        "is_harmony_approved": False,
        "reference_comment": None,
        "candidate_comment": None,
        "contract_type": None,
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
    assert "context" in data


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
    # PATCH /me calls update_identity then get_identity — mock both
    mocker.patch(
        "app.modules.identity.router.service.update_identity",
        AsyncMock(return_value=None),
    )
    mocker.patch(
        "app.modules.identity.router.service.get_identity",
        AsyncMock(return_value=_identity()),
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
        "external_yacht_name": "Lady Aurora",
        "role": "Bosun",
        "start_date": "2024-01-01",
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
