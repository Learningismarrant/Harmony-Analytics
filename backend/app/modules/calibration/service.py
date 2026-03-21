# app/modules/calibration/service.py
"""
Orchestration du module calibration.

Logique métier uniquement — zéro SQL direct.
Toutes les opérations DB passent par CalibrationRepository.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.modules.calibration.repository import CalibrationRepository
from app.modules.calibration.schemas import (
    CalibratorRegisterIn,
    CalibratorLoginIn,
    CalibratorTokenOut,
    CatalogueInfoOut,
    QuestionOut,
    StartSessionIn,
    SessionOut,
    SubmitResponsesIn,
    SubmitResponsesOut,
)

repo = CalibrationRepository()


def _build_token(calibrator_id: int, name: str) -> CalibratorTokenOut:
    """Génère un JWT pour un calibrateur."""
    access_token = create_access_token(
        {"sub": str(calibrator_id), "role": "calibrator"}
    )
    return CalibratorTokenOut(
        access_token=access_token,
        token_type="bearer",
        calibrator_id=calibrator_id,
        name=name,
    )


class CalibrationService:

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def register(
        self, db: AsyncSession, data: CalibratorRegisterIn
    ) -> CalibratorTokenOut:
        """
        Enregistre un nouveau calibrateur.
        - 409 si email déjà utilisé.
        """
        existing = await repo.get_calibrator_by_email(db, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": True,
                    "message": "Un compte avec cet email existe déjà.",
                    "code": "EMAIL_ALREADY_EXISTS",
                },
            )

        calibrator = await repo.create_calibrator(
            db=db,
            email=data.email,
            name=data.name,
            hashed_password=hash_password(data.password),
            cohort=data.cohort,
        )
        return _build_token(calibrator.id, calibrator.name)

    async def login(
        self, db: AsyncSession, data: CalibratorLoginIn
    ) -> CalibratorTokenOut:
        """
        Authentifie un calibrateur.
        - 401 si email inconnu ou mot de passe incorrect.
        """
        calibrator = await repo.get_calibrator_by_email(db, data.email)
        if not calibrator or not verify_password(data.password, calibrator.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": True,
                    "message": "Email ou mot de passe incorrect.",
                    "code": "INVALID_CREDENTIALS",
                },
            )
        if not calibrator.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": True,
                    "message": "Compte désactivé.",
                    "code": "ACCOUNT_DISABLED",
                },
            )
        return _build_token(calibrator.id, calibrator.name)

    # ── Catalogues ────────────────────────────────────────────────────────────

    async def list_catalogues(self, db: AsyncSession) -> list[CatalogueInfoOut]:
        """Retourne tous les catalogues actifs."""
        catalogues = await repo.get_all_catalogues(db)
        return [CatalogueInfoOut.model_validate(c) for c in catalogues]

    async def get_questions(
        self, db: AsyncSession, catalogue_id: int
    ) -> list[QuestionOut]:
        """
        Retourne les questions ordonnées d'un catalogue.
        - 404 si catalogue inexistant ou inactif.
        """
        catalogue = await repo.get_catalogue_by_id(db, catalogue_id)
        if not catalogue or not catalogue.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Catalogue introuvable.",
                    "code": "CATALOGUE_NOT_FOUND",
                },
            )
        questions = await repo.get_questions_for_catalogue(db, catalogue_id)
        return [QuestionOut.model_validate(q) for q in questions]

    # ── Sessions ──────────────────────────────────────────────────────────────

    async def start_session(
        self,
        db: AsyncSession,
        calibrator_id: int,
        data: StartSessionIn,
    ) -> SessionOut:
        """
        Démarre une session de passation.
        - 404 si catalogue inexistant.
        - 409 si une session déjà complétée existe pour ce catalogue.
        """
        catalogue = await repo.get_catalogue_by_id(db, data.catalogue_id)
        if not catalogue or not catalogue.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Catalogue introuvable.",
                    "code": "CATALOGUE_NOT_FOUND",
                },
            )

        existing = await repo.get_session_for_calibrator(
            db, calibrator_id, data.catalogue_id
        )
        if existing and existing.completed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": True,
                    "message": "Ce catalogue a déjà été passé. Une seule passation par calibrateur.",
                    "code": "SESSION_ALREADY_COMPLETED",
                },
            )

        # Si une session existe mais n'est pas complétée → on la retourne (reprise)
        if existing:
            return SessionOut.model_validate(existing)

        session = await repo.create_session(
            db=db,
            calibrator_id=calibrator_id,
            catalogue_id=data.catalogue_id,
            device_info=data.device_info,
        )
        return SessionOut.model_validate(session)

    async def list_sessions(
        self, db: AsyncSession, calibrator_id: int
    ) -> list[SessionOut]:
        sessions = await repo.list_sessions_for_calibrator(db, calibrator_id)
        return [SessionOut.model_validate(s) for s in sessions]

    # ── Réponses ──────────────────────────────────────────────────────────────

    async def submit_responses(
        self,
        db: AsyncSession,
        calibrator_id: int,
        session_id: int,
        data: SubmitResponsesIn,
    ) -> SubmitResponsesOut:
        """
        Soumet des réponses pour une session en cours.
        - 404 si session introuvable.
        - 403 si la session n'appartient pas au calibrateur.
        - 409 si la session est déjà complétée.
        Auto-complète la session si toutes les réponses ont été soumises.
        """
        session = await repo.get_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Session introuvable.",
                    "code": "SESSION_NOT_FOUND",
                },
            )

        if session.calibrator_id != calibrator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": True,
                    "message": "Cette session ne vous appartient pas.",
                    "code": "SESSION_FORBIDDEN",
                },
            )

        if session.completed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": True,
                    "message": "La session est déjà terminée.",
                    "code": "SESSION_ALREADY_COMPLETED",
                },
            )

        n_saved = await repo.save_responses(db, session_id, data.responses)

        # Auto-complétion : compare les réponses totales au nombre de questions
        catalogue = await repo.get_catalogue_by_id(db, session.catalogue_id)
        total_responses = await repo.count_responses_for_session(db, session_id)
        completed = False
        if catalogue and total_responses >= catalogue.n_questions:
            await repo.complete_session(db, session)
            completed = True

        return SubmitResponsesOut(
            session_id=session_id,
            n_responses=n_saved,
            completed=completed,
        )
