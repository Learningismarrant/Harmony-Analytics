# tests/modules/auth/test_router.py
"""
Tests HTTP pour modules.auth.router

Pattern : httpx.AsyncClient + mocker.patch() sur service

Couverture :
    POST /auth/register/crew   → 201 + TokenOut JSON
    POST /auth/register/crew   payload invalide → 422
    POST /auth/register/employer → 201
    POST /auth/login           → 200 + TokenOut JSON
    POST /auth/login           mauvais mot de passe → 401
    POST /auth/refresh         → 200 + AccessTokenOut
    GET  /auth/me              sans token → 401
    GET  /auth/me              avec token (dependency override) → 200
"""
import pytest
from unittest.mock import AsyncMock
from types import SimpleNamespace

from app.modules.auth.schemas import TokenOut, AccessTokenOut
from app.shared.enums import UserRole
from tests.conftest import make_user

pytestmark = pytest.mark.router


def _token_out() -> SimpleNamespace:
    return SimpleNamespace(
        access_token="access_abc",
        refresh_token="refresh_xyz",
        token_type="bearer",
        role=UserRole.CANDIDATE,
        user_id=1,
        profile_id=1,
        model_dump=lambda: {
            "access_token": "access_abc",
            "refresh_token": "refresh_xyz",
            "token_type": "bearer",
            "role": "CANDIDATE",
            "user_id": 1,
            "profile_id": 1,
        },
    )


# ── POST /auth/register/crew ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_crew_201(client, mocker):
    """Inscription marin valide → 201 + champs TokenOut."""
    mock_token = TokenOut(
        access_token="acc", refresh_token="ref",
        role=UserRole.CANDIDATE, user_id=1, profile_id=1,
    )
    mocker.patch(
        "app.modules.auth.router.service.register_crew",
        AsyncMock(return_value=mock_token),
    )
    resp = await client.post("/auth/register/crew", json={
        "email": "crew@test.com",
        "password": "secret123",
        "name": "Test Crew",
        "position_targeted": "Deckhand",
        "experience_years": 2,
    })
    assert resp.status_code == 201
    data = resp.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["role"] == "candidate"


@pytest.mark.asyncio
async def test_register_crew_payload_invalide_422(client):
    """Payload manquant champs obligatoires → 422."""
    resp = await client.post("/auth/register/crew", json={
        "email": "not_valid_email",
        # password manquant
        "name": "A",  # trop court
    })
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_register_crew_email_duplique_409(client, mocker):
    """Email déjà utilisé → 409."""
    from fastapi import HTTPException
    mocker.patch(
        "app.modules.auth.router.service.register_crew",
        AsyncMock(side_effect=HTTPException(status_code=409, detail="Email déjà utilisé")),
    )
    resp = await client.post("/auth/register/crew", json={
        "email": "taken@test.com",
        "password": "secret123",
        "name": "Taken User",
        "position_targeted": "Deckhand",
        "experience_years": 0,
    })
    assert resp.status_code == 409


# ── POST /auth/register/employer ──────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_employer_201(client, mocker):
    mock_token = TokenOut(
        access_token="acc", refresh_token="ref",
        role=UserRole.CLIENT, user_id=2, profile_id=1,
    )
    mocker.patch(
        "app.modules.auth.router.service.register_employer",
        AsyncMock(return_value=mock_token),
    )
    resp = await client.post("/auth/register/employer", json={
        "email": "employer@test.com",
        "password": "secret123",
        "name": "Eric Owner",
        "company_name": "Sea Ventures",
    })
    assert resp.status_code == 201
    assert resp.json()["role"] == "client"


# ── POST /auth/login ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_login_200(client, mocker):
    mock_token = TokenOut(
        access_token="acc", refresh_token="ref",
        role=UserRole.CANDIDATE, user_id=1, profile_id=1,
    )
    mocker.patch(
        "app.modules.auth.router.service.login",
        AsyncMock(return_value=mock_token),
    )
    resp = await client.post("/auth/login", json={
        "email": "user@test.com",
        "password": "secret123",
    })
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "acc"


@pytest.mark.asyncio
async def test_login_401_mauvais_password(client, mocker):
    from fastapi import HTTPException
    mocker.patch(
        "app.modules.auth.router.service.login",
        AsyncMock(side_effect=HTTPException(status_code=401, detail="Identifiants incorrects")),
    )
    resp = await client.post("/auth/login", json={
        "email": "user@test.com",
        "password": "wrong_password",
    })
    assert resp.status_code == 401


# ── POST /auth/refresh ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_refresh_200(client, mocker):
    mocker.patch(
        "app.modules.auth.router.service.refresh",
        AsyncMock(return_value={"access_token": "new_acc", "token_type": "bearer"}),
    )
    resp = await client.post("/auth/refresh", json={"refresh_token": "valid_refresh"})
    assert resp.status_code == 200
    assert resp.json()["access_token"] == "new_acc"


# ── GET /auth/me ──────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_me_sans_token_401(client):
    """Sans override de dépendance auth → 401 (bearer token manquant)."""
    # Note : le client fixture override get_db mais PAS get_current_user
    # Donc l'endpoint /auth/me doit retourner 401/403
    resp = await client.get("/auth/me")
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_me_avec_auth_200(crew_client):
    """Avec dependency override crew → 200 + champs utilisateur."""
    resp = await crew_client.get("/auth/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "id" in data
    assert "email" in data
    assert "role" in data
