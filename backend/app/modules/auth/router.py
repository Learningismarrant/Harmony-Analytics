# app/modules/auth/router.py
from fastapi import APIRouter
from app.modules.auth.schemas import (
    RegisterCrewIn, RegisterEmployerIn, LoginIn, TokenOut,
    RefreshIn, AccessTokenOut, ChangePasswordIn,
)
from app.modules.auth.service import AuthService
from app.shared.deps import DbDep, UserDep

router = APIRouter(prefix="/auth", tags=["Auth"])
service = AuthService()


@router.post("/register/crew", response_model=TokenOut, status_code=201)
async def register_crew(payload: RegisterCrewIn, db: DbDep):
    """Inscription marin / candidat → crée User + CrewProfile."""
    return await service.register_crew(db, payload)


@router.post("/register/employer", response_model=TokenOut, status_code=201)
async def register_employer(payload: RegisterEmployerIn, db: DbDep):
    """Inscription client / owner → crée User + EmployerProfile."""
    return await service.register_employer(db, payload)


@router.post("/login", response_model=TokenOut)
async def login(payload: LoginIn, db: DbDep):
    return await service.login(db, payload)


@router.post("/refresh", response_model=AccessTokenOut)
async def refresh(payload: RefreshIn, db: DbDep):
    return await service.refresh(db, payload.refresh_token)


@router.post("/change-password", status_code=204)
async def change_password(payload: ChangePasswordIn, current_user: UserDep, db: DbDep):
    await service.change_password(db, current_user, payload.current_password, payload.new_password)


@router.get("/me")
async def me(current_user: UserDep):
    """Retourne les infos minimales du token."""
    return {
        "id": current_user.id,
        "email": current_user.email,
        "name": current_user.name,
        "role": current_user.role,
        "is_harmony_verified": current_user.is_harmony_verified,
    }