# tests/modules/calibration/test_router.py
"""
Tests HTTP pour modules.calibration.router

Couverture :
    POST /calibration/auth/register → 201 succès, 409 email dupliqué
    POST /calibration/auth/login    → 200 succès, 401 mauvais mot de passe
    GET  /calibration/catalogues    → 401 sans auth, 200 avec auth
    GET  /calibration/catalogues/{id}/questions → 200 succès
    GET  /calibration/me            → 200 succès, 401 sans auth
    PATCH /calibration/me           → 200 succès, 422 payload invalide
    POST /calibration/sessions      → 201 succès
    GET  /calibration/sessions      → 200 liste
    POST /calibration/sessions/{id}/responses → 201 succès, 403 mauvaise session
"""
from __future__ import annotations

import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock

from fastapi import HTTPException
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.database import get_db
from app.modules.calibration.deps import get_current_calibrator
from app.modules.calibration.schemas import (
    CalibratorTokenOut,
    CalibratorMeOut,
    CatalogueInfoOut,
    QuestionOut,
    SessionOut,
    SubmitResponsesOut,
    TraitScoreOut,
    SessionScoreOut,
)

pytestmark = pytest.mark.router


# ── Factories locales ─────────────────────────────────────────────────────────

def _token_out() -> CalibratorTokenOut:
    return CalibratorTokenOut(
        access_token="eyJfake.token.here",
        token_type="bearer",
        calibrator_id=1,
        name="Alice",
    )


def _catalogue_out() -> CatalogueInfoOut:
    return CatalogueInfoOut(
        id=1,
        name="IPIP-50",
        description="Big Five",
        test_type="likert",
        n_questions=50,
        status="ALPHA",
        license="PUBLIC_DOMAIN",
        domain="personality",
    )


def _question_out(q_id: int = 1) -> QuestionOut:
    return QuestionOut(
        id=q_id,
        order=q_id,
        text="Je me fais facilement des amis.",
        question_type="likert",
        trait="agreeableness",
        options=None,
        reverse=False,
    )


def _session_out() -> SessionOut:
    return SessionOut(
        id=1,
        calibrator_id=1,
        catalogue_id=1,
        started_at=datetime(2026, 3, 1, 10, 0),
        completed_at=None,
    )


def _mock_calibrator() -> SimpleNamespace:
    return SimpleNamespace(
        id=1,
        email="alice@test.com",
        name="Alice",
        is_active=True,
    )


def _me_out(**kwargs) -> CalibratorMeOut:
    defaults = dict(
        id=1,
        email="alice@test.com",
        name="Alice",
        cohort="ENSM 2026",
        gender=None,
        birth_year=None,
        education_level=None,
        native_language=None,
        years_at_sea=None,
        maritime_role=None,
        nationality=None,
        created_at=datetime(2026, 1, 1),
    )
    defaults.update(kwargs)
    return CalibratorMeOut(**defaults)


# ── Fixture client non authentifié ────────────────────────────────────────────

@pytest.fixture
async def client():
    """Client sans auth calibrateur."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from unittest.mock import AsyncMock as AM
    mock_db = AM(spec=AsyncSession)
    app.dependency_overrides[get_db] = lambda: mock_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


@pytest.fixture
async def calib_client():
    """Client authentifié comme calibrateur."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from unittest.mock import AsyncMock as AM
    mock_db = AM(spec=AsyncSession)
    mock_calib = _mock_calibrator()
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_current_calibrator] = lambda: mock_calib
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()


# ── POST /calibration/auth/register ──────────────────────────────────────────

