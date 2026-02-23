# tests/modules/assessment/test_service.py
"""
Tests unitaires pour modules.assessment.service.AssessmentService

Couverture :
    get_catalogue() :
        - Appelle repo.get_all_active_tests() et retourne le résultat

    submit_and_score() :
        - Réponses vides → ValueError
        - Test introuvable → ValueError
        - Succès : calculate_scores() appelé, résultat sauvegardé
        - Background task _propagate_to_vessel_and_fleet planifiée
        - _refresh_crew_snapshot appelé synchroniquement

    get_results_for_crew() :
        - Délègue à repo.get_results_by_crew()

    get_results_for_candidate() :
        - Accès refusé (check_requester_access=False) → retourne None
        - Accès autorisé → retourne liste
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import BackgroundTasks

from app.modules.assessment.service import AssessmentService
from tests.conftest import (
    make_crew_profile, make_test_catalogue, make_question, make_test_result
)

pytestmark = pytest.mark.service

service = AssessmentService()


def _make_responses(n: int = 5) -> list:
    return [{"question_id": i + 1, "value": 3, "time_seconds": 8} for i in range(n)]


def _make_questions_map(n: int = 5) -> dict:
    return {
        i + 1: make_question(id=i + 1, test_id=1, trait="agreeableness")
        for i in range(n)
    }


class TestGetCatalogue:
    @pytest.mark.asyncio
    async def test_appelle_repo_et_retourne_liste(self, mocker):
        mock_tests = [make_test_catalogue(id=1), make_test_catalogue(id=2)]
        mocker.patch(
            "app.modules.assessment.service.repo.get_all_active_tests",
            AsyncMock(return_value=mock_tests),
        )
        db = AsyncMock()
        result = await service.get_catalogue(db)
        assert result == mock_tests


class TestSubmitAndScore:
    @pytest.mark.asyncio
    async def test_reponses_vides_leve_value_error(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        bt = MagicMock(spec=BackgroundTasks)

        with pytest.raises(ValueError, match="Aucune réponse"):
            await service.submit_and_score(db, crew, test_id=1, responses=[], background_tasks=bt)

    @pytest.mark.asyncio
    async def test_test_introuvable_leve_value_error(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        bt = MagicMock(spec=BackgroundTasks)

        mocker.patch(
            "app.modules.assessment.service.repo.get_test_info",
            AsyncMock(return_value=None),
        )
        with pytest.raises(ValueError, match="Test introuvable"):
            await service.submit_and_score(
                db, crew, test_id=99, responses=_make_responses(), background_tasks=bt
            )

    @pytest.mark.asyncio
    async def test_succes_sauvegarde_et_retourne_result(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile(id=1)
        bt = MagicMock(spec=BackgroundTasks)

        test_info  = make_test_catalogue(id=1, test_type="likert", max_score_per_question=5)
        questions  = list(_make_questions_map(3).values())
        saved      = make_test_result(id=10, crew_profile_id=1, global_score=70.0)

        mocker.patch("app.modules.assessment.service.repo.get_test_info", AsyncMock(return_value=test_info))
        mocker.patch("app.modules.assessment.service.repo.get_questions_by_test", AsyncMock(return_value=questions))
        mocker.patch("app.modules.assessment.service.repo.save_result", AsyncMock(return_value=saved))
        mocker.patch("app.modules.assessment.service.repo.get_results_by_crew", AsyncMock(return_value=[saved]))
        mocker.patch("app.modules.assessment.service.repo.update_crew_snapshot", AsyncMock())

        # Patch calculate_scores pour retourner un résultat valide
        mock_scores = {
            "traits": {"agreeableness": {"score": 70.0, "niveau": "Élevé"}},
            "global_score": 70.0,
            "reliability": {"is_reliable": True},
            "meta": {"total_time_seconds": 24},
        }
        mocker.patch("app.modules.assessment.service.calculate_scores", return_value=mock_scores)

        result = await service.submit_and_score(
            db, crew, test_id=1, responses=_make_responses(3), background_tasks=bt
        )

        assert result == saved
        bt.add_task.assert_called_once()

    @pytest.mark.asyncio
    async def test_background_task_planifiee(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile(id=7)
        bt = MagicMock(spec=BackgroundTasks)

        test_info = make_test_catalogue(id=1, test_type="likert")
        questions = list(_make_questions_map(2).values())
        saved     = make_test_result()

        mocker.patch("app.modules.assessment.service.repo.get_test_info", AsyncMock(return_value=test_info))
        mocker.patch("app.modules.assessment.service.repo.get_questions_by_test", AsyncMock(return_value=questions))
        mocker.patch("app.modules.assessment.service.repo.save_result", AsyncMock(return_value=saved))
        mocker.patch("app.modules.assessment.service.repo.get_results_by_crew", AsyncMock(return_value=[]))
        mocker.patch("app.modules.assessment.service.repo.update_crew_snapshot", AsyncMock())
        mocker.patch("app.modules.assessment.service.calculate_scores", return_value={
            "traits": {}, "global_score": 50.0, "reliability": {}, "meta": {}
        })

        await service.submit_and_score(db, crew, test_id=1, responses=_make_responses(2), background_tasks=bt)

        assert bt.add_task.call_count == 1
        call_args = bt.add_task.call_args[0]
        assert call_args[0] == service._propagate_to_vessel_and_fleet


class TestGetResultsForCrew:
    @pytest.mark.asyncio
    async def test_delegue_repo(self, mocker):
        db = AsyncMock()
        expected = [make_test_result()]
        mocker.patch(
            "app.modules.assessment.service.repo.get_results_by_crew",
            AsyncMock(return_value=expected),
        )
        result = await service.get_results_for_crew(db, crew_profile_id=1)
        assert result == expected


class TestGetResultsForCandidate:
    @pytest.mark.asyncio
    async def test_acces_refuse_retourne_none(self, mocker):
        db = AsyncMock()
        mocker.patch(
            "app.modules.assessment.service.repo.check_requester_access",
            AsyncMock(return_value=False),
        )
        result = await service.get_results_for_candidate(db, crew_profile_id=1, requester_employer_id=99)
        assert result is None

    @pytest.mark.asyncio
    async def test_acces_autorise_retourne_liste(self, mocker):
        db = AsyncMock()
        expected = [make_test_result()]
        mocker.patch(
            "app.modules.assessment.service.repo.check_requester_access",
            AsyncMock(return_value=True),
        )
        mocker.patch(
            "app.modules.assessment.service.repo.get_results_by_crew",
            AsyncMock(return_value=expected),
        )
        result = await service.get_results_for_candidate(db, crew_profile_id=1, requester_employer_id=1)
        assert result == expected
