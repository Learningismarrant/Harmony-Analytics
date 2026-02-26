# tests/modules/recruitment/test_router.py
"""
Tests HTTP pour modules.recruitment.router

Couverture :
    POST  /recruitment/campaigns        → 201 + CampaignOut
    GET   /recruitment/campaigns        → 200 liste
    DELETE /recruitment/campaigns/{id} → 204
    DELETE /recruitment/campaigns/{id} accès refusé → 403
    GET   /recruitment/campaigns/{id}/matching → 200 liste
    POST  /recruitment/apply/{token}   → 201 (crew)
"""
import pytest
from unittest.mock import AsyncMock

from tests.conftest import make_campaign

pytestmark = pytest.mark.router


def _campaign_out():
    c = make_campaign(id=1)
    return {
        "id": c.id,
        "title": c.title,
        "yacht_id": c.yacht_id,
        "status": "open",
        "is_archived": False,
        "invite_token": c.invite_token,
        "candidate_count": 0,
        "yacht_name": "Lady Aurora",
        "employer_profile_id": c.employer_profile_id,
        "position": c.position,
        "description": c.description,
        "created_at": "2025-01-01T00:00:00",
        "updated_at": "2025-01-01T00:00:00",
    }


def _match_row():
    return {
        "crew_profile_id": 1,
        "name": "Jean Marin",
        "avatar_url": None,
        "location": None,
        "experience_years": 2,
        "test_status": "completed",
        "is_pipeline_pass": True,
        "filtered_at": None,
        "profile_fit": {
            "g_fit": 72.0,
            "fit_label": "GOOD",
            "overall_centile": 68.0,
            "centile_by_competency": {},
            "safety_level": "CLEAR",
            "safety_flags": [],
        },
        "team_integration": {
            "available": True,
            "y_success": 65.0,
            "success_label": "GOOD",
            "p_ind": 70.0,
            "f_team": 60.0,
            "f_env": 55.0,
            "f_lmx": 58.0,
            "team_delta": 2.0,
            "confidence": "HIGH",
            "reason": None,
        },
        "is_hired": False,
        "is_rejected": False,
        "application_status": "pending",
        "rejected_reason": None,
    }


# ── POST /recruitment/campaigns ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_create_campaign_201(employer_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.create_campaign",
        AsyncMock(return_value=make_campaign()),
    )
    resp = await employer_client.post("/recruitment/campaigns", json={
        "title": "Deckhand Méditerranée",
        "position": "deckhand",
        "description": "Poste CDI.",
        "yacht_id": 1,
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_create_campaign_sans_auth_401(client):
    resp = await client.post("/recruitment/campaigns", json={
        "title": "Test", "position": "deckhand", "description": "Desc",
    })
    assert resp.status_code in (401, 403)


# ── GET /recruitment/campaigns ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_campaigns_200(employer_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.get_my_campaigns",
        AsyncMock(return_value=[make_campaign()]),
    )
    resp = await employer_client.get("/recruitment/campaigns")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


# ── DELETE /recruitment/campaigns/{id} ────────────────────────────────────────

@pytest.mark.asyncio
async def test_archive_campaign_204(employer_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.archive_campaign",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.delete("/recruitment/campaigns/1")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_archive_campaign_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.archive_campaign",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.delete("/recruitment/campaigns/99")
    assert resp.status_code == 403


# ── GET /recruitment/campaigns/{id}/matching ─────────────────────────────────

@pytest.mark.asyncio
async def test_get_matching_200(employer_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.get_matching",
        AsyncMock(return_value=[_match_row()]),
    )
    resp = await employer_client.get("/recruitment/campaigns/1/matching")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_matching_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.get_matching",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.get("/recruitment/campaigns/99/matching")
    assert resp.status_code == 403


# ── POST /recruitment/apply/{invite_token} ────────────────────────────────────

@pytest.mark.asyncio
async def test_apply_to_campaign_201(crew_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.apply_to_campaign",
        AsyncMock(return_value={"message": "Candidature enregistrée.", "campaign_id": 1, "application_id": 10}),
    )
    resp = await crew_client.post("/recruitment/apply/invite-abc123")
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_apply_campaign_token_invalide_400(crew_client, mocker):
    mocker.patch(
        "app.modules.recruitment.router.service.apply_to_campaign",
        AsyncMock(side_effect=ValueError("CAMPAIGN_NOT_FOUND_OR_CLOSED")),
    )
    resp = await crew_client.post("/recruitment/apply/bad-token")
    assert resp.status_code == 400