class TestRegisterEndpoint:
    @pytest.mark.asyncio
    async def test_register_success(self, client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.register",
            AsyncMock(return_value=_token_out()),
        )
        resp = await client.post(
            "/calibration/auth/register",
            json={
                "email": "alice@test.com",
                "name": "Alice",
                "password": "securepassword",
                "cohort": "ENSM 2026",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["calibrator_id"] == 1
        assert data["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_returns_409(self, client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.register",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=409,
                    detail={"error": True, "message": "Email dupliqué", "code": "EMAIL_ALREADY_EXISTS"},
                )
            ),
        )
        resp = await client.post(
            "/calibration/auth/register",
            json={"email": "alice@test.com", "name": "Alice", "password": "securepassword"},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_register_invalid_payload_returns_422(self, client):
        resp = await client.post(
            "/calibration/auth/register",
            json={"email": "not-an-email", "name": "A", "password": "short"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_register_missing_fields_returns_422(self, client):
        resp = await client.post("/calibration/auth/register", json={})
        assert resp.status_code == 422


# ── POST /calibration/auth/login ──────────────────────────────────────────────

class TestLoginEndpoint:
    @pytest.mark.asyncio
    async def test_login_success(self, client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.login",
            AsyncMock(return_value=_token_out()),
        )
        resp = await client.post(
            "/calibration/auth/login",
            json={"email": "alice@test.com", "password": "securepassword"},
        )
        assert resp.status_code == 200
        assert resp.json()["access_token"] != ""

    @pytest.mark.asyncio
    async def test_login_wrong_password_returns_401(self, client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.login",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=401,
                    detail={"error": True, "message": "Mauvais mdp", "code": "INVALID_CREDENTIALS"},
                )
            ),
        )
        resp = await client.post(
            "/calibration/auth/login",
            json={"email": "alice@test.com", "password": "wrongpassword"},
        )
        assert resp.status_code == 401


# ── GET /calibration/catalogues ───────────────────────────────────────────────

class TestListCataloguesEndpoint:
    @pytest.mark.asyncio
    async def test_list_catalogues_unauthorized_returns_401(self, client):
        """Sans token → 401 ou 403 selon l'implémentation HTTPBearer."""
        resp = await client.get("/calibration/catalogues")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_catalogues_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.list_catalogues",
            AsyncMock(return_value=[_catalogue_out()]),
        )
        resp = await calib_client.get("/calibration/catalogues")
        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert data[0]["id"] == 1


# ── GET /calibration/catalogues/{id}/questions ───────────────────────────────

class TestGetQuestionsEndpoint:
    @pytest.mark.asyncio
    async def test_get_questions_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.get_questions",
            AsyncMock(return_value=[_question_out(1), _question_out(2)]),
        )
        resp = await calib_client.get("/calibration/catalogues/1/questions")
        assert resp.status_code == 200
        assert len(resp.json()) == 2

    @pytest.mark.asyncio
    async def test_get_questions_not_found_returns_404(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.get_questions",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=404,
                    detail={"error": True, "message": "Catalogue introuvable", "code": "CATALOGUE_NOT_FOUND"},
                )
            ),
        )
        resp = await calib_client.get("/calibration/catalogues/99/questions")
        assert resp.status_code == 404


# ── POST /calibration/sessions ────────────────────────────────────────────────

class TestStartSessionEndpoint:
    @pytest.mark.asyncio
    async def test_start_session_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.start_session",
            AsyncMock(return_value=_session_out()),
        )
        resp = await calib_client.post(
            "/calibration/sessions",
            json={"catalogue_id": 1},
        )
        assert resp.status_code == 201
        assert resp.json()["catalogue_id"] == 1

    @pytest.mark.asyncio
    async def test_start_session_already_completed_returns_409(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.start_session",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=409,
                    detail={"error": True, "message": "Déjà passé", "code": "SESSION_ALREADY_COMPLETED"},
                )
            ),
        )
        resp = await calib_client.post(
            "/calibration/sessions",
            json={"catalogue_id": 1},
        )
        assert resp.status_code == 409

    @pytest.mark.asyncio
    async def test_start_session_invalid_payload_returns_422(self, calib_client):
        resp = await calib_client.post("/calibration/sessions", json={"catalogue_id": -1})
        assert resp.status_code == 422


# ── GET /calibration/sessions ─────────────────────────────────────────────────

class TestListSessionsEndpoint:
    @pytest.mark.asyncio
    async def test_list_sessions_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.list_sessions",
            AsyncMock(return_value=[_session_out()]),
        )
        resp = await calib_client.get("/calibration/sessions")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)


# ── POST /calibration/sessions/{id}/responses ────────────────────────────────

