# tests/modules/assessment/test_router.py
"""
Tests HTTP pour modules.assessment.router

Couverture :
    GET  /assessments/catalogue          → 200 liste
    GET  /assessments/catalogue          aucun test → 404
    GET  /assessments/{test_id}/questions → 200
    POST /assessments/submit             sans auth → 401
    POST /assessments/submit             valide → 201 + TestResultOut
    POST /assessments/submit             test inconnu → 400
    GET  /assessments/results/me         → 200 liste
    GET  /assessments/results/{id}       → 200 (employer) ou 403
"""
import pytest
from unittest.mock import AsyncMock

from tests.conftest import make_test_catalogue, make_test_result, make_question

pytestmark = pytest.mark.router


def _catalogue_item():
    return make_test_catalogue(
        id=1,
        nom_du_test="Big Five v1",
        description_courte="Test de personnalité",
        test_type="likert",
    )


def _result_item():
    return make_test_result(id=1, test_id=1, global_score=72.0, test_name="big_five_v1")


# ── GET /assessments/catalogue ────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_catalogue_200(crew_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.get_catalogue",
        AsyncMock(return_value=[_catalogue_item()]),
    )
    resp = await crew_client.get("/assessments/catalogue")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_catalogue_vide_404(crew_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.get_catalogue",
        AsyncMock(return_value=[]),
    )
    resp = await crew_client.get("/assessments/catalogue")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_catalogue_sans_auth_401(client):
    resp = await client.get("/assessments/catalogue")
    assert resp.status_code in (401, 403)


# ── GET /assessments/{test_id}/questions ─────────────────────────────────────

@pytest.mark.asyncio
async def test_get_questions_200(crew_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.get_questions_for_crew",
        AsyncMock(return_value=[make_question(id=1), make_question(id=2)]),
    )
    resp = await crew_client.get("/assessments/1/questions")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_get_questions_sans_auth_401(client):
    resp = await client.get("/assessments/1/questions")
    assert resp.status_code in (401, 403)


# ── POST /assessments/submit ──────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_submit_sans_auth_401(client):
    resp = await client.post("/assessments/submit", json={
        "test_id": 1,
        "responses": [{"question_id": 1, "valeur_choisie": "3", "seconds_spent": 5.0}],
    })
    assert resp.status_code in (401, 403)


@pytest.mark.asyncio
async def test_submit_200_avec_auth(crew_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.submit_and_score",
        AsyncMock(return_value=_result_item()),
    )
    resp = await crew_client.post("/assessments/submit", json={
        "test_id": 1,
        "responses": [{"question_id": 1, "valeur_choisie": "3", "seconds_spent": 5.0}],
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_submit_test_inconnu_400(crew_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.submit_and_score",
        AsyncMock(side_effect=ValueError("Test introuvable.")),
    )
    resp = await crew_client.post("/assessments/submit", json={
        "test_id": 999,
        "responses": [{"question_id": 1, "valeur_choisie": "3", "seconds_spent": 5.0}],
    })
    assert resp.status_code == 400


# ── POST /assessments/submit — forced_choice (T-IRT) ─────────────────────────

@pytest.mark.asyncio
async def test_submit_tirt_forced_choice_201(crew_client, mocker):
    """Soumission d'un test T-IRT avec réponses forced_choice → 201."""
    tirt_result = make_test_result(
        id=5, test_id=3, global_score=74.0, test_name="CUTTY SARK T-IRT",
    )
    mocker.patch(
        "app.modules.assessment.router.service.submit_and_score",
        AsyncMock(return_value=tirt_result),
    )
    resp = await crew_client.post("/assessments/submit", json={
        "test_id": 3,
        "responses": [{"question_id": 1, "valeur_choisie": "left", "seconds_spent": 4.5}],
    })
    assert resp.status_code == 201


@pytest.mark.asyncio
async def test_submit_tirt_invalid_valeur_400(crew_client, mocker):
    """Soumission T-IRT avec valeur_choisie invalide → service lève ValueError → 400."""
    mocker.patch(
        "app.modules.assessment.router.service.submit_and_score",
        AsyncMock(side_effect=ValueError("Réponse invalide pour paire forcée.")),
    )
    resp = await crew_client.post("/assessments/submit", json={
        "test_id": 3,
        "responses": [{"question_id": 1, "valeur_choisie": "invalid_choice", "seconds_spent": 1.0}],
    })
    assert resp.status_code == 400


# ── GET /assessments/results/me ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_results_me_200(crew_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.get_results_for_crew",
        AsyncMock(return_value=[_result_item()]),
    )
    resp = await crew_client.get("/assessments/results/me")
    assert resp.status_code == 200
    assert isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_results_me_sans_auth_401(client):
    resp = await client.get("/assessments/results/me")
    assert resp.status_code in (401, 403)


# ── GET /assessments/results/{crew_profile_id} ───────────────────────────────

@pytest.mark.asyncio
async def test_results_candidat_acces_autorise_200(employer_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.get_results_for_candidate",
        AsyncMock(return_value=[_result_item()]),
    )
    resp = await employer_client.get("/assessments/results/1")
    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_results_candidat_acces_refuse_403(employer_client, mocker):
    mocker.patch(
        "app.modules.assessment.router.service.get_results_for_candidate",
        AsyncMock(return_value=None),
    )
    resp = await employer_client.get("/assessments/results/99")
    assert resp.status_code == 403
