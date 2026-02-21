# modules/survey/router.py
"""
Endpoints du système de Feedback Surveys.

Deux acteurs :
- Cap/Owner : déclenche les surveys, consulte les résultats agrégés
- Crew (candidat) : reçoit les surveys, soumet ses réponses
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
from app.modules.survey.service import SurveyService
from app.modules.survey.schemas import (
    SurveyTriggerIn,
    SurveyTriggerOut,
    SurveyResponseIn,
    SurveyResponseOut,
    SurveyResultsOut,
    PendingSurveyOut,
)

router = APIRouter(prefix="/surveys", tags=["Surveys"])
service = SurveyService()


# ─────────────────────────────────────────────
# CAP / OWNER — Déclenchement & Résultats
# ─────────────────────────────────────────────

@router.post(
    "/trigger",
    response_model=SurveyTriggerOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Déclencher un survey",
    description=(
        "Le cap/owner déclenche un survey sur son équipage. "
        "Types disponibles : post_charter, post_season, monthly_pulse, "
        "conflict_event, exit_interview. "
        "Notifie automatiquement les membres ciblés."
    ),
)
def trigger_survey(
    payload: SurveyTriggerIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.trigger_survey(
            db,
            yacht_id=payload.yacht_id,
            trigger_type=payload.trigger_type,
            triggered_by_id=current_user.id,
            target_crew_ids=payload.target_crew_ids,
        )
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


@router.get(
    "/{survey_id}/results",
    response_model=SurveyResultsOut,
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Résultats agrégés d'un survey",
    description=(
        "Retourne les résultats anonymisés et agrégés. "
        "Les réponses individuelles ne sont pas exposées ici (anonymat garanti)."
    ),
)
def get_survey_results(
    survey_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        results = service.get_survey_results(db, survey_id, requester_id=current_user.id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")

    if not results:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Survey introuvable.")
    return results


@router.get(
    "/yacht/{yacht_id}/history",
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Historique des surveys d'un yacht",
)
def get_yacht_survey_history(
    yacht_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.get_yacht_survey_history(db, yacht_id, requester_id=current_user.id)
    except PermissionError:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")


# ─────────────────────────────────────────────
# CREW — Réception & Soumission
# ─────────────────────────────────────────────

@router.get(
    "/pending",
    response_model=List[PendingSurveyOut],
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Mes surveys en attente",
)
def get_pending_surveys(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Retourne les surveys auxquels le marin doit encore répondre."""
    return service.get_pending_surveys(db, user_id=current_user.id)


@router.post(
    "/{survey_id}/respond",
    response_model=SurveyResponseOut,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(role_required(["candidate", "admin"]))],
    summary="Répondre à un survey",
    description=(
        "Le marin soumet sa réponse. "
        "Déclenche la mise à jour du vessel_snapshot et du RecruitmentEvent associé. "
        "Si le seuil ML est atteint, la régression est schedulée en background."
    ),
)
def submit_survey_response(
    survey_id: int,
    payload: SurveyResponseIn,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    try:
        return service.submit_response(
            db,
            survey_id=survey_id,
            respondent_id=current_user.id,
            payload=payload,
        )
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except ValueError as e:
        code = str(e)
        if code == "ALREADY_RESPONDED":
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Vous avez déjà répondu à ce survey."
            )
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=code)


