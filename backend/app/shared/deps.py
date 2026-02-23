# app/shared/deps.py
"""
Dépendances FastAPI réutilisables dans tous les routers.
Injectées via Depends() — jamais appelées directement.
"""
from typing import Annotated
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import decode_token
from app.shared.models import User, CrewProfile, EmployerProfile
from app.shared.enums import UserRole


bearer = HTTPBearer()


async def _get_user_from_token(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(bearer)],
    db: Annotated[AsyncSession, Depends(get_db)],
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token invalide ou expiré",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = decode_token(credentials.credentials)
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    result = await db.execute(
        select(User)
        .options(
            selectinload(User.crew_profile),
            selectinload(User.employer_profile),
        )
        .where(User.id == int(user_id))
    )

    user = result.scalar_one_or_none()

    if not user or not user.is_active:
        raise credentials_exception

    return user


# ── Deps publiques ─────────────────────────────────────────

async def get_current_user(
    user: Annotated[User, Depends(_get_user_from_token)],
) -> User:
    """Utilisateur authentifié (tout rôle)."""
    return user


async def get_current_crew(
    user: Annotated[User, Depends(_get_user_from_token)],
) -> CrewProfile:
    if not user.crew_profile:
        raise HTTPException(status_code=403, detail="Profil marin requis")
    return user.crew_profile



async def get_current_employer(
    user: Annotated[User, Depends(_get_user_from_token)],
) -> EmployerProfile:
    if user.role not in (UserRole.CLIENT, UserRole.ADMIN):
        raise HTTPException(status_code=403, detail="Accès recruteur requis")

    if not user.employer_profile:
        raise HTTPException(status_code=403, detail="Profil employeur introuvable")

    return user.employer_profile



async def get_current_admin(
    user: Annotated[User, Depends(_get_user_from_token)],
) -> User:
    """Exige le rôle ADMIN."""
    if user.role != UserRole.ADMIN:
        raise HTTPException(status_code=403, detail="Accès administrateur requis")
    return user


# ── Type aliases pour les routers ─────────────────────────
DbDep       = Annotated[AsyncSession, Depends(get_db)]
UserDep     = Annotated[User, Depends(get_current_user)]
CrewDep     = Annotated[CrewProfile, Depends(get_current_crew)]
EmployerDep = Annotated[EmployerProfile, Depends(get_current_employer)]
AdminDep    = Annotated[User, Depends(get_current_admin)]