# tests/modules/calibration/test_service.py
"""
Tests unitaires pour modules.calibration.service.CalibrationService

Couverture :
    register()   : succès, email dupliqué → 409
    login()      : succès, mauvais mot de passe → 401
    get_me()     : succès, calibrateur introuvable → 404
    update_demographics() : succès, calibrateur introuvable → 404
    list_catalogues() : délègue au repo
    get_questions()   : succès, catalogue inexistant → 404
    start_session()   : succès, session déjà complétée → 409
    submit_responses(): succès, session tierce → 403, session complétée → 409
"""
from __future__ import annotations

import pytest
from types import SimpleNamespace
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

from app.modules.calibration.service import CalibrationService
from app.modules.calibration.schemas import (
    CalibratorRegisterIn,
    CalibratorLoginIn,
    CalibratorDemographicsIn,
    StartSessionIn,
    SubmitResponsesIn,
    ResponseItemIn,
    SessionScoreOut,
)

pytestmark = pytest.mark.service

service = CalibrationService()


# ── Factories ─────────────────────────────────────────────────────────────────

def make_calibrator(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "email": "calibrator@test.com",
        "name": "Alice",
        "hashed_password": "$2b$12$fakehashfakehash",
        "cohort": "ENSM Nantes 2026-03",
        "is_active": True,
        "created_at": datetime(2026, 1, 1),
        "gender": None,
        "birth_year": None,
        "education_level": None,
        "native_language": None,
        "years_at_sea": None,
        "maritime_role": None,
        "nationality": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_catalogue(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "name": "IPIP-50",
        "description": "Big Five 50 items",
        "test_type": "likert",
        "n_questions": 50,
        "status": "ALPHA",
        "license": "PUBLIC_DOMAIN",
        "is_active": True,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_session(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "calibrator_id": 1,
        "catalogue_id": 1,
        "started_at": datetime(2026, 3, 1, 10, 0),
        "completed_at": None,
        "device_info": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


def make_question(**kwargs) -> SimpleNamespace:
    defaults = {
        "id": 1,
        "test_id": 1,
        "text": "Je me fais facilement des amis.",
        "question_type": "likert",
        "options": None,
        "trait": "agreeableness",
        "reverse": False,
        "order": 1,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── register ──────────────────────────────────────────────────────────────────

class TestRegister:
    @pytest.mark.asyncio
    async def test_register_ok(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_email",
            AsyncMock(return_value=None),
        )
        mock_created = make_calibrator(id=5, name="Bob")
        mocker.patch(
            "app.modules.calibration.service.repo.create_calibrator",
            AsyncMock(return_value=mock_created),
        )

        payload = CalibratorRegisterIn(
            email="bob@test.com",
            name="Bob",
            password="securepassword",
            cohort="ENSM 2026",
        )
        result = await service.register(db, payload)
        assert result.calibrator_id == 5
        assert result.name == "Bob"
        assert result.access_token != ""
        assert result.token_type == "bearer"

    @pytest.mark.asyncio
    async def test_register_duplicate_email_raises_409(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_email",
            AsyncMock(return_value=make_calibrator()),
        )
        payload = CalibratorRegisterIn(
            email="calibrator@test.com",
            name="Alice",
            password="securepassword",
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.register(db, payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "EMAIL_ALREADY_EXISTS"


# ── login ─────────────────────────────────────────────────────────────────────

class TestLogin:
    @pytest.mark.asyncio
    async def test_login_ok(self, mocker):
        db = AsyncMock()
        calibrator = make_calibrator()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_email",
            AsyncMock(return_value=calibrator),
        )
        mocker.patch(
            "app.modules.calibration.service.verify_password",
            return_value=True,
        )
        payload = CalibratorLoginIn(email="calibrator@test.com", password="password123")
        result = await service.login(db, payload)
        assert result.calibrator_id == 1
        assert result.name == "Alice"

    @pytest.mark.asyncio
    async def test_login_bad_password_raises_401(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_email",
            AsyncMock(return_value=make_calibrator()),
        )
        mocker.patch(
            "app.modules.calibration.service.verify_password",
            return_value=False,
        )
        payload = CalibratorLoginIn(email="calibrator@test.com", password="wrongpassword")
        with pytest.raises(HTTPException) as exc_info:
            await service.login(db, payload)
        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "INVALID_CREDENTIALS"

    @pytest.mark.asyncio
    async def test_login_unknown_email_raises_401(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_email",
            AsyncMock(return_value=None),
        )
        payload = CalibratorLoginIn(email="unknown@test.com", password="any")
        with pytest.raises(HTTPException) as exc_info:
            await service.login(db, payload)
        assert exc_info.value.status_code == 401


# ── list_catalogues ───────────────────────────────────────────────────────────

class TestListCatalogues:
    @pytest.mark.asyncio
    async def test_returns_catalogues(self, mocker):
        db = AsyncMock()
        catalogues = [make_catalogue(id=1), make_catalogue(id=2)]
        mocker.patch(
            "app.modules.calibration.service.repo.get_all_catalogues",
            AsyncMock(return_value=catalogues),
        )
        result = await service.list_catalogues(db)
        assert len(result) == 2
        assert result[0].id == 1


# ── get_questions ─────────────────────────────────────────────────────────────

class TestGetQuestions:
    @pytest.mark.asyncio
    async def test_returns_questions(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue()),
        )
        questions = [make_question(id=i + 1, order=i + 1) for i in range(5)]
        mocker.patch(
            "app.modules.calibration.service.repo.get_questions_for_catalogue",
            AsyncMock(return_value=questions),
        )
        result = await service.get_questions(db, catalogue_id=1)
        assert len(result) == 5

    @pytest.mark.asyncio
    async def test_catalogue_not_found_raises_404(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=None),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.get_questions(db, catalogue_id=99)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "CATALOGUE_NOT_FOUND"


# ── start_session ─────────────────────────────────────────────────────────────

class TestStartSession:
    @pytest.mark.asyncio
    async def test_start_session_ok(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue()),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session_for_calibrator",
            AsyncMock(return_value=None),
        )
        new_session = make_session()
        mocker.patch(
            "app.modules.calibration.service.repo.create_session",
            AsyncMock(return_value=new_session),
        )
        payload = StartSessionIn(catalogue_id=1)
        result = await service.start_session(db, calibrator_id=1, data=payload)
        assert result.id == 1
        assert result.catalogue_id == 1

    @pytest.mark.asyncio
    async def test_start_session_already_completed_raises_409(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue()),
        )
        completed_session = make_session(
            completed_at=datetime(2026, 2, 1, tzinfo=timezone.utc)
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session_for_calibrator",
            AsyncMock(return_value=completed_session),
        )
        payload = StartSessionIn(catalogue_id=1)
        with pytest.raises(HTTPException) as exc_info:
            await service.start_session(db, calibrator_id=1, data=payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "SESSION_ALREADY_COMPLETED"

    @pytest.mark.asyncio
    async def test_start_session_resumes_in_progress(self, mocker):
        """Si une session existe mais n'est pas complétée, elle est retournée."""
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue()),
        )
        in_progress = make_session(id=7, completed_at=None)
        mocker.patch(
            "app.modules.calibration.service.repo.get_session_for_calibrator",
            AsyncMock(return_value=in_progress),
        )
        payload = StartSessionIn(catalogue_id=1)
        result = await service.start_session(db, calibrator_id=1, data=payload)
        assert result.id == 7


# ── submit_responses ──────────────────────────────────────────────────────────

class TestSubmitResponses:
    @pytest.mark.asyncio
    async def test_submit_ok_not_completed(self, mocker):
        db = AsyncMock()
        session = make_session(id=1, calibrator_id=1, catalogue_id=1)
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.save_responses",
            AsyncMock(return_value=10),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(n_questions=50)),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.count_responses_for_session",
            AsyncMock(return_value=10),   # 10 < 50 → pas complétée
        )
        payload = SubmitResponsesIn(
            responses=[ResponseItemIn(question_id=i + 1, value=3) for i in range(10)]
        )
        result = await service.submit_responses(db, calibrator_id=1, session_id=1, data=payload)
        assert result.n_responses == 10
        assert result.completed is False

    @pytest.mark.asyncio
    async def test_submit_auto_completes(self, mocker):
        db = AsyncMock()
        session = make_session(id=1, calibrator_id=1, catalogue_id=1)
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.save_responses",
            AsyncMock(return_value=50),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(n_questions=50)),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.count_responses_for_session",
            AsyncMock(return_value=50),   # 50 == 50 → complétée
        )
        mocker.patch(
            "app.modules.calibration.service.repo.complete_session",
            AsyncMock(return_value=make_session(completed_at=datetime.now(timezone.utc))),
        )
        payload = SubmitResponsesIn(
            responses=[ResponseItemIn(question_id=i + 1, value=3) for i in range(50)]
        )
        result = await service.submit_responses(db, calibrator_id=1, session_id=1, data=payload)
        assert result.completed is True

    @pytest.mark.asyncio
    async def test_submit_wrong_session_raises_403(self, mocker):
        db = AsyncMock()
        # Session appartient au calibrateur 99, pas 1
        session = make_session(id=1, calibrator_id=99)
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=session),
        )
        payload = SubmitResponsesIn(
            responses=[ResponseItemIn(question_id=1, value=3)]
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.submit_responses(db, calibrator_id=1, session_id=1, data=payload)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "SESSION_FORBIDDEN"

    @pytest.mark.asyncio
    async def test_submit_completed_session_raises_409(self, mocker):
        db = AsyncMock()
        session = make_session(
            id=1, calibrator_id=1,
            completed_at=datetime(2026, 2, 1, tzinfo=timezone.utc),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=session),
        )
        payload = SubmitResponsesIn(
            responses=[ResponseItemIn(question_id=1, value=3)]
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.submit_responses(db, calibrator_id=1, session_id=1, data=payload)
        assert exc_info.value.status_code == 409
        assert exc_info.value.detail["code"] == "SESSION_ALREADY_COMPLETED"


# ── get_me ────────────────────────────────────────────────────────────────────

class TestGetMe:
    @pytest.mark.asyncio
    async def test_get_me_ok(self, mocker):
        db = AsyncMock()
        calibrator = make_calibrator(id=1, name="Alice", birth_year=1990, years_at_sea=5)
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_id",
            AsyncMock(return_value=calibrator),
        )
        result = await service.get_me(db, calibrator_id=1)
        assert result.id == 1
        assert result.name == "Alice"
        assert result.birth_year == 1990
        assert result.years_at_sea == 5

    @pytest.mark.asyncio
    async def test_get_me_not_found_raises_404(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_id",
            AsyncMock(return_value=None),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.get_me(db, calibrator_id=99)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "CALIBRATOR_NOT_FOUND"


# ── update_demographics ───────────────────────────────────────────────────────

class TestUpdateDemographics:
    @pytest.mark.asyncio
    async def test_update_demographics_ok(self, mocker):
        db = AsyncMock()
        calibrator = make_calibrator()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_id",
            AsyncMock(return_value=calibrator),
        )
        updated = make_calibrator(gender="female", birth_year=1992, maritime_role="officer")
        mocker.patch(
            "app.modules.calibration.service.repo.update_demographics",
            AsyncMock(return_value=updated),
        )
        payload = CalibratorDemographicsIn(
            gender="female",
            birth_year=1992,
            maritime_role="officer",
        )
        result = await service.update_demographics(db, calibrator_id=1, data=payload)
        assert result.gender == "female"
        assert result.birth_year == 1992
        assert result.maritime_role == "officer"

    @pytest.mark.asyncio
    async def test_update_demographics_not_found_raises_404(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_calibrator_by_id",
            AsyncMock(return_value=None),
        )
        payload = CalibratorDemographicsIn(gender="male")
        with pytest.raises(HTTPException) as exc_info:
            await service.update_demographics(db, calibrator_id=99, data=payload)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "CALIBRATOR_NOT_FOUND"


