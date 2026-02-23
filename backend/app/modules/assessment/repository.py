# modules/assessment/repository.py
"""
Accès DB pour le module assessment.
Adapté split User → CrewProfile / EmployerProfile.

Changements v2 :
- TestResult.crew_profile_id  (était user_id)
- psychometric_snapshot sur   CrewProfile (était User)
- CampaignCandidate.crew_profile_id (était candidate_id)
- CrewAssignment.crew_profile_id    (était user_id)
- Yacht.employer_profile_id         (était client_id)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, String
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.shared.models import TestCatalogue, Question, TestResult, User, CrewProfile,Yacht, CrewAssignment, Campaign, CampaignCandidate

class AssessmentRepository:

    # ── Catalogue ─────────────────────────────────────────────

    async def get_all_active_tests(self, db: AsyncSession) -> List[TestCatalogue]:
        r = await db.execute(select(TestCatalogue).where(TestCatalogue.is_active == True))
        return r.scalars().all()

    async def get_test_info(self, db: AsyncSession, test_id: int) -> Optional[TestCatalogue]:
        r = await db.execute(select(TestCatalogue).where(TestCatalogue.id == test_id))
        return r.scalar_one_or_none()

    async def get_questions_by_test(self, db: AsyncSession, test_id: int) -> List[Question]:
        r = await db.execute(
            select(Question).where(Question.test_id == test_id).order_by(Question.order)
        )
        return r.scalars().all()

    # ── Résultats ─────────────────────────────────────────────

    async def save_result(
        self,
        db: AsyncSession,
        crew_profile_id: int,   # v2 : était user_id
        test_id: int,
        scores: Dict[str, Any],
        global_score: float,
    ) -> TestResult:
        db_obj = TestResult(
            crew_profile_id=crew_profile_id,
            test_id=test_id,
            scores=scores,
            global_score=global_score,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def get_results_by_crew(
        self, db: AsyncSession, crew_profile_id: int
    ) -> List[TestResult]:
        r = await db.execute(
            select(TestResult)
            .where(TestResult.crew_profile_id == crew_profile_id)
            .order_by(TestResult.created_at.asc())
        )
        return r.scalars().all()

    async def get_latest_result_for_test(
        self, db: AsyncSession, crew_profile_id: int, test_id: int
    ) -> Optional[TestResult]:
        r = await db.execute(
            select(TestResult)
            .where(
                TestResult.crew_profile_id == crew_profile_id,
                TestResult.test_id == test_id,
            )
            .order_by(TestResult.created_at.desc())
        )
        return r.scalars().first()

    # ── Benchmarking normatif ─────────────────────────────────

    async def get_pool_scores_for_trait(
        self,
        db: AsyncSession,
        trait: str,
        position_key: str,
        test_id: int,
    ) -> List[float]:
        """
        v2 : joint via CrewProfile.
        position_targeted est sur CrewProfile, pas sur User.
        """
        r = await db.execute(
            select(TestResult.scores)
            .join(CrewProfile, CrewProfile.id == TestResult.crew_profile_id)
            .where(
                TestResult.test_id == test_id,
                func.lower(cast(CrewProfile.position_targeted, String)) == position_key.lower(),
            )
        )
        pool = []
        for (scores,) in r.all():
            if not scores:
                continue
            traits_data = scores.get("traits", scores)
            val = traits_data.get(trait)
            if val is None:
                continue
            pool.append(val.get("score", 0) if isinstance(val, dict) else val)
        return pool

    # ── Snapshot management ───────────────────────────────────

    async def update_crew_snapshot(
        self, db: AsyncSession, crew_profile_id: int, snapshot: Dict[str, Any]
    ) -> None:
        """v2 : psychometric_snapshot sur CrewProfile, pas sur User."""
        r = await db.execute(select(CrewProfile).where(CrewProfile.id == crew_profile_id))
        crew = r.scalar_one_or_none()
        if crew:
            crew.psychometric_snapshot = snapshot
            crew.snapshot_updated_at = datetime.now(timezone.utc)
            await db.commit()

    async def get_crew_snapshot(
        self, db: AsyncSession, crew_profile_id: int
    ) -> Optional[Dict]:
        r = await db.execute(
            select(CrewProfile.psychometric_snapshot)
            .where(CrewProfile.id == crew_profile_id)
        )
        return r.scalar_one_or_none()

    # ── Contrôle d'accès ─────────────────────────────────────

    async def check_requester_access(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester_employer_id: int,   # v2 : employer_profile_id
    ) -> bool:
        """
        Le requester est un EmployerProfile.
        Vérifie : campagne active OU équipage actif sur un de ses yachts.
        """
        r = await db.execute(
            select(CampaignCandidate)
            .join(Campaign, Campaign.id == CampaignCandidate.campaign_id)
            .where(
                CampaignCandidate.crew_profile_id == crew_profile_id,
                Campaign.employer_profile_id == requester_employer_id,
            )
        )
        if r.scalar_one_or_none():
            return True

        r = await db.execute(
            select(CrewAssignment)
            .join(Yacht, Yacht.id == CrewAssignment.yacht_id)
            .where(
                CrewAssignment.crew_profile_id == crew_profile_id,
                CrewAssignment.is_active == True,
                Yacht.employer_profile_id == requester_employer_id,
            )
        )
        return r.scalar_one_or_none() is not None

    # ── Propagation background ────────────────────────────────

    async def get_active_yacht_ids(
        self, db: AsyncSession, crew_profile_id: int
    ) -> List[int]:
        r = await db.execute(
            select(CrewAssignment.yacht_id)
            .where(
                CrewAssignment.crew_profile_id == crew_profile_id,
                CrewAssignment.is_active == True,
            )
        )
        return list(r.scalars().all())