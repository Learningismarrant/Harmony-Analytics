# modules/crew/repository.py
"""
Accès DB pour les assignments d'équipage et le Daily Pulse.

Changements v2 :
- CrewAssignment.crew_profile_id (était user_id)
- DailyPulse.crew_profile_id    (était user_id)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List, Optional
from datetime import datetime, date, timezone, timedelta

from app.shared.models import CrewAssignment, DailyPulse, CrewProfile, User as UserModel


class CrewRepository:

    # ── Assignments ───────────────────────────────────────────

    async def get_active_assignment(
        self, db: AsyncSession, crew_profile_id: int   # v2
    ) -> Optional[CrewAssignment]:
        r = await db.execute(
            select(CrewAssignment).where(
                CrewAssignment.crew_profile_id == crew_profile_id,
                CrewAssignment.is_active == True,
            )
        )
        return r.scalar_one_or_none()

    async def get_active_crew(
        self, db: AsyncSession, yacht_id: int
    ) -> List[CrewAssignment]:
        r = await db.execute(
            select(CrewAssignment).where(
                CrewAssignment.yacht_id == yacht_id,
                CrewAssignment.is_active == True,
            )
        )
        return r.scalars().all()

    async def get_assignment(
        self, db: AsyncSession, yacht_id: int, crew_profile_id: int  # v2
    ) -> Optional[CrewAssignment]:
        r = await db.execute(
            select(CrewAssignment).where(
                CrewAssignment.yacht_id == yacht_id,
                CrewAssignment.crew_profile_id == crew_profile_id,
            )
        )
        return r.scalar_one_or_none()

    async def create_assignment(
        self, db: AsyncSession, yacht_id: int, payload
    ) -> CrewAssignment:
        db_obj = CrewAssignment(
            yacht_id=yacht_id,
            crew_profile_id=payload.crew_profile_id,   # v2
            role=payload.role,
            is_active=True,
            start_date=payload.start_date or datetime.now(timezone.utc),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def deactivate_assignment(
        self, db: AsyncSession, yacht_id: int, crew_profile_id: int  # v2
    ) -> bool:
        assignment = await self.get_assignment(db, yacht_id, crew_profile_id)
        if not assignment or not assignment.is_active:
            return False
        assignment.is_active = False
        assignment.end_date = datetime.now(timezone.utc)
        await db.commit()
        return True

    # ── Daily Pulse ───────────────────────────────────────────

    async def has_pulse_today(
        self, db: AsyncSession, crew_profile_id: int, today: date  # v2
    ) -> bool:
        r = await db.execute(
            select(DailyPulse).where(
                DailyPulse.crew_profile_id == crew_profile_id,
                func.date(DailyPulse.created_at) == today,
            )
        )
        return r.scalar_one_or_none() is not None

    async def create_pulse(
        self,
        db: AsyncSession,
        crew_profile_id: int,   # v2
        yacht_id: int,
        score: int,
        comment: str = None,
    ) -> DailyPulse:
        db_obj = DailyPulse(
            crew_profile_id=crew_profile_id,    # v2
            yacht_id=yacht_id,
            score=score,
            comment=comment,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_recent_pulse_data(
        self, db: AsyncSession, yacht_id: int, days: int = 7
    ) -> List[DailyPulse]:
        since = datetime.now(timezone.utc) - timedelta(days=days)
        r = await db.execute(
            select(DailyPulse).where(
                DailyPulse.yacht_id == yacht_id,
                DailyPulse.created_at >= since,
            )
        )
        return r.scalars().all()

    async def get_pulse_history(
        self, db: AsyncSession, crew_profile_id: int, limit: int = 30  # v2
    ) -> List[DailyPulse]:
        r = await db.execute(
            select(DailyPulse)
            .where(DailyPulse.crew_profile_id == crew_profile_id)
            .order_by(DailyPulse.created_at.desc())
            .limit(limit)
        )
        return r.scalars().all()

    # ── Sociogram helpers ─────────────────────────────────────

    async def get_active_crew_with_profiles(
        self, db: AsyncSession, yacht_id: int
    ) -> List[dict]:
        """Active crew enriched with name, avatar_url, role and psychometric snapshot."""
        r = await db.execute(
            select(
                CrewAssignment.crew_profile_id,
                CrewAssignment.role,
                UserModel.name,
                UserModel.avatar_url,
                CrewProfile.psychometric_snapshot,
            )
            .join(CrewProfile, CrewProfile.id == CrewAssignment.crew_profile_id)
            .join(UserModel, UserModel.id == CrewProfile.user_id)
            .where(
                CrewAssignment.yacht_id == yacht_id,
                CrewAssignment.is_active == True,
            )
        )
        rows = r.all()
        return [
            {
                "crew_profile_id": row.crew_profile_id,
                "role": row.role.value if hasattr(row.role, "value") else str(row.role),
                "name": row.name or f"Membre {i + 1}",
                "avatar_url": row.avatar_url,
                "snapshot": row.psychometric_snapshot or {},
            }
            for i, row in enumerate(rows)
        ]

    async def get_crew_profile_with_snapshot(
        self, db: AsyncSession, crew_profile_id: int
    ) -> Optional[dict]:
        """Single crew profile enriched with user identity and psychometric snapshot."""
        r = await db.execute(
            select(
                CrewProfile.id,
                CrewProfile.position_targeted,
                CrewProfile.psychometric_snapshot,
                UserModel.name,
                UserModel.avatar_url,
            )
            .join(UserModel, UserModel.id == CrewProfile.user_id)
            .where(CrewProfile.id == crew_profile_id)
        )
        row = r.one_or_none()
        if not row:
            return None
        pos = row.position_targeted
        return {
            "crew_profile_id": row.id,
            "role": pos.value if hasattr(pos, "value") else str(pos or "Deckhand"),
            "name": row.name,
            "avatar_url": row.avatar_url,
            "snapshot": row.psychometric_snapshot or {},
            "dnre_fit_label": "",
            "dnre_safety_level": "CLEAR",
        }