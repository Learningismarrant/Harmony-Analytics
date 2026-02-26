# tests/modules/recruitment/test_service.py
"""
Tests unitaires pour modules.recruitment.service.RecruitmentService

Couverture :
    create_campaign() :
        - Délègue à repo.create_campaign() et retourne le résultat

    get_matching() :
        - Campagne introuvable / accès refusé → PermissionError
        - Aucun candidat → retourne []
        - pipeline.run_batch() appelé avec bons arguments

    _sort_matching() :
        - sort_by="g_fit" → tri par DNRE score décroissant
        - sort_by="y_success" → tri par MLPSM score décroissant
        - sort_by="dnre_then_mlpsm" → filtrés en bas
        - is_pipeline_pass=False toujours en bas

    archive_campaign() :
        - Campagne introuvable → PermissionError
        - Succès → reject_pending_candidates et archive appelés

    apply_to_campaign() :
        - Token invalide → ValueError
        - Candidature déjà existante → ValueError
        - Succès → retourne dict avec campaign_id
"""
import pytest
from unittest.mock import AsyncMock, MagicMock

from app.modules.recruitment.service import RecruitmentService
from tests.conftest import make_employer_profile, make_crew_profile, make_campaign

pytestmark = pytest.mark.service

service = RecruitmentService()


def _make_matching_row(g_fit: float = 70.0, y_success: float = 65.0, is_pass: bool = True) -> dict:
    return {
        "crew_profile_id": "cand_1",
        "is_pipeline_pass": is_pass,
        "filtered_at": None if is_pass else "DNRE",
        "profile_fit": {"g_fit": g_fit, "safety_level": "CLEAR", "safety_flags": []},
        "team_integration": {
            "available": is_pass,
            "y_success": y_success if is_pass else None,
        },
    }


# ── create_campaign() ─────────────────────────────────────────────────────────

