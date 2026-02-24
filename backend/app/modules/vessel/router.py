# modules/vessel/router.py
"""
Endpoints de gestion des yachts (VesselProfile).
CRUD yacht + paramètres environnementaux JD-R + token boarding.
"""

from fastapi import APIRouter, HTTPException, status
from typing import List

from app.shared.deps import DbDep, EmployerDep
from app.modules.vessel.service import VesselService
from app.modules.vessel.schemas import (
    YachtCreateIn,
    YachtUpdateIn,
    YachtOut,
    YachtEnvironmentUpdateIn,
    YachtTokenOut,
)

router = APIRouter(prefix="/vessels", tags=["Vessel"])
service = VesselService()


# ─────────────────────────────────────────────
# CRUD YACHTS
# ─────────────────────────────────────────────

@router.post(
    "/",
    # EmployerDep garantit déjà le rôle Client ou Admin via deps.py
    response_model=YachtOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un yacht",
)
async def create_yacht(
    payload: YachtCreateIn,
    db: DbDep,
    employer: EmployerDep,
):
    return await service.create(db, payload, employer)


@router.get(
    "/",
    response_model=List[YachtOut],
    summary="Mes yachts",
)
async def list_my_yachts(
    db: DbDep,
    employer: EmployerDep,
):
    return await service.get_all_for_employer(db, employer)


@router.get(
    "/{yacht_id}",
    response_model=YachtOut,
    summary="Détail d'un yacht",
)
async def get_yacht(
    yacht_id: int,
    db: DbDep,
    employer: EmployerDep,
):
    yacht = await service.get_secure(db, yacht_id=yacht_id, requester_id=employer.user_id)
    if not yacht:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yacht introuvable ou accès refusé."
        )
    return yacht


@router.patch(
    "/{yacht_id}",
    response_model=YachtOut,
    summary="Modifier un yacht",
)
async def update_yacht(
    yacht_id: int,
    payload: YachtUpdateIn,
    db: DbDep,
    employer: EmployerDep,
):
    try:
        return await service.update(
            db, yacht_id=yacht_id, payload=payload, requester_id=employer.user_id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.delete(
    "/{yacht_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Supprimer un yacht",
)
async def delete_yacht(
    yacht_id: int,
    db: DbDep,
    employer: EmployerDep,
):
    try:
        await service.delete(db, yacht_id=yacht_id, requester_id=employer.user_id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# PARAMÈTRES ENVIRONNEMENTAUX (JD-R)
# ─────────────────────────────────────────────

@router.patch(
    "/{yacht_id}/environment",
    response_model=YachtOut,
    summary="Configurer l'environnement du yacht (JD-R)",
    description=(
        "Met à jour les paramètres JD-R : charter_intensity, management_pressure, "
        "salary_index, rest_days_ratio."
    ),
)
async def update_environment(
    yacht_id: int,
    payload: YachtEnvironmentUpdateIn,
    db: DbDep,
    employer: EmployerDep,
):
    try:
        return await service.update_environment(
            db, yacht_id=yacht_id, payload=payload, requester_id=employer.user_id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# TOKEN D'EMBARQUEMENT (QR Code)
# ─────────────────────────────────────────────

@router.post(
    "/{yacht_id}/boarding-token/refresh",
    response_model=YachtTokenOut,
    summary="Régénérer le token d'embarquement",
)
async def refresh_boarding_token(
    yacht_id: int,
    db: DbDep,
    employer: EmployerDep,
):
    """Génère un nouveau boarding_token. L'ancien est immédiatement invalidé."""
    try:
        return await service.refresh_boarding_token(
            db, yacht_id=yacht_id, requester_id=employer.user_id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")