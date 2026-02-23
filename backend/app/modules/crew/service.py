# modules/crew/service.py
"""
Orchestration de la gestion d'équipage et du Daily Pulse.

Changements v2 :
- Les méthodes reçoivent crew (CrewProfile) au lieu de user_id
- Les checks ownership utilisent employer_profile_id
- Daily Pulse filtre via crew_profile_id

Unification moteur d'équipe (v2.1) :
- engine.team.harmony retiré — remplacé par f_team.compute_baseline()
- Source unique : engine.recruitment.f_team pour TOUT le calcul d'équipe
  (dashboard crew ET pipeline de matching)
- Mapping FTeamResult → HarmonyMetricsOut via _to_harmony_metrics()
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict
from datetime import date

from app.engine.recruitment.MLPSM.f_team import compute_baseline, compute_delta, FTeamResult
from app.engine.benchmarking.diagnosis import generate_combined_diagnosis
from app.modules.crew.repository import CrewRepository
from app.modules.vessel.repository import VesselRepository
from app.shared.models import CrewProfile, EmployerProfile

crew_repo   = CrewRepository()
vessel_repo = VesselRepository()


class CrewService:

    # ── Affectations ──────────────────────────────────────────

    async def get_active_assignment(
        self, db: AsyncSession, crew_profile_id: int
    ) -> Optional[Dict]:
        return await crew_repo.get_active_assignment(db, crew_profile_id)

    async def get_active_crew(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ) -> Optional[List]:
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            return None
        return await crew_repo.get_active_crew(db, yacht_id)

    async def assign_member(
        self,
        db: AsyncSession,
        yacht_id: int,
        payload,
        employer: EmployerProfile,
    ):
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            raise PermissionError("Accès refusé.")

        existing = await crew_repo.get_assignment(db, yacht_id, payload.crew_profile_id)
        if existing and existing.is_active:
            raise ValueError("Ce marin est déjà assigné à ce yacht.")

        assignment = await crew_repo.create_assignment(db, yacht_id, payload)
        await self._refresh_vessel_snapshot(db, yacht_id)
        return assignment

    async def remove_member(
        self,
        db: AsyncSession,
        yacht_id: int,
        crew_profile_id: int,
        employer: EmployerProfile,
    ) -> None:
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            raise PermissionError("Accès refusé.")

        success = await crew_repo.deactivate_assignment(db, yacht_id, crew_profile_id)
        if not success:
            raise KeyError("Membre introuvable ou déjà inactif.")

        await self._refresh_vessel_snapshot(db, yacht_id)

    # ── Dashboard ─────────────────────────────────────────────

    async def get_full_dashboard(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ) -> Optional[Dict]:
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            return None

        vessel_snapshot = await vessel_repo.get_vessel_snapshot(db, yacht_id)
        pulse_data      = await crew_repo.get_recent_pulse_data(db, yacht_id, days=7)

        # ── Métriques d'harmonie ──────────────────────────────
        # Source unique : f_team.compute_baseline()
        # Le vessel_snapshot est utilisé si disponible (évite recalcul),
        # sinon recalcul depuis les snapshots crew.
        if vessel_snapshot and vessel_snapshot.get("harmony_result"):
            harmony_metrics = vessel_snapshot["harmony_result"]
        else:
            crew_snapshots = await vessel_repo.get_crew_snapshots(db, yacht_id)
            if len(crew_snapshots) < 2:
                return self._empty_dashboard(yacht_id)

            f_team = compute_baseline(crew_snapshots)
            harmony_metrics = _to_harmony_metrics(f_team)

        weather        = self._compute_weather_trend(pulse_data)
        full_diagnosis = generate_combined_diagnosis(
            harmony_metrics=harmony_metrics,
            weather=weather,
        )

        return {
            "yacht_id":        yacht_id,
            "harmony_metrics": harmony_metrics,
            "weather_trend":   weather,
            "full_diagnosis":  full_diagnosis,
        }

    # ── Daily Pulse ───────────────────────────────────────────

    async def submit_daily_pulse(
        self, db: AsyncSession, crew: CrewProfile, payload
    ) -> Dict:
        assignment = await crew_repo.get_active_assignment(db, crew.id)
        if not assignment:
            raise ValueError("NO_ACTIVE_ASSIGNMENT")

        already_done = await crew_repo.has_pulse_today(db, crew.id, date.today())
        if already_done:
            raise ValueError("ALREADY_SUBMITTED_TODAY")

        return await crew_repo.create_pulse(
            db,
            crew_profile_id=crew.id,
            yacht_id=assignment.yacht_id,
            score=payload.score,
            comment=payload.comment,
        )

    async def get_pulse_history(
        self, db: AsyncSession, crew_profile_id: int
    ) -> List:
        return await crew_repo.get_pulse_history(db, crew_profile_id, limit=30)

    # ── Internals ─────────────────────────────────────────────

    async def _refresh_vessel_snapshot(
        self, db: AsyncSession, yacht_id: int
    ) -> None:
        """
        Recalcule le vessel_snapshot après un changement d'équipage.

        v2.1 : utilise f_team.compute_baseline() au lieu de harmony.compute().
        Le format du snapshot est identique — seule la source change.
        Appelé en synchrone après assign_member() / remove_member()
        pour que le dashboard reflète immédiatement le changement.
        """
        crew_snapshots = await vessel_repo.get_crew_snapshots(db, yacht_id)
        if len(crew_snapshots) < 2:
            return

        f_team = compute_baseline(crew_snapshots)

        await vessel_repo.update_vessel_snapshot(db, yacht_id, {
            "crew_count":    len(crew_snapshots),
            "team_scores": {
                "min_agreeableness":        f_team.jerk_filter.min_agreeableness,
                "sigma_conscientiousness":  f_team.faultline.sigma_conscientiousness,
                "mean_emotional_stability": f_team.emotional.mean_emotional_stability,
                "mean_gca":                 getattr(f_team, "mean_gca", 0),
            },
            # Format attendu par HarmonyMetricsOut et generate_combined_diagnosis()
            "harmony_result": _to_harmony_metrics(f_team),

            # Stockage du FTeamResult complet pour le pipeline MLPSM (Temps 2)
            # Évite de recalculer le baseline lors du matching
            "f_team_baseline_score":     f_team.score,
            "f_team_data_quality":       f_team.data_quality,
            "f_team_flags":              f_team.flags[:5],
        })

    def _compute_weather_trend(self, pulses: List) -> Dict:
        if not pulses:
            return {
                "average": 0, "status": "no_data",
                "response_count": 0, "std": 0.0, "days_observed": 0,
            }

        scores = [p.score for p in pulses]
        avg    = sum(scores) / len(scores)

        import numpy as np
        std = float(np.std(scores)) if len(scores) > 1 else 0.0

        if avg >= 4.5:   status = "excellent"
        elif avg >= 3.5: status = "stable"
        elif avg < 2.5:  status = "critical"
        else:            status = "turbulent"

        return {
            "average":        round(avg, 1),
            "std":            round(std, 2),
            "response_count": len(scores),
            "days_observed":  len(set(p.created_at.date() for p in pulses)),
            "status":         status,
        }

    def _empty_dashboard(self, yacht_id: int) -> Dict:
        return {
            "yacht_id": yacht_id,
            "harmony_metrics": {
                "performance": 0, "cohesion": 0,
                "risk_factors": {
                    "conscientiousness_divergence": 0,
                    "weakest_link_stability": 0,
                }
            },
            "weather_trend": {
                "average": 0, "status": "no_data",
                "response_count": 0, "std": 0.0, "days_observed": 0,
            },
            "full_diagnosis": {
                "crew_type": "N/A", "risk_level": "N/A",
                "volatility_index": 0, "hidden_conflict": 0,
                "short_term_prediction": "Équipage insuffisant (minimum 2 membres).",
                "recommended_action":   "Recruter ou activer un équipage.",
                "early_warning":        "N/A",
            },
        }


# ── Mapper FTeamResult → HarmonyMetricsOut ────────────────────────────────────

def _to_harmony_metrics(f_team: FTeamResult) -> Dict:
    """
    Mappe un FTeamResult sur le format HarmonyMetricsOut attendu par :
    - crew/service.py   (dashboard)
    - vessel/service.py (vessel_snapshot.harmony_result)
    - generate_combined_diagnosis() (engine.team.diagnosis)

    Mapping :
        performance ← f_team.score
            Le score global IS la performance de l'équipe.

        cohesion ← (min_agreeableness + mean_ES) / 2
            Proxy : la cohésion sociale est la moyenne du lien affectif
            (agréabilité minimale, modèle disjonctif) et du tampon
            émotionnel collectif. Pas de composante séparée dans FTeamResult,
            ce calcul est documenté ici pour la traçabilité.

        risk_factors.conscientiousness_divergence ← sigma_conscientiousness
            Directement disponible dans FaultlineRiskDetail.

        risk_factors.weakest_link_stability ← min_emotional_stability
            Le maillon le plus fragile émotionnellement — mesure de risque
            ponctuelle (différente de la moyenne qui sert au buffer).
    """
    min_a   = f_team.jerk_filter.min_agreeableness
    mean_es = f_team.emotional.mean_emotional_stability
    min_es  = f_team.emotional.min_emotional_stability
    sigma_c = f_team.faultline.sigma_conscientiousness

    cohesion = round((min_a + mean_es) / 2, 1)

    return {
        "performance": f_team.score,
        "cohesion":    cohesion,
        "risk_factors": {
            "conscientiousness_divergence": round(sigma_c, 1),
            "weakest_link_stability":       round(min_es, 1),
        }
    }