# app/modules/calibration/service.py
"""
Orchestration du module calibration.

Logique métier uniquement — zéro SQL direct.
Toutes les opérations DB passent par CalibrationRepository.
"""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password, verify_password, create_access_token
from app.modules.calibration.repository import CalibrationRepository
from app.modules.calibration.schemas import (
    CalibratorRegisterIn,
    CalibratorLoginIn,
    CalibratorTokenOut,
    CalibratorDemographicsIn,
    CalibratorMeOut,
    CatalogueInfoOut,
    QuestionOut,
    StartSessionIn,
    SessionOut,
    SubmitResponsesIn,
    SubmitResponsesOut,
    TraitScoreOut,
    SessionScoreOut,
)

repo = CalibrationRepository()

# Labels lisibles pour chaque trait psychométrique.
# Utilisés dans SessionScoreOut pour faciliter l'affichage frontend.
TRAIT_LABELS: dict[str, str] = {
    # Big Five / IPIP
    "openness": "Ouverture",
    "conscientiousness": "Conscience",
    "extraversion": "Extraversion",
    "agreeableness": "Agréabilité",
    "neuroticism": "Neuroticisme",
    # GCA / Raven
    "fluid_intelligence": "Intelligence Fluide",
    "abstract_reasoning": "Raisonnement Abstrait",
    "spatial_reasoning": "Raisonnement Spatial",
    "numerical_reasoning": "Raisonnement Numérique",
    "verbal_reasoning": "Raisonnement Verbal",
    # Sécurité / Safety
    "safety_awareness": "Conscience Sécurité",
    "risk_tolerance": "Tolérance au Risque",
    # Leadership / LMX
    "leadership": "Leadership",
    "teamwork": "Travail en Équipe",
    "communication": "Communication",
    # Valeurs
    "integrity": "Intégrité",
    "adaptability": "Adaptabilité",
    "resilience": "Résilience",
}


def _build_token(calibrator_id: int, name: str) -> CalibratorTokenOut:
    """Génère un JWT pour un calibrateur."""
    access_token = create_access_token(
        {"sub": str(calibrator_id), "role": "calibrator"}
    )
    return CalibratorTokenOut(
        access_token=access_token,
        token_type="bearer",
        calibrator_id=calibrator_id,
        name=name,
    )


