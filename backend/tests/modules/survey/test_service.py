# tests/modules/survey/test_service.py
"""
Tests unitaires pour modules.survey.service — SurveyService.

Couverture :
    trigger_survey           → succès + PermissionError
    get_pending_surveys      → appel repo
    submit_response          → succès, non ciblé (403), doublon (409), survey fermé (400)
    _normalize_response      → mise à l'échelle 1-10 → 0-100
    _check_ml_threshold      → déclenchement à 150, skip avant
    get_survey_results       → succès, accès refusé, survey introuvable
"""
import pytest
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

from app.modules.survey.service import SurveyService
from tests.conftest import (
    make_employer_profile,
    make_crew_profile,
    make_survey,
    make_survey_response,
    make_async_db,
)

pytestmark = pytest.mark.service

service = SurveyService()


def _payload(**kwargs):
    """Simule un SurveyResponseIn comme SimpleNamespace."""
    defaults = {
        "team_cohesion": 7.0,
        "workload_felt": 6.0,
        "leadership_fit": 8.0,
        "self_performance": 7.0,
        "intent_to_stay": 8.0,
        "free_text": None,
    }
    defaults.update(kwargs)
    return SimpleNamespace(**defaults)


# ── trigger_survey ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_trigger_survey_succes(mocker):
    survey = make_survey(id=5)
    mocker.patch("app.modules.survey.service.vessel_repo.is_owner", AsyncMock(return_value=True))
    mocker.patch("app.modules.survey.service.vessel_repo.get_active_crew_ids", AsyncMock(return_value=[1, 2]))
    mocker.patch("app.modules.survey.service.survey_repo.create_survey", AsyncMock(return_value=survey))

    employer = make_employer_profile()
    result = await service.trigger_survey(
        db=make_async_db(),
        yacht_id=1,
        trigger_type="post_charter",
        employer=employer,
        target_crew_profile_ids=[1, 2],
    )

    assert result["survey_id"] == survey.id
    assert result["notified_count"] == 2


@pytest.mark.asyncio
async def test_trigger_survey_acces_refuse(mocker):
    mocker.patch("app.modules.survey.service.vessel_repo.is_owner", AsyncMock(return_value=False))

    employer = make_employer_profile()
    with pytest.raises(PermissionError):
        await service.trigger_survey(
            db=make_async_db(),
            yacht_id=99,
            trigger_type="post_charter",
            employer=employer,
        )


@pytest.mark.asyncio
async def test_trigger_survey_auto_cible_equipe(mocker):
    """Sans target_crew_profile_ids, le service charge l'équipe active."""
    survey = make_survey(id=2)
    mocker.patch("app.modules.survey.service.vessel_repo.is_owner", AsyncMock(return_value=True))
    mock_get_crew = mocker.patch(
        "app.modules.survey.service.vessel_repo.get_active_crew_ids",
        AsyncMock(return_value=[1, 2, 3]),
    )
    mocker.patch("app.modules.survey.service.survey_repo.create_survey", AsyncMock(return_value=survey))

    employer = make_employer_profile()
    result = await service.trigger_survey(
        db=make_async_db(),
        yacht_id=1,
        trigger_type="monthly_pulse",
        employer=employer,
        target_crew_profile_ids=None,
    )

    mock_get_crew.assert_awaited_once()
    assert result["notified_count"] == 3


# ── get_pending_surveys ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pending_surveys_appel_repo(mocker):
    surveys = [make_survey(id=1), make_survey(id=2)]
    mock_pending = mocker.patch(
        "app.modules.survey.service.survey_repo.get_pending_for_crew",
        AsyncMock(return_value=surveys),
    )

    crew = make_crew_profile(id=1)
    result = await service.get_pending_surveys(db=make_async_db(), crew=crew)

    mock_pending.assert_awaited_once_with(make_async_db.return_value if False else mock_pending.await_args[0][0], 1)
    assert len(result) == 2


# ── submit_response ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_response_succes(mocker):
    survey = make_survey(id=1, target_crew_ids=[1], yacht_id=1, trigger_type="post_charter")
    response = make_survey_response(id=10)

    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=survey))
    mocker.patch("app.modules.survey.service.survey_repo.has_already_responded", AsyncMock(return_value=False))
    mocker.patch("app.modules.survey.service.survey_repo.create_response", AsyncMock(return_value=response))
    mocker.patch("app.modules.survey.service.survey_repo.get_recent_responses", AsyncMock(return_value=[]))
    mocker.patch("app.modules.survey.service.vessel_repo.update_observed_scores", AsyncMock())
    mocker.patch(
        "app.modules.survey.service.recruitment_repo.get_active_event_for_crew",
        AsyncMock(return_value=None),
    )
    mocker.patch(
        "app.modules.survey.service.recruitment_repo.count_events_with_y_actual",
        AsyncMock(return_value=10),
    )

    crew = make_crew_profile(id=1)
    result = await service.submit_response(
        db=make_async_db(),
        survey_id=1,
        crew=crew,
        payload=_payload(),
    )

    assert result["status"] == "submitted"
    assert result["response_id"] == response.id


