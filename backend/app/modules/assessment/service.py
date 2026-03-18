# modules/assessment/service.py
"""
Orchestration du cycle de vie des évaluations.

Changements v2 :
- Toutes les méthodes reçoivent crew_profile (CrewProfile) au lieu de user_id
- psychometric_snapshot lu/écrit sur CrewProfile
- propagation background utilise crew_profile_id
"""
import logging
from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

logger = logging.getLogger(__name__)

from app.engine.psychometrics.scoring import calculate_scores
from app.engine.psychometrics.snapshot import build_snapshot
from app.modules.assessment.repository import AssessmentRepository
from app.shared.models import CrewProfile

repo = AssessmentRepository()


def _gf_level(score: float) -> str:
    """Convertit un score 0-100 en niveau qualitatif."""
    if score >= 70:
        return "Élevé"
    if score >= 40:
        return "Moyen"
    return "Faible"


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
        """Propagation vessel + fleet — TODO post-bêta (snapshots denormalisés)."""
        logger.debug("propagate_to_vessel_and_fleet crew_profile_id=%s (noop)", crew_profile_id)
