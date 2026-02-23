# app/modules/auth/service.py
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.shared.models import User, CrewProfile, EmployerProfile
from app.shared.enums import UserRole
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.modules.auth.schemas import (
    RegisterCrewIn, RegisterEmployerIn, LoginIn, TokenOut,
)
from jose import JWTError


class AuthService:

    # ── Register ─────────────────────────────────────────────

    async def register_crew(self, db: AsyncSession, payload: RegisterCrewIn) -> TokenOut:
        await self._assert_email_free(db, payload.email)

        user = User(
            email=payload.email,
            name=payload.name,
            phone=payload.phone,
            location=payload.location,
            hashed_password=hash_password(payload.password),
            role=UserRole.CANDIDATE,
        )
        db.add(user)
        await db.flush()   # user.id disponible

        crew = CrewProfile(
            user_id=user.id,
            position_targeted=payload.position_targeted,
            experience_years=payload.experience_years,
        )
        db.add(crew)
        await db.commit()
        await db.refresh(user)
        await db.refresh(crew)

        return self._build_tokens(user, profile_id=crew.id)

    async def register_employer(self, db: AsyncSession, payload: RegisterEmployerIn) -> TokenOut:
        await self._assert_email_free(db, payload.email)

        user = User(
            email=payload.email,
            name=payload.name,
            phone=payload.phone,
            location=payload.location,
            hashed_password=hash_password(payload.password),
            role=UserRole.CLIENT,
        )
        db.add(user)
        await db.flush()

        employer = EmployerProfile(
            user_id=user.id,
            company_name=payload.company_name,
        )
        db.add(employer)
        await db.commit()
        await db.refresh(user)
        await db.refresh(employer)

        return self._build_tokens(user, profile_id=employer.id)

    # ── Login ─────────────────────────────────────────────────

    async def login(self, db: AsyncSession, payload: LoginIn) -> TokenOut:
        result = await db.execute(select(User).where(User.email == payload.email))
        user = result.scalar_one_or_none()

        if not user or not verify_password(payload.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Email ou mot de passe incorrect",
            )
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Compte désactivé")

        profile_id = await self._get_profile_id(db, user)
        return self._build_tokens(user, profile_id=profile_id)

    # ── Refresh ───────────────────────────────────────────────

    async def refresh(self, db: AsyncSession, refresh_token: str) -> dict:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError
            user_id = int(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise HTTPException(status_code=401, detail="Refresh token invalide")

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user or not user.is_active:
            raise HTTPException(status_code=401, detail="Utilisateur introuvable")

        access_token = create_access_token({"sub": str(user.id), "role": user.role})
        return {"access_token": access_token, "token_type": "bearer"}

    # ── Mot de passe ──────────────────────────────────────────

    async def change_password(
        self, db: AsyncSession, user: User, current_pw: str, new_pw: str
    ) -> None:
        if not verify_password(current_pw, user.hashed_password):
            raise HTTPException(status_code=400, detail="Mot de passe actuel incorrect")
        user.hashed_password = hash_password(new_pw)
        await db.commit()

    # ── Privé ─────────────────────────────────────────────────

    async def _assert_email_free(self, db: AsyncSession, email: str) -> None:
        result = await db.execute(select(User).where(User.email == email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=409, detail="Email déjà utilisé")

    async def _get_profile_id(self, db: AsyncSession, user: User) -> int:
        if user.role == UserRole.CANDIDATE:
            result = await db.execute(
                select(CrewProfile).where(CrewProfile.user_id == user.id)
            )
            profile = result.scalar_one_or_none()
        else:
            result = await db.execute(
                select(EmployerProfile).where(EmployerProfile.user_id == user.id)
            )
            profile = result.scalar_one_or_none()
        return profile.id if profile else 0

    def _build_tokens(self, user: User, profile_id: int) -> TokenOut:
        data = {"sub": str(user.id), "role": user.role}
        return TokenOut(
            access_token=create_access_token(data),
            refresh_token=create_refresh_token(data),
            role=user.role,
            user_id=user.id,
            profile_id=profile_id,
        )