class CalibrationService:

    # ── Auth ──────────────────────────────────────────────────────────────────

    async def register(
        self, db: AsyncSession, data: CalibratorRegisterIn
    ) -> CalibratorTokenOut:
        """
        Enregistre un nouveau calibrateur.
        - 409 si email déjà utilisé.
        """
        existing = await repo.get_calibrator_by_email(db, data.email)
        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": True,
                    "message": "Un compte avec cet email existe déjà.",
                    "code": "EMAIL_ALREADY_EXISTS",
                },
            )

        calibrator = await repo.create_calibrator(
            db=db,
            email=data.email,
            name=data.name,
            hashed_password=hash_password(data.password),
            cohort=data.cohort,
        )
        return _build_token(calibrator.id, calibrator.name)

    async def get_me(
        self, db: AsyncSession, calibrator_id: int
    ) -> CalibratorMeOut:
        """Retourne le profil du calibrateur courant. 404 si introuvable."""
        calibrator = await repo.get_calibrator_by_id(db, calibrator_id)
        if not calibrator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Calibrateur introuvable.",
                    "code": "CALIBRATOR_NOT_FOUND",
                },
            )
        return CalibratorMeOut.model_validate(calibrator)

    async def update_demographics(
        self,
        db: AsyncSession,
        calibrator_id: int,
        data: CalibratorDemographicsIn,
    ) -> CalibratorMeOut:
        """Met à jour les données démographiques. 404 si calibrateur introuvable."""
        calibrator = await repo.get_calibrator_by_id(db, calibrator_id)
        if not calibrator:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Calibrateur introuvable.",
                    "code": "CALIBRATOR_NOT_FOUND",
                },
            )
        updated = await repo.update_demographics(db, calibrator, data)
        return CalibratorMeOut.model_validate(updated)

    async def login(
        self, db: AsyncSession, data: CalibratorLoginIn
    ) -> CalibratorTokenOut:
        """
        Authentifie un calibrateur.
        - 401 si email inconnu ou mot de passe incorrect.
        """
        calibrator = await repo.get_calibrator_by_email(db, data.email)
        if not calibrator or not verify_password(data.password, calibrator.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "error": True,
                    "message": "Email ou mot de passe incorrect.",
                    "code": "INVALID_CREDENTIALS",
                },
            )
        if not calibrator.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": True,
                    "message": "Compte désactivé.",
                    "code": "ACCOUNT_DISABLED",
                },
            )
        return _build_token(calibrator.id, calibrator.name)

    # ── Catalogues ────────────────────────────────────────────────────────────

    async def list_catalogues(self, db: AsyncSession) -> list[CatalogueInfoOut]:
        """Retourne tous les catalogues actifs."""
        catalogues = await repo.get_all_catalogues(db)
        return [CatalogueInfoOut.model_validate(c) for c in catalogues]

    async def get_questions(
        self, db: AsyncSession, catalogue_id: int
    ) -> list[QuestionOut]:
        """
        Retourne les questions ordonnées d'un catalogue.
        - 404 si catalogue inexistant ou inactif.
        """
        catalogue = await repo.get_catalogue_by_id(db, catalogue_id)
        if not catalogue or not catalogue.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Catalogue introuvable.",
                    "code": "CATALOGUE_NOT_FOUND",
                },
            )
        questions = await repo.get_questions_for_catalogue(db, catalogue_id)
        return [QuestionOut.model_validate(q) for q in questions]

    # ── Sessions ──────────────────────────────────────────────────────────────

    async def start_session(
        self,
        db: AsyncSession,
        calibrator_id: int,
        data: StartSessionIn,
    ) -> SessionOut:
        """
        Démarre une session de passation.
        - 404 si catalogue inexistant.
        - 409 si une session déjà complétée existe pour ce catalogue.
        """
        catalogue = await repo.get_catalogue_by_id(db, data.catalogue_id)
        if not catalogue or not catalogue.is_active:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Catalogue introuvable.",
                    "code": "CATALOGUE_NOT_FOUND",
                },
            )

        existing = await repo.get_session_for_calibrator(
            db, calibrator_id, data.catalogue_id
        )
        if existing and existing.completed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": True,
                    "message": "Ce catalogue a déjà été passé. Une seule passation par calibrateur.",
                    "code": "SESSION_ALREADY_COMPLETED",
                },
            )

        # Si une session existe mais n'est pas complétée → on la retourne (reprise)
        if existing:
            return SessionOut.model_validate(existing)

        session = await repo.create_session(
            db=db,
            calibrator_id=calibrator_id,
            catalogue_id=data.catalogue_id,
            device_info=data.device_info,
        )
        return SessionOut.model_validate(session)

    async def list_sessions(
        self, db: AsyncSession, calibrator_id: int
    ) -> list[SessionOut]:
        sessions = await repo.list_sessions_for_calibrator(db, calibrator_id)
        return [SessionOut.model_validate(s) for s in sessions]

    # ── Réponses ──────────────────────────────────────────────────────────────

    async def submit_responses(
        self,
        db: AsyncSession,
        calibrator_id: int,
        session_id: int,
        data: SubmitResponsesIn,
    ) -> SubmitResponsesOut:
        """
        Soumet des réponses pour une session en cours.
        - 404 si session introuvable.
        - 403 si la session n'appartient pas au calibrateur.
        - 409 si la session est déjà complétée.
        Auto-complète la session si toutes les réponses ont été soumises.
        """
        session = await repo.get_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Session introuvable.",
                    "code": "SESSION_NOT_FOUND",
                },
            )

        if session.calibrator_id != calibrator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": True,
                    "message": "Cette session ne vous appartient pas.",
                    "code": "SESSION_FORBIDDEN",
                },
            )

        if session.completed_at is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "error": True,
                    "message": "La session est déjà terminée.",
                    "code": "SESSION_ALREADY_COMPLETED",
                },
            )

        n_saved = await repo.save_responses(db, session_id, data.responses)

        # Auto-complétion : compare les réponses totales au nombre de questions
        catalogue = await repo.get_catalogue_by_id(db, session.catalogue_id)
        total_responses = await repo.count_responses_for_session(db, session_id)
        completed = False
        if catalogue and total_responses >= catalogue.n_questions:
            await repo.complete_session(db, session)
            completed = True

        return SubmitResponsesOut(
            session_id=session_id,
            n_responses=n_saved,
            completed=completed,
        )

    # ── Score CTT ─────────────────────────────────────────────────────────────

    async def get_session_score(
        self,
        db: AsyncSession,
        calibrator_id: int,
        session_id: int,
    ) -> SessionScoreOut:
        """
        Calcule le score CTT d'une session complétée.

        Règles :
        - 404 si session introuvable.
        - 403 si la session n'appartient pas au calibrateur.
        - 400 (SESSION_NOT_COMPLETED) si session.completed_at is None.

        Scoring :
        - Likert : grouper par trait, reverse si question.reverse
          (score = max_val - value), moyenne brute par trait, normaliser → 0-100.
        - QCM/raven : correct si response.value == index(correct_answer in options[].key).
        - overall_score = moyenne des trait scores normalisés.
        """
        session = await repo.get_session(db, session_id)
        if not session:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "error": True,
                    "message": "Session introuvable.",
                    "code": "SESSION_NOT_FOUND",
                },
            )

        if session.calibrator_id != calibrator_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={
                    "error": True,
                    "message": "Cette session ne vous appartient pas.",
                    "code": "SESSION_FORBIDDEN",
                },
            )

        if session.completed_at is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": True,
                    "message": "La session n'est pas encore terminée.",
                    "code": "SESSION_NOT_COMPLETED",
                },
            )

        catalogue = await repo.get_catalogue_by_id(db, session.catalogue_id)
        max_val: int = catalogue.max_score_per_question if catalogue else 5

        responses = await repo.get_responses_with_questions(db, session_id)

        # Grouper les réponses par trait
        trait_values: dict[str, list[float]] = {}
        for resp in responses:
            question = resp.question
            if question is None:
                continue

            trait = question.trait or "unknown"
            q_type = question.question_type or "likert"

            if q_type in ("qcm", "raven"):
                # Score binaire : 1 si bonne réponse, 0 sinon
                correct_key = question.correct_answer
                options = question.options or []
                correct_index: int | None = None
                for idx, opt in enumerate(options):
                    key = opt.get("key") if isinstance(opt, dict) else None
                    if key == correct_key:
                        correct_index = idx
                        break
                score = 1.0 if (correct_index is not None and resp.value == correct_index) else 0.0
            else:
                # Likert — reverse scoring si nécessaire
                raw = float(resp.value)
                if question.reverse:
                    raw = float(max_val) - raw
                score = raw

            if trait not in trait_values:
                trait_values[trait] = []
            trait_values[trait].append(score)

        trait_scores: list[TraitScoreOut] = []
        for trait, values in trait_values.items():
            if not values:
                continue
            raw_mean = sum(values) / len(values)
            # Normalisation 0-100 :
            # - Likert : max_val est le plafond (ex: 5 pour échelle 1-5, ou 7 pour 1-7)
            # - QCM/raven : max déjà 1.0 → multiplier par 100
            # On utilise max_val pour les deux (QCM retourne 0 ou 1, max_val=1 possible)
            # Pour QCM/raven le max théorique est 1.0
            q_type_first = None
            for resp in responses:
                if resp.question and resp.question.trait == trait:
                    q_type_first = resp.question.question_type
                    break
            if q_type_first in ("qcm", "raven"):
                normalized = round(raw_mean * 100.0, 2)
            else:
                normalized = round((raw_mean / max_val) * 100.0, 2) if max_val > 0 else 0.0
            normalized = max(0.0, min(100.0, normalized))

            label = TRAIT_LABELS.get(trait, trait.replace("_", " ").title())
            trait_scores.append(
                TraitScoreOut(
                    trait=trait,
                    label=label,
                    raw_mean=round(raw_mean, 4),
                    score=normalized,
                    n_items=len(values),
                )
            )

        overall = (
            round(sum(t.score for t in trait_scores) / len(trait_scores), 2)
            if trait_scores
            else 0.0
        )

        return SessionScoreOut(
            session_id=session_id,
            catalogue_id=session.catalogue_id,
            overall_score=overall,
            traits=trait_scores,
            n_responses=len(responses),
        )
