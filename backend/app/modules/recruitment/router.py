# modules/recruitment/router.py
"""
Endpoints du cycle de vie complet d'une campagne de recrutement.
Couvre : CRUD campagne, statuts, matching psychométrique, décisions candidats.

Architecture :
- Toute logique métier → recruitment_service
- Matching psychométrique → engine/matching/* via le service
- Zéro import de crud/, models/ ou engine/ directement ici
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
from app.shared.enums import CampaignStatus
from app.modules.recruitment.service import RecruitmentService
from app.modules.recruitment.schemas import (
    CampaignCreateIn,
    CampaignUpdateIn,
    CampaignOut,
    CampaignOverviewOut,
    CampaignMatchResultOut,
    CampaignStatisticsOut,
    CandidateDecisionIn,
    CandidateDecisionOut,
    BulkRejectIn,
    CampaignPublicOut,
    MyApplicationOut,
    RecruitmentImpactOut,
)

router = APIRouter(prefix="/recruitment", tags=["Recruitment"])
service = RecruitmentService()


# ─────────────────────────────────────────────
# CRUD CAMPAGNES
# ─────────────────────────────────────────────

@router.post(
    "/campaigns",
    response_model=CampaignOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Créer une campagne",
)
def create_campaign(
    payload: CampaignCreateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Crée une campagne avec vérifications :
    propriété du yacht, absence de doublon actif, validation des données.
    """
    try:
        return service.create_campaign(db, payload=payload, client_id=current_user.id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get(
    "/campaigns",
    response_model=List[CampaignOverviewOut],
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Mes campagnes",
)
def list_campaigns(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    campaign_status: Optional[CampaignStatus] = Query(None, alias="status"),
    is_archived: bool = Query(False),
):
    return service.list_campaigns(
        db,
        client_id=current_user.id,
        campaign_status=campaign_status,
        is_archived=is_archived,
    )


@router.get(
    "/campaigns/{campaign_id}",
    response_model=CampaignOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Détail d'une campagne",
)
def get_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    campaign = service.get_campaign(db, campaign_id=campaign_id, client_id=current_user.id)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campagne introuvable.")
    return campaign


@router.patch(
    "/campaigns/{campaign_id}",
    response_model=CampaignOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Modifier une campagne",
)
def update_campaign(
    campaign_id: int,
    payload: CampaignUpdateIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.update_campaign(
            db, campaign_id=campaign_id, payload=payload, client_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.delete(
    "/campaigns/{campaign_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Supprimer une campagne (soft delete)",
)
def delete_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        service.delete_campaign(db, campaign_id=campaign_id, client_id=current_user.id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# ─────────────────────────────────────────────
# STATUTS & CYCLE DE VIE
# ─────────────────────────────────────────────

@router.patch(
    "/campaigns/{campaign_id}/status",
    response_model=CampaignOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Changer le statut (DRAFT → OPEN → CLOSED)",
)
def change_status(
    campaign_id: int,
    payload: dict,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        new_status = CampaignStatus(payload.get("status"))
        return service.change_status(
            db, campaign_id=campaign_id, new_status=new_status, client_id=current_user.id
        )
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Statut invalide. Valeurs acceptées : DRAFT, OPEN, CLOSED."
        )


@router.post(
    "/campaigns/{campaign_id}/archive",
    response_model=CampaignOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Archiver (rejette automatiquement les candidats non embauchés)",
)
def archive_campaign(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.archive_campaign(
            db, campaign_id=campaign_id, client_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# MATCHING & ANALYTICS
# Alimentés par engine/matching/* via le service
# ─────────────────────────────────────────────

@router.get(
    "/campaigns/{campaign_id}/matching",
    response_model=List[CampaignMatchResultOut],
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Classement psychométrique des candidats",
    description=(
        "Retourne le matching sur 3 axes : "
        "candidat vs SME, candidat vs pool, candidat vs équipe cible (T3). "
        "Trié : Hired → Score décroissant → Rejected."
    ),
)
def get_matching(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.get_matching(
            db, campaign_id=campaign_id, client_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.get(
    "/campaigns/{campaign_id}/impact/{candidate_id}",
    response_model=RecruitmentImpactOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Simulation d'impact recrutement (What-If)",
    description=(
        "Calcule le delta sur la dynamique d'équipe si ce candidat est recruté : "
        "impact sur min(agréabilité), σ(conscienciosité), μ(stabilité émotionnelle), "
        "score Ŷ_success."
    ),
)
def get_recruitment_impact(
    campaign_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Endpoint What-If : 'Que se passe-t-il si j'embauche ce candidat ?'
    Utilise engine/recruitment/simulator.py via le service.
    """
    impact = service.simulate_recruitment_impact(
        db,
        campaign_id=campaign_id,
        candidate_id=candidate_id,
        client_id=current_user.id,
    )
    if not impact:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Candidat ou campagne introuvable."
        )
    return impact


@router.get(
    "/campaigns/{campaign_id}/statistics",
    response_model=CampaignStatisticsOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Statistiques de la campagne",
)
def get_statistics(
    campaign_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.get_statistics(
            db, campaign_id=campaign_id, client_id=current_user.id
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# DÉCISIONS CANDIDATS
# ─────────────────────────────────────────────

@router.post(
    "/campaigns/{campaign_id}/candidates/{candidate_id}/joined",
    response_model=CandidateDecisionOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Passer en onboarding",
)
def joined_onboarding(
    campaign_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.process_joined_onboarding(
            db, campaign_id=campaign_id, candidate_id=candidate_id, client_id=current_user.id
        )
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/campaigns/{campaign_id}/candidates/{candidate_id}/hire",
    response_model=CandidateDecisionOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Recruter un candidat",
)
def hire_candidate(
    campaign_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.process_hiring(
            db, campaign_id=campaign_id, candidate_id=candidate_id, client_id=current_user.id
        )
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/campaigns/{campaign_id}/candidates/{candidate_id}/unhire",
    response_model=CandidateDecisionOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Annuler le recrutement",
)
def unhire_candidate(
    campaign_id: int,
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.process_unhire(
            db, campaign_id=campaign_id, candidate_id=candidate_id, client_id=current_user.id
        )
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/campaigns/{campaign_id}/candidates/{candidate_id}/reject",
    response_model=CandidateDecisionOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Rejeter un candidat",
)
def reject_candidate(
    campaign_id: int,
    candidate_id: int,
    payload: CandidateDecisionIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.process_rejection(
            db,
            campaign_id=campaign_id,
            candidate_id=candidate_id,
            reason=payload.rejected_reason,
            client_id=current_user.id,
        )
    except (PermissionError, ValueError) as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/campaigns/{campaign_id}/candidates/bulk-reject",
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Rejet en masse",
)
def bulk_reject(
    campaign_id: int,
    payload: BulkRejectIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        count = service.bulk_reject(
            db,
            campaign_id=campaign_id,
            candidate_ids=payload.candidate_ids,
            reason=payload.reason,
            client_id=current_user.id,
        )
        return {"rejected_count": count}
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# VUE CANDIDAT
# ─────────────────────────────────────────────

@router.get(
    "/my-applications",
    response_model=List[MyApplicationOut],
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Mes candidatures",
)
def get_my_applications(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    return service.get_candidate_applications(db, candidate_id=current_user.id)


# ─────────────────────────────────────────────
# ENDPOINTS PUBLICS (sans auth ou auth candidat)
# ─────────────────────────────────────────────

@router.get(
    "/public/{invite_token}",
    response_model=CampaignPublicOut,
    summary="Informations publiques d'une campagne (via QR code)",
)
def get_public_campaign(
    invite_token: str,
    db: Session = Depends(get_db),
):
    """Accessible sans authentification pour l'affichage pré-candidature."""
    campaign = service.get_public_campaign(db, invite_token=invite_token)
    if not campaign:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Campagne introuvable.")
    if campaign.get("is_archived"):
        raise HTTPException(status_code=status.HTTP_410_GONE, detail="Cette campagne n'est plus active.")
    return campaign


@router.post(
    "/public/{invite_token}/join",
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["candidate"]))],
    summary="Postuler via lien d'invitation",
)
def join_campaign(
    invite_token: str,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.join_campaign(
            db, invite_token=invite_token, candidate_id=current_user.id
        )
    except ValueError as e:
        code = str(e)
        if code == "CAMPAIGN_CLOSED":
            raise HTTPException(status_code=status.HTTP_410_GONE, detail="Cette campagne n'accepte plus de candidatures.")
        if code == "ALREADY_APPLIED":
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Vous avez déjà postulé.")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)