# ── get_session_score ──────────────────────────────────────────────────────────

def make_response_with_question(
    resp_id: int,
    value: int,
    question_id: int,
    trait: str = "agreeableness",
    question_type: str = "likert",
    reverse: bool = False,
    options: list | None = None,
    correct_answer: str | None = None,
) -> SimpleNamespace:
    """Crée une CalibResponse simulée avec sa question embedded."""
    question = SimpleNamespace(
        id=question_id,
        trait=trait,
        question_type=question_type,
        reverse=reverse,
        options=options,
        correct_answer=correct_answer,
    )
    return SimpleNamespace(
        id=resp_id,
        session_id=1,
        question_id=question_id,
        value=value,
        question=question,
    )


class TestGetSessionScore:
    @pytest.mark.asyncio
    async def test_score_ok_likert(self, mocker):
        """Session complétée avec réponses Likert — vérifie le score normalisé."""
        db = AsyncMock()
        completed_session = make_session(
            id=1, calibrator_id=1, catalogue_id=1,
            completed_at=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=completed_session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(max_score_per_question=5)),
        )
        # 3 réponses Likert pour le même trait, valeurs 3, 4, 5 → mean=4.0 / 5 → 80%
        responses = [
            make_response_with_question(1, 3, 1, trait="agreeableness"),
            make_response_with_question(2, 4, 2, trait="agreeableness"),
            make_response_with_question(3, 5, 3, trait="agreeableness"),
        ]
        mocker.patch(
            "app.modules.calibration.service.repo.get_responses_with_questions",
            AsyncMock(return_value=responses),
        )
        result = await service.get_session_score(db, calibrator_id=1, session_id=1)
        assert isinstance(result, SessionScoreOut)
        assert result.session_id == 1
        assert result.n_responses == 3
        assert len(result.traits) == 1
        trait = result.traits[0]
        assert trait.trait == "agreeableness"
        assert trait.n_items == 3
        assert abs(trait.raw_mean - 4.0) < 0.01
        assert abs(trait.score - 80.0) < 0.01
        assert abs(result.overall_score - 80.0) < 0.01

    @pytest.mark.asyncio
    async def test_score_ok_reverse_item(self, mocker):
        """Item reverse : score = max_val - value."""
        db = AsyncMock()
        completed_session = make_session(
            id=1, calibrator_id=1, catalogue_id=1,
            completed_at=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=completed_session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(max_score_per_question=5)),
        )
        # value=1, reverse=True → scored as 5-1=4 → mean=4.0/5=80%
        responses = [
            make_response_with_question(1, 1, 1, trait="neuroticism", reverse=True),
        ]
        mocker.patch(
            "app.modules.calibration.service.repo.get_responses_with_questions",
            AsyncMock(return_value=responses),
        )
        result = await service.get_session_score(db, calibrator_id=1, session_id=1)
        trait = result.traits[0]
        assert abs(trait.raw_mean - 4.0) < 0.01
        assert abs(trait.score - 80.0) < 0.01

    @pytest.mark.asyncio
    async def test_score_ok_qcm_correct(self, mocker):
        """QCM — bonne réponse → score=100."""
        db = AsyncMock()
        completed_session = make_session(
            id=1, calibrator_id=1, catalogue_id=1,
            completed_at=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=completed_session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(max_score_per_question=1)),
        )
        # options = [{"key":"A"}, {"key":"B"}, {"key":"C"}]
        # correct_answer = "B" → index 1, response.value=1 → correct
        options = [{"key": "A"}, {"key": "B"}, {"key": "C"}]
        responses = [
            make_response_with_question(
                1, 1, 1,
                trait="fluid_intelligence",
                question_type="qcm",
                options=options,
                correct_answer="B",
            ),
        ]
        mocker.patch(
            "app.modules.calibration.service.repo.get_responses_with_questions",
            AsyncMock(return_value=responses),
        )
        result = await service.get_session_score(db, calibrator_id=1, session_id=1)
        trait = result.traits[0]
        assert abs(trait.score - 100.0) < 0.01

    @pytest.mark.asyncio
    async def test_score_ok_qcm_wrong(self, mocker):
        """QCM — mauvaise réponse → score=0."""
        db = AsyncMock()
        completed_session = make_session(
            id=1, calibrator_id=1, catalogue_id=1,
            completed_at=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=completed_session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(max_score_per_question=1)),
        )
        options = [{"key": "A"}, {"key": "B"}, {"key": "C"}]
        responses = [
            make_response_with_question(
                1, 2, 1,
                trait="fluid_intelligence",
                question_type="qcm",
                options=options,
                correct_answer="B",  # index=1, réponse=2 → faux
            ),
        ]
        mocker.patch(
            "app.modules.calibration.service.repo.get_responses_with_questions",
            AsyncMock(return_value=responses),
        )
        result = await service.get_session_score(db, calibrator_id=1, session_id=1)
        trait = result.traits[0]
        assert abs(trait.score - 0.0) < 0.01

    @pytest.mark.asyncio
    async def test_score_session_not_found_raises_404(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=None),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.get_session_score(db, calibrator_id=1, session_id=99)
        assert exc_info.value.status_code == 404
        assert exc_info.value.detail["code"] == "SESSION_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_score_wrong_calibrator_raises_403(self, mocker):
        db = AsyncMock()
        # session appartient au calibrateur 99, pas 1
        session = make_session(calibrator_id=99, completed_at=datetime(2026, 3, 2, tzinfo=timezone.utc))
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=session),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.get_session_score(db, calibrator_id=1, session_id=1)
        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "SESSION_FORBIDDEN"

    @pytest.mark.asyncio
    async def test_score_session_not_completed_raises_400(self, mocker):
        db = AsyncMock()
        session = make_session(calibrator_id=1, completed_at=None)
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=session),
        )
        with pytest.raises(HTTPException) as exc_info:
            await service.get_session_score(db, calibrator_id=1, session_id=1)
        assert exc_info.value.status_code == 400
        assert exc_info.value.detail["code"] == "SESSION_NOT_COMPLETED"

    @pytest.mark.asyncio
    async def test_score_overall_is_mean_of_traits(self, mocker):
        """overall_score = moyenne des trait scores."""
        db = AsyncMock()
        completed_session = make_session(
            id=1, calibrator_id=1, catalogue_id=1,
            completed_at=datetime(2026, 3, 2, 10, 0, tzinfo=timezone.utc),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_session",
            AsyncMock(return_value=completed_session),
        )
        mocker.patch(
            "app.modules.calibration.service.repo.get_catalogue_by_id",
            AsyncMock(return_value=make_catalogue(max_score_per_question=5)),
        )
        # trait1 (agreeableness): value=5 → 100%
        # trait2 (neuroticism): value=0 → 0%
        # overall = 50%
        responses = [
            make_response_with_question(1, 5, 1, trait="agreeableness"),
            make_response_with_question(2, 0, 2, trait="neuroticism"),
        ]
        mocker.patch(
            "app.modules.calibration.service.repo.get_responses_with_questions",
            AsyncMock(return_value=responses),
        )
        result = await service.get_session_score(db, calibrator_id=1, session_id=1)
        assert len(result.traits) == 2
        assert abs(result.overall_score - 50.0) < 0.01
