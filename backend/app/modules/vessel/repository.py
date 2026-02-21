# modules/vessel/repository.py
"""
Accès DB pour les yachts, équipages et snapshots vessel/fleet.
"""
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone, timedelta

from app.models.yacht import Yacht, CrewAssignment
from app.models.user import User
from app.schemas.yacht import YachtCreate, YachtUpdate


class VesselRepository:

    # ─────────────────────────────────────────────
    # YACHTS
    # ─────────────────────────────────────────────

    def get_yachts_by_client(self, db: Session, client_id: int) -> List[Yacht]:
        return db.query(Yacht).filter(Yacht.client_id == client_id).all()

    def get_by_id(self, db: Session, yacht_id: int) -> Optional[Yacht]:
        return db.query(Yacht).filter(Yacht.id == yacht_id).first()

    def get_secure(self, db: Session, yacht_id: int, client_id: int) -> Optional[Yacht]:
        return db.query(Yacht).filter(
            Yacht.id == yacht_id,
            Yacht.client_id == client_id,
        ).first()

    def is_owner(self, db: Session, yacht_id: int, client_id: int) -> bool:
        return self.get_secure(db, yacht_id, client_id) is not None

    def create(self, db: Session, payload: YachtCreate, client_id: int) -> Yacht:
        db_obj = Yacht(**payload.model_dump(), client_id=client_id)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, yacht: Yacht, payload: YachtUpdate) -> Yacht:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(yacht, field, value)
        db.commit()
        db.refresh(yacht)
        return yacht

    def get_by_boarding_token(self, db: Session, token: str) -> Optional[Yacht]:
        return db.query(Yacht).filter(Yacht.boarding_token == token).first()

    def rotate_boarding_token(self, db: Session, yacht: Yacht) -> str:
        import secrets
        yacht.boarding_token = secrets.token_urlsafe(16)
        db.commit()
        return yacht.boarding_token

    # ─────────────────────────────────────────────
    # ÉQUIPAGE
    # ─────────────────────────────────────────────

    def get_active_crew(self, db: Session, yacht_id: int) -> List[CrewAssignment]:
        return db.query(CrewAssignment).filter(
            CrewAssignment.yacht_id == yacht_id,
            CrewAssignment.is_active == True,
        ).all()

    def get_active_crew_ids(self, db: Session, yacht_id: int) -> List[int]:
        rows = db.query(CrewAssignment.user_id).filter(
            CrewAssignment.yacht_id == yacht_id,
            CrewAssignment.is_active == True,
        ).all()
        return [r.user_id for r in rows]

    def get_assignment(
        self, db: Session, yacht_id: int, user_id: int
    ) -> Optional[CrewAssignment]:
        return db.query(CrewAssignment).filter(
            CrewAssignment.yacht_id == yacht_id,
            CrewAssignment.user_id == user_id,
            CrewAssignment.is_active == True,
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
        if not assignment:
            return False
        assignment.is_active = False
        assignment.end_date = datetime.now(timezone.utc)
        db.commit()
        return True

    # ─────────────────────────────────────────────
    # SNAPSHOTS — le cœur de l'architecture cache
    # ─────────────────────────────────────────────

    def get_crew_snapshots(self, db: Session, yacht_id: int) -> List[Dict]:
        """
        Retourne la liste des psychometric_snapshots de l'équipage actif.
        C'est l'input principal de l'engine team/harmony.
        Filtre les membres sans snapshot (profil incomplet).
        """
        rows = (
            db.query(User.psychometric_snapshot)
            .join(CrewAssignment, CrewAssignment.user_id == User.id)
            .filter(
                CrewAssignment.yacht_id == yacht_id,
                CrewAssignment.is_active == True,
                User.psychometric_snapshot.isnot(None),
            )
            .all()
        )
        return [r.psychometric_snapshot for r in rows if r.psychometric_snapshot]

    def get_vessel_snapshot(self, db: Session, yacht_id: int) -> Optional[Dict]:
        yacht = self.get_by_id(db, yacht_id)
        return yacht.vessel_snapshot if yacht else None

    def update_vessel_snapshot(
        self, db: Session, yacht_id: int, snapshot: Dict[str, Any]
    ) -> None:
        """
        Mise à jour du vessel_snapshot après changement d'équipe ou test.
        Appelé par le background task depuis assessment/service.py
        ou directement par crew/service.py lors d'une affectation.
        """
        yacht = self.get_by_id(db, yacht_id)
        if yacht:
            yacht.vessel_snapshot = snapshot
            yacht.snapshot_updated_at = datetime.utcnow()
            db.commit()

    def update_observed_scores(
        self, db: Session, yacht_id: int, observed: Dict[str, Any]
    ) -> None:
        """
        Enrichit le vessel_snapshot avec les scores observés depuis les surveys.
        Merge partiel — ne remplace pas le snapshot entier.
        """
        yacht = self.get_by_id(db, yacht_id)
        if not yacht:
            return
        current = yacht.vessel_snapshot or {}
        current["observed_scores"] = observed
        yacht.vessel_snapshot = current
        db.commit()

    def is_vessel_snapshot_stale(
        self, db: Session, yacht_id: int, ttl_minutes: int = 10
    ) -> bool:
        yacht = self.get_by_id(db, yacht_id)
        if not yacht or not yacht.snapshot_updated_at:
            return True
        age = datetime.utcnow() - yacht.snapshot_updated_at
        return age > timedelta(minutes=ttl_minutes)

    def get_captain_vector(self, db: Session, yacht_id: int) -> Optional[Dict]:
        yacht = self.get_by_id(db, yacht_id)
        return yacht.captain_leadership_vector if yacht else None

    def update_environment_params(
        self, db: Session, yacht_id: int, params: Dict[str, Any]
    ) -> Optional[Yacht]:
        """
        Met à jour les paramètres JD-R (F_env) et le vecteur capitaine (F_lmx).
        Stocké dans vessel_snapshot.jdr_params et captain_leadership_vector.
        """
        yacht = self.get_by_id(db, yacht_id)
        if not yacht:
            return None

        # Paramètres JD-R → vessel_snapshot
        current = yacht.vessel_snapshot or {}
        current["jdr_params"] = {
            "charter_intensity": params.get("charter_intensity", 0.5),
            "management_pressure": params.get("management_pressure", 0.5),
            "salary_index": params.get("salary_index", 0.5),
            "rest_days_ratio": params.get("rest_days_ratio", 0.5),
            "private_cabin_ratio": params.get("private_cabin_ratio", 0.5),
        }
        yacht.vessel_snapshot = current

        # Vecteur capitaine → colonne dédiée
        if any(k in params for k in ("captain_autonomy_given", "captain_feedback_style", "captain_structure_imposed")):
            yacht.captain_leadership_vector = {
                "autonomy_given": params.get("captain_autonomy_given", 0.5),
                "feedback_style": params.get("captain_feedback_style", 0.5),
                "structure_imposed": params.get("captain_structure_imposed", 0.5),
            }

        db.commit()
        db.refresh(yacht)
        return yacht

    # ─────────────────────────────────────────────
    # FLEET (Office)
    # ─────────────────────────────────────────────

    def get_office_ids_for_yachts(
        self, db: Session, yacht_ids: List[int]
    ) -> List[int]:
        """
        Retourne les client_ids (office) propriétaires des yachts impactés.
        Permet de savoir quels fleet_snapshots doivent être recalculés.
        """
        rows = (
            db.query(Yacht.client_id)
            .filter(Yacht.id.in_(yacht_ids))
            .distinct()
            .all()
        )
        return [r.client_id for r in rows]

    def get_all_vessel_snapshots_for_office(
        self, db: Session, office_id: int
    ) -> List[Dict]:
        """Pour le recalcul du fleet_snapshot (clustering, ANOVA)."""
        rows = (
            db.query(Yacht.id, Yacht.vessel_snapshot)
            .filter(Yacht.client_id == office_id)
            .all()
        )
        return [
            {"yacht_id": r.id, "snapshot": r.vessel_snapshot}
            for r in rows
            if r.vessel_snapshot
        ]