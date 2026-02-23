# modules/vessel/repository.py
"""
Accès DB pour les yachts, équipages et snapshots vessel/fleet.

Changements v2 :
- Yacht.employer_profile_id (était client_id)
- CrewAssignment.crew_profile_id (était user_id)
- get_crew_snapshots joint via CrewProfile (pas User)
- get_employer_ids_for_yachts (était get_office_ids_for_yachts)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta
import secrets

from app.shared.models import (Yacht, CrewAssignment,
                               User, CrewProfile)


class VesselRepository:

    # ── Yachts ────────────────────────────────────────────────

    async def get_yachts_by_employer(
        self, db: AsyncSession, employer_profile_id: int  # v2 : était client_id
    ) -> List[Yacht]:
        r = await db.execute(
            select(Yacht).where(Yacht.employer_profile_id == employer_profile_id)
        )
        return r.scalars().all()

    async def get_by_id(self, db: AsyncSession, yacht_id: int) -> Optional[Yacht]:
        r = await db.execute(select(Yacht).where(Yacht.id == yacht_id))
        return r.scalar_one_or_none()

    async def get_secure(
        self, db: AsyncSession, yacht_id: int, employer_profile_id: int  # v2
    ) -> Optional[Yacht]:
        r = await db.execute(
            select(Yacht).where(
                Yacht.id == yacht_id,
                Yacht.employer_profile_id == employer_profile_id,
            )
        )
        return r.scalar_one_or_none()

    async def is_owner(
        self, db: AsyncSession, yacht_id: int, employer_profile_id: int  # v2
    ) -> bool:
        return await self.get_secure(db, yacht_id, employer_profile_id) is not None

    async def create(
        self, db: AsyncSession, payload, employer_profile_id: int  # v2
    ) -> Yacht:
        db_obj = Yacht(
            **payload.model_dump(),
            employer_profile_id=employer_profile_id,
            boarding_token=secrets.token_urlsafe(16),
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update(self, db: AsyncSession, yacht: Yacht, payload) -> Yacht:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(yacht, field, value)
        await db.commit()
        await db.refresh(yacht)
        return yacht

    async def delete(self, db: AsyncSession, yacht: Yacht) -> None:
        await db.delete(yacht)
        await db.commit()

    async def get_by_boarding_token(
        self, db: AsyncSession, token: str
    ) -> Optional[Yacht]:
        r = await db.execute(
            select(Yacht).where(Yacht.boarding_token == token)
        )
        return r.scalar_one_or_none()

    async def rotate_boarding_token(
        self, db: AsyncSession, yacht: Yacht
    ) -> str:
        yacht.boarding_token = secrets.token_urlsafe(16)
        await db.commit()
        return yacht.boarding_token

    # ── Équipage ──────────────────────────────────────────────

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

    async def get_active_crew_ids(
        self, db: AsyncSession, yacht_id: int
    ) -> List[int]:
        """
        v2 : retourne crew_profile_ids (pas user_ids).
        Utilisé par SurveyService pour cibler les répondants.
        """
        r = await db.execute(
            select(CrewAssignment.crew_profile_id)
            .where(
                CrewAssignment.yacht_id == yacht_id,
                CrewAssignment.is_active == True,
            )
        )
        return list(r.scalars().all())

    # ── Snapshots ─────────────────────────────────────────────

    async def get_crew_snapshots(
        self, db: AsyncSession, yacht_id: int
    ) -> List[Dict]:
        """
        v2 : joint via CrewProfile (pas User).
        psychometric_snapshot sur CrewProfile.
        Filtre les membres sans snapshot (profil incomplet).
        """
        r = await db.execute(
            select(CrewProfile.psychometric_snapshot)
            .join(CrewAssignment, CrewAssignment.crew_profile_id == CrewProfile.id)
            .where(
                CrewAssignment.yacht_id == yacht_id,
                CrewAssignment.is_active == True,
                CrewProfile.psychometric_snapshot.isnot(None),
            )
        )
        return [snap for snap in r.scalars().all() if snap]

    async def get_vessel_snapshot(
        self, db: AsyncSession, yacht_id: int
    ) -> Optional[Dict]:
        yacht = await self.get_by_id(db, yacht_id)
        return yacht.vessel_snapshot if yacht else None

    async def update_vessel_snapshot(
        self, db: AsyncSession, yacht_id: int, snapshot: Dict[str, Any]
    ) -> None:
        yacht = await self.get_by_id(db, yacht_id)
        if yacht:
            yacht.vessel_snapshot = snapshot
            yacht.snapshot_updated_at = datetime.now(timezone.utc)
            await db.commit()

    async def update_observed_scores(
        self, db: AsyncSession, yacht_id: int, observed: Dict[str, Any]
    ) -> None:
        """Merge partiel — enrichit observed_scores dans le vessel_snapshot."""
        yacht = await self.get_by_id(db, yacht_id)
        if not yacht:
            return
        current = yacht.vessel_snapshot or {}
        current["observed_scores"] = observed
        yacht.vessel_snapshot = current
        await db.commit()

    async def is_vessel_snapshot_stale(
        self, db: AsyncSession, yacht_id: int, ttl_minutes: int = 10
    ) -> bool:
        yacht = await self.get_by_id(db, yacht_id)
        if not yacht or not yacht.snapshot_updated_at:
            return True
        age = datetime.now(timezone.utc) - yacht.snapshot_updated_at.replace(tzinfo=timezone.utc)
        return age > timedelta(minutes=ttl_minutes)

    async def get_captain_vector(
        self, db: AsyncSession, yacht_id: int
    ) -> Optional[Dict]:
        yacht = await self.get_by_id(db, yacht_id)
        return yacht.captain_leadership_vector if yacht else None

    async def update_environment_params(
        self, db: AsyncSession, yacht_id: int, params: Dict[str, Any]
    ) -> Optional[Yacht]:
        """
        Stocke les paramètres JD-R (F_env) et le vecteur capitaine (F_lmx).
        jdr_params → vessel_snapshot["jdr_params"]
        captain_vector → Yacht.captain_leadership_vector
        """
        yacht = await self.get_by_id(db, yacht_id)
        if not yacht:
            return None

        current = yacht.vessel_snapshot or {}
        current["jdr_params"] = {
            "charter_intensity":    params.get("charter_intensity", 0.5),
            "management_pressure":  params.get("management_pressure", 0.5),
            "salary_index":         params.get("salary_index", 0.5),
            "rest_days_ratio":      params.get("rest_days_ratio", 0.5),
            "private_cabin_ratio":  params.get("private_cabin_ratio", 0.5),
        }
        yacht.vessel_snapshot = current

        if any(k in params for k in (
            "captain_autonomy_given", "captain_feedback_style", "captain_structure_imposed"
        )):
            yacht.captain_leadership_vector = {
                "autonomy_given":    params.get("captain_autonomy_given", 0.5),
                "feedback_style":    params.get("captain_feedback_style", 0.5),
                "structure_imposed": params.get("captain_structure_imposed", 0.5),
            }

        await db.commit()
        await db.refresh(yacht)
        return yacht

    # ── Fleet ─────────────────────────────────────────────────

    async def get_employer_ids_for_yachts(
        self, db: AsyncSession, yacht_ids: List[int]
    ) -> List[int]:
        """
        v2 : employer_profile_id (était client_id).
        Pour savoir quels fleet_snapshots recalculer après une mise à jour.
        """
        if not yacht_ids:
            return []
        r = await db.execute(
            select(Yacht.employer_profile_id)
            .where(Yacht.id.in_(yacht_ids))
            .distinct()
        )
        return list(r.scalars().all())

    async def get_all_vessel_snapshots_for_employer(
        self, db: AsyncSession, employer_profile_id: int  # v2 : était office_id
    ) -> List[Dict]:
        """Pour le recalcul du fleet_snapshot (clustering, ANOVA)."""
        r = await db.execute(
            select(Yacht.id, Yacht.vessel_snapshot)
            .where(Yacht.employer_profile_id == employer_profile_id)
        )
        return [
            {"yacht_id": row.id, "snapshot": row.vessel_snapshot}
            for row in r.all()
            if row.vessel_snapshot
        ]