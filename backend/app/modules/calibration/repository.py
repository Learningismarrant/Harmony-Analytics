# app/modules/calibration/repository.py
"""
Accès DB pour le module calibration.
SQL pur — zéro logique métier.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.shared.models import TestCatalogue, Question
from app.shared.models.Calibration import CalibratorUser, CalibSession, CalibResponse
from app.modules.calibration.schemas import ResponseItemIn


class CalibrationRepository:

    # ── CalibratorUser ────────────────────────────────────────────────────────

    async def get_calibrator_by_email(
        self, db: AsyncSession, email: str
    ) -> Optional[CalibratorUser]:
        r = await db.execute(
            select(CalibratorUser).where(CalibratorUser.email == email)
        )
        return r.scalar_one_or_none()

    async def get_calibrator_by_id(
        self, db: AsyncSession, calibrator_id: int
    ) -> Optional[CalibratorUser]:
        r = await db.execute(
            select(CalibratorUser).where(CalibratorUser.id == calibrator_id)
        )
        return r.scalar_one_or_none()

    async def create_calibrator(
        self,
        db: AsyncSession,
        email: str,
        name: str,
        hashed_password: str,
        cohort: Optional[str],
    ) -> CalibratorUser:
        obj = CalibratorUser(
            email=email,
            name=name,
            hashed_password=hashed_password,
            cohort=cohort,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    # ── Catalogues ────────────────────────────────────────────────────────────

    async def get_all_catalogues(self, db: AsyncSession) -> list[TestCatalogue]:
        """Retourne tous les catalogues actifs."""
        r = await db.execute(
            select(TestCatalogue).where(TestCatalogue.is_active == True)
        )
        return list(r.scalars().all())

    async def get_catalogue_by_id(
        self, db: AsyncSession, catalogue_id: int
    ) -> Optional[TestCatalogue]:
        r = await db.execute(
            select(TestCatalogue).where(TestCatalogue.id == catalogue_id)
        )
        return r.scalar_one_or_none()

    async def get_questions_for_catalogue(
        self, db: AsyncSession, catalogue_id: int
    ) -> list[Question]:
        r = await db.execute(
            select(Question)
            .where(Question.test_id == catalogue_id)
            .order_by(Question.order)
        )
        return list(r.scalars().all())

    # ── CalibSession ──────────────────────────────────────────────────────────

    async def get_session(
        self, db: AsyncSession, session_id: int
    ) -> Optional[CalibSession]:
        r = await db.execute(
            select(CalibSession).where(CalibSession.id == session_id)
        )
        return r.scalar_one_or_none()

    async def get_session_for_calibrator(
        self, db: AsyncSession, calibrator_id: int, catalogue_id: int
    ) -> Optional[CalibSession]:
        """Retourne la session existante pour ce couple (calibrateur, catalogue)."""
        r = await db.execute(
            select(CalibSession).where(
                CalibSession.calibrator_id == calibrator_id,
                CalibSession.catalogue_id == catalogue_id,
            )
        )
        return r.scalar_one_or_none()

    async def list_sessions_for_calibrator(
        self, db: AsyncSession, calibrator_id: int
    ) -> list[CalibSession]:
        r = await db.execute(
            select(CalibSession)
            .where(CalibSession.calibrator_id == calibrator_id)
            .order_by(CalibSession.started_at.desc())
        )
        return list(r.scalars().all())

    async def create_session(
        self,
        db: AsyncSession,
        calibrator_id: int,
        catalogue_id: int,
        device_info: Optional[dict],
    ) -> CalibSession:
        obj = CalibSession(
            calibrator_id=calibrator_id,
            catalogue_id=catalogue_id,
            device_info=device_info,
        )
        db.add(obj)
        await db.commit()
        await db.refresh(obj)
        return obj

    async def complete_session(
        self, db: AsyncSession, session: CalibSession
    ) -> CalibSession:
        """Marque la session comme terminée (set completed_at = maintenant)."""
        session.completed_at = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(session)
        return session

    # ── CalibResponse ─────────────────────────────────────────────────────────

    async def save_responses(
        self,
        db: AsyncSession,
        session_id: int,
        responses: list[ResponseItemIn],
    ) -> int:
        """Insère toutes les réponses en bulk. Retourne le nombre sauvegardé."""
        objects = [
            CalibResponse(
                session_id=session_id,
                question_id=r.question_id,
                value=r.value,
                seconds_spent=r.seconds_spent,
            )
            for r in responses
        ]
        for obj in objects:
            db.add(obj)
        await db.commit()
        return len(objects)

    async def count_responses_for_session(
        self, db: AsyncSession, session_id: int
    ) -> int:
        r = await db.execute(
            select(CalibResponse).where(CalibResponse.session_id == session_id)
        )
        return len(r.scalars().all())
