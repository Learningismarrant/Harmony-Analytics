# tests/modules/calibration/test_repository.py
"""
Tests du repository calibration avec DB mockée (pattern AsyncMock).

Ces tests vérifient que le repository effectue les bonnes opérations DB.
Pas de vraie connexion PostgreSQL — on mocke l'AsyncSession.

Couverture :
    create_calibrator     : crée et retourne un CalibratorUser
    get_calibrator_by_email : existant → retour, inconnu → None
    create_session        : crée et retourne un CalibSession
    save_responses        : insère les réponses et retourne le compte
    count_responses_for_session : compte les réponses d'une session
    get_session           : retourne une session ou None
    get_session_for_calibrator : retourne la session par (calibrator, catalogue) ou None
"""
from __future__ import annotations

import pytest
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

from app.modules.calibration.repository import CalibrationRepository
from app.modules.calibration.schemas import ResponseItemIn
from app.shared.models.Calibration import CalibratorUser
from app.shared.models.Assessment import TestSession, TestResponse

pytestmark = pytest.mark.service  # pas de marqueur "db" — tests unitaires via mock

repo = CalibrationRepository()


def _make_mock_execute_result(return_value):
    """
    Simule le résultat d'un db.execute() qui retourne une valeur unique.
    """
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = return_value
    mock_result.scalars.return_value.all.return_value = (
        return_value if isinstance(return_value, list) else [return_value] if return_value else []
    )
    return mock_result


# ── create_calibrator ─────────────────────────────────────────────────────────

class TestCreateCalibrator:
    @pytest.mark.asyncio
    async def test_create_calibrator(self, mocker):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        created_obj = SimpleNamespace(
            id=1,
            email="alice@test.com",
            name="Alice",
            hashed_password="$2b$...",
            cohort="ENSM 2026",
            is_active=True,
        )
        db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", 1))

        # On patche CalibratorUser pour retourner notre objet
        with patch("app.modules.calibration.repository.CalibratorUser") as MockClass:
            MockClass.return_value = created_obj
            result = await repo.create_calibrator(
                db,
                email="alice@test.com",
                name="Alice",
                hashed_password="$2b$...",
                cohort="ENSM 2026",
            )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result == created_obj


# ── get_calibrator_by_email ───────────────────────────────────────────────────

class TestGetCalibratorByEmail:
    @pytest.mark.asyncio
    async def test_existing_calibrator(self, mocker):
        db = AsyncMock()
        existing = SimpleNamespace(id=1, email="alice@test.com", name="Alice")
        db.execute = AsyncMock(return_value=_make_mock_execute_result(existing))

        result = await repo.get_calibrator_by_email(db, "alice@test.com")
        assert result == existing

    @pytest.mark.asyncio
    async def test_unknown_email_returns_none(self, mocker):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_mock_execute_result(None))

        result = await repo.get_calibrator_by_email(db, "unknown@test.com")
        assert result is None


# ── create_session ────────────────────────────────────────────────────────────

class TestCreateSession:
    @pytest.mark.asyncio
    async def test_create_session(self, mocker):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        session_obj = SimpleNamespace(
            id=1,
            calibrator_id=1,
            catalogue_id=1,
            started_at=datetime(2026, 3, 1),
            completed_at=None,
            device_info={"platform": "web"},
        )
        db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, "id", 1))

        with patch("app.modules.calibration.repository.TestSession") as MockClass:
            MockClass.return_value = session_obj
            result = await repo.create_session(
                db,
                calibrator_id=1,
                catalogue_id=1,
                device_info={"platform": "web"},
            )

        db.add.assert_called_once()
        db.commit.assert_called_once()
        assert result == session_obj


# ── save_responses ────────────────────────────────────────────────────────────

class TestSaveResponses:
    @pytest.mark.asyncio
    async def test_save_responses_returns_count(self, mocker):
        db = AsyncMock()
        db.add = MagicMock()
        db.commit = AsyncMock()

        responses = [
            ResponseItemIn(question_id=i + 1, response_value="3", seconds_spent=5.0)
            for i in range(5)
        ]

        with patch("app.modules.calibration.repository.TestResponse") as MockClass:
            MockClass.side_effect = lambda **kwargs: SimpleNamespace(**kwargs)
            count = await repo.save_responses(db, session_id=1, catalogue_id=1, responses=responses)

        assert count == 5
        assert db.add.call_count == 5
        db.commit.assert_called_once()


# ── count_responses_for_session ───────────────────────────────────────────────

class TestCountResponsesForSession:
    @pytest.mark.asyncio
    async def test_count_responses(self, mocker):
        db = AsyncMock()
        # 3 réponses dans la liste
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [
            SimpleNamespace(id=1),
            SimpleNamespace(id=2),
            SimpleNamespace(id=3),
        ]
        db.execute = AsyncMock(return_value=mock_result)

        count = await repo.count_responses_for_session(db, session_id=1)
        assert count == 3


# ── get_session ───────────────────────────────────────────────────────────────

class TestGetSession:
    @pytest.mark.asyncio
    async def test_get_existing_session(self, mocker):
        db = AsyncMock()
        session = SimpleNamespace(id=1, calibrator_id=1, catalogue_id=1)
        db.execute = AsyncMock(return_value=_make_mock_execute_result(session))

        result = await repo.get_session(db, session_id=1)
        assert result == session

    @pytest.mark.asyncio
    async def test_get_unknown_session_returns_none(self, mocker):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_mock_execute_result(None))

        result = await repo.get_session(db, session_id=99)
        assert result is None


# ── get_session_for_calibrator ────────────────────────────────────────────────

class TestGetSessionForCalibrator:
    @pytest.mark.asyncio
    async def test_get_existing_session_for_calibrator(self, mocker):
        db = AsyncMock()
        session = SimpleNamespace(id=1, calibrator_id=1, catalogue_id=1)
        db.execute = AsyncMock(return_value=_make_mock_execute_result(session))

        result = await repo.get_session_for_calibrator(db, calibrator_id=1, catalogue_id=1)
        assert result == session

    @pytest.mark.asyncio
    async def test_no_session_for_calibrator_returns_none(self, mocker):
        db = AsyncMock()
        db.execute = AsyncMock(return_value=_make_mock_execute_result(None))

        result = await repo.get_session_for_calibrator(db, calibrator_id=1, catalogue_id=99)
        assert result is None
