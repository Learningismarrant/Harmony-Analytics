# modules/vessel/service.py
"""
Orchestration des yachts — CRUD + snapshots + paramètres JD-R.

Changements v2 :
- Toutes les méthodes reçoivent employer (EmployerProfile)
- employer_profile_id partout (était client_id / owner_id)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List, Dict

from app.engine.recruitment.MLPSM.f_team import compute_baseline
from app.modules.vessel.repository import VesselRepository
from app.shared.models import EmployerProfile

repo = VesselRepository()


class VesselService:

    # ── CRUD yachts ───────────────────────────────────────────

    async def create(
        self, db: AsyncSession, payload, employer: EmployerProfile
    ):
        return await repo.create(db, payload, employer_profile_id=employer.id)

    async def get_all_for_employer(
        self, db: AsyncSession, employer: EmployerProfile
    ) -> List:
        return await repo.get_yachts_by_employer(db, employer.id)

    async def get_secure(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ):
        return await repo.get_secure(db, yacht_id, employer.id)

    async def update(
        self, db: AsyncSession, yacht_id: int, payload, employer: EmployerProfile
    ):
        yacht = await repo.get_secure(db, yacht_id, employer.id)
        if not yacht:
            raise PermissionError("Yacht introuvable ou accès refusé.")
        return await repo.update(db, yacht, payload)

    async def delete(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ) -> None:
        yacht = await repo.get_secure(db, yacht_id, employer.id)
        if not yacht:
            raise PermissionError("Yacht introuvable ou accès refusé.")
        await repo.delete(db, yacht)

    # ── Paramètres JD-R (F_env) + vecteur capitaine (F_lmx) ──

    async def update_environment(
        self, db: AsyncSession, yacht_id: int, payload, employer: EmployerProfile
    ):
        """
        Met à jour les paramètres JD-R et le vecteur capitaine.
        Déclenche le recalcul du vessel_snapshot.
        """
        if not await repo.is_owner(db, yacht_id, employer.id):
            raise PermissionError("Accès refusé.")

        yacht = await repo.update_environment_params(
            db, yacht_id, payload.model_dump(exclude_unset=True)
        )

        # Recalcul vessel_snapshot après changement d'environnement
        await self._refresh_vessel_snapshot_from_harmony(db, yacht_id)

        return yacht

    # ── Token d'embarquement ──────────────────────────────────

    async def refresh_boarding_token(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ) -> Dict:
        yacht = await repo.get_secure(db, yacht_id, employer.id)
        if not yacht:
            raise PermissionError("Accès refusé.")
        new_token = await repo.rotate_boarding_token(db, yacht)
        return {"yacht_id": yacht_id, "boarding_token": new_token}

    # ── Snapshots (appelés par d'autres services) ─────────────

    async def update_vessel_snapshot(
        self, db: AsyncSession, yacht_id: int, harmony
    ) -> None:
        """
        Appelé en background par assessment/service.py après un test.
        Reçoit un HarmonyResult (engine/team/harmony.py).
        """
        await repo.update_vessel_snapshot(db, yacht_id, {
            "crew_count": getattr(harmony, "crew_count", 0),
            "team_scores": {
                "min_agreeableness":        harmony.min_agreeableness,
                "sigma_conscientiousness":  harmony.sigma_conscientiousness,
                "mean_emotional_stability": harmony.mean_emotional_stability,
                "mean_gca":                 getattr(harmony, "mean_gca", 0),
            },
            "harmony_result": {
                "performance": harmony.performance,
                "cohesion":    harmony.cohesion,
                "risk_factors": {
                    "conscientiousness_divergence": harmony.sigma_conscientiousness,
                    "weakest_link_stability":       harmony.mean_emotional_stability,
                }
            }
        })

    async def refresh_fleet_snapshot_if_stale(
        self, db: AsyncSession, employer_profile_id: int
    ) -> None:
        """
        Recalcule le fleet_snapshot si au moins un vessel_snapshot est périmé.
        Appelé en background depuis assessment/service.py.
        v2 : employer_profile_id (était office_id).
        """
        snapshots = await repo.get_all_vessel_snapshots_for_employer(db, employer_profile_id)
        if len(snapshots) < 2:
            return
        # TODO Temps 2 : clustering + ANOVA inter-yachts
        # fleet_engine.compute_fleet_snapshot(snapshots)

    async def _refresh_vessel_snapshot_from_harmony(
        self, db: AsyncSession, yacht_id: int
    ) -> None:
        """Recalcule l'harmonie depuis les snapshots crew actuels."""
        crew_snapshots = await repo.get_crew_snapshots(db, yacht_id)
        if len(crew_snapshots) < 2:
            return
        harmony = compute_baseline(crew_snapshots)
        await self.update_vessel_snapshot(db, yacht_id, harmony)