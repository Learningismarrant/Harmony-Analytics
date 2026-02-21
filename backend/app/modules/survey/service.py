# modules/survey/service.py
"""
Gestion des Feedback Surveys — le moteur d'apprentissage du Temps 2.

Les surveys transforment les opinions qualitatives en données quantitatives
qui alimentent la régression multiple et valident les prédictions de l'algo.

Types de triggers :
- post_charter    : déclenché par cap/owner après chaque charter
- post_season     : fin de saison — signal le plus riche
- monthly_pulse   : pulse enrichi mensuel (différent du daily pulse 1-5)
- conflict_event  : déclenché manuellement après un incident
- exit_interview  : départ d'un marin — Y_actual définitif

Flux de données :
Survey → SurveyResponse → mise à jour vessel_snapshot
                        → mise à jour recruitment_event.y_actual
                        → si n > 150 events : trigger régression
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import datetime

from modules.survey.repository import SurveyRepository
from modules.vessel.repository import VesselRepository
from modules.recruitment.repository import RecruitmentRepository

survey_repo = SurveyRepository()
vessel_repo = VesselRepository()
recruitment_repo = RecruitmentRepository()


class SurveyService:

    # ─────────────────────────────────────────────
    # DÉCLENCHEMENT (cap / owner)
    # ─────────────────────────────────────────────

    def trigger_survey(
        self,
        db: Session,
        yacht_id: int,
        trigger_type: str,
        triggered_by_id: int,
        target_crew_ids: Optional[List[int]] = None,
    ) -> Dict:
        """
        Crée un survey et notifie les membres d'équipage concernés.

        Args:
            target_crew_ids: Si None → tous les membres actifs du yacht
        """
        if not vessel_repo.is_owner(db, yacht_id, triggered_by_id):
            raise PermissionError("Accès refusé.")

        # Cible : tous les actifs si non spécifié
        if target_crew_ids is None:
            active = vessel_repo.get_active_crew_ids(db, yacht_id)
            target_crew_ids = active

        survey = survey_repo.create_survey(db, {
            "yacht_id": yacht_id,
            "trigger_type": trigger_type,
            "triggered_by_id": triggered_by_id,
            "target_crew_ids": target_crew_ids,
            "created_at": datetime.utcnow(),
            "is_open": True,
        })

        # Notification (infra/notifications.py — non bloquant)
        # notification_service.notify_crew(target_crew_ids, survey.id)

        return {
            "survey_id": survey.id,
            "trigger_type": trigger_type,
            "notified_count": len(target_crew_ids),
        }

    def get_pending_surveys(self, db: Session, user_id: int) -> List:
        """Surveys en attente de réponse pour un marin."""
        return survey_repo.get_pending_for_user(db, user_id)

    # ─────────────────────────────────────────────
    # SOUMISSION DE RÉPONSE (marin)
    # ─────────────────────────────────────────────

    def submit_response(
        self,
        db: Session,
        survey_id: int,
        respondent_id: int,
        payload,
    ) -> Dict:
        """
        Traite la réponse d'un marin à un survey.

        Pipeline :
        1. Validation (survey existe, marin est ciblé, pas déjà répondu)
        2. Sauvegarde SurveyResponse
        3. Mise à jour vessel_snapshot (dimensions observées)
        4. Mise à jour RecruitmentEvent.y_actual (proxy Y_actual)
        5. Check si seuil régression atteint
        """
        survey = survey_repo.get_survey(db, survey_id)
        if not survey or not survey.is_open:
            raise ValueError("SURVEY_NOT_FOUND_OR_CLOSED")

        if respondent_id not in survey.target_crew_ids:
            raise PermissionError("Vous n'êtes pas ciblé par ce survey.")

        if survey_repo.has_already_responded(db, survey_id, respondent_id):
            raise ValueError("ALREADY_RESPONDED")

        # Normalisation des réponses (1-10 → 0-100)
        normalized = self._normalize_response(payload)

        response = survey_repo.create_response(db, {
            "survey_id": survey_id,
            "respondent_id": respondent_id,
            "yacht_id": survey.yacht_id,
            "trigger_type": survey.trigger_type,

            # Dimensions observées (valident les prédictions de l'algo)
            "team_cohesion_observed": normalized["team_cohesion"],
            "workload_felt": normalized["workload_satisfaction"],
            "leadership_fit_felt": normalized["leadership_satisfaction"],
            "individual_performance_self": normalized.get("individual_performance"),

            # La variable dépendante principale
            "intent_to_stay": normalized["intent_to_stay"],

            "free_text": payload.free_text if hasattr(payload, "free_text") else None,
            "submitted_at": datetime.utcnow(),
        })

        # Mise à jour des données observées dans vessel_snapshot
        self._update_observed_scores(db, survey.yacht_id)

        # Mise à jour Y_actual dans le RecruitmentEvent correspondant
        self._update_recruitment_event_y_actual(
            db,
            yacht_id=survey.yacht_id,
            respondent_id=respondent_id,
            intent_to_stay=normalized["intent_to_stay"],
            trigger_type=survey.trigger_type,
        )

        # Check seuil ML (si n > 150 → trigger régression en background)
        self._check_ml_threshold(db)

        return {"status": "submitted", "response_id": response.id}

    def get_survey_results(
        self, db: Session, survey_id: int, requester_id: int
    ) -> Optional[Dict]:
        """
        Résultats agrégés d'un survey (cap/owner uniquement).
        Les réponses individuelles sont anonymisées vis-à-vis des autres membres.
        """
        survey = survey_repo.get_survey(db, survey_id)
        if not survey:
            return None

        if not vessel_repo.is_owner(db, survey.yacht_id, requester_id):
            raise PermissionError("Accès refusé.")

        responses = survey_repo.get_responses_for_survey(db, survey_id)
        if not responses:
            return {"survey_id": survey_id, "response_count": 0, "aggregated": None}

        return self._aggregate_results(survey, responses)

    # ─────────────────────────────────────────────
    # INTERNALS
    # ─────────────────────────────────────────────

    def _normalize_response(self, payload) -> Dict:
        """
        Normalise les réponses du survey de l'échelle 1-10 vers 0-100.
        intent_to_stay est inversé : 1=partir → Y_actual=0, 10=rester → Y_actual=100
        """
        def scale(val, min_=1, max_=10):
            return round(((val - min_) / (max_ - min_)) * 100, 1) if val else 50.0

        return {
            "team_cohesion": scale(payload.team_cohesion),
            "workload_satisfaction": scale(payload.workload_satisfaction),
            "leadership_satisfaction": scale(payload.leadership_satisfaction),
            "individual_performance": scale(payload.individual_performance) if hasattr(payload, "individual_performance") else None,
            "intent_to_stay": scale(payload.intent_to_stay),
        }

    def _update_observed_scores(self, db: Session, yacht_id: int) -> None:
        """
        Recalcule les scores observés dans vessel_snapshot
        depuis les réponses récentes.

        Ces scores permettent de comparer prédit vs observé sur F_team, F_env, F_lmx.
        """
        recent_responses = survey_repo.get_recent_responses(db, yacht_id, limit=20)
        if not recent_responses:
            return

        avg_cohesion = sum(r.team_cohesion_observed for r in recent_responses) / len(recent_responses)
        avg_workload = sum(r.workload_felt for r in recent_responses) / len(recent_responses)
        avg_leadership = sum(r.leadership_fit_felt for r in recent_responses) / len(recent_responses)
        avg_intent = sum(r.intent_to_stay for r in recent_responses) / len(recent_responses)

        # Mise à jour du vessel_snapshot avec les valeurs observées
        vessel_repo.update_observed_scores(db, yacht_id, {
            "f_team_observed": round(avg_cohesion, 1),
            "f_env_observed": round(avg_workload, 1),
            "f_lmx_observed": round(avg_leadership, 1),
            "intent_to_stay_avg": round(avg_intent, 1),
            "survey_count": len(recent_responses),
            "last_survey_update": datetime.utcnow().isoformat(),
        })

    def _update_recruitment_event_y_actual(
        self,
        db: Session,
        yacht_id: int,
        respondent_id: int,
        intent_to_stay: float,
        trigger_type: str,
    ) -> None:
        """
        Met à jour y_actual dans le RecruitmentEvent du marin.

        intent_to_stay est un proxy continu de Y_actual :
        - post_charter  : signal partiel, pondération 0.3
        - post_season   : signal fort, pondération 0.7
        - exit_interview: signal définitif, pondération 1.0 (écrase tout)
        """
        event = recruitment_repo.get_active_event_for_crew(db, yacht_id, respondent_id)
        if not event:
            return

        WEIGHTS = {
            "post_charter": 0.3,
            "monthly_pulse": 0.3,
            "post_season": 0.7,
            "conflict_event": 0.5,
            "exit_interview": 1.0,
        }
        weight = WEIGHTS.get(trigger_type, 0.3)

        # Moyenne pondérée avec le y_actual existant
        current_y = event.y_actual
        if current_y is None:
            new_y = intent_to_stay
        elif trigger_type == "exit_interview":
            new_y = intent_to_stay  # Écrase — signal définitif
        else:
            new_y = (current_y * (1 - weight)) + (intent_to_stay * weight)

        recruitment_repo.update_y_actual(db, event.id, round(new_y, 1))

    def _check_ml_threshold(self, db: Session) -> None:
        """
        Vérifie si le seuil de données est atteint pour déclencher
        la régression multiple en background.

        Seuil : 150 RecruitmentEvents avec y_actual non null.
        """
        count = recruitment_repo.count_events_with_y_actual(db)
        ML_THRESHOLD = 150

        if count >= ML_THRESHOLD and count % 50 == 0:
            # Déclenche la régression tous les 50 nouveaux événements après le seuil
            print(f"[ML] Seuil atteint ({count} events) — régression schedulée.")
            # TODO: Celery task → engine/fleet/regression.py
            # run_beta_regression_task.delay()

    def _aggregate_results(self, survey, responses: List) -> Dict:
        """Agrège les réponses pour le cap/owner."""
        import numpy as np

        def agg(vals):
            arr = [v for v in vals if v is not None]
            return {
                "mean": round(float(np.mean(arr)), 1) if arr else None,
                "std": round(float(np.std(arr)), 1) if len(arr) > 1 else None,
            }

        return {
            "survey_id": survey.id,
            "trigger_type": survey.trigger_type,
            "response_count": len(responses),
            "response_rate": round(len(responses) / max(len(survey.target_crew_ids), 1), 2),
            "aggregated": {
                "team_cohesion": agg([r.team_cohesion_observed for r in responses]),
                "workload_satisfaction": agg([r.workload_felt for r in responses]),
                "leadership_satisfaction": agg([r.leadership_fit_felt for r in responses]),
                "intent_to_stay": agg([r.intent_to_stay for r in responses]),
            },
            # Les réponses individuelles ne sont PAS retournées ici (anonymat)
            # Un endpoint admin séparé peut y accéder si nécessaire
        }