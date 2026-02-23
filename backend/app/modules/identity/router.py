# modules/identity/router.py
"""
Endpoints de gestion du profil identitaire du candidat.
Couvre : identité, expériences, documents, rapports psychométriques.

Changements v2 :
- Session sync → DbDep (AsyncSession)
- get_current_user → CrewDep / EmployerDep / UserDep selon l'endpoint
- candidate_id → crew_profile_id dans les paths
- Toutes les fonctions sync → async
- role_required() remplacé par EmployerDep directement
"""
from fastapi import APIRouter, HTTPException, File, Form, UploadFile, BackgroundTasks, status
from typing import Optional

from app.shared.deps import DbDep, UserDep, CrewDep, EmployerDep
from app.modules.identity.service import IdentityService
from app.modules.identity.schemas import (
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


# ── Full profile (usage restreint) ────────────────────────

@router.get(
    "/candidate/{crew_profile_id}",           # v2 : crew_profile_id (était candidate_id)
    response_model=FullCrewProfileOut,
    summary="Profil complet ⚠️ endpoint lourd",
    description=(
        "Intégralité du profil : identité, expériences, documents, rapports. "
        "Utiliser uniquement au premier chargement. Ne pas utiliser pour du polling."
    ),
)
async def get_full_profile(
    crew_profile_id: int,
    db: DbDep,
    current_user: UserDep,    # v2 : UserDep — accès depuis crew OU employer
):
    """
    Accès depuis deux contextes :
    - Candidat (CrewProfile) : auto-consultation
    - Client (EmployerProfile) : candidat dans sa campagne ou son équipage
    Le service.get_full_profile() résout le contexte via resolve_access_context().
    """
    profile = await service.get_full_profile(
        db, crew_profile_id=crew_profile_id, requester=current_user
    )
    if not profile:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès non autorisé.")
    return profile


# ── Endpoints modulaires (légers) ─────────────────────────

@router.get(
    "/candidate/{crew_profile_id}/identity",
    response_model=UserIdentityOut,
    summary="Identité uniquement",
)
async def get_identity(
    crew_profile_id: int,
    db: DbDep,
    current_user: UserDep,
):
    """À utiliser après un PATCH /identity/me pour rafraîchir sans tout recharger."""
    data = await service.get_identity(
        db, crew_profile_id=crew_profile_id, requester=current_user
    )
    if not data:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès non autorisé.")
    return data


@router.get(
    "/candidate/{crew_profile_id}/experiences",
    response_model=list[ExperienceOut],
    summary="Expériences professionnelles",
)
async def get_experiences(
    crew_profile_id: int,
    db: DbDep,
    current_user: UserDep,
):
    data = await service.get_experiences(
        db, crew_profile_id=crew_profile_id, requester=current_user
    )
    if data is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès non autorisé.")
    return data


@router.get(
    "/candidate/{crew_profile_id}/documents",
    response_model=list[DocumentOut],
    summary="Documents et certificats",
    description="Peut être utilisé en polling léger pour les vérifications Harmony.",
)
async def get_documents(
    crew_profile_id: int,
    db: DbDep,
    current_user: UserDep,
):
    data = await service.get_documents(
        db, crew_profile_id=crew_profile_id, requester=current_user
    )
    if data is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès non autorisé.")
    return data


@router.get(
    "/candidate/{crew_profile_id}/reports",
    response_model=PsychometricReportOut,
    summary="Rapports psychométriques",
)
async def get_reports(
    crew_profile_id: int,
    db: DbDep,
    current_user: UserDep,
    view_mode: Optional[str] = None,
):
    """
    view_mode='onboarding' → inclut les conseils d'intégration personnalisés.
    Accessible depuis tout contexte autorisé (candidat, recruteur, manager).
    """
    data = await service.get_reports(
        db,
        crew_profile_id=crew_profile_id,
        requester=current_user,
        force_onboarding=(view_mode == "onboarding"),
    )
    if not data:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    return data


@router.get(
    "/candidate/{crew_profile_id}/onboarding-advice",
    response_model=OnboardingAdviceOut,
    summary="Conseils d'onboarding post-recrutement",
    description=(
        "Accessible uniquement si le candidat est en statut JOINED "
        "dans une campagne de cet employeur. "
        "Extrait les onboarding_tips du psychometric_snapshot."
    ),
)
async def get_onboarding_advice(
    crew_profile_id: int,
    db: DbDep,
    current_employer: EmployerDep,    # v2 : EmployerDep (était role_required("client"))
):
    """
    v2 : EmployerDep garantit que le requester est bien un EmployerProfile.
    Le service vérifie en plus que le candidat est JOINED dans une de ses campagnes.
    """
    advice = await service.get_onboarding_advice(
        db,
        crew_profile_id=crew_profile_id,
        employer_profile_id=current_employer.id,    # v2
    )
    if not advice:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Le candidat doit être recruté pour accéder aux conseils d'onboarding."
        )
    return advice


# ── Mise à jour identité ───────────────────────────────────

@router.patch(
    "/me",
    response_model=UserIdentityOut,
    summary="Mettre à jour mon identité",
    description=(
        "Retourne uniquement l'identité mise à jour. "
        "Le frontend met à jour son cache local sans refetch du full-profile."
    ),
)
async def update_my_identity(
    payload: IdentityUpdateIn,
    db: DbDep,
    current_crew: CrewDep,    # v2 : CrewDep — seul le marin modifie son profil
):
    """
    v2 : current_crew (CrewProfile) remplace current_user.
    Les champs identitaires modifiables (nom, bio, disponibilité...)
    sont sur CrewProfile et User — le service orchestre les deux.
    """
    await service.update_identity(db, crew=current_crew, payload=payload)
    return await service.get_identity(
        db, crew_profile_id=current_crew.id, requester=current_crew.user
    )


# ── Expériences ────────────────────────────────────────────

@router.post(
    "/me/experiences",
    response_model=ExperienceOut,
    status_code=status.HTTP_201_CREATED,
    summary="Ajouter une expérience",
)
async def add_experience(
    payload: ExperienceCreateIn,
    db: DbDep,
    current_crew: CrewDep,    # v2 : CrewDep
):
    """
    v2 : lie l'expérience à crew_profile_id (pas user_id).
    """
    return await service.add_experience(db, crew=current_crew, payload=payload)


# ── Documents & Upload ─────────────────────────────────────

@router.post(
    "/me/documents",
    response_model=UploadResponseOut,
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un document ou un avatar",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    db: DbDep,
    current_crew: CrewDep,    # v2 : CrewDep
    title: str = Form(...),
    file: UploadFile = File(...),
):
    """
    Upload d'un document ou d'un avatar.
    - Avatar (title='AVATAR_USER') : traitement synchrone immédiat.
    - Document : sauvegarde immédiate + vérification Harmony en background.

    v2 : current_crew.user_id → UserDocument.user_id (les documents restent
    sur User pour l'accès cross-profil par l'admin).
    """
    return await service.upload_document(
        db=db,
        crew=current_crew,
        title=title,
        file=file,
        background_tasks=background_tasks,
    )