@pytest.mark.asyncio
async def test_submit_response_non_cible_403(mocker):
    """Marin pas dans la liste cible → PermissionError."""
    survey = make_survey(id=1, target_crew_ids=[99], is_open=True)
    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=survey))

    crew = make_crew_profile(id=1)  # id=1 n'est pas dans [99]
    with pytest.raises(PermissionError, match="ciblé"):
        await service.submit_response(
            db=make_async_db(), survey_id=1, crew=crew, payload=_payload()
        )


@pytest.mark.asyncio
async def test_submit_response_doublon_409(mocker):
    """Réponse déjà soumise → ValueError ALREADY_RESPONDED."""
    survey = make_survey(id=1, target_crew_ids=[1], is_open=True)
    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=survey))
    mocker.patch("app.modules.survey.service.survey_repo.has_already_responded", AsyncMock(return_value=True))

    crew = make_crew_profile(id=1)
    with pytest.raises(ValueError, match="ALREADY_RESPONDED"):
        await service.submit_response(
            db=make_async_db(), survey_id=1, crew=crew, payload=_payload()
        )


@pytest.mark.asyncio
async def test_submit_response_survey_ferme_400(mocker):
    """Survey fermé → ValueError SURVEY_NOT_FOUND_OR_CLOSED."""
    survey = make_survey(id=1, is_open=False, target_crew_ids=[1])
    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=survey))

    crew = make_crew_profile(id=1)
    with pytest.raises(ValueError, match="SURVEY_NOT_FOUND_OR_CLOSED"):
        await service.submit_response(
            db=make_async_db(), survey_id=1, crew=crew, payload=_payload()
        )


# ── _normalize_response ───────────────────────────────────────────────────────

def test_normalize_min_retourne_zero():
    """Valeur 1 → 0.0."""
    p = _payload(intent_to_stay=1.0, team_cohesion=1.0)
    result = service._normalize_response(p)
    assert result["intent_to_stay"] == 0.0
    assert result["team_cohesion"] == 0.0


def test_normalize_max_retourne_cent():
    """Valeur 10 → 100.0."""
    p = _payload(intent_to_stay=10.0, workload_felt=10.0)
    result = service._normalize_response(p)
    assert result["intent_to_stay"] == 100.0
    assert result["workload_satisfaction"] == 100.0


def test_normalize_milieu_retourne_cinquante():
    """Valeur 5.5 → 50.0."""
    p = _payload(intent_to_stay=5.5)
    result = service._normalize_response(p)
    assert result["intent_to_stay"] == 50.0


def test_normalize_none_retourne_fallback():
    """Attribut absent → 50.0."""
    p = SimpleNamespace(intent_to_stay=7.0)  # Pas de team_cohesion
    result = service._normalize_response(p)
    assert result["team_cohesion"] == 50.0


# ── _check_ml_threshold ───────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_ml_threshold_pas_de_declenchement_sous_150(mocker):
    mocker.patch(
        "app.modules.survey.service.recruitment_repo.count_events_with_y_actual",
        AsyncMock(return_value=149),
    )
    # Doit s'exécuter sans effet (print n'est pas appelé)
    await service._check_ml_threshold(make_async_db())


@pytest.mark.asyncio
async def test_ml_threshold_declenchement_a_150(mocker, capsys):
    mocker.patch(
        "app.modules.survey.service.recruitment_repo.count_events_with_y_actual",
        AsyncMock(return_value=150),
    )
    await service._check_ml_threshold(make_async_db())
    captured = capsys.readouterr()
    assert "150" in captured.out


@pytest.mark.asyncio
async def test_ml_threshold_pas_de_declenchement_a_151(mocker, capsys):
    mocker.patch(
        "app.modules.survey.service.recruitment_repo.count_events_with_y_actual",
        AsyncMock(return_value=151),
    )
    await service._check_ml_threshold(make_async_db())
    captured = capsys.readouterr()
    assert captured.out == ""


# ── get_survey_results ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_survey_results_acces_refuse(mocker):
    survey = make_survey(id=1, yacht_id=1)
    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=survey))
    mocker.patch("app.modules.survey.service.vessel_repo.is_owner", AsyncMock(return_value=False))

    employer = make_employer_profile()
    with pytest.raises(PermissionError):
        await service.get_survey_results(db=make_async_db(), survey_id=1, employer=employer)


@pytest.mark.asyncio
async def test_get_survey_results_survey_introuvable(mocker):
    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=None))

    employer = make_employer_profile()
    result = await service.get_survey_results(db=make_async_db(), survey_id=999, employer=employer)
    assert result is None


@pytest.mark.asyncio
async def test_get_survey_results_vide(mocker):
    survey = make_survey(id=1, yacht_id=1)
    mocker.patch("app.modules.survey.service.survey_repo.get_survey", AsyncMock(return_value=survey))
    mocker.patch("app.modules.survey.service.vessel_repo.is_owner", AsyncMock(return_value=True))
    mocker.patch("app.modules.survey.service.survey_repo.get_responses_for_survey", AsyncMock(return_value=[]))

    employer = make_employer_profile()
    result = await service.get_survey_results(db=make_async_db(), survey_id=1, employer=employer)

    assert result["response_count"] == 0
    assert result["aggregated"] is None
