# modules/assessment/service.py
"""
Orchestration du cycle de vie des évaluations.

Responsabilités :
1. Interroger la DB via repository (questions, test info)
2. Déléguer le calcul à engine/psychometrics/scoring.py
3. Sauvegarder le résultat
4. Déclencher la mise à jour du psychometric_snapshot (synchrone)
5. Propager aux niveaux vessel + fleet (background)
"""
from fastapi import BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from engine.psychometrics.scoring import calculate_scores
from engine.psychometrics.snapshot import build_snapshot
from modules.assessment.repository import AssessmentRepository

repo = AssessmentRepository()


class AssessmentService:

    def get_catalogue(self, db: Session) -> List:
        return repo.get_all_active_tests(db)

    def get_questions_for_user(self, db: Session, test_id: int, user_id: int) -> Optional[List]:
        """
        Retourne les questions.
        TODO : Vérifier qu'il n'y a pas de session en cours (anti-triche).
        """
        return repo.get_questions_by_test(db, test_id)

    def submit_and_score(
        self,
        db: Session,
        user_id: int,
        test_id: int,
        responses: List,
        background_tasks: BackgroundTasks,
    ) -> Dict:
        """
        Pipeline complet de soumission :
        1. Validation des données
        2. Calcul pur (engine)
        3. Sauvegarde résultat
        4. Refresh snapshot crew (synchrone — l'utilisateur voit son profil à jour)
        5. Propagation vessel + fleet (background — 0ms ressenti)
        """
        if not responses:
            raise ValueError("Aucune réponse fournie.")

        # 1. Hydratation des données test (seul accès DB dans ce flux)
        test_info = repo.get_test_info(db, test_id)
        if not test_info:
            raise ValueError("Test introuvable.")

        questions = repo.get_questions_by_test(db, test_id)
        questions_map = {q.id: q for q in questions}

        # 2. Calcul pur — engine ne touche pas la DB
        result = calculate_scores(
            responses=responses,
            questions_map=questions_map,
            test_type=test_info.test_type,
            max_score_per_question=test_info.max_score_per_question,
        )

        # 3. Sauvegarde
        saved = repo.save_result(
            db,
            user_id=user_id,
            test_id=test_id,
            scores=result,
            global_score=result["global_score"],
        )

        # 4. Refresh psychometric_snapshot (SYNCHRONE)
        self._refresh_crew_snapshot(db, user_id)

        # 5. Propagation vessel + fleet (BACKGROUND — ne bloque pas la réponse HTTP)
        background_tasks.add_task(
            self._propagate_to_vessel_and_fleet, user_id
        )

        return saved

    def get_results_for_user(self, db: Session, user_id: int) -> List:
        return repo.get_results_by_user(db, user_id)

    def get_results_for_candidate(
        self, db: Session, candidate_id: int, requester_id: int
    ) -> Optional[List]:
        """
        Vérifie que le requester a accès au candidat
        (campagne active ou équipage actif).
        """
        has_access = repo.check_requester_access(db, candidate_id, requester_id)
        if not has_access:
            return None
        return repo.get_results_by_user(db, candidate_id)

    # ─────────────────────────────────────────────
    # SNAPSHOT MANAGEMENT
    # ─────────────────────────────────────────────

    def _refresh_crew_snapshot(self, db: Session, user_id: int) -> None:
        """
        Relit tous les TestResult du candidat et reconstruit le snapshot.
        Synchrone — appelé immédiatement après la soumission.
        """
        all_results = repo.get_results_by_user(db, user_id)
        snapshot = build_snapshot(all_results)
        repo.update_crew_snapshot(db, user_id, snapshot)

    def _propagate_to_vessel_and_fleet(self, user_id: int) -> None:
        """
        Background task : recalcule vessel_snapshot et fleet_snapshot.
        Tourne après que la réponse HTTP est envoyée.

        Utilise sa propre session DB (background task isolée).
        """
        from core.database import SessionLocal
        from modules.vessel.repository import VesselRepository
        from modules.vessel.service import VesselService
        from engine.team.harmony import compute as compute_harmony

        db = SessionLocal()
        vessel_repo = VesselRepository()
        vessel_service = VesselService()

        try:
            # Quels yachts sont impactés par ce marin ?
            active_yacht_ids = repo.get_active_yacht_ids(db, user_id)

            for yacht_id in active_yacht_ids:
                # Récupère tous les snapshots de l'équipe
                crew_snapshots = vessel_repo.get_crew_snapshots(db, yacht_id)

                if len(crew_snapshots) >= 2:
                    harmony = compute_harmony(crew_snapshots)
                    vessel_service.update_vessel_snapshot(db, yacht_id, harmony)

            # Fleet si les yachts appartiennent à un office
            office_ids = vessel_repo.get_office_ids_for_yachts(db, active_yacht_ids)
            for office_id in office_ids:
                vessel_service.refresh_fleet_snapshot_if_stale(db, office_id)

        except Exception as e:
            print(f"[BACKGROUND] Erreur propagation snapshot user {user_id}: {e}")
        finally:
            db.close()