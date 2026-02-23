# tests/modules/auth/test_service.py
"""
Tests unitaires pour modules.auth.service.AuthService

Pattern : mock db.execute() et db.scalar_one_or_none() pour contrôler
les résultats SQL sans base de données réelle.

Couverture :
    register_crew() :
        - Email libre → crée User + CrewProfile, retourne TokenOut
        - Email déjà pris → HTTPException 409

    register_employer() :
        - Email libre → crée User + EmployerProfile, retourne TokenOut
        - Email déjà pris → HTTPException 409

    login() :
        - Credentials corrects → retourne TokenOut
        - Mauvais mot de passe → HTTPException 401
        - Email inconnu → HTTPException 401
        - Compte inactif → HTTPException 403

    refresh() :
        - Token valide → retourne dict access_token
        - Token invalide → HTTPException 401

    change_password() :
        - Bon mot de passe actuel → met à jour hashed_password
        - Mauvais mot de passe → HTTPException 400
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi import HTTPException

from app.modules.auth.service import AuthService
from app.modules.auth.schemas import RegisterCrewIn, RegisterEmployerIn, LoginIn
from app.shared.enums import UserRole, YachtPosition
from tests.conftest import make_user, make_crew_profile, make_employer_profile, make_async_db

pytestmark = pytest.mark.service

service = AuthService()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _register_crew_payload(**kwargs) -> RegisterCrewIn:
    defaults = dict(
        email="new@test.com",
        password="password123",
        name="Jean Marin",
        position_targeted=YachtPosition.DECKHAND,
        experience_years=2,
    )
    defaults.update(kwargs)
    return RegisterCrewIn(**defaults)


def _register_employer_payload(**kwargs) -> RegisterEmployerIn:
    defaults = dict(
        email="employer@test.com",
        password="password123",
        name="Eric Owner",
        company_name="Sea Ventures",
    )
    defaults.update(kwargs)
    return RegisterEmployerIn(**defaults)


def _login_payload(email="user@test.com", password="secret") -> LoginIn:
    return LoginIn(email=email, password=password)


# ── register_crew() ───────────────────────────────────────────────────────────

class TestRegisterCrew:
    @pytest.mark.asyncio
    async def test_succes_retourne_token_out(self):
        """Email libre → TokenOut avec access_token, refresh_token, role."""
        db = make_async_db()

        # _assert_email_free: aucun user existant → scalar_one_or_none() = None
        mock_result_free = MagicMock()
        mock_result_free.scalar_one_or_none.return_value = None

        # _build_tokens doit recevoir un user avec id
        db.execute = AsyncMock(return_value=mock_result_free)

        with patch("app.modules.auth.service.hash_password", return_value="hashed"):
            with patch("app.modules.auth.service.create_access_token", return_value="access_123"):
                with patch("app.modules.auth.service.create_refresh_token", return_value="refresh_456"):
                    payload = _register_crew_payload()
                    result = await service.register_crew(db, payload)

        assert result.access_token == "access_123"
        assert result.refresh_token == "refresh_456"
        assert result.role == UserRole.CANDIDATE
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_email_duplique_leve_409(self):
        """Email déjà existant → HTTPException 409."""
        db = make_async_db()

        mock_result_taken = MagicMock()
        mock_result_taken.scalar_one_or_none.return_value = make_user(email="new@test.com")
        db.execute = AsyncMock(return_value=mock_result_taken)

        with pytest.raises(HTTPException) as exc_info:
            await service.register_crew(db, _register_crew_payload(email="new@test.com"))

        assert exc_info.value.status_code == 409


# ── register_employer() ───────────────────────────────────────────────────────

class TestRegisterEmployer:
    @pytest.mark.asyncio
    async def test_succes_retourne_token_out(self):
        db = make_async_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.modules.auth.service.hash_password", return_value="hashed"):
            with patch("app.modules.auth.service.create_access_token", return_value="acc"):
                with patch("app.modules.auth.service.create_refresh_token", return_value="ref"):
                    result = await service.register_employer(db, _register_employer_payload())

        assert result.role == UserRole.CLIENT

    @pytest.mark.asyncio
    async def test_email_duplique_leve_409(self):
        db = make_async_db()
        mock_taken = MagicMock()
        mock_taken.scalar_one_or_none.return_value = make_user(role=UserRole.CLIENT)
        db.execute = AsyncMock(return_value=mock_taken)

        with pytest.raises(HTTPException) as exc_info:
            await service.register_employer(db, _register_employer_payload())

        assert exc_info.value.status_code == 409


# ── login() ───────────────────────────────────────────────────────────────────

class TestLogin:
    @pytest.mark.asyncio
    async def test_succes_retourne_token_out(self):
        db = make_async_db()
        user = make_user(email="user@test.com", role=UserRole.CANDIDATE)

        mock_user_result = MagicMock()
        mock_user_result.scalar_one_or_none.return_value = user

        mock_profile_result = MagicMock()
        mock_profile_result.scalar_one_or_none.return_value = make_crew_profile(id=5)

        db.execute = AsyncMock(side_effect=[mock_user_result, mock_profile_result])

        with patch("app.modules.auth.service.verify_password", return_value=True):
            with patch("app.modules.auth.service.create_access_token", return_value="acc"):
                with patch("app.modules.auth.service.create_refresh_token", return_value="ref"):
                    result = await service.login(db, _login_payload())

        assert result.access_token == "acc"
        assert result.role == UserRole.CANDIDATE

    @pytest.mark.asyncio
    async def test_email_inconnu_leve_401(self):
        db = make_async_db()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        db.execute = AsyncMock(return_value=mock_result)

        with pytest.raises(HTTPException) as exc_info:
            await service.login(db, _login_payload(email="ghost@test.com"))

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_mauvais_mot_de_passe_leve_401(self):
        db = make_async_db()
        user = make_user()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.modules.auth.service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await service.login(db, _login_payload(password="wrong"))

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_compte_inactif_leve_403(self):
        db = make_async_db()
        user = make_user(is_active=False)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.modules.auth.service.verify_password", return_value=True):
            with pytest.raises(HTTPException) as exc_info:
                await service.login(db, _login_payload())

        assert exc_info.value.status_code == 403


# ── refresh() ────────────────────────────────────────────────────────────────

class TestRefresh:
    @pytest.mark.asyncio
    async def test_token_valide_retourne_access_token(self):
        db = make_async_db()
        user = make_user(id=1)
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user
        db.execute = AsyncMock(return_value=mock_result)

        with patch("app.modules.auth.service.decode_token", return_value={"sub": "1", "type": "refresh"}):
            with patch("app.modules.auth.service.create_access_token", return_value="new_access"):
                result = await service.refresh(db, "valid_refresh_token")

        assert result["access_token"] == "new_access"
        assert result["token_type"] == "bearer"

    @pytest.mark.asyncio
    async def test_token_invalide_leve_401(self):
        db = make_async_db()

        with patch("app.modules.auth.service.decode_token", side_effect=Exception("bad token")):
            with pytest.raises(HTTPException) as exc_info:
                await service.refresh(db, "bad_token")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_token_pas_refresh_type_leve_401(self):
        db = make_async_db()

        with patch("app.modules.auth.service.decode_token", return_value={"sub": "1", "type": "access"}):
            with pytest.raises(HTTPException) as exc_info:
                await service.refresh(db, "access_token_wrongly_used")

        assert exc_info.value.status_code == 401


# ── change_password() ────────────────────────────────────────────────────────

class TestChangePassword:
    @pytest.mark.asyncio
    async def test_succes_met_a_jour_password(self):
        db = make_async_db()
        user = make_user()

        with patch("app.modules.auth.service.verify_password", return_value=True):
            with patch("app.modules.auth.service.hash_password", return_value="new_hashed"):
                await service.change_password(db, user, "old_pw", "new_pw_different")

        assert user.hashed_password == "new_hashed"
        db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_mauvais_mot_de_passe_actuel_leve_400(self):
        db = make_async_db()
        user = make_user()

        with patch("app.modules.auth.service.verify_password", return_value=False):
            with pytest.raises(HTTPException) as exc_info:
                await service.change_password(db, user, "wrong_pw", "new_pw")

        assert exc_info.value.status_code == 400
