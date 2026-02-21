# modules/assessment/router.py
"""
Endpoints du cycle de vie des évaluations psychométriques.
Catalogue → Questions → Soumission → Résultats

Règle : ce fichier ne touche jamais la DB ni l'engine.
Tout passe par assessment_service.
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List

from app.core.database import get_db
from app.shared.deps import get_current_user, role_required
from app.modules.assessment.service import AssessmentService
from app.modules.assessment.schemas import (
    TestInfoOut,
    QuestionOut,
    SubmitTestIn,
    TestResultOut,
)

router = APIRouter(prefix="/assessments", tags=["Assessment"])
service = AssessmentService()


# ─────────────────────────────────────────────
# CATALOGUE
# ─────────────────────────────────────────────

@router.get(
    "/catalogue",
    response_model=List[TestInfoOut],
    summary="Liste des tests disponibles",
)
def list_catalogue(db: Session = Depends(get_db)):
    """
    Retourne tous les tests actifs du catalogue.
    Public pour les candidats authentifiés.
    """
    tests = service.get_catalogue(db)
    if not tests:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Aucun test disponible pour le moment."
        )
    return tests


# ─────────────────────────────────────────────
# SESSION DE TEST
# ─────────────────────────────────────────────

@router.get(
    "/{test_id}/questions",
    response_model=List[QuestionOut],
    summary="Questions d'un test",
)
def get_questions(
    test_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Retourne les questions d'un test.
    Vérifie que le candidat n'a pas déjà une session en cours.
    """
    questions = service.get_questions_for_user(db, test_id, current_user.id)
    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test introuvable ou sans questions."
        )
    return questions


@router.post(
    "/submit",
    response_model=TestResultOut,
    status_code=status.HTTP_201_CREATED,
    summary="Soumettre les réponses d'un test",
)
def submit_test(
    payload: SubmitTestIn,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Traite les réponses, calcule les scores, déclenche la mise à jour
    du psychometric_snapshot en arrière-plan.

    Synchrone  : scoring + sauvegarde résultat + snapshot crew
    Background : refresh vessel_snapshot + fleet_snapshot si applicable
    """
    try:
        result = service.submit_and_score(
            db=db,
            user_id=current_user.id,
            test_id=payload.test_id,
            responses=payload.responses,
            background_tasks=background_tasks,
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except PermissionError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))


# ─────────────────────────────────────────────
# RÉSULTATS (lecture)
# ─────────────────────────────────────────────

@router.get(
    "/results/me",
    response_model=List[TestResultOut],
    summary="Mes résultats de tests",
)
def get_my_results(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Historique des résultats du candidat connecté."""
    return service.get_results_for_user(db, current_user.id)


@router.get(
    "/results/{candidate_id}",
    response_model=List[TestResultOut],
    dependencies=[Depends(role_required(["client", "admin"]))],
    summary="Résultats d'un candidat (client/admin)",
)
def get_candidate_results(
    candidate_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Accès client/admin aux résultats d'un candidat.
    Le service vérifie que le candidat est bien dans une campagne du client.
    """
    results = service.get_results_for_candidate(
        db, candidate_id=candidate_id, requester_id=current_user.id
    )
    if results is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé.")
    return results