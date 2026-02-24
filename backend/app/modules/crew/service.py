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
from datetime import date, datetime, timezone

from app.engine.recruitment.MLPSM.f_team import compute_baseline, compute_delta, FTeamResult
from app.engine.benchmarking.diagnosis import generate_combined_diagnosis
from app.engine.benchmarking.matrice import compute_sociogram
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

    # ── Sociogram ─────────────────────────────────────────────

    async def get_sociogram(
        self, db: AsyncSession, yacht_id: int, employer: EmployerProfile
    ) -> Optional[Dict]:
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            return None

        crew = await crew_repo.get_active_crew_with_profiles(db, yacht_id)
        pulse_data = await crew_repo.get_recent_pulse_data(db, yacht_id, days=7)
        weather = self._compute_weather_trend(pulse_data)

        crew_members = [
            {
                "crew_profile_id": str(m["crew_profile_id"]),
                "name": m["name"],
                "role": m["role"],
                "snapshot": m["snapshot"],
            }
            for m in crew
        ]

        sociogram = compute_sociogram(yacht_id, crew_members, weather)
        return _sociogram_to_out(sociogram, crew)

    async def simulate_candidate(
        self,
        db: AsyncSession,
        yacht_id: int,
        candidate_id: int,
        employer: EmployerProfile,
    ) -> Optional[Dict]:
        if not await vessel_repo.is_owner(db, yacht_id, employer.id):
            return None

        crew = await crew_repo.get_active_crew_with_profiles(db, yacht_id)
        crew_snapshots = [m["snapshot"] for m in crew]

        candidate = await crew_repo.get_crew_profile_with_snapshot(db, candidate_id)
        if not candidate:
            raise KeyError("Candidat introuvable.")

        cand_snapshot = candidate["snapshot"]

        # F_team before and after
        f_before = compute_baseline(crew_snapshots) if crew_snapshots else None
        f_after  = compute_delta(crew_snapshots, cand_snapshot)

        delta_f_team = f_after.delta.delta if f_after.delta else 0.0

        before_cohesion = 0.0
        if f_before:
            before_cohesion = (
                f_before.jerk_filter.min_agreeableness
                + f_before.emotional.mean_emotional_stability
            ) / 2.0
        after_cohesion = (
            f_after.jerk_filter.min_agreeableness
            + f_after.emotional.mean_emotional_stability
        ) / 2.0
        delta_cohesion = after_cohesion - before_cohesion

        # Candidate ↔ existing crew edges
        new_edges = [
            {
                "source_id": candidate_id,
                "target_id": m["crew_profile_id"],
                **_edge_details(cand_snapshot, m["snapshot"]),
            }
            for m in crew
        ]

        # Flags
        flags: List[str] = list(f_after.flags)
        if f_after.delta:
            if f_after.delta.net_impact == "NEGATIVE":
                flags.insert(0, f"TEAM_NEGATIVE_IMPACT: F_team {delta_f_team:+.1f}")
            elif f_after.delta.net_impact == "POSITIVE":
                flags.insert(0, f"TEAM_POSITIVE_IMPACT: F_team {delta_f_team:+.1f}")

        if delta_f_team >= 5.0:    recommendation = "STRONG_FIT"
        elif delta_f_team >= 0.0:  recommendation = "MODERATE_FIT"
        elif delta_f_team >= -5.0: recommendation = "WEAK_FIT"
        else:                      recommendation = "RISK"

        return {
            "candidate_id": candidate_id,
            "candidate_name": candidate["name"],
            "delta_f_team": round(delta_f_team, 2),
            "delta_cohesion": round(delta_cohesion, 2),
            "new_edges": new_edges,
            "impact_flags": flags,
            "recommendation": recommendation,
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


# ── Sociogram helpers ──────────────────────────────────────────────────────────

def _snap_get(snapshot: Dict, trait: str) -> Optional[float]:
    """Extract a psychometric trait from snapshot (handles both formats)."""
    if trait == "emotional_stability":
        val = snapshot.get("emotional_stability")
        if val is not None:
            return float(val)
        bf = snapshot.get("big_five") or {}
        n = bf.get("neuroticism")
        if n is None:
            return None
        n_score = n.get("score", n) if isinstance(n, dict) else n
        return 100.0 - float(n_score)
    if trait == "gca":
        return (snapshot.get("cognitive") or {}).get("gca_score")
    bf = snapshot.get("big_five") or {}
    val = bf.get(trait)
    if val is None:
        return None
    return float(val.get("score", val)) if isinstance(val, dict) else float(val)


def _compute_p_ind(snapshot: Dict) -> float:
    """Simplified P_ind proxy: 0.6 × GCA + 0.4 × conscientiousness."""
    gca = _snap_get(snapshot, "gca") or 50.0
    c   = _snap_get(snapshot, "conscientiousness") or 50.0
    return round(0.6 * gca + 0.4 * c, 1)


def _compute_completeness(snapshot: Dict) -> float:
    """Estimate psychometric completeness from snapshot keys."""
    if not snapshot:
        return 0.0
    if "completeness" in snapshot:
        return float(snapshot["completeness"])
    sections = ["big_five", "cognitive", "motivation"]
    present = sum(1 for s in sections if snapshot.get(s))
    return round(present / len(sections), 2)


def _edge_details(snap_a: Dict, snap_b: Dict) -> Dict:
    """Compute pairwise compatibility components for a sociogram edge."""
    def g(snap: Dict, trait: str) -> float:
        v = _snap_get(snap, trait)
        return v if v is not None else 50.0

    a_a, c_a, es_a = g(snap_a, "agreeableness"), g(snap_a, "conscientiousness"), g(snap_a, "emotional_stability")
    a_b, c_b, es_b = g(snap_b, "agreeableness"), g(snap_b, "conscientiousness"), g(snap_b, "emotional_stability")

    sim_a   = 1.0 - abs(a_a - a_b) / 100.0
    sim_c   = 1.0 - abs(c_a - c_b) / 100.0
    es_bond = (es_a / 100.0) * (es_b / 100.0)

    dyad = (0.40 * sim_a + 0.35 * sim_c + 0.25 * es_bond) * 100.0

    flags = []
    if sim_a < 0.5:    flags.append("agreeableness_mismatch")
    if sim_c < 0.5:    flags.append("conscientiousness_faultline")
    if es_bond < 0.2:  flags.append("low_es_bond")

    return {
        "dyad_score":                    round(max(0.0, min(100.0, dyad)), 1),
        "agreeableness_compatibility":   round(sim_a * 100.0, 1),
        "conscientiousness_compatibility": round(sim_c * 100.0, 1),
        "es_compatibility":              round(es_bond * 100.0, 1),
        "risk_flags":                    flags,
    }


def _sociogram_to_out(sociogram, crew_with_profiles: List[Dict]) -> Dict:
    """Convert engine SociogramData to the frontend SociogramOut format."""
    profile_map = {str(m["crew_profile_id"]): m for m in crew_with_profiles}

    nodes = []
    for node in sociogram.nodes:
        profile  = profile_map.get(node.id, {})
        snapshot = profile.get("snapshot") or {}
        nodes.append({
            "crew_profile_id":           int(node.id),
            "name":                      node.label,
            "avatar_url":                profile.get("avatar_url"),
            "position":                  node.role,
            "psychometric_completeness": _compute_completeness(snapshot),
            "p_ind":                     _compute_p_ind(snapshot),
        })

    snap_map = {str(m["crew_profile_id"]): m.get("snapshot") or {} for m in crew_with_profiles}
    edges = []
    for edge in sociogram.edges:
        edges.append({
            "source_id": int(edge.source),
            "target_id": int(edge.target),
            **_edge_details(snap_map.get(edge.source, {}), snap_map.get(edge.target, {})),
        })

    return {
        "nodes":          nodes,
        "edges":          edges,
        "f_team_global":  sociogram.team_state.f_team_score,
        "computed_at":    datetime.now(timezone.utc).isoformat(),
    }