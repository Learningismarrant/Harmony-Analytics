# tests/modules/crew/test_router.py
"""
Tests HTTP pour modules.crew.router

Couverture :
    GET  /crew/me/assignment         → 200 (crew) ou 401 sans auth
    GET  /crew/{yacht_id}/members    → 200 liste (employer)
    GET  /crew/{yacht_id}/members    sans auth → 401
    POST /crew/{yacht_id}/members    → 201 (employer)
    POST /crew/{yacht_id}/members    accès refusé → 403
    DELETE /crew/{yacht_id}/members/{id} → 204
    GET  /crew/{yacht_id}/dashboard  → 200 (employer)
    GET  /crew/{yacht_id}/dashboard  non trouvé → 404
    POST /crew/pulse                 → 201 (crew)
    POST /crew/pulse                 doublon → 409
    GET  /crew/pulse/history         → 200 liste
"""
import pytest
from unittest.mock import AsyncMock

from tests.conftest import make_crew_assignment, make_daily_pulse

pytestmark = pytest.mark.router


def _assignment():
    return make_crew_assignment(id=1, yacht_id=1)


def _pulse():
    return make_daily_pulse(id=1, score=4)


# ── GET /crew/me/assignment ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_my_assignment_200(crew_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.get_active_assignment",
        AsyncMock(return_value=_assignment()),
    )
    resp = await crew_client.get("/crew/me/assignment")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_get_my_assignment_sans_auth_401(client):
    resp = await client.get("/crew/me/assignment")
    assert resp.status_code in (401, 403)


# ── GET /crew/{yacht_id}/members ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_list_crew_200(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.get_active_crew",
        AsyncMock(return_value=[_assignment()]),
    )
    resp = await employer_client.get("/crew/1/members")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_list_crew_yacht_non_trouve_404(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.get_active_crew",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.get("/crew/999/members")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_list_crew_sans_auth_401(client):
    resp = await client.get("/crew/1/members")
    assert resp.status_code in (401, 403)


# ── POST /crew/{yacht_id}/members ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_crew_member_201(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.assign_member",
        AsyncMock(return_value=_assignment()),
    )
    resp = await employer_client.post("/crew/1/members", json={"crew_profile_id": 1})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_add_crew_member_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.assign_member",
        AsyncMock(side_effect=PermissionError("Accès refusé.")),
    )
    resp = await employer_client.post("/crew/1/members", json={"crew_profile_id": 1})
    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_add_crew_member_deja_assigne_400(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.assign_member",
        AsyncMock(side_effect=ValueError("Ce marin est déjà assigné à ce yacht.")),
    )
    resp = await employer_client.post("/crew/1/members", json={"crew_profile_id": 1})
    assert resp.status_code == 400


# ── DELETE /crew/{yacht_id}/members/{crew_profile_id} ─────────────────────────

@pytest.mark.asyncio
async def test_remove_crew_member_204(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.remove_member",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.delete("/crew/1/members/1")
    assert resp.status_code == 204


@pytest.mark.asyncio
async def test_remove_crew_member_introuvable_404(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.remove_member",
        AsyncMock(side_effect=KeyError("Membre introuvable.")),
    )
    resp = await employer_client.delete("/crew/1/members/99")
    assert resp.status_code == 404


# ── GET /crew/{yacht_id}/dashboard ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_dashboard_200(employer_client, mocker):
    dashboard = {
        "yacht_id": 1,
        "harmony_metrics": {
            "performance": 65.0, "cohesion": 60.0,
            "risk_factors": {"conscientiousness_divergence": 10.0, "weakest_link_stability": 55.0},
        },
        "weather_trend": {"average": 4.0, "status": "stable", "response_count": 5, "std": 0.3, "days_observed": 5},
        "full_diagnosis": {
            "crew_type": "FUNCTIONAL CREW", "risk_level": "low",
            "volatility_index": 20.0, "hidden_conflict": 15.0,
            "short_term_prediction": "Stable.", "recommended_action": "Maintenir.",
            "early_warning": "Aucune alerte.",
        },
    }
    mocker.patch(
        "app.modules.crew.router.service.get_full_dashboard",
        AsyncMock(return_value=dashboard),
    )
    resp = await employer_client.get("/crew/1/dashboard")
    assert resp.status_code == 200
    data = resp.json()
    assert "harmony_metrics" in data
    assert "weather_trend" in data


@pytest.mark.asyncio
async def test_dashboard_non_trouve_404(employer_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.get_full_dashboard",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.get("/crew/999/dashboard")
    assert resp.status_code == 404


# ── POST /crew/pulse ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_pulse_201(crew_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.submit_daily_pulse",
        AsyncMock(return_value=_pulse()),
    )
    resp = await crew_client.post("/crew/pulse", json={"score": 4, "comment": None})
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_submit_pulse_doublon_409(crew_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.submit_daily_pulse",
        AsyncMock(side_effect=ValueError("ALREADY_SUBMITTED_TODAY")),
    )
    resp = await crew_client.post("/crew/pulse", json={"score": 4, "comment": None})
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_submit_pulse_sans_assignation_403(crew_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.submit_daily_pulse",
        AsyncMock(side_effect=ValueError("NO_ACTIVE_ASSIGNMENT")),
    )
    resp = await crew_client.post("/crew/pulse", json={"score": 3, "comment": None})
    assert resp.status_code == 403


# ── GET /crew/pulse/history ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pulse_history_200(crew_client, mocker):
    mocker.patch(
        "app.modules.crew.router.service.get_pulse_history",
        AsyncMock(return_value=[_pulse()]),
    )
    resp = await crew_client.get("/crew/pulse/history")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)
