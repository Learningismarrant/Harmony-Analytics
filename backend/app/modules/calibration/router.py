# app/modules/calibration/router.py
"""
Endpoints du module d'étalonnage psychométrique.

Authentification : JWT propre (CalibDep) — isolé du système de rôles principal.

Routes :
    POST /calibration/auth/register           → register (public, rate-limited)
    POST /calibration/auth/login              → login    (public, rate-limited)
    GET  /calibration/catalogues              → list_catalogues   (auth required)
    GET  /calibration/me                      → get_me            (auth required)
    PATCH /calibration/me                     → update_demographics (auth required)
    GET  /calibration/catalogues              → list_catalogues   (auth required)
    GET  /calibration/catalogues/{id}/questions → get_questions   (auth required)
    POST /calibration/sessions                → start_session     (auth required)
    GET  /calibration/sessions                → list_sessions     (auth required)
    POST /calibration/sessions/{id}/responses → submit_responses  (auth required)
"""
from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException, Path, Request, status

from app.shared.deps import DbDep
from app.shared.limiter import limiter
from app.modules.calibration.deps import CalibDep, get_current_calibrator
from app.modules.calibration.service import CalibrationService
from app.modules.calibration.schemas import (
    CalibratorRegisterIn,
    CalibratorLoginIn,
    CalibratorTokenOut,
    CalibratorDemographicsIn,
    CalibratorMeOut,
    CatalogueInfoOut,
    QuestionOut,
    StartSessionIn,
    SessionOut,
    SubmitResponsesIn,
    SubmitResponsesOut,
    SessionScoreOut,
)

router = APIRouter(prefix="/calibration", tags=["Calibration"])
service = CalibrationService()


# ── Auth ─────────────────────────────────────────────────────────────────────

@router.post(
    "/auth/register",
    response_model=CalibratorTokenOut,
    status_code=status.HTTP_201_CREATED,
    summary="Enregistrement d'un calibrateur",
)
@limiter.limit("5/15minutes")
async def register(
    request: Request,
    payload: CalibratorRegisterIn,
    db: DbDep,
) -> CalibratorTokenOut:
    """Crée un compte calibrateur et retourne un JWT."""
    return await service.register(db, payload)


@router.post(
    "/auth/login",
    response_model=CalibratorTokenOut,
    summary="Connexion calibrateur",
)
@limiter.limit("5/15minutes")
async def login(
    request: Request,
    payload: CalibratorLoginIn,
    db: DbDep,
) -> CalibratorTokenOut:
    """Authentifie un calibrateur et retourne un JWT."""
    return await service.login(db, payload)


# ── Profil calibrateur ────────────────────────────────────────────────────────

@router.get(
    "/me",
    response_model=CalibratorMeOut,
    summary="Profil du calibrateur courant",
)
@limiter.limit("100/minute")
async def get_me(
    request: Request,
    db: DbDep,
    current_calibrator: CalibDep,
) -> CalibratorMeOut:
    """Retourne le profil complet du calibrateur authentifié."""
    return await service.get_me(db, current_calibrator.id)


@router.patch(
    "/me",
    response_model=CalibratorMeOut,
    summary="Mettre à jour les données démographiques",
)
@limiter.limit("100/minute")
async def update_demographics(
    request: Request,
    payload: CalibratorDemographicsIn,
    db: DbDep,
    current_calibrator: CalibDep,
) -> CalibratorMeOut:
    """
    Met à jour les données démographiques du calibrateur (PATCH sémantique).
    Ces données servent à l'analyse DIF (Differential Item Functioning).
    """
    return await service.update_demographics(db, current_calibrator.id, payload)


# ── Catalogues ────────────────────────────────────────────────────────────────

@router.get(
    "/catalogues",
    response_model=List[CatalogueInfoOut],
    summary="Liste des catalogues actifs",
)
@limiter.limit("100/minute")
async def list_catalogues(
    request: Request,
    db: DbDep,
    current_calibrator: CalibDep,
) -> List[CatalogueInfoOut]:
    """Retourne tous les catalogues de tests disponibles pour l'étalonnage."""
    return await service.list_catalogues(db)


@router.get(
    "/catalogues/{catalogue_id}/questions",
    response_model=List[QuestionOut],
    summary="Questions d'un catalogue",
)
@limiter.limit("100/minute")
async def get_questions(
    request: Request,
    db: DbDep,
    current_calibrator: CalibDep,
    catalogue_id: int = Path(..., gt=0),
) -> List[QuestionOut]:
    """Retourne les questions ordonnées du catalogue demandé."""
    return await service.get_questions(db, catalogue_id)


# ── Sessions ──────────────────────────────────────────────────────────────────

@router.post(
    "/sessions",
    response_model=SessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Démarrer une session de passation",
)
@limiter.limit("100/minute")
async def start_session(
    request: Request,
    payload: StartSessionIn,
    db: DbDep,
    current_calibrator: CalibDep,
) -> SessionOut:
    """Crée (ou reprend) une session de passation pour un catalogue donné."""
    return await service.start_session(db, current_calibrator.id, payload)


@router.get(
    "/sessions",
    response_model=List[SessionOut],
    summary="Sessions du calibrateur courant",
)
@limiter.limit("100/minute")
async def list_sessions(
    request: Request,
    db: DbDep,
    current_calibrator: CalibDep,
) -> List[SessionOut]:
    """Retourne toutes les sessions du calibrateur authentifié."""
    return await service.list_sessions(db, current_calibrator.id)


@router.post(
    "/sessions/{session_id}/responses",
    response_model=SubmitResponsesOut,
    status_code=status.HTTP_201_CREATED,
    summary="Soumettre des réponses",
)
@limiter.limit("100/minute")
async def submit_responses(
    request: Request,
    payload: SubmitResponsesIn,
    db: DbDep,
    current_calibrator: CalibDep,
    session_id: int = Path(..., gt=0),
) -> SubmitResponsesOut:
    """
    Soumet les réponses d'une session.
    Auto-complète la session si toutes les réponses ont été soumises.
    """
    try:
        return await service.submit_responses(
            db, current_calibrator.id, session_id, payload
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": True,
                "message": str(exc),
                "code": "SUBMIT_ERROR",
            },
        ) from exc


@router.get(
    "/sessions/{session_id}/score",
    response_model=SessionScoreOut,
    summary="Score CTT d'une session complétée",
)
@limiter.limit("30/minute")
async def get_session_score(
    request: Request,
    db: DbDep,
    current_calibrator: CalibDep,
    session_id: int = Path(..., gt=0),
) -> SessionScoreOut:
    """
    Calcule et retourne le score CTT d'une session terminée.

    - 404 si session introuvable.
    - 403 si la session n'appartient pas au calibrateur courant.
    - 400 (SESSION_NOT_COMPLETED) si la session n'est pas encore terminée.
    """
    return await service.get_session_score(db, current_calibrator.id, session_id)
