# modules/identity/service.py
"""
Orchestration du profil identitaire du candidat.

Responsabilités :
1. Contrôle d'accès via resolve_access_context() (repo)
2. Composition des vues selon le view_mode (candidate / recruiter / manager / onboarding)
3. Extraction et formatage des rapports psychométriques depuis le snapshot
4. Upload de fichiers (avatar ou documents) + vérification Harmony en background
5. Mise à jour identité (User + CrewProfile en une transaction logique)

Règle de séparation :
    - Le service ne touche jamais la DB directement.
    - Toute la logique SQL est dans IdentityRepository.
    - La logique de présentation (formatage snapshot → rapport) est ici.

Contextes d'accès (view_mode) :
    "candidate"  → le marin consulte son propre profil (rapport complet)
    "recruiter"  → employeur avec ce marin en candidature (rapport recruteur)
    "manager"    → employeur avec ce marin dans son équipage (rapport manager)
    "onboarding" → employeur avec ce marin embauché (rapport onboarding + conseils)
"""
from __future__ import annotations

from fastapi import BackgroundTasks, UploadFile
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Dict, List, Optional, Any

from app.modules.identity.repository import IdentityRepository
from app.shared.models import User, CrewProfile, EmployerProfile
from app.shared.enums import ApplicationStatus

repo = IdentityRepository()

# Titres de documents qui déclenchent le traitement avatar
AVATAR_TITLES = {"AVATAR_USER", "avatar"}


