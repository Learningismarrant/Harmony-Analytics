# modules/vessel/router.py
"""
Endpoints de gestion des yachts (VesselProfile).
CRUD yacht + paramètres environnementaux JD-R + token boarding.

Règle : zéro logique métier ici. Tout passe par vessel_service.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
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
    response_model=YachtOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Créer un yacht",
)
def create_yacht(
    payload: YachtCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.create(db, payload=payload, owner_id=current_user.id)


@router.get(
    "/",
    response_model=List[YachtOut],
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Mes yachts",
)
def list_my_yachts(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_all_for_owner(db, owner_id=current_user.id)


@router.get(
    "/{yacht_id}",
    response_model=YachtOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Détail d'un yacht",
)
def get_yacht(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    yacht = service.get_secure(db, yacht_id=yacht_id, requester_id=current_user.id)
    if not yacht:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Yacht introuvable ou accès refusé."
        )
    return yacht


@router.patch(
    "/{yacht_id}",
    response_model=YachtOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Modifier un yacht",
)
def update_yacht(
    yacht_id: int,
    payload: YachtUpdateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.update(
            db, yacht_id=yacht_id, payload=payload, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.delete(
    "/{yacht_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Supprimer un yacht",
)
def delete_yacht(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        service.delete(db, yacht_id=yacht_id, requester_id=current_user.id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# PARAMÈTRES ENVIRONNEMENTAUX (JD-R)
# Alimentent F_env dans l'équation maîtresse
# ─────────────────────────────────────────────

@router.patch(
    "/{yacht_id}/environment",
    response_model=YachtOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Configurer l'environnement du yacht (JD-R)",
    description=(
        "Met à jour les paramètres JD-R : charter_intensity, management_pressure, "
        "salary_index, rest_days_ratio. Déclenche le recalcul du vessel_snapshot."
    ),
)
def update_environment(
    yacht_id: int,
    payload: YachtEnvironmentUpdateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Paramètres qui alimentent F_env = (R_yacht / D_yacht) × Resilience_ind.
    Modification déclenche un recalcul du vessel_snapshot en background.
    """
    try:
        return service.update_environment(
            db, yacht_id=yacht_id, payload=payload, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# TOKEN D'EMBARQUEMENT (QR Code)
# ─────────────────────────────────────────────

@router.post(
    "/{yacht_id}/boarding-token/refresh",
    response_model=YachtTokenOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Régénérer le token d'embarquement",
)
def refresh_boarding_token(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Génère un nouveau boarding_token. L'ancien est immédiatement invalidé."""
    try:
        return service.refresh_boarding_token(
            db, yacht_id=yacht_id, requester_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")