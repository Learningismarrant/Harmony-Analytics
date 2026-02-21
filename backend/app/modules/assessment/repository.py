# modules/assessment/repository.py
"""
Accès DB pour le module assessment.
Toute la logique SQL est ici — les services n'écrivent jamais de queries directes.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func, cast, String
from typing import List, Optional, Dict, Any
from datetime import datetime

from app.models.assessment import TestCatalogue, Question, TestResult
from app.models.user import User
from app.models.yacht import CrewAssignment, Yacht
from app.models.campaign import Campaign, CampaignCandidate


class AssessmentRepository:

    # ─────────────────────────────────────────────
    # CATALOGUE
    # ─────────────────────────────────────────────

    def get_all_active_tests(self, db: Session) -> List[TestCatalogue]:
        return db.query(TestCatalogue).all()

    def get_test_info(self, db: Session, test_id: int) -> Optional[TestCatalogue]:
        return db.query(TestCatalogue).filter(TestCatalogue.id == test_id).first()

    def get_questions_by_test(self, db: Session, test_id: int) -> List[Question]:
        return db.query(Question).filter(Question.test_id == test_id).all()

    # ─────────────────────────────────────────────
    # RÉSULTATS
    # ─────────────────────────────────────────────

    def save_result(
        self,
        db: Session,
        user_id: int,
        test_id: int,
        scores: Dict[str, Any],
        global_score: float,
    ) -> TestResult:
        db_obj = TestResult(
            user_id=user_id,
            test_id=test_id,
            scores=scores,
            global_score=global_score,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def get_results_by_user(self, db: Session, user_id: int) -> List[TestResult]:
        return (
            db.query(TestResult)
            .filter(TestResult.user_id == user_id)
            .order_by(TestResult.created_at.asc())
            .all()
        )

    def get_latest_result_for_test(
        self, db: Session, user_id: int, test_id: int
    ) -> Optional[TestResult]:
        return (
            db.query(TestResult)
            .filter(TestResult.user_id == user_id, TestResult.test_id == test_id)
            .order_by(TestResult.created_at.desc())
            .first()
        )

    def get_distinct_test_ids(self, db: Session, user_id: int) -> List[int]:
        rows = (
            db.query(TestResult.test_id)
            .filter(TestResult.user_id == user_id)
            .distinct()
            .all()
        )
        return [r.test_id for r in rows]

    # ─────────────────────────────────────────────
    # BENCHMARKING — pool de comparaison
    # ─────────────────────────────────────────────

    def get_pool_scores_for_trait(
        self,
        db: Session,
        trait: str,
        position_key: str,
        test_id: int,
    ) -> List[float]:
        """
        Récupère les scores d'un trait pour tous les candidats
        ciblant le même poste — utilisé par l'engine de benchmarking.
        """
        rows = (
            db.query(TestResult.scores)
            .join(User, User.id == TestResult.user_id)
            .filter(
                TestResult.test_id == test_id,
                func.lower(cast(User.position_targeted, String)) == position_key.lower(),
            )
            .all()
        )

        pool = []
        for (scores,) in rows:
            if not scores:
                continue
            # Support ancien et nouveau format
            traits_data = scores.get("traits", scores)
            val = traits_data.get(trait)
            if val is None:
                continue
            pool.append(val.get("score", 0) if isinstance(val, dict) else val)

        return pool

    # ─────────────────────────────────────────────
    # SNAPSHOT MANAGEMENT
    # ─────────────────────────────────────────────

    def update_crew_snapshot(
        self, db: Session, user_id: int, snapshot: Dict[str, Any]
    ) -> None:
        """
        Met à jour le psychometric_snapshot sur le profil candidat.
        Appelé après chaque soumission de test (synchrone).
        """
        user = db.query(User).filter(User.id == user_id).first()
        if user:
            user.psychometric_snapshot = snapshot
            user.snapshot_updated_at = datetime.utcnow()
            db.commit()

    def get_crew_snapshot(self, db: Session, user_id: int) -> Optional[Dict]:
        user = db.query(User).filter(User.id == user_id).first()
        return user.psychometric_snapshot if user else None

    # ─────────────────────────────────────────────
    # CONTRÔLE D'ACCÈS
    # ─────────────────────────────────────────────

    def check_requester_access(
        self, db: Session, candidate_id: int, requester_id: int
    ) -> bool:
        """
        Vérifie que le requester est :
        - le candidat lui-même
        - un client avec ce candidat dans une campagne active
        - un client avec ce candidat dans son équipage actif
        """
        if candidate_id == requester_id:
            return True

        in_campaign = (
            db.query(CampaignCandidate)
            .join(Campaign, Campaign.id == CampaignCandidate.campaign_id)
            .filter(
                CampaignCandidate.candidate_id == candidate_id,
                Campaign.client_id == requester_id,
            )
            .first()
        )
        if in_campaign:
            return True

        in_crew = (
            db.query(CrewAssignment)
            .join(Yacht, Yacht.id == CrewAssignment.yacht_id)
            .filter(
                CrewAssignment.user_id == candidate_id,
                CrewAssignment.is_active == True,
                Yacht.client_id == requester_id,
            )
            .first()
        )
        return bool(in_crew)

    # ─────────────────────────────────────────────
    # PROPAGATION BACKGROUND
    # ─────────────────────────────────────────────

    def get_active_yacht_ids(self, db: Session, user_id: int) -> List[int]:
        """Yachts où le marin est actuellement actif — pour la propagation background."""
        rows = (
            db.query(CrewAssignment.yacht_id)
            .filter(
                CrewAssignment.user_id == user_id,
                CrewAssignment.is_active == True,
            )
            .all()
        )
        return [r.yacht_id for r in rows]