# modules/identity/repository.py
"""
Accès DB pour les profils candidats, expériences et documents.

Changements v2 :
- position_targeted et experience_years sur CrewProfile (pas User)
- resolve_access_context utilise employer_profile_id
- CrewAssignment.crew_profile_id (était user_id)
- Yacht.employer_profile_id (était client_id)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone

from app.shared.models import (User, UserDocument, CrewProfile, EmployerProfile,
                            CrewAssignment, Yacht,
                            Campaign, CampaignCandidate)

from app.core.security import hash_password
from app.shared.enums import ApplicationStatus, UserRole


class IdentityRepository:

    # ── Lecture utilisateur ───────────────────────────────────

    async def get_user_by_id(self, db: AsyncSession, user_id: int) -> Optional[User]:
        r = await db.execute(select(User).where(User.id == user_id))
        return r.scalar_one_or_none()

    async def get_crew_by_id(
        self, db: AsyncSession, crew_profile_id: int
    ) -> Optional[CrewProfile]:
        r = await db.execute(
            select(CrewProfile).where(CrewProfile.id == crew_profile_id)
        )
        return r.scalar_one_or_none()

    async def get_crew_by_user_id(
        self, db: AsyncSession, user_id: int
    ) -> Optional[CrewProfile]:
        r = await db.execute(
            select(CrewProfile).where(CrewProfile.user_id == user_id)
        )
        return r.scalar_one_or_none()

    # ── Mise à jour identité (User) ───────────────────────────

    async def update_identity(
        self, db: AsyncSession, user: User, data: Dict[str, Any]
    ) -> User:
        for key, value in data.items():
            if value is not None and hasattr(user, key):
                setattr(user, key, value)
        await db.commit()
        await db.refresh(user)
        return user

    async def update_avatar(
        self, db: AsyncSession, user: User, new_url: str
    ) -> User:
        user.avatar_url = new_url
        await db.commit()
        await db.refresh(user)
        return user

    async def invalidate_harmony_verification(
        self, db: AsyncSession, user: User
    ) -> None:
        user.is_harmony_verified = False
        await db.commit()

    # ── Mise à jour profil crew (CrewProfile) ─────────────────

    async def update_crew_profile(
        self, db: AsyncSession, crew: CrewProfile, data: Dict[str, Any]
    ) -> CrewProfile:
        """
        v2 : position_targeted, availability_status, experience_years
        sont sur CrewProfile, pas sur User.
        """
        for key, value in data.items():
            if value is not None and hasattr(crew, key):
                setattr(crew, key, value)
        await db.commit()
        await db.refresh(crew)
        return crew

    # ── Contrôle d'accès ─────────────────────────────────────

    async def resolve_access_context(
        self,
        db: AsyncSession,
        crew_profile_id: int,       # v2 : subject est un CrewProfile
        requester_user_id: int,
    ) -> Optional[Dict]:
        """
        Détermine le niveau d'accès du requester sur ce crew_profile.

        v2 :
        - Self-check via User.crew_profile.id
        - Manager : employeur avec ce marin dans son équipage (employer_profile_id)
        - Recruiter : campagne de cet employeur avec ce crew_profile_id candidat

        Retourne None si accès refusé.
        """
        # Auto-consultation
        crew_check = await db.execute(
            select(CrewProfile).where(
                CrewProfile.id == crew_profile_id,
                CrewProfile.user_id == requester_user_id,
            )
        )
        if crew_check.scalar_one_or_none():
            crew = await self.get_crew_by_id(db, crew_profile_id)
            return {
                "view_mode": "candidate",
                "context_position": str(crew.position_targeted) if crew else None,
                "label": "Mon Profil",
                "is_active_crew": False,
            }

        # Vérifier que le requester est bien un employer
        r = await db.execute(
            select(EmployerProfile).where(EmployerProfile.user_id == requester_user_id)
        )
        employer = r.scalar_one_or_none()
        if not employer:
            return None  # Ni self ni employer → refusé

        # Équipage actif d'un yacht appartenant à cet employer
        r = await db.execute(
            select(CrewAssignment, Yacht)
            .join(Yacht, Yacht.id == CrewAssignment.yacht_id)
            .where(
                CrewAssignment.crew_profile_id == crew_profile_id,   # v2
                CrewAssignment.is_active == True,
                Yacht.employer_profile_id == employer.id,             # v2
            )
        )
        row = r.first()
        if row:
            assignment, yacht = row
            return {
                "view_mode": "manager",
                "context_position": str(assignment.role),
                "label": f"Équipage – {yacht.name}",
                "is_active_crew": True,
            }

        # Candidat dans une campagne de cet employer
        r = await db.execute(
            select(CampaignCandidate, Campaign)
            .join(Campaign, Campaign.id == CampaignCandidate.campaign_id)
            .where(
                CampaignCandidate.crew_profile_id == crew_profile_id,  # v2
                Campaign.employer_profile_id == employer.id,            # v2
            )
        )
        row = r.first()
        if row:
            candidacy, campaign = row
            is_joined = candidacy.status == ApplicationStatus.JOINED
            return {
                "view_mode": "onboarding" if is_joined else "recruiter",
                "context_position": campaign.position,
                "label": f"{'Onboarding' if is_joined else 'Candidat'} – {campaign.title}",
                "is_active_crew": False,
                "campaign_id": candidacy.campaign_id,
            }

        return None  # Aucune relation trouvée

    # ── Expériences (CrewAssignment) ──────────────────────────

    async def get_experiences(
        self, db: AsyncSession, crew_profile_id: int   # v2
    ) -> List[CrewAssignment]:
        r = await db.execute(
            select(CrewAssignment)
            .where(CrewAssignment.crew_profile_id == crew_profile_id)
            .order_by(CrewAssignment.start_date.desc())
        )
        return r.scalars().all()

    async def create_experience(
        self, db: AsyncSession, crew_profile_id: int, data: Dict  # v2
    ) -> CrewAssignment:
        db_obj = CrewAssignment(
            crew_profile_id=crew_profile_id,
            is_harmony_approved=False,
            **data,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def approve_experience(
        self, db: AsyncSession, exp_id: int, comment: str
    ) -> Optional[CrewAssignment]:
        r = await db.execute(
            select(CrewAssignment).where(CrewAssignment.id == exp_id)
        )
        exp = r.scalar_one_or_none()
        if not exp:
            return None
        exp.is_harmony_approved = True
        exp.reference_comment = comment
        await db.commit()
        await db.refresh(exp)
        return exp

    # ── Documents ─────────────────────────────────────────────

    async def get_documents(
        self, db: AsyncSession, user_id: int
    ) -> List[UserDocument]:
        r = await db.execute(
            select(UserDocument).where(UserDocument.user_id == user_id)
        )
        return r.scalars().all()

    async def create_pending_document(
        self, db: AsyncSession, user_id: int, file_url: str, title: str
    ) -> UserDocument:
        db_obj = UserDocument(
            user_id=user_id,
            file_url=file_url,
            title=title,
            is_verified=False,
        )
        db.add(db_obj)
        await db.commit()
        await db.refresh(db_obj)
        return db_obj

    async def update_document_verification(
        self, db: AsyncSession, doc_id: int, verification_result: Dict
    ) -> Optional[UserDocument]:
        """OCR + Promete → mise à jour du statut du document."""
        r = await db.execute(
            select(UserDocument).where(UserDocument.id == doc_id)
        )
        doc = r.scalar_one_or_none()
        if not doc:
            return None

        official = verification_result.get("official_data", {})
        ocr_data = verification_result.get("ocr_data", {}).get("extracted", {})

        doc.is_verified = verification_result.get("is_officially_valid", False)
        doc.verified_at = datetime.now(timezone.utc)
        doc.verification_metadata = verification_result

        if official:
            doc.official_id            = official.get("num_titre")
            doc.official_brevet        = official.get("brevet_libelle")
            doc.num_titulaire_officiel = official.get("num_titulaire")
            if doc.official_brevet:
                doc.title = doc.official_brevet

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

        await db.commit()
        await db.refresh(doc)
        return doc

    # ── Gateway (token boarding / campagne) ───────────────────

    async def get_yacht_by_boarding_token(
        self, db: AsyncSession, token: str
    ) -> Optional[Yacht]:
        r = await db.execute(
            select(Yacht).where(Yacht.boarding_token == token)
        )
        return r.scalar_one_or_none()

    async def join_crew_via_token(
        self, db: AsyncSession, yacht: Yacht, crew_profile_id: int  # v2
    ) -> Optional[CrewAssignment]:
        """
        Le marin rejoint un yacht via QR code.
        v2 : utilise crew_profile_id.
        Rotation du boarding_token après usage (1 usage par token).
        """
        import secrets
        r = await db.execute(
            select(CrewAssignment).where(
                CrewAssignment.yacht_id == yacht.id,
                CrewAssignment.crew_profile_id == crew_profile_id,
                CrewAssignment.is_active == True,
            )
        )
        if r.scalar_one_or_none():
            return None  # Déjà assigné

        assignment = CrewAssignment(
            yacht_id=yacht.id,
            crew_profile_id=crew_profile_id,    # v2
            role="Deckhand",
            is_active=True,
        )
        db.add(assignment)
        yacht.boarding_token = secrets.token_urlsafe(16)
        await db.commit()
        await db.refresh(assignment)
        return assignment