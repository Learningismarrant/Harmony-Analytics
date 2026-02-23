# modules/survey/router.py
"""
Endpoints des Feedback Surveys.

Changements v2 :
- cap/owner → EmployerDep
- crew (candidat) → CrewDep
"""
from fastapi import APIRouter, HTTPException, status
from typing import List

from app.shared.deps import DbDep, CrewDep, EmployerDep
from app.modules.survey.service import SurveyService
from app.modules.survey.schemas import (
    SurveyTriggerIn,
    SurveyOut,
    SurveyResponseIn,
    SurveyResponseOut,
    SurveyAggregatedOut,
)

router = APIRouter(prefix="/surveys", tags=["Surveys"])
service = SurveyService()


# ── Cap / Owner ────────────────────────────────────────────

@router.post("/trigger", response_model=SurveyOut, status_code=201)
async def trigger_survey(
    payload: SurveyTriggerIn,
    db: DbDep,
    current_employer: EmployerDep,   # v2
):
    try:
        return await service.trigger_survey(
            db,
            yacht_id=payload.yacht_id,
            trigger_type=payload.trigger_type,
            employer=current_employer,
            target_crew_profile_ids=payload.target_crew_profile_ids,  # v2
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")


@router.get("/{survey_id}/results", response_model=SurveyAggregatedOut)
async def get_survey_results(
    survey_id: int,
    db: DbDep,
    current_employer: EmployerDep,
):
    try:
        results = await service.get_survey_results(
            db, survey_id, employer=current_employer
        )
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    if not results:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Survey introuvable.")
    return results


@router.get("/yacht/{yacht_id}/history")
async def get_yacht_survey_history(
    yacht_id: int,
    db: DbDep,
    current_employer: EmployerDep,
):
    try:
        return await service.get_yacht_survey_history(db, yacht_id, employer=current_employer)
    except PermissionError:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")


# ── Crew ───────────────────────────────────────────────────

@router.get("/pending", response_model=List[SurveyOut])
async def get_pending_surveys(db: DbDep, current_crew: CrewDep):
    """Surveys en attente pour ce marin."""
    return await service.get_pending_surveys(db, crew=current_crew)


@router.post("/{survey_id}/respond", response_model=SurveyResponseOut, status_code=201)
async def submit_survey_response(
    survey_id: int,
    payload: SurveyResponseIn,
    db: DbDep,
    current_crew: CrewDep,   # v2
):
    try:
        return await service.submit_response(
            db,
            survey_id=survey_id,
            crew=current_crew,      # v2
            payload=payload,
        )
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))
    except ValueError as e:
        code = str(e)
        if code == "ALREADY_RESPONDED":
            raise HTTPException(status.HTTP_409_CONFLICT, "Vous avez déjà répondu.")
        raise HTTPException(status.HTTP_400_BAD_REQUEST, code)