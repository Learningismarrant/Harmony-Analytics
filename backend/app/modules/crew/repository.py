# modules/crew/repository.py
"""
Accès DB pour les assignments d'équipage et le Daily Pulse.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime, date, timezone, timedelta

from app.models.yacht import CrewAssignment
from app.models import DailyPulse


class CrewRepository:

    # ─────────────────────────────────────────────
    # ASSIGNMENTS
    # ─────────────────────────────────────────────

    def get_active_assignment(self, db: Session, user_id: int) -> Optional[CrewAssignment]:
        return db.query(CrewAssignment).filter(
            CrewAssignment.user_id == user_id,
            CrewAssignment.is_active == True,
        ).first()

    def get_active_crew(self, db: Session, yacht_id: int) -> List[CrewAssignment]:
        return db.query(CrewAssignment).filter(
            CrewAssignment.yacht_id == yacht_id,
            CrewAssignment.is_active == True,
        ).all()

    def get_assignment(
        self, db: Session, yacht_id: int, user_id: int
    ) -> Optional[CrewAssignment]:
        return db.query(CrewAssignment).filter(
            CrewAssignment.yacht_id == yacht_id,
            CrewAssignment.user_id == user_id,
        ).first()

    def create_assignment(self, db: Session, yacht_id: int, payload) -> CrewAssignment:
        db_obj = CrewAssignment(
            yacht_id=yacht_id,
            user_id=payload.user_id,
            role=payload.role,
            is_active=True,
            start_date=payload.start_date or datetime.now(timezone.utc),
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def deactivate_assignment(self, db: Session, yacht_id: int, user_id: int) -> bool:
        assignment = self.get_assignment(db, yacht_id, user_id)
        if not assignment or not assignment.is_active:
            return False
        assignment.is_active = False
        assignment.end_date = datetime.now(timezone.utc)
        db.commit()
        return True

    # ─────────────────────────────────────────────
    # DAILY PULSE
    # ─────────────────────────────────────────────

    def has_pulse_today(self, db: Session, user_id: int, today: date) -> bool:
        return db.query(DailyPulse).filter(
            DailyPulse.user_id == user_id,
            func.date(DailyPulse.created_at) == today,
        ).first() is not None

    def create_pulse(
        self, db: Session, user_id: int, yacht_id: int, score: int, comment: str = None
    ) -> DailyPulse:
        db_obj = DailyPulse(
            user_id=user_id,
            yacht_id=yacht_id,
            score=score,
            comment=comment,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_recent_pulse_data(
        self, db: Session, yacht_id: int, days: int = 7
    ) -> List[DailyPulse]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        return db.query(DailyPulse).filter(
            DailyPulse.yacht_id == yacht_id,
            DailyPulse.created_at >= since,
        ).all()

    def get_pulse_history(
        self, db: Session, user_id: int, limit: int = 30
    ) -> List[DailyPulse]:
        return (
            db.query(DailyPulse)
            .filter(DailyPulse.user_id == user_id)
            .order_by(DailyPulse.created_at.desc())
            .limit(limit)
            .all()
        )