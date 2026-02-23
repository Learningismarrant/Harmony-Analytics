# modules/assessment/service.py
"""
Orchestration du cycle de vie des évaluations.

Changements v2 :
- Toutes les méthodes reçoivent crew_profile (CrewProfile) au lieu de user_id
- psychometric_snapshot lu/écrit sur CrewProfile
- propagation background utilise crew_profile_id
"""
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

from app.engine.psychometrics.scoring import calculate_scores
from app.engine.psychometrics.snapshot import build_snapshot
from app.modules.assessment.repository import AssessmentRepository
from app.shared.models import CrewProfile

repo = AssessmentRepository()


class AssessmentService:

    async def get_catalogue(self, db: AsyncSession) -> List:
        return await repo.get_all_active_tests(db)

    async def get_questions_for_crew(
        self, db: AsyncSession, test_id: int, crew_profile_id: int
    ) -> Optional[List]:
        """
        Retourne les questions. Anti-triche Temps 2 : vérifier session en cours.
        """
        return await repo.get_questions_by_test(db, test_id)

    async def submit_and_score(
        self,
        db: AsyncSession,
        crew: CrewProfile,          # v2 : CrewProfile complet (pas user_id)
        test_id: int,
        responses: List,
        background_tasks: BackgroundTasks,
    ) -> Dict:
        """
        Pipeline complet :
        1. Validation + hydratation test
        2. Calcul pur (engine — zéro DB)
        3. Sauvegarde TestResult via crew_profile_id
        4. Refresh psychometric_snapshot sur CrewProfile (synchrone)
        5. Propagation vessel + fleet (background)
        """
        if not responses:
            raise ValueError("Aucune réponse fournie.")

        test_info = await repo.get_test_info(db, test_id)
        if not test_info:
            raise ValueError("Test introuvable.")

        questions = await repo.get_questions_by_test(db, test_id)
        questions_map = {q.id: q for q in questions}

        # ── Calcul pur (engine) ───────────────────────────────
        result = calculate_scores(
            responses=responses,
            questions_map=questions_map,
            test_type=test_info.test_type,
            max_score_per_question=test_info.max_score_per_question,
        )

        # ── Sauvegarde via crew_profile_id ────────────────────
        saved = await repo.save_result(
            db,
            crew_profile_id=crew.id,    # v2
            test_id=test_id,
            scores=result,
            global_score=result["global_score"],
        )

        # ── Refresh snapshot (synchrone) ──────────────────────
        await self._refresh_crew_snapshot(db, crew.id)

        # ── Propagation vessel + fleet (background) ───────────
        background_tasks.add_task(
            self._propagate_to_vessel_and_fleet, crew.id
        )

        return saved

    async def get_results_for_crew(
        self, db: AsyncSession, crew_profile_id: int
    ) -> List:
        return await repo.get_results_by_crew(db, crew_profile_id)

    async def get_results_for_candidate(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester_employer_id: int,   # v2 : employer_profile_id du client
    ) -> Optional[List]:
        has_access = await repo.check_requester_access(
            db, crew_profile_id, requester_employer_id
        )
        if not has_access:
            return None
        return await repo.get_results_by_crew(db, crew_profile_id)

    # ── Snapshot management ───────────────────────────────────

    async def _refresh_crew_snapshot(
        self, db: AsyncSession, crew_profile_id: int
    ) -> None:
        """
        Relit tous les TestResult du crew et reconstruit le snapshot.
        v2 : opère sur CrewProfile.psychometric_snapshot.
        """
        all_results = await repo.get_results_by_crew(db, crew_profile_id)
        snapshot = build_snapshot(all_results)
        await repo.update_crew_snapshot(db, crew_profile_id, snapshot)

    async def _propagate_to_vessel_and_fleet(self, crew_profile_id: int) -> None:
        """
        Background task : recalcule vessel_snapshot et fleet_snapshot.
        v2 : utilise crew_profile_id partout.
        Session DB indépendante (isolée du contexte HTTP).
        """
        from app.core.database import AsyncSessionLocal
        from app.modules.vessel.repository import VesselRepository
        from app.modules.vessel.service import VesselService
        from engine.team.harmony import compute as compute_harmony

        vessel_repo = VesselRepository()
        vessel_service = VesselService()

        async with AsyncSessionLocal() as db:
            try:
                active_yacht_ids = await repo.get_active_yacht_ids(db, crew_profile_id)

                for yacht_id in active_yacht_ids:
                    crew_snapshots = await vessel_repo.get_crew_snapshots(db, yacht_id)
                    if len(crew_snapshots) >= 2:
                        harmony = compute_harmony(crew_snapshots)
                        await vessel_service.update_vessel_snapshot(db, yacht_id, harmony)

                employer_ids = await vessel_repo.get_employer_ids_for_yachts(db, active_yacht_ids)
                for employer_id in employer_ids:
                    await vessel_service.refresh_fleet_snapshot_if_stale(db, employer_id)

            except Exception as e:
                print(f"[BACKGROUND] Propagation snapshot crew {crew_profile_id}: {e}")