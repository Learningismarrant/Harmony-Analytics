# modules/assessment/router.py
"""
Endpoints du cycle de vie des évaluations psychométriques.

Changements v2 :
- current_user → current_crew (CrewProfile) pour les candidats
- Accès client via employer (EmployerProfile)
- service.submit_and_score reçoit crew (CrewProfile)
"""
from fastapi import APIRouter, BackgroundTasks, HTTPException, status
from typing import List

from app.shared.deps import DbDep, CrewDep, EmployerDep, UserDep
from app.modules.assessment.service import AssessmentService
from app.modules.assessment.schemas import (
    TestInfoOut,
    QuestionOut,
    SubmitTestIn,
    TestResultOut,
)

router = APIRouter(prefix="/assessments", tags=["Assessment"])
service = AssessmentService()


# ── Catalogue ──────────────────────────────────────────────

@router.get("/catalogue", response_model=List[TestInfoOut])
async def list_catalogue(db: DbDep):
    """Tests actifs — public pour tout utilisateur authentifié."""
    tests = await service.get_catalogue(db)
    if not tests:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aucun test disponible.")
    return tests


# ── Session de test ────────────────────────────────────────

@router.get("/{test_id}/questions", response_model=List[QuestionOut])
async def get_questions(
    test_id: int,
    db: DbDep,
    current_crew: CrewDep,      # v2 : CrewProfile requis
):
    questions = await service.get_questions_for_crew(db, test_id, current_crew.id)
    if not questions:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Test introuvable ou sans questions.")
    return questions


@router.post("/submit", response_model=TestResultOut, status_code=201)
async def submit_test(
    payload: SubmitTestIn,
    background_tasks: BackgroundTasks,
    db: DbDep,
    current_crew: CrewDep,      # v2 : le marin qui soumet
):
    """
    Traite les réponses, calcule les scores.
    Synchrone  : scoring + sauvegarde + refresh psychometric_snapshot
    Background : refresh vessel_snapshot + fleet_snapshot
    """
    try:
        return await service.submit_and_score(
            db=db,
            crew=current_crew,          # v2 : CrewProfile complet
            test_id=payload.test_id,
            responses=payload.responses,
            background_tasks=background_tasks,
        )
    except ValueError as e:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(e))
    except PermissionError as e:
        raise HTTPException(status.HTTP_403_FORBIDDEN, str(e))


# ── Résultats (lecture) ────────────────────────────────────

@router.get("/results/me", response_model=List[TestResultOut])
async def get_my_results(db: DbDep, current_crew: CrewDep):
    """Mes résultats — filtré via crew_profile_id."""
    return await service.get_results_for_crew(db, current_crew.id)


@router.get("/results/{crew_profile_id}", response_model=List[TestResultOut])
async def get_candidate_results(
    crew_profile_id: int,
    db: DbDep,
    current_employer: EmployerDep,   # v2 : client via EmployerProfile
):
    """
    Accès client/admin aux résultats d'un candidat.
    Vérifie que le candidat est dans une campagne ou un équipage de l'employer.
    """
    results = await service.get_results_for_candidate(
        db,
        crew_profile_id=crew_profile_id,
        requester_employer_id=current_employer.id,  # v2
    )
    if results is None:
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Accès refusé.")
    return results