class TestSubmitResponsesEndpoint:
    @pytest.mark.asyncio
    async def test_submit_responses_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.submit_responses",
            AsyncMock(
                return_value=SubmitResponsesOut(session_id=1, n_responses=5, completed=False)
            ),
        )
        resp = await calib_client.post(
            "/calibration/sessions/1/responses",
            json={
                "responses": [
                    {"question_id": i + 1, "response_value": "3"} for i in range(5)
                ]
            },
        )
        assert resp.status_code == 201
        assert resp.json()["n_responses"] == 5

    @pytest.mark.asyncio
    async def test_submit_responses_wrong_session_returns_403(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.submit_responses",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail={"error": True, "message": "Session tierce", "code": "SESSION_FORBIDDEN"},
                )
            ),
        )
        resp = await calib_client.post(
            "/calibration/sessions/99/responses",
            json={"responses": [{"question_id": 1, "response_value": "3"}]},
        )
        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_submit_responses_invalid_value_returns_422(self, calib_client):
        """response_value vide (min_length=1) → 422."""
        resp = await calib_client.post(
            "/calibration/sessions/1/responses",
            json={"responses": [{"question_id": 1, "response_value": ""}]},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_submit_responses_empty_list_returns_422(self, calib_client):
        resp = await calib_client.post(
            "/calibration/sessions/1/responses",
            json={"responses": []},
        )
        assert resp.status_code == 422


# ── GET /calibration/me ───────────────────────────────────────────────────────

class TestGetMeEndpoint:
    @pytest.mark.asyncio
    async def test_get_me_unauthorized_returns_401_or_403(self, client):
        resp = await client.get("/calibration/me")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_me_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.get_me",
            AsyncMock(return_value=_me_out(birth_year=1990, years_at_sea=3)),
        )
        resp = await calib_client.get("/calibration/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["name"] == "Alice"
        assert data["birth_year"] == 1990
        assert data["years_at_sea"] == 3


# ── PATCH /calibration/me ────────────────────────────────────────────────────

class TestUpdateDemographicsEndpoint:
    @pytest.mark.asyncio
    async def test_update_demographics_success(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.update_demographics",
            AsyncMock(
                return_value=_me_out(gender="female", birth_year=1992, maritime_role="officer")
            ),
        )
        resp = await calib_client.patch(
            "/calibration/me",
            json={"gender": "female", "birth_year": 1992, "maritime_role": "officer"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["gender"] == "female"
        assert data["birth_year"] == 1992
        assert data["maritime_role"] == "officer"

    @pytest.mark.asyncio
    async def test_update_demographics_invalid_gender_returns_422(self, calib_client):
        resp = await calib_client.patch(
            "/calibration/me",
            json={"gender": "unknown_value"},
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_demographics_invalid_birth_year_returns_422(self, calib_client):
        """birth_year hors plage [1940, 2010] → 422."""
        resp = await calib_client.patch(
            "/calibration/me",
            json={"birth_year": 1800},
        )
        assert resp.status_code == 422


# ── GET /calibration/sessions/{id}/score ─────────────────────────────────────

def _session_score_out() -> SessionScoreOut:
    return SessionScoreOut(
        session_id=1,
        catalogue_id=1,
        catalogue_name="LMX-7",
        test_type="likert",
        overall_score=72.5,
        traits=[
            TraitScoreOut(
                trait="agreeableness",
                label="Agréabilité",
                raw_mean=3.625,
                score=72.5,
                n_items=8,
            )
        ],
        n_responses=8,
    )


class TestGetScoreEndpoint:
    @pytest.mark.asyncio
    async def test_get_score_success(self, calib_client, mocker):
        """Session complétée → 200 avec le score CTT."""
        mocker.patch(
            "app.modules.calibration.router.service.get_session_score",
            AsyncMock(return_value=_session_score_out()),
        )
        resp = await calib_client.get("/calibration/sessions/1/score")
        assert resp.status_code == 200
        data = resp.json()
        assert data["session_id"] == 1
        assert data["overall_score"] == 72.5
        assert len(data["traits"]) == 1
        assert data["traits"][0]["trait"] == "agreeableness"
        assert data["n_responses"] == 8

    @pytest.mark.asyncio
    async def test_get_score_unauthorized_returns_401_or_403(self, client):
        """Sans token → 401/403."""
        resp = await client.get("/calibration/sessions/1/score")
        assert resp.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_get_score_session_not_found_returns_404(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.get_session_score",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=404,
                    detail={"error": True, "message": "Session introuvable.", "code": "SESSION_NOT_FOUND"},
                )
            ),
        )
        resp = await calib_client.get("/calibration/sessions/99/score")
        assert resp.status_code == 404
        assert resp.json()["detail"]["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_get_score_wrong_calibrator_returns_403(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.get_session_score",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=403,
                    detail={"error": True, "message": "Session tierce.", "code": "SESSION_FORBIDDEN"},
                )
            ),
        )
        resp = await calib_client.get("/calibration/sessions/5/score")
        assert resp.status_code == 403
        assert resp.json()["detail"]["code"] == "SESSION_FORBIDDEN"

    @pytest.mark.asyncio
    async def test_get_score_not_completed_returns_400(self, calib_client, mocker):
        mocker.patch(
            "app.modules.calibration.router.service.get_session_score",
            AsyncMock(
                side_effect=HTTPException(
                    status_code=400,
                    detail={
                        "error": True,
                        "message": "La session n'est pas encore terminée.",
                        "code": "SESSION_NOT_COMPLETED",
                    },
                )
            ),
        )
        resp = await calib_client.get("/calibration/sessions/2/score")
        assert resp.status_code == 400
        assert resp.json()["detail"]["code"] == "SESSION_NOT_COMPLETED"

    @pytest.mark.asyncio
    async def test_get_score_invalid_session_id_returns_422(self, calib_client):
        """session_id=0 est hors plage (gt=0) → 422."""
        resp = await calib_client.get("/calibration/sessions/0/score")
        assert resp.status_code == 422
