# modules/recruitment/router.py
"""
Endpoints de recrutement — campagnes, matching, décisions.

Changements v2 :
- Employer → EmployerDep (EmployerProfile)
- Candidat → CrewDep (CrewProfile)
- crew_profile_id dans les paths (était candidate_id / user_id)
"""
from fastapi import APIRouter, HTTPException, status
from typing import List, Optional

from app.shared.deps import DbDep, CrewDep, EmployerDep
from app.modules.recruitment.service import RecruitmentService
from app.modules.recruitment.schemas import (
    CampaignCreateIn,
    CampaignUpdateIn,
    CampaignOut,
    CampaignPublicOut,
    MatchResultOut,
    RecruitmentImpactOut,
    CandidateDecisionIn,
    CampaignStatsOut,
    MyApplicationOut,
)

router = APIRouter(prefix="/recruitment", tags=["Recruitment"])
service = RecruitmentService()


# ── Campagnes (employer) ───────────────────────────────────

@router.post("/campaigns", response_model=CampaignOut, status_code=201)
async def create_campaign(
    payload: CampaignCreateIn,
    db: DbDep,
    current_employer: EmployerDep,
):
    return await service.create_campaign(db, payload, employer=current_employer)


@router.get("/campaigns", response_model=List[CampaignOut])
async def list_my_campaigns(
    db: DbDep,
    current_employer: EmployerDep,
    archived: bool = False,
):
    return await service.get_my_campaigns(db, employer=current_employer, is_archived=archived)


@router.patch("/campaigns/{campaign_id}", response_model=CampaignOut)
async def update_campaign(
    campaign_id: int,
    payload: CampaignUpdateIn,
    db: DbDep,
    current_employer: EmployerDep,
):
    try:
        return await service.update_campaign(db, campaign_id, payload, employer=current_employer)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")


@router.delete("/campaigns/{campaign_id}", status_code=204)
async def archive_campaign(
    campaign_id: int,
    db: DbDep,
    current_employer: EmployerDep,
):
    try:
        await service.archive_campaign(db, campaign_id, employer=current_employer)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")


# ── Matching ──────────────────────────────────────────────

@router.get("/campaigns/{campaign_id}/matching", response_model=List[MatchResultOut])
async def get_matching(
    campaign_id: int,
    db: DbDep,
    current_employer: EmployerDep,
):
    """
    Score MLPSM pour tous les candidats de la campagne.
    Trié par y_success décroissant.
    Utilise compute_batch(with_delta=True) → MLPSMResult riche.
    """
    try:
        return await service.get_matching(db, campaign_id, employer=current_employer)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")


@router.get(
    "/campaigns/{campaign_id}/impact/{crew_profile_id}",  # v2 : était candidate_id
    response_model=RecruitmentImpactOut,
)
async def get_candidate_impact(
    campaign_id: int,
    crew_profile_id: int,   # v2
    db: DbDep,
    current_employer: EmployerDep,
):
    """
    Rapport What-If détaillé pour un candidat.
    Retourne to_impact_report() du MLPSMResult complet.
    """
    try:
        return await service.get_candidate_impact(
            db, campaign_id, crew_profile_id, employer=current_employer
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


# ── Décisions (employer) ───────────────────────────────────

@router.post("/campaigns/{campaign_id}/hire/{crew_profile_id}", status_code=200)
async def hire_candidate(
    campaign_id: int,
    crew_profile_id: int,   # v2
    db: DbDep,
    current_employer: EmployerDep,
):
    """
    Embauche un candidat + crée le RecruitmentEvent (pour ML Temps 2).
    """
    try:
        return await service.hire_candidate(
            db, campaign_id, crew_profile_id, employer=current_employer
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.post("/campaigns/{campaign_id}/reject/{crew_profile_id}", status_code=200)
async def reject_candidate(
    campaign_id: int,
    crew_profile_id: int,   # v2
    payload: CandidateDecisionIn,
    db: DbDep,
    current_employer: EmployerDep,
):
    try:
        return await service.reject_candidate(
            db,
            campaign_id,
            crew_profile_id,
            reason=payload.rejected_reason or "",
            employer=current_employer,
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))


@router.get("/campaigns/{campaign_id}/stats", response_model=CampaignStatsOut)
async def get_campaign_stats(
    campaign_id: int,
    db: DbDep,
    current_employer: EmployerDep,
):
    try:
        return await service.get_campaign_statistics(db, campaign_id, employer=current_employer)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")


# ── Candidat ──────────────────────────────────────────────

@router.post("/apply/{invite_token}", status_code=201)
async def apply_to_campaign(
    invite_token: str,
    db: DbDep,
    current_crew: CrewDep,   # v2
):
    """Le candidat postule via le token d'invitation (QR code / lien)."""
    try:
        return await service.apply_to_campaign(db, invite_token, crew=current_crew)
    except ValueError as e:
        code = str(e)
        if code == "ALREADY_APPLIED":
            raise HTTPException(status.HTTP_409_CONFLICT, "Vous avez déjà postulé.")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, code)


@router.get("/my-applications", response_model=List[MyApplicationOut])
async def get_my_applications(db: DbDep, current_crew: CrewDep):
    """Toutes mes candidatures — vue marin."""
    return await service.get_my_applications(db, crew=current_crew)