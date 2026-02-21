# modules/identity/router.py
"""
Endpoints de gestion du profil identitaire du candidat.
Couvre : identité, expériences, documents, rapports psychométriques.

Design : endpoints modulaires pour éviter l'over-fetching.
Le full-profile reste disponible mais son usage est découragé en polling.
"""
from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import Optional

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
from .service import IdentityService
from .schemas import (
    FullCrewProfileOut,
    UserIdentityOut,
    IdentityUpdateIn,
    ExperienceCreateIn,
    ExperienceOut,
    DocumentOut,
    UploadResponseOut,
    PsychometricReportOut,
    OnboardingAdviceOut,
)

router = APIRouter(prefix="/identity", tags=["Identity"])
service = IdentityService()


# ─────────────────────────────────────────────
# FULL PROFILE — usage restreint
# ─────────────────────────────────────────────

@router.get(
    "/candidate/{candidate_id}",
    response_model=FullCrewProfileOut,
    summary="Profil complet ⚠️ endpoint lourd",
    description=(
        "Récupère l'intégralité du profil : identité, expériences, documents, rapports. "
        "Utiliser uniquement au premier chargement. Ne pas utiliser pour du polling."
    ),
)
def get_full_profile(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    profile = service.get_full_profile(db, candidate_id=candidate_id, requester=current_user)
    if not profile:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé.")
    return profile


# ─────────────────────────────────────────────
# ENDPOINTS MODULAIRES — légers
# ─────────────────────────────────────────────

@router.get(
    "/candidate/{candidate_id}/identity",
    response_model=UserIdentityOut,
    summary="Identité uniquement",
)
def get_identity(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """À utiliser après un PATCH /identity/me pour rafraîchir sans tout recharger."""
    data = service.get_identity(db, candidate_id=candidate_id, requester=current_user)
    if not data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé.")
    return data


@router.get(
    "/candidate/{candidate_id}/experiences",
    response_model=list[ExperienceOut],
    summary="Expériences professionnelles",
)
def get_experiences(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = service.get_experiences(db, candidate_id=candidate_id, requester=current_user)
    if data is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé.")
    return data


@router.get(
    "/candidate/{candidate_id}/documents",
    response_model=list[DocumentOut],
    summary="Documents et certificats",
    description="Peut être utilisé en polling léger pour les vérifications Harmony.",
)
def get_documents(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    data = service.get_documents(db, candidate_id=candidate_id, requester=current_user)
    if data is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès non autorisé.")
    return data


@router.get(
    "/candidate/{candidate_id}/reports",
    response_model=PsychometricReportOut,
    summary="Rapports psychométriques",
)
def get_reports(
    candidate_id: int,
    view_mode: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retourne les rapports psychométriques issus du psychometric_snapshot.
    view_mode='onboarding' → inclut les conseils d'intégration.
    """
    data = service.get_reports(
        db,
        candidate_id=candidate_id,
        requester=current_user,
        force_onboarding=(view_mode == "onboarding"),
    )
    if not data:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
    return data


@router.get(
    "/candidate/{candidate_id}/onboarding-advice",
    response_model=OnboardingAdviceOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Conseils d'onboarding post-recrutement",
)
def get_onboarding_advice(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Accessible uniquement si le candidat est en statut JOINED dans une campagne du client.
    Extrait les onboarding_tips du psychometric_snapshot.
    """
    advice = service.get_onboarding_advice(
        db, candidate_id=candidate_id, requester_id=current_user.id
    )
    if not advice:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Le candidat doit être recruté pour accéder aux conseils d'onboarding."
        )
    return advice


# ─────────────────────────────────────────────
# MISE À JOUR IDENTITÉ
# ─────────────────────────────────────────────

@router.patch(
    "/me",
    response_model=UserIdentityOut,
    summary="Mettre à jour mon identité",
    description=(
        "Retourne uniquement l'identité mise à jour. "
        "Le frontend doit mettre à jour son cache local, sans refetch du full-profile."
    ),
)
def update_my_identity(
    payload: IdentityUpdateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    service.update_identity(db, user=current_user, payload=payload)
    return service.get_identity(db, candidate_id=current_user.id, requester=current_user)


# ─────────────────────────────────────────────
# EXPÉRIENCES
# ─────────────────────────────────────────────

@router.post(
    "/me/experiences",
    response_model=ExperienceOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Ajouter une expérience",
)
def add_experience(
    payload: ExperienceCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.add_experience(db, user=current_user, payload=payload)


# ─────────────────────────────────────────────
# DOCUMENTS & UPLOAD
# ─────────────────────────────────────────────

@router.post(
    "/me/documents",
    response_model=UploadResponseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un document ou un avatar",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    title: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Upload d'un document ou d'un avatar.
    - Avatar (title='AVATAR_USER') : traitement synchrone immédiat.
    - Document : sauvegarde immédiate + vérification Harmony en background.
    """
    return await service.upload_document(
        db=db,
        user=current_user,
        title=title,
        file=file,
        background_tasks=background_tasks,
    )