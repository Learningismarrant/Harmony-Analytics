# modules/identity/repository.py
"""
Accès DB pour les profils candidats, expériences et documents.
Agrège les CRUD user.py, candidates.py et links.py existants.
"""
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.models.user import User, UserDocument
from app.models.yacht import CrewAssignment, Yacht
from app.models.campaign import Campaign, CampaignCandidate
from app.core.security import hash_password
from backend.app.shared.enums import ApplicationStatus, UserRole


class IdentityRepository:

    # ─────────────────────────────────────────────
    # LECTURE UTILISATEUR
    # ─────────────────────────────────────────────

    def get_by_id(self, db: Session, user_id: int) -> Optional[User]:
        return db.query(User).filter(User.id == user_id).first()

    def get_by_email(self, db: Session, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def create_user(self, db: Session, payload) -> User:
        user_data = payload.model_dump()
        password = user_data.pop("password")
        user_data["hashed_password"] = hash_password(password)
        db_obj = User(**user_data)
        try:
            db.add(db_obj)
            db.commit()
            db.refresh(db_obj)
            return db_obj
        except IntegrityError:
            db.rollback()
            raise ValueError("EMAIL_ALREADY_EXISTS")

    # ─────────────────────────────────────────────
    # MISE À JOUR IDENTITÉ
    # ─────────────────────────────────────────────

    def update_identity(self, db: Session, user: User, data: Dict[str, Any]) -> User:
        for key, value in data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        db.commit()
        db.refresh(user)
        return user

    def update_avatar(self, db: Session, user: User, new_url: str) -> User:
        user.avatar_url = new_url
        db.commit()
        db.refresh(user)
        return user

    def invalidate_harmony_verification(self, db: Session, user: User) -> None:
        """Appelé si le nom change — la vérification manuelle doit être rejouée."""
        user.is_harmony_verified = False
        db.commit()

    # ─────────────────────────────────────────────
    # CONTRÔLE D'ACCÈS
    # ─────────────────────────────────────────────

    def resolve_access_context(
        self, db: Session, subject_id: int, requester_id: int
    ) -> Optional[Dict]:
        """
        Détermine le niveau d'accès et retourne le contexte métier.
        Retourne None si l'accès est refusé.

        Contextes possibles :
        - CANDIDATE  : auto-consultation
        - MANAGER    : client avec ce marin dans son équipage actif
        - RECRUITER  : client avec ce marin candidat dans une campagne
        - ONBOARDING : client avec ce marin embauché (status=JOINED)
        """
        # Auto-consultation
        if subject_id == requester_id:
            subject = self.get_by_id(db, subject_id)
            return {
                "view_mode": "candidate",
                "context_position": subject.position_targeted if subject else None,
                "label": "Mon Profil",
                "is_active_crew": False,
            }

        requester = self.get_by_id(db, requester_id)
        if not requester or requester.role not in (UserRole.CLIENT, UserRole.ADMIN):
            return None

        # Client : est-il dans l'équipage actif ?
        crew = (
            db.query(CrewAssignment)
            .join(Yacht, Yacht.id == CrewAssignment.yacht_id)
            .filter(
                CrewAssignment.user_id == subject_id,
                CrewAssignment.is_active == True,
                Yacht.client_id == requester_id,
            )
            .first()
        )
        if crew:
            return {
                "view_mode": "manager",
                "context_position": crew.role,
                "label": f"Équipage – {crew.yacht.name}",
                "is_active_crew": True,
            }

        # Client : est-il candidat à une campagne ?
        candidacy = (
            db.query(CampaignCandidate)
            .join(Campaign, Campaign.id == CampaignCandidate.campaign_id)
            .filter(
                CampaignCandidate.candidate_id == subject_id,
                Campaign.client_id == requester_id,
            )
            .first()
        )
        if candidacy:
            is_joined = candidacy.status == ApplicationStatus.JOINED
            return {
                "view_mode": "onboarding" if is_joined else "recruiter",
                "context_position": candidacy.campaign.position,
                "label": f"{'Onboarding' if is_joined else 'Candidat'} – {candidacy.campaign.title}",
                "is_active_crew": False,
                "campaign_id": candidacy.campaign_id,
            }

        return None

    # ─────────────────────────────────────────────
    # EXPÉRIENCES
    # ─────────────────────────────────────────────

    def get_experiences(self, db: Session, user_id: int) -> List[CrewAssignment]:
        return (
            db.query(CrewAssignment)
            .filter(CrewAssignment.user_id == user_id)
            .order_by(CrewAssignment.start_date.desc())
            .all()
        )

    def create_experience(self, db: Session, user_id: int, data: Dict) -> CrewAssignment:
        db_obj = CrewAssignment(
            user_id=user_id,
            is_harmony_approved=False,
            **data,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def approve_experience(self, db: Session, exp_id: int, comment: str) -> Optional[CrewAssignment]:
        exp = db.query(CrewAssignment).filter(CrewAssignment.id == exp_id).first()
        if not exp:
            return None
        exp.is_harmony_approved = True
        exp.reference_comment = comment
        db.commit()
        db.refresh(exp)
        return exp

    # ─────────────────────────────────────────────
    # DOCUMENTS
    # ─────────────────────────────────────────────

    def get_documents(self, db: Session, user_id: int) -> List[UserDocument]:
        return db.query(UserDocument).filter(UserDocument.user_id == user_id).all()

    def create_pending_document(
        self, db: Session, user_id: int, file_url: str, title: str
    ) -> UserDocument:
        db_obj = UserDocument(
            user_id=user_id,
            file_url=file_url,
            title=title,
            is_verified=False,
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update_document_verification(
        self, db: Session, doc_id: int, verification_result: Dict
    ) -> Optional[UserDocument]:
        """
        Met à jour le statut de vérification d'un document.
        Appelé par infra/verification.py après OCR + Promete.
        """
        doc = db.query(UserDocument).filter(UserDocument.id == doc_id).first()
        if not doc:
            return None

        official = verification_result.get("official_data", {})
        ocr_data = verification_result.get("ocr_data", {}).get("extracted", {})

        doc.is_verified = verification_result.get("is_officially_valid", False)
        doc.verified_at = datetime.utcnow()
        doc.verification_metadata = verification_result

        if official:
            doc.official_id = official.get("num_titre")
            doc.official_brevet = official.get("brevet_libelle")
            doc.num_titulaire_officiel = official.get("num_titulaire")
            if doc.official_brevet:
                doc.title = doc.official_brevet

            # Date expiration : officiel en priorité, OCR en fallback
            expiry_str = official.get("date_expiration")
            if not expiry_str or expiry_str == "N/A":
                expiry_str = ocr_data.get("date_expiration")

            if expiry_str:
                try:
                    import re
                    match = re.search(r"(\d{2}/\d{2}/\d{4})", str(expiry_str))
                    if match:
                        doc.expiry_date = datetime.strptime(match.group(1), "%d/%m/%Y")
                except Exception:
                    pass

        db.commit()
        db.refresh(doc)
        return doc

    # ─────────────────────────────────────────────
    # GATEWAY (token boarding / campagne)
    # ─────────────────────────────────────────────

    def get_yacht_by_boarding_token(self, db: Session, token: str) -> Optional[Yacht]:
        return db.query(Yacht).filter(Yacht.boarding_token == token).first()

    def join_crew_via_token(self, db: Session, yacht: Yacht, user_id: int) -> Optional[CrewAssignment]:
        import secrets
        existing = db.query(CrewAssignment).filter(
            CrewAssignment.yacht_id == yacht.id,
            CrewAssignment.user_id == user_id,
            CrewAssignment.is_active == True,
        ).first()
        if existing:
            return None

        assignment = CrewAssignment(
            yacht_id=yacht.id,
            user_id=user_id,
            role="Deckhand",
            is_active=True,
        )
        db.add(assignment)
        # Rotation du token après usage
        yacht.boarding_token = secrets.token_urlsafe(16)
        db.commit()
        db.refresh(assignment)
        return assignment