class TestCreateCampaign:
    @pytest.mark.asyncio
    async def test_delegue_repo(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile(id=1)
        mock_campaign = make_campaign(id=1)
        payload = MagicMock()

        mock_create = mocker.patch(
            "app.modules.recruitment.service.repo.create_campaign",
            AsyncMock(return_value=mock_campaign),
        )

        result = await service.create_campaign(db, payload, employer)
        assert result == mock_campaign
        mock_create.assert_called_once_with(db, payload, employer.id)


# ── get_matching() ────────────────────────────────────────────────────────────

class TestGetMatching:
    @pytest.mark.asyncio
    async def test_campagne_introuvable_leve_permission_error(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile()
        mocker.patch("app.modules.recruitment.service.repo.get_campaign_secure", AsyncMock(return_value=None))

        with pytest.raises(PermissionError):
            await service.get_matching(db, campaign_id=99, employer=employer)

    @pytest.mark.asyncio
    async def test_aucun_candidat_retourne_liste_vide(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile()
        campaign = make_campaign(id=1, yacht_id=None)

        mocker.patch("app.modules.recruitment.service.repo.get_campaign_secure", AsyncMock(return_value=campaign))
        mocker.patch("app.modules.recruitment.service.repo.get_candidates_with_snapshots", AsyncMock(return_value=[]))

        result = await service.get_matching(db, campaign_id=1, employer=employer)
        assert result == []

    @pytest.mark.asyncio
    async def test_succes_appelle_pipeline(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile()
        campaign  = make_campaign(id=1, yacht_id=None)
        candidates = [
            {"crew_profile_id": "c1", "snapshot": {}, "experience_years": 2,
             "position_targeted": "bosun", "name": "Jean", "avatar_url": None,
             "location": None},
        ]
        from app.engine.recruitment.pipeline import PipelineResult, PipelineStage, DNREResult
        # Create a mock PipelineResult
        mock_pr = MagicMock(spec=PipelineResult)
        mock_pr.crew_profile_id = "c1"
        mock_pr.is_pipeline_pass = True
        mock_pr.filtered_at = None
        mock_pr.to_matching_row.return_value = _make_matching_row()

        mocker.patch("app.modules.recruitment.service.repo.get_campaign_secure", AsyncMock(return_value=campaign))
        mocker.patch("app.modules.recruitment.service.repo.get_candidates_with_snapshots", AsyncMock(return_value=candidates))
        mocker.patch("app.modules.recruitment.service.repo.get_active_model_betas", AsyncMock(return_value={}))
        mocker.patch("app.modules.recruitment.service.repo.get_active_job_weight_config", AsyncMock(return_value=None))
        mocker.patch("app.modules.recruitment.service.repo.get_applications_status_map", AsyncMock(return_value={}))
        mock_pipeline = mocker.patch(
            "app.modules.recruitment.service.pipeline.run_batch",
            return_value=[mock_pr],
        )

        result = await service.get_matching(db, campaign_id=1, employer=employer)
        mock_pipeline.assert_called_once()
        assert isinstance(result, list)
        assert len(result) == 1


# ── _sort_matching() ──────────────────────────────────────────────────────────

class TestSortMatching:
    def test_sort_by_g_fit(self):
        rows = [
            _make_matching_row(g_fit=50.0),
            _make_matching_row(g_fit=80.0),
            _make_matching_row(g_fit=65.0),
        ]
        result = service._sort_matching(rows, sort_by="g_fit")
        scores = [r["profile_fit"]["g_fit"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_sort_by_y_success(self):
        rows = [
            _make_matching_row(y_success=50.0),
            _make_matching_row(y_success=80.0),
            _make_matching_row(y_success=65.0),
        ]
        result = service._sort_matching(rows, sort_by="y_success")
        scores = [r["team_integration"]["y_success"] for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_filtre_en_bas(self):
        rows = [
            _make_matching_row(g_fit=90.0, is_pass=False),   # DISQUALIFIED
            _make_matching_row(g_fit=70.0, is_pass=True),
            _make_matching_row(g_fit=80.0, is_pass=True),
        ]
        result = service._sort_matching(rows, sort_by="g_fit")
        # Le candidat non passé doit être en dernière position
        assert result[-1]["is_pipeline_pass"] is False

    def test_sort_by_dnre_then_mlpsm(self):
        rows = [
            _make_matching_row(g_fit=70, y_success=80),
            _make_matching_row(g_fit=70, y_success=50),
            _make_matching_row(g_fit=90, y_success=60),
        ]
        result = service._sort_matching(rows, sort_by="dnre_then_mlpsm")
        # Premier doit avoir le meilleur g_fit
        assert result[0]["profile_fit"]["g_fit"] == 90.0


# ── archive_campaign() ────────────────────────────────────────────────────────

class TestArchiveCampaign:
    @pytest.mark.asyncio
    async def test_campagne_introuvable(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile()
        mocker.patch("app.modules.recruitment.service.repo.get_campaign_secure", AsyncMock(return_value=None))

        with pytest.raises(PermissionError):
            await service.archive_campaign(db, campaign_id=1, employer=employer)

    @pytest.mark.asyncio
    async def test_succes_rejette_puis_archive(self, mocker):
        db = AsyncMock()
        employer = make_employer_profile()
        campaign = make_campaign(id=1)

        mocker.patch("app.modules.recruitment.service.repo.get_campaign_secure", AsyncMock(return_value=campaign))
        mock_reject  = mocker.patch("app.modules.recruitment.service.repo.reject_pending_candidates", AsyncMock())
        mock_archive = mocker.patch("app.modules.recruitment.service.repo.archive_campaign", AsyncMock())

        await service.archive_campaign(db, campaign_id=1, employer=employer)
        mock_reject.assert_called_once_with(db, 1, reason="Campagne archivée")
        mock_archive.assert_called_once()


# ── apply_to_campaign() ───────────────────────────────────────────────────────

class TestApplyToCampaign:
    @pytest.mark.asyncio
    async def test_token_invalide_leve_value_error(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        mocker.patch("app.modules.recruitment.service.repo.get_by_invite_token", AsyncMock(return_value=None))

        with pytest.raises(ValueError, match="CAMPAIGN_NOT_FOUND_OR_CLOSED"):
            await service.apply_to_campaign(db, invite_token="bad_token", crew=crew)

    @pytest.mark.asyncio
    async def test_candidature_existante_leve_value_error(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile()
        campaign = make_campaign(id=1)
        campaign.status = MagicMock()
        campaign.status.value = "open"

        mocker.patch("app.modules.recruitment.service.repo.get_by_invite_token", AsyncMock(return_value=campaign))
        mocker.patch("app.modules.recruitment.service.repo.get_application", AsyncMock(return_value=MagicMock()))

        with pytest.raises(ValueError, match="ALREADY_APPLIED"):
            await service.apply_to_campaign(db, invite_token="valid_token", crew=crew)

    @pytest.mark.asyncio
    async def test_succes_retourne_confirmation(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile(id=5)
        campaign = make_campaign(id=1)
        campaign.status = MagicMock()
        campaign.status.value = "open"
        link = MagicMock(id=10)

        mocker.patch("app.modules.recruitment.service.repo.get_by_invite_token", AsyncMock(return_value=campaign))
        mocker.patch("app.modules.recruitment.service.repo.get_application", AsyncMock(return_value=None))
        mocker.patch("app.modules.recruitment.service.repo.create_application", AsyncMock(return_value=link))

        result = await service.apply_to_campaign(db, invite_token="valid_token", crew=crew)
        assert result["campaign_id"] == campaign.id
        assert result["application_id"] == 10