class IdentityService:

    # ── Full profile ──────────────────────────────────────────────────────────

    async def get_full_profile(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester: User,
    ) -> Optional[Dict]:
        """
        Profil complet — usage restreint (premier chargement uniquement).
        Résout le contexte d'accès puis assemble toutes les sections.
        Retourne None si l'accès est refusé.
        """
        ctx = await repo.resolve_access_context(db, crew_profile_id, requester.id)
        if not ctx:
            return None

        crew = await repo.get_crew_by_id(db, crew_profile_id)
        if not crew:
            return None

        user = await repo.get_user_by_id(db, crew.user_id)
        if not user:
            return None

        experiences = await repo.get_experiences(db, crew_profile_id)
        documents   = await repo.get_documents(db, user.id)
        reports     = self._build_psychometric_report(
            crew.psychometric_snapshot,
            view_mode=ctx["view_mode"],
            context_position=ctx.get("context_position"),
        )

        return {
            "crew_profile_id":  crew.id,
            "view_mode":        ctx["view_mode"],
            "context_label":    ctx["label"],
            "is_active_crew":   ctx["is_active_crew"],

            # ── Identité ─────────────────────────────────────────
            "identity": self._format_identity(user, crew),

            # ── Expériences ───────────────────────────────────────
            "experiences": [self._format_experience(e) for e in experiences],

            # ── Documents ─────────────────────────────────────────
            "documents": [self._format_document(d) for d in documents],

            # ── Rapports psychométriques ──────────────────────────
            "reports": reports,
        }

    # ── Endpoints modulaires ──────────────────────────────────────────────────

    async def get_identity(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester: User,
    ) -> Optional[Dict]:
        ctx = await repo.resolve_access_context(db, crew_profile_id, requester.id)
        if not ctx:
            return None

        crew = await repo.get_crew_by_id(db, crew_profile_id)
        if not crew:
            return None

        user = await repo.get_user_by_id(db, crew.user_id)
        if not user:
            return None

        return self._format_identity(user, crew)

    async def get_experiences(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester: User,
    ) -> Optional[List[Dict]]:
        ctx = await repo.resolve_access_context(db, crew_profile_id, requester.id)
        if not ctx:
            return None

        experiences = await repo.get_experiences(db, crew_profile_id)
        return [self._format_experience(e) for e in experiences]

    async def get_documents(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester: User,
    ) -> Optional[List[Dict]]:
        ctx = await repo.resolve_access_context(db, crew_profile_id, requester.id)
        if not ctx:
            return None

        crew = await repo.get_crew_by_id(db, crew_profile_id)
        if not crew:
            return None

        documents = await repo.get_documents(db, crew.user_id)
        return [self._format_document(d) for d in documents]

    async def get_reports(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        requester: User,
        force_onboarding: bool = False,
    ) -> Optional[Dict]:
        ctx = await repo.resolve_access_context(db, crew_profile_id, requester.id)
        if not ctx:
            return None

        crew = await repo.get_crew_by_id(db, crew_profile_id)
        if not crew:
            return None

        view_mode = "onboarding" if force_onboarding else ctx["view_mode"]

        return self._build_psychometric_report(
            crew.psychometric_snapshot,
            view_mode=view_mode,
            context_position=ctx.get("context_position"),
        )

    async def get_onboarding_advice(
        self,
        db: AsyncSession,
        crew_profile_id: int,
        employer_profile_id: int,   # v2 : EmployerProfile.id (pas user_id)
    ) -> Optional[Dict]:
        """
        Accessible uniquement si le candidat est JOINED dans une campagne
        de cet employeur. Extrait les onboarding_tips du snapshot.
        """
        # Vérification : le marin est bien JOINED pour cet employer
        employer = await db.get(EmployerProfile, employer_profile_id)
        if not employer:
            return None

        # Réutilise resolve_access_context via user_id de l'employer
        ctx = await repo.resolve_access_context(db, crew_profile_id, employer.user_id)
        if not ctx or ctx["view_mode"] not in ("onboarding", "manager"):
            return None

        crew = await repo.get_crew_by_id(db, crew_profile_id)
        if not crew or not crew.psychometric_snapshot:
            return None

        tips = crew.psychometric_snapshot.get("onboarding_tips") or {}
        if not tips:
            return None

        return {
            "crew_profile_id":   crew_profile_id,
            "context_position":  ctx.get("context_position"),
            "onboarding_tips":   tips,
            "integration_risks": crew.psychometric_snapshot.get("integration_risks", []),
            "management_advice": crew.psychometric_snapshot.get("management_advice", {}),
        }

    # ── Mise à jour ───────────────────────────────────────────────────────────

    async def update_identity(
        self,
        db: AsyncSession,
        crew: CrewProfile,
        payload,
    ) -> None:
        """
        v2 : les champs identitaires sont répartis entre User et CrewProfile.

        Sur User           : name, location, phone, bio
        Sur CrewProfile    : position_targeted, availability_status,
                             experience_years, languages, nationality
        """
        data = payload.model_dump(exclude_unset=True)

        # Champs User
        user_fields = {"name", "location", "phone", "bio", "avatar_url"}
        user_data   = {k: v for k, v in data.items() if k in user_fields}

        # Champs CrewProfile
        crew_fields = {
            "position_targeted", "availability_status",
            "experience_years", "languages", "nationality",
        }
        crew_data = {k: v for k, v in data.items() if k in crew_fields}

        user = await repo.get_user_by_id(db, crew.user_id)
        if user and user_data:
            # Invalide la vérification Harmony si le nom change
            if "name" in user_data and user_data["name"] != user.name:
                await repo.invalidate_harmony_verification(db, user)
            await repo.update_identity(db, user, user_data)

        if crew_data:
            await repo.update_crew_profile(db, crew, crew_data)

    async def add_experience(
        self,
        db: AsyncSession,
        crew: CrewProfile,
        payload,
    ) -> Dict:
        """
        Ajoute une expérience professionnelle liée à crew_profile_id.
        is_harmony_approved = False par défaut — vérification en background.
        """
        data = payload.model_dump(exclude_unset=True)
        experience = await repo.create_experience(db, crew.id, data)
        return self._format_experience(experience)

    # ── Upload ────────────────────────────────────────────────────────────────

    async def upload_document(
        self,
        db: AsyncSession,
        crew: CrewProfile,
        title: str,
        file: UploadFile,
        background_tasks: BackgroundTasks,
    ) -> Dict:
        """
        Upload avatar ou document.

        Avatar (title in AVATAR_TITLES) :
            → Stockage synchrone + mise à jour User.avatar_url immédiate.

        Document :
            → Stockage + création UserDocument (is_verified=False)
            → Vérification Harmony (OCR + Promete) en background.

        Note : UserDocument reste lié à user_id (pas crew_profile_id)
        pour l'accès admin cross-profil.
        """
        from app.infra.storage import upload_file

        user = await repo.get_user_by_id(db, crew.user_id)
        if not user:
            raise ValueError("Utilisateur introuvable.")

        # ── Lecture du fichier ────────────────────────────────
        content = await file.read()
        if not content:
            raise ValueError("Fichier vide.")

        # ── Avatar ────────────────────────────────────────────
        if title.upper() in {t.upper() for t in AVATAR_TITLES}:
            file_url = await upload_file(
                content=content,
                filename=file.filename or "avatar.jpg",
                content_type=file.content_type or "image/jpeg",
                folder=f"avatars/{user.id}",
            )
            await repo.update_avatar(db, user, file_url)
            return {
                "type":     "avatar",
                "file_url": file_url,
                "message":  "Avatar mis à jour.",
            }

        # ── Document ──────────────────────────────────────────
        file_url = await upload_file(
            content=content,
            filename=file.filename or title,
            content_type=file.content_type or "application/octet-stream",
            folder=f"documents/{user.id}",
        )

        doc = await repo.create_pending_document(
            db,
            user_id=user.id,     # UserDocument lié à user_id
            file_url=file_url,
            title=title,
        )

        # Vérification Harmony en background (OCR + Promete)
        background_tasks.add_task(
            self._verify_document_background,
            doc_id=doc.id,
            file_url=file_url,
            title=title,
        )

        return {
            "type":        "document",
            "document_id": doc.id,
            "file_url":    file_url,
            "title":       title,
            "is_verified": False,
            "message":     "Document reçu. Vérification en cours.",
        }

    # ── Background tasks ──────────────────────────────────────────────────────

    async def _verify_document_background(
        self,
        doc_id: int,
        file_url: str,
        title: str,
    ) -> None:
        """
        Vérification OCR + Promete en background.
        Utilise sa propre session DB (isolée du contexte HTTP).
        """
        from app.core.database import AsyncSessionLocal
        from app.infra.ocr import extract_document_data
        from app.infra.promete import verify_with_promete

        async with AsyncSessionLocal() as db:
            try:
                ocr_result = await extract_document_data(file_url, title)
                promete_result = await verify_with_promete(ocr_result)

                verification = {
                    "ocr_data":           ocr_result,
                    "official_data":      promete_result.get("official_data", {}),
                    "is_officially_valid": promete_result.get("is_valid", False),
                }

                await repo.update_document_verification(db, doc_id, verification)

            except Exception as e:
                print(f"[BACKGROUND] Vérification document {doc_id} échouée : {e}")

    # ── Formatters ────────────────────────────────────────────────────────────

    def _format_identity(self, user: User, crew: CrewProfile) -> Dict:
        """
        Vue identité — fusion User (données compte) + CrewProfile (données métier).
        """
        return {
            "crew_profile_id":      crew.id,
            "user_id":              user.id,

            # Données User
            "name":                 user.name,
            "email":                user.email,
            "avatar_url":           user.avatar_url,
            "location":             user.location,
            "phone":                getattr(user, "phone", None),
            "bio":                  getattr(user, "bio", None),
            "is_harmony_verified":  getattr(user, "is_harmony_verified", False),

            # Données CrewProfile
            "position_targeted":    str(crew.position_targeted) if crew.position_targeted else None,
            "availability_status":  str(crew.availability_status) if crew.availability_status else None,
            "experience_years":     crew.experience_years,
            "nationality":          getattr(crew, "nationality", None),
            "languages":            getattr(crew, "languages", []),
        }

    def _format_experience(self, exp) -> Dict:
        return {
            "id":                   exp.id,
            "yacht_id":             exp.yacht_id,
            "role":                 exp.role,
            "start_date":           exp.start_date.isoformat() if exp.start_date else None,
            "end_date":             exp.end_date.isoformat() if exp.end_date else None,
            "is_active":            exp.is_active,
            "is_harmony_approved":  getattr(exp, "is_harmony_approved", False),
            "reference_comment":    getattr(exp, "reference_comment", None),
        }

    def _format_document(self, doc) -> Dict:
        return {
            "id":            doc.id,
            "title":         doc.title,
            "file_url":      doc.file_url,
            "is_verified":   doc.is_verified,
            "verified_at":   doc.verified_at.isoformat() if doc.verified_at else None,
            "expiry_date":   doc.expiry_date.isoformat() if doc.expiry_date else None,
            "official_brevet": getattr(doc, "official_brevet", None),
        }

    def _build_psychometric_report(
        self,
        snapshot: Optional[Dict],
        view_mode: str,
        context_position: Optional[str] = None,
    ) -> Dict:
        """
        Formate le psychometric_snapshot en rapport selon le view_mode.

        Niveaux de détail par contexte :
            candidate  → rapport complet (tous les traits + scores bruts)
            recruiter  → rapport filtré (pas les scores bruts, juste les dimensions)
            manager    → rapport axé cohésion/style de travail
            onboarding → rapport axé intégration + conseils managériaux

        Si snapshot absent → rapport vide avec has_data=False.
        """
        if not snapshot:
            return {
                "has_data":     False,
                "view_mode":    view_mode,
                "message":      "Aucune évaluation psychométrique complétée.",
            }

        big_five   = snapshot.get("big_five", {})
        cognitive  = snapshot.get("cognitive", {})
        resilience = snapshot.get("resilience")

        # ── Scores normalisés (communs à tous les modes) ──────
        dimensions = self._extract_dimensions(big_five, cognitive, resilience)

        base = {
            "has_data":          True,
            "view_mode":         view_mode,
            "context_position":  context_position,
            "snapshot_version":  snapshot.get("version", "1.0"),
            "dimensions":        dimensions,
        }

        # ── Vue candidat : rapport complet ────────────────────
        if view_mode == "candidate":
            base["raw_scores"]   = self._extract_raw_scores(big_five, cognitive)
            base["benchmarks"]   = snapshot.get("benchmarks", {})
            base["test_history"] = snapshot.get("test_history", [])
            return base

        # ── Vue recruteur : dimensions + signaux clés ─────────
        if view_mode == "recruiter":
            base["key_signals"]  = self._extract_key_signals(snapshot, context_position)
            base["risk_signals"] = snapshot.get("risk_signals", [])
            return base

        # ── Vue manager : style de travail + cohésion ─────────
        if view_mode == "manager":
            base["work_style"]        = snapshot.get("work_style", {})
            base["team_contribution"] = snapshot.get("team_contribution", {})
            base["communication_tips"] = snapshot.get("communication_tips", [])
            return base

        # ── Vue onboarding : intégration + conseils ───────────
        if view_mode == "onboarding":
            base["onboarding_tips"]   = snapshot.get("onboarding_tips", {})
            base["integration_risks"] = snapshot.get("integration_risks", [])
            base["management_advice"] = snapshot.get("management_advice", {})
            base["key_signals"]       = self._extract_key_signals(snapshot, context_position)
            return base

        # Fallback : dimensions uniquement
        return base

    def _extract_dimensions(
        self,
        big_five: Dict,
        cognitive: Dict,
        resilience: Optional[float],
    ) -> Dict:
        """
        Extrait les dimensions psychométriques normalisées (0-100).
        Gère les deux formats de snapshot (score direct ou dict avec "score").
        """
        def get_score(val: Any) -> Optional[float]:
            if val is None:
                return None
            if isinstance(val, dict):
                return val.get("score")
            return float(val)

        n_score = get_score(big_five.get("neuroticism"))
        es = round(100.0 - n_score, 1) if n_score is not None else None

        return {
            "agreeableness":      get_score(big_five.get("agreeableness")),
            "conscientiousness":  get_score(big_five.get("conscientiousness")),
            "openness":           get_score(big_five.get("openness")),
            "extraversion":       get_score(big_five.get("extraversion")),
            "emotional_stability": es,
            "gca":                cognitive.get("gca_score"),
            "resilience":         resilience,
        }

    def _extract_raw_scores(self, big_five: Dict, cognitive: Dict) -> Dict:
        """Scores bruts pour la vue candidat (accès complet)."""
        return {
            "big_five":  big_five,
            "cognitive": cognitive,
        }

    def _extract_key_signals(
        self,
        snapshot: Dict,
        context_position: Optional[str],
    ) -> List[Dict]:
        """
        Signaux clés pour les vues recruteur et onboarding.
        Extraits depuis les flags du snapshot ou calculés à la volée.
        """
        signals = snapshot.get("key_signals", [])
        if signals:
            return signals

        # Génération à la volée si key_signals absent du snapshot
        big_five  = snapshot.get("big_five", {})
        cognitive = snapshot.get("cognitive", {})
        generated = []

        def score_of(val):
            if isinstance(val, dict):
                return val.get("score")
            return val

        a = score_of(big_five.get("agreeableness"))
        c = score_of(big_five.get("conscientiousness"))
        n = score_of(big_five.get("neuroticism"))
        gca = cognitive.get("gca_score")

        if a is not None and a >= 70:
            generated.append({"type": "strength", "label": "Esprit d'équipe élevé", "trait": "agreeableness"})
        if a is not None and a < 35:
            generated.append({"type": "risk", "label": "Risque friction équipe", "trait": "agreeableness"})

        if c is not None and c >= 70:
            generated.append({"type": "strength", "label": "Très organisé et fiable", "trait": "conscientiousness"})
        if c is not None and c < 35:
            generated.append({"type": "risk", "label": "Manque de rigueur", "trait": "conscientiousness"})

        if n is not None and (100 - n) < 35:
            generated.append({"type": "risk", "label": "Fragilité émotionnelle", "trait": "emotional_stability"})

        if gca is not None and gca >= 70:
            generated.append({"type": "strength", "label": "Forte capacité d'apprentissage", "trait": "gca"})

        return generated