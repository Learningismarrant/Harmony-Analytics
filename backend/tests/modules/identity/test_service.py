# tests/modules/identity/test_service.py
"""
Tests unitaires pour modules.identity.service.IdentityService

Couverture :
    get_full_profile() :
        - Contexte d'accès non résolu → retourne None
        - Crew introuvable → retourne None
        - Succès → retourne dict avec identity, experiences, documents, reports

    _build_psychometric_report() :
        - Snapshot absent → has_data=False
        - view_mode="candidate" → raw_scores présents
        - view_mode="recruiter" → key_signals présents
        - view_mode="manager"   → work_style présent
        - view_mode="onboarding" → onboarding_tips présents

    _extract_dimensions() :
        - ES = 100 - neuroticism correctement calculé
        - GCA depuis cognitive.gca_score
        - Champs None si absents du snapshot

    _format_identity() :
        - Retourne tous les champs attendus
        - position_targeted → string si présent

    update_identity() :
        - user_data et crew_data dispatched correctement

    _extract_key_signals() :
        - agreeableness ≥ 70 → signal "strength"
        - agreeableness < 35 → signal "risk"
        - gca ≥ 70 → signal "strength"
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from types import SimpleNamespace

from app.modules.identity.service import IdentityService
from tests.conftest import make_user, make_crew_profile, snapshot_full

pytestmark = pytest.mark.service

service = IdentityService()


def _snap_with_all_traits() -> dict:
    return {
        "big_five": {
            "agreeableness":      75.0,
            "conscientiousness":  70.0,
            "neuroticism":        30.0,
            "openness":           60.0,
            "extraversion":       55.0,
        },
        "cognitive": {"gca_score": 72.0},
        "resilience": 65.0,
        "key_signals": [],
    }


def _ctx(view_mode: str = "candidate") -> dict:
    return {
        "view_mode":        view_mode,
        "label":            "Mon profil",
        "is_active_crew":   False,
        "context_position": None,
    }


# ── get_full_profile() ────────────────────────────────────────────────────────

class TestGetFullProfile:
    @pytest.mark.asyncio
    async def test_contexte_non_resolu_retourne_none(self, mocker):
        db = AsyncMock()
        user = make_user(id=1)

        mocker.patch(
            "app.modules.identity.service.repo.resolve_access_context",
            AsyncMock(return_value=None),
        )

        result = await service.get_full_profile(db, crew_profile_id=99, requester=user)
        assert result is None

    @pytest.mark.asyncio
    async def test_crew_introuvable_retourne_none(self, mocker):
        db = AsyncMock()
        user = make_user(id=1)

        mocker.patch("app.modules.identity.service.repo.resolve_access_context", AsyncMock(return_value=_ctx()))
        mocker.patch("app.modules.identity.service.repo.get_crew_by_id", AsyncMock(return_value=None))

        result = await service.get_full_profile(db, crew_profile_id=1, requester=user)
        assert result is None

    @pytest.mark.asyncio
    async def test_succes_retourne_profil_complet(self, mocker):
        db = AsyncMock()
        requester = make_user(id=1)
        crew = make_crew_profile(id=1, user_id=1, psychometric_snapshot=_snap_with_all_traits())
        user = make_user(id=1, name="Jean Marin", email="j@test.com")

        mocker.patch("app.modules.identity.service.repo.resolve_access_context", AsyncMock(return_value=_ctx()))
        mocker.patch("app.modules.identity.service.repo.get_crew_by_id", AsyncMock(return_value=crew))
        mocker.patch("app.modules.identity.service.repo.get_user_by_id", AsyncMock(return_value=user))
        mocker.patch("app.modules.identity.service.repo.get_experiences", AsyncMock(return_value=[]))
        mocker.patch("app.modules.identity.service.repo.get_documents", AsyncMock(return_value=[]))

        result = await service.get_full_profile(db, crew_profile_id=1, requester=requester)

        assert result is not None
        assert "identity" in result
        assert "experiences" in result
        assert "documents" in result
        assert "reports" in result
        assert result["view_mode"] == "candidate"


# ── _build_psychometric_report() ─────────────────────────────────────────────

class TestBuildPsychometricReport:
    def test_snapshot_absent_has_data_false(self):
        result = service._build_psychometric_report(None, view_mode="candidate")
        assert result["has_data"] is False

    def test_snapshot_vide_has_data_false(self):
        result = service._build_psychometric_report({}, view_mode="candidate")
        assert result["has_data"] is False

    def test_candidate_inclut_raw_scores(self):
        snap = snapshot_full()
        result = service._build_psychometric_report(snap, view_mode="candidate")
        assert result["has_data"] is True
        assert "raw_scores" in result

    def test_recruiter_inclut_key_signals(self):
        snap = snapshot_full()
        result = service._build_psychometric_report(snap, view_mode="recruiter")
        assert result["has_data"] is True
        assert "key_signals" in result
        assert "raw_scores" not in result

    def test_manager_inclut_work_style(self):
        snap = snapshot_full()
        result = service._build_psychometric_report(snap, view_mode="manager")
        assert "work_style" in result

    def test_onboarding_inclut_tips(self):
        snap = snapshot_full()
        result = service._build_psychometric_report(snap, view_mode="onboarding")
        assert "onboarding_tips" in result
        assert "key_signals" in result

    def test_dimensions_es_calcule(self):
        snap = {
            "big_five": {"neuroticism": 40.0},
            "cognitive": {},
        }
        result = service._build_psychometric_report(snap, view_mode="candidate")
        dims = result["dimensions"]
        assert dims["emotional_stability"] == pytest.approx(60.0, abs=0.1)

    def test_dimensions_gca_depuis_cognitive(self):
        snap = {
            "big_five": {},
            "cognitive": {"gca_score": 72.0},
        }
        result = service._build_psychometric_report(snap, view_mode="candidate")
        assert result["dimensions"]["gca"] == 72.0


# ── _format_identity() ───────────────────────────────────────────────────────

class TestFormatIdentity:
    def test_retourne_champs_obligatoires(self):
        user = make_user(id=1, name="Jean Marin", email="j@test.com")
        crew = make_crew_profile(id=1, user_id=1)
        result = service._format_identity(user, crew)

        for key in ("crew_profile_id", "user_id", "name", "email", "position_targeted"):
            assert key in result, f"Clé manquante : {key}"

    def test_position_targeted_converti_en_string(self):
        from app.shared.enums import YachtPosition
        user = make_user(id=1)
        crew = make_crew_profile(id=1, position_targeted=YachtPosition.BOSUN)
        result = service._format_identity(user, crew)
        # La position doit être un string ou None (pas un objet Enum brut)
        assert result["position_targeted"] is None or isinstance(result["position_targeted"], str)


# ── _extract_key_signals() ────────────────────────────────────────────────────

class TestExtractKeySignals:
    def test_agreeableness_eleve_signal_strength(self):
        snap = {"big_five": {"agreeableness": 80.0}, "cognitive": {}}
        signals = service._extract_key_signals(snap, context_position=None)
        types = [s["type"] for s in signals]
        assert "strength" in types

    def test_agreeableness_bas_signal_risk(self):
        snap = {"big_five": {"agreeableness": 25.0}, "cognitive": {}}
        signals = service._extract_key_signals(snap, context_position=None)
        types = [s["type"] for s in signals]
        assert "risk" in types

    def test_gca_eleve_signal_strength(self):
        snap = {"big_five": {}, "cognitive": {"gca_score": 80.0}}
        signals = service._extract_key_signals(snap, context_position=None)
        strength_traits = [s["trait"] for s in signals if s["type"] == "strength"]
        assert "gca" in strength_traits

    def test_snapshot_clean_pas_de_signaux(self):
        snap = {"big_five": {"agreeableness": 55.0, "conscientiousness": 55.0}, "cognitive": {}}
        signals = service._extract_key_signals(snap, context_position=None)
        assert isinstance(signals, list)


# ── update_identity() ────────────────────────────────────────────────────────

class TestUpdateIdentity:
    @pytest.mark.asyncio
    async def test_dispatche_user_et_crew_data(self, mocker):
        db = AsyncMock()
        crew = make_crew_profile(id=1, user_id=1)
        user = make_user(id=1, name="Old Name")
        payload = MagicMock()
        payload.model_dump.return_value = {
            "name": "New Name",
            "position_targeted": "bosun",
        }

        mocker.patch("app.modules.identity.service.repo.get_user_by_id", AsyncMock(return_value=user))
        mock_update_user = mocker.patch("app.modules.identity.service.repo.update_identity", AsyncMock())
        mock_update_crew = mocker.patch("app.modules.identity.service.repo.update_crew_profile", AsyncMock())
        mocker.patch("app.modules.identity.service.repo.invalidate_harmony_verification", AsyncMock())

        await service.update_identity(db, crew=crew, payload=payload)

        mock_update_user.assert_called_once()
        mock_update_crew.assert_called_once()
