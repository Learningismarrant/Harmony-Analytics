# modules/crew/service.py
"""
Orchestration de la gestion d'équipage et du Daily Pulse.

Responsabilités :
- Assignation / retrait d'un marin (avec propagation snapshot)
- Dashboard yacht (harmony + pulse combinés)
- Daily Pulse
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict
from datetime import date

from engine.team.harmony import compute as compute_harmony
from engine.team.diagnosis import generate_matrix_diagnosis, generate_combined_diagnosis
from modules.crew.repository import CrewRepository
from modules.vessel.repository import VesselRepository

crew_repo = CrewRepository()
vessel_repo = VesselRepository()


class CrewService:

    # ─────────────────────────────────────────────
    # AFFECTATIONS
    # ─────────────────────────────────────────────

    def get_active_assignment(self, db: Session, user_id: int) -> Optional[Dict]:
        return crew_repo.get_active_assignment(db, user_id)

    def get_active_crew(
        self, db: Session, yacht_id: int, requester_id: int
    ) -> Optional[List]:
        if not vessel_repo.is_owner(db, yacht_id, requester_id):
            return None
        return crew_repo.get_active_crew(db, yacht_id)

    def assign_member(
        self, db: Session, yacht_id: int, payload, requester_id: int
    ):
        if not vessel_repo.is_owner(db, yacht_id, requester_id):
            raise PermissionError("Accès refusé.")

        # Vérification : le marin n'est pas déjà actif sur ce yacht
        existing = crew_repo.get_assignment(db, yacht_id, payload.user_id)
        if existing and existing.is_active:
            raise ValueError("Ce marin est déjà assigné à ce yacht.")

        assignment = crew_repo.create_assignment(db, yacht_id, payload)

        # Recalcul vessel_snapshot (synchrone — l'équipe change maintenant)
        self._refresh_vessel_snapshot(db, yacht_id)

        return assignment

    def remove_member(
        self, db: Session, yacht_id: int, user_id: int, requester_id: int
    ) -> None:
        if not vessel_repo.is_owner(db, yacht_id, requester_id):
            raise PermissionError("Accès refusé.")

        success = crew_repo.deactivate_assignment(db, yacht_id, user_id)
        if not success:
            raise KeyError("Membre introuvable ou déjà inactif.")

        # Recalcul vessel_snapshot
        self._refresh_vessel_snapshot(db, yacht_id)

    # ─────────────────────────────────────────────
    # DASHBOARD
    # ─────────────────────────────────────────────

    def get_full_dashboard(
        self, db: Session, yacht_id: int, requester_id: int
    ) -> Optional[Dict]:
        if not vessel_repo.is_owner(db, yacht_id, requester_id):
            return None

        # Données depuis vessel_snapshot (cache) + pulse récent
        vessel_snapshot = vessel_repo.get_vessel_snapshot(db, yacht_id)
        pulse_data = crew_repo.get_recent_pulse_data(db, yacht_id, days=7)

        if not vessel_snapshot or not vessel_snapshot.get("harmony_result"):
            # Snapshot absent ou trop vieux — recalcul en direct
            crew_snapshots = vessel_repo.get_crew_snapshots(db, yacht_id)
            if len(crew_snapshots) < 2:
                return self._empty_dashboard(yacht_id)
            harmony = compute_harmony(crew_snapshots)
            vessel_snapshot = {
                "harmony_result": {
                    "performance": harmony.performance,
                    "cohesion": harmony.cohesion,
                    "risk_factors": {
                        "conscientiousness_divergence": harmony.sigma_conscientiousness,
                        "weakest_link_stability": harmony.mean_emotional_stability,
                    }
                }
            }

        harmony_metrics = vessel_snapshot["harmony_result"]
        weather = self._compute_weather_trend(pulse_data)

        # Diagnostic combiné (engine pur)
        full_diagnosis = generate_combined_diagnosis(
            harmony_metrics=harmony_metrics,
            weather=weather,
        )

        return {
            "harmony_analysis": {
                "yacht_id": yacht_id,
                "metrics": harmony_metrics,
                "diagnosis": generate_matrix_diagnosis(
                    perf=harmony_metrics["performance"],
                    cohesion=harmony_metrics["cohesion"],
                ),
            },
            "weather_trend": weather,
            "full_diagnosis": full_diagnosis,
        }

    # ─────────────────────────────────────────────
    # DAILY PULSE
    # ─────────────────────────────────────────────

    def submit_daily_pulse(self, db: Session, user, payload) -> Dict:
        assignment = crew_repo.get_active_assignment(db, user.id)
        if not assignment:
            raise ValueError("NO_ACTIVE_ASSIGNMENT")

        already_done = crew_repo.has_pulse_today(db, user.id, date.today())
        if already_done:
            raise ValueError("ALREADY_SUBMITTED_TODAY")

        return crew_repo.create_pulse(
            db,
            user_id=user.id,
            yacht_id=assignment.yacht_id,
            score=payload.score,
            comment=payload.comment,
        )

    def get_pulse_history(self, db: Session, user_id: int) -> List:
        return crew_repo.get_pulse_history(db, user_id, limit=30)

    # ─────────────────────────────────────────────
    # INTERNALS
    # ─────────────────────────────────────────────

    def _refresh_vessel_snapshot(self, db: Session, yacht_id: int) -> None:
        """Recalcule le vessel_snapshot après un changement d'équipe."""
        crew_snapshots = vessel_repo.get_crew_snapshots(db, yacht_id)
        if len(crew_snapshots) < 2:
            return

        harmony = compute_harmony(crew_snapshots)
        vessel_repo.update_vessel_snapshot(db, yacht_id, {
            "crew_count": len(crew_snapshots),
            "team_scores": {
                "min_agreeableness": harmony.min_agreeableness,
                "sigma_conscientiousness": harmony.sigma_conscientiousness,
                "mean_emotional_stability": harmony.mean_emotional_stability,
                "mean_gca": harmony.mean_gca,
            },
            "harmony_result": {
                "performance": harmony.performance,
                "cohesion": harmony.cohesion,
                "risk_factors": {
                    "conscientiousness_divergence": harmony.sigma_conscientiousness,
                    "weakest_link_stability": harmony.mean_emotional_stability,
                }
            }
        })

    def _compute_weather_trend(self, pulses: List) -> Dict:
        if not pulses:
            return {"average": 0, "status": "no_data", "response_count": 0, "std": 0.0}

        scores = [p.score for p in pulses]
        avg = sum(scores) / len(scores)

        import numpy as np
        std = float(np.std(scores)) if len(scores) > 1 else 0.0

        status = "stable"
        if avg >= 4.5:   status = "excellent"
        elif avg >= 3.5: status = "good"
        elif avg < 2.5:  status = "warning"

        return {
            "average": round(avg, 1),
            "std": round(std, 2),
            "response_count": len(scores),
            "days_observed": len(set(p.created_at.date() for p in pulses)),
            "status": status,
        }

    def _empty_dashboard(self, yacht_id: int) -> Dict:
        return {
            "harmony_analysis": {
                "yacht_id": yacht_id,
                "metrics": {
                    "performance": 0, "cohesion": 0,
                    "risk_factors": {"conscientiousness_divergence": 0, "weakest_link_stability": 0}
                },
                "diagnosis": "Équipage insuffisant pour analyse (minimum 2 membres requis).",
            },
            "weather_trend": {"average": 0, "status": "no_data", "response_count": 0},
            "full_diagnosis": {
                "crew_type": "N/A", "risk_level": "N/A",
                "volatility_index": 0, "hidden_conflict": 0,
                "short_term_prediction": "Analyse impossible : équipage insuffisant.",
                "recommended_action": "Recruter ou activer un équipage.",
                "early_warning": "N/A",
            },
        }