# modules/survey/service.py
"""
Gestion des Feedback Surveys — moteur d'apprentissage Temps 2.

Changements v2 :
- triggered_by_id → employer.id (EmployerProfile)
- respondent_id → crew.id (CrewProfile)
- target_crew_ids → crew_profile_ids
- get_active_event_for_crew utilise crew_profile_id
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import datetime, timezone

from app.modules.survey.repository import SurveyRepository
from app.modules.vessel.repository import VesselRepository
from app.modules.recruitment.repository import RecruitmentRepository
from app.shared.models import CrewProfile, EmployerProfile

survey_repo = SurveyRepository()
vessel_repo = VesselRepository()
recruitment_repo = RecruitmentRepository()

# Pondérations par type de trigger pour la mise à jour y_actual
TRIGGER_WEIGHTS = {
    "post_charter":   0.3,
    "monthly_pulse":  0.3,
    "post_season":    0.7,
    "conflict_event": 0.5,
    "exit_interview": 1.0,  # Définitif — écrase tout
}


class SurveyService:

    # ── Déclenchement (cap / owner) ───────────────────────────

    async def trigger_survey(
        self,
        db: AsyncSession,
        yacht_id: int,
        trigger_type: str,
        employer: EmployerProfile,          # v2
        target_crew_profile_ids: Optional[List[int]] = None,
    ) -> Dict:
        """
        Crée un survey et notifie les membres concernés.
        v2 : target_crew_profile_ids (était target_crew_ids avec user_ids)
        """
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            raise PermissionError("Accès refusé.")

        if target_crew_profile_ids is None:
            target_crew_profile_ids = await vessel_repo.get_active_crew_ids(db, yacht_id)

        survey = await survey_repo.create_survey(db, {
            "yacht_id":         yacht_id,
            "trigger_type":     trigger_type,
            "triggered_by_id":  employer.id,        # v2 : employer_profile_id
            "target_crew_ids":  target_crew_profile_ids,  # v2 : crew_profile_ids
            "is_open":          True,
        })

        return {
            "survey_id":      survey.id,
            "trigger_type":   trigger_type,
            "notified_count": len(target_crew_profile_ids),
        }

    async def get_yacht_survey_history(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ) -> List:
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            raise PermissionError("Accès refusé.")
        return await survey_repo.get_yacht_survey_history(db, yacht_id)

    # ── Réponse (marin) ───────────────────────────────────────

    async def get_pending_surveys(
        self, db: AsyncSession, crew: CrewProfile   # v2
    ) -> List:
        return await survey_repo.get_pending_for_crew(db, crew.id)

    async def submit_response(
        self,
        db: AsyncSession,
        survey_id: int,
        crew: CrewProfile,              # v2 : CrewProfile complet
        payload,
    ) -> Dict:
        """
        Pipeline :
        1. Validation (ciblage + doublon)
        2. Sauvegarde SurveyResponse avec crew_profile_id
        3. Update vessel_snapshot (scores observés)
        4. Update RecruitmentEvent.y_actual
        5. Check seuil régression ML
        """
        survey = await survey_repo.get_survey(db, survey_id)
        if not survey or not survey.is_open:
            raise ValueError("SURVEY_NOT_FOUND_OR_CLOSED")

        if crew.id not in (survey.target_crew_ids or []):
            raise PermissionError("Vous n'êtes pas ciblé par ce survey.")

        if await survey_repo.has_already_responded(db, survey_id, crew.id):
            raise ValueError("ALREADY_RESPONDED")

        normalized = self._normalize_response(payload)

        response = await survey_repo.create_response(db, {
            "survey_id":                    survey_id,
            "crew_profile_id":              crew.id,    # v2
            "yacht_id":                     survey.yacht_id,
            "trigger_type":                 survey.trigger_type,
            "team_cohesion_observed":       normalized["team_cohesion"],
            "workload_felt":                normalized["workload_satisfaction"],
            "leadership_fit_felt":          normalized["leadership_satisfaction"],
            "individual_performance_self":  normalized.get("individual_performance"),
            "intent_to_stay":               normalized["intent_to_stay"],
            "free_text":                    getattr(payload, "free_text", None),
        })

        await self._update_observed_scores(db, survey.yacht_id)
        await self._update_recruitment_event_y_actual(
            db,
            yacht_id=survey.yacht_id,
            crew_profile_id=crew.id,            # v2
            intent_to_stay=normalized["intent_to_stay"],
            trigger_type=survey.trigger_type,
        )
        await self._check_ml_threshold(db)

        return {"status": "submitted", "response_id": response.id}

    # ── Résultats agrégés (cap / owner) ──────────────────────

    async def get_survey_results(
        self, db: AsyncSession, survey_id: int, employer: EmployerProfile
    ) -> Optional[Dict]:
        survey = await survey_repo.get_survey(db, survey_id)
        if not survey:
            return None

        if not await vessel_repo.is_owner(db, survey.yacht_id, employer.id):
            raise PermissionError("Accès refusé.")

        responses = await survey_repo.get_responses_for_survey(db, survey_id)
        if not responses:
            return {
                "survey_id": survey_id,
                "response_count": 0,
                "aggregated": None,
            }

        return self._aggregate_results(survey, responses)

    # ── Internals ─────────────────────────────────────────────

    def _normalize_response(self, payload) -> Dict:
        """1-10 → 0-100. intent_to_stay est direct (pas inversé)."""
        def scale(val):
            return round(((float(val) - 1) / 9) * 100, 1) if val is not None else 50.0

        return {
            "team_cohesion":        scale(getattr(payload, "team_cohesion", None)),
            "workload_satisfaction": scale(getattr(payload, "workload_felt", None)),
            "leadership_satisfaction": scale(getattr(payload, "leadership_fit", None)),
            "individual_performance": scale(getattr(payload, "self_performance", None)),
            "intent_to_stay":       scale(getattr(payload, "intent_to_stay", None)),
        }

    async def _update_observed_scores(
        self, db: AsyncSession, yacht_id: int
    ) -> None:
        """
        Recalcule les scores observés dans vessel_snapshot.
        Ces scores permettent de comparer prédit vs observé sur les 4 facteurs.
        """
        recent = await survey_repo.get_recent_responses(db, yacht_id, limit=20)
        if not recent:
            return

        def avg(vals):
            filtered = [v for v in vals if v is not None]
            return round(sum(filtered) / len(filtered), 1) if filtered else None

        await vessel_repo.update_observed_scores(db, yacht_id, {
            "f_team_observed": avg([r.team_cohesion_observed for r in recent]),
            "f_env_observed":  avg([r.workload_felt for r in recent]),
            "f_lmx_observed":  avg([r.leadership_fit_felt for r in recent]),
            "intent_to_stay_avg": avg([r.intent_to_stay for r in recent]),
            "survey_count":    len(recent),
            "last_survey_update": datetime.now(timezone.utc).isoformat(),
        })

    async def _update_recruitment_event_y_actual(
        self,
        db: AsyncSession,
        yacht_id: int,
        crew_profile_id: int,       # v2
        intent_to_stay: float,
        trigger_type: str,
    ) -> None:
        """
        Met à jour y_actual dans le RecruitmentEvent.
        Pondération progressive selon le type de trigger.
        exit_interview est définitif (écrase le y_actual existant).
        """
        event = await recruitment_repo.get_active_event_for_crew(
            db, yacht_id, crew_profile_id
        )
        if not event:
            return

        weight = TRIGGER_WEIGHTS.get(trigger_type, 0.3)

        current_y = event.y_actual
        if current_y is None:
            new_y = intent_to_stay
        elif trigger_type == "exit_interview":
            new_y = intent_to_stay  # Signal définitif
        else:
            new_y = (current_y * (1 - weight)) + (intent_to_stay * weight)

        await recruitment_repo.update_y_actual(db, event.id, round(new_y, 1))

    async def _check_ml_threshold(self, db: AsyncSession) -> None:
        """
        Déclenche la régression quand n ≥ 150 events avec y_actual.
        Ensuite toutes les 50 nouvelles observations.
        """
        count = await recruitment_repo.count_events_with_y_actual(db)
        ML_THRESHOLD = 150

        if count >= ML_THRESHOLD and count % 50 == 0:
            print(f"[ML] Seuil atteint ({count} events) — régression schedulée.")
            # TODO Temps 2 : Celery → engine/fleet/regression.py
            # run_beta_regression.delay()

    def _aggregate_results(self, survey, responses: List) -> Dict:
        """Agrège anonymement les réponses pour le cap/owner."""
        import numpy as np

        def agg(vals):
            arr = [v for v in vals if v is not None]
            return {
                "mean": round(float(np.mean(arr)), 1) if arr else None,
                "std":  round(float(np.std(arr)), 1) if len(arr) > 1 else None,
                "n":    len(arr),
            }

        return {
            "survey_id":     survey.id,
            "trigger_type":  survey.trigger_type,
            "response_count": len(responses),
            "response_rate": round(
                len(responses) / max(len(survey.target_crew_ids or [1]), 1), 2
            ),
            "aggregated": {
                "team_cohesion":        agg([r.team_cohesion_observed for r in responses]),
                "workload_felt":        agg([r.workload_felt for r in responses]),
                "leadership_fit_felt":  agg([r.leadership_fit_felt for r in responses]),
                "intent_to_stay":       agg([r.intent_to_stay for r in responses]),
            },
            # Pas de réponses individuelles (anonymat garanti)
        }