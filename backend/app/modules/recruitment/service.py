# modules/recruitment/service.py
"""
Service de recrutement — utilise le pipeline DNRE → MLPSM à deux étages.

Flux matching :
    1. pipeline.run_batch()       → PipelineResult[] (DNRE + MLPSM)
    2. Fusion avec statuts DB     (is_hired, is_rejected, status)
    3. Tri configurable           (par G_fit, par Ŷ_success, ou les deux)
    4. Stockage RecruitmentEvent  (to_event_snapshot() compact)
"""
from sqlalchemy.ext.asyncio import AsyncSession
from typing import List, Optional, Dict

from app.engine.recruitment import pipeline
from app.engine.recruitment.pipeline import PipelineResult
from app.modules.recruitment.repository import RecruitmentRepository
from app.modules.vessel.repository import VesselRepository
from app.shared.models import CrewProfile, EmployerProfile

repo         = RecruitmentRepository()
vessel_repo  = VesselRepository()


class RecruitmentService:

    # ── Campagnes ─────────────────────────────────────────────────────────────

    async def create_campaign(self, db: AsyncSession, payload, employer: EmployerProfile):
        return await repo.create_campaign(db, payload, employer.id)

    async def get_my_campaigns(self, db: AsyncSession, employer: EmployerProfile,
                                status=None, is_archived: bool = False) -> List:
        return await repo.get_campaigns_for_employer(db, employer.id, status, is_archived)

    async def get_campaign_secure(self, db: AsyncSession, campaign_id: int, employer: EmployerProfile):
        return await repo.get_campaign_secure(db, campaign_id, employer.id)

    async def update_campaign(self, db: AsyncSession, campaign_id: int, payload, employer: EmployerProfile):
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Campagne introuvable ou accès refusé.")
        return await repo.update_campaign(db, campaign, payload)

    async def archive_campaign(self, db: AsyncSession, campaign_id: int, employer: EmployerProfile):
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        await repo.reject_pending_candidates(db, campaign_id, reason="Campagne archivée")
        await repo.archive_campaign(db, campaign)

    # ── Candidatures (vue candidat) ───────────────────────────────────────────

    async def apply_to_campaign(self, db: AsyncSession, invite_token: str, crew: CrewProfile) -> Dict:
        campaign = await repo.get_by_invite_token(db, invite_token)
        if not campaign or campaign.status.value != "open":
            raise ValueError("CAMPAIGN_NOT_FOUND_OR_CLOSED")
        existing = await repo.get_application(db, campaign.id, crew.id)
        if existing:
            raise ValueError("ALREADY_APPLIED")
        link = await repo.create_application(db, campaign.id, crew.id)
        return {"message": "Candidature enregistrée.", "campaign_id": campaign.id, "application_id": link.id}

    async def get_my_applications(self, db: AsyncSession, crew: CrewProfile) -> List:
        return await repo.get_applications_for_crew(db, crew.id)

    # ── Matching (pipeline DNRE → MLPSM) ─────────────────────────────────────

    async def get_matching(
        self,
        db: AsyncSession,
        campaign_id: int,
        employer: EmployerProfile,
        sort_by: str = "g_fit",   # "g_fit" | "y_success" | "dnre_then_mlpsm"
    ) -> List[Dict]:
        """
        Exécute le pipeline complet sur tous les candidats de la campagne.

        Étage 1 (DNRE batch) :
            G_fit + centile + safety pour tous les candidats.
            Les DISQUALIFIED sont inclus dans la réponse (visible par l'employeur)
            mais identifiés via is_pipeline_pass=False.

        Étage 2 (MLPSM individuel) :
            Ŷ_success + team delta pour les candidats non-DISQUALIFIED.

        sort_by :
            "g_fit"          → tri DNRE uniquement (profil/poste)
            "y_success"      → tri MLPSM uniquement (intégration équipe)
            "dnre_then_mlpsm" → tri primaire G_fit, secondaire Ŷ_success
                                (recommandé — DNRE filtre d'abord)
        """
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Campagne introuvable ou accès refusé.")

        candidates_data = await repo.get_candidates_with_snapshots(db, campaign_id)
        if not candidates_data:
            return []

        # ── Hydratation contexte yacht ────────────────────────────────────────
        vessel_params  = {}
        captain_vector = {}
        crew_snapshots = []

        if campaign.yacht_id:
            vs = await vessel_repo.get_vessel_snapshot(db, campaign.yacht_id)
            if vs:
                vessel_params = vs.get("jdr_params", {})
            captain_vector = await vessel_repo.get_captain_vector(db, campaign.yacht_id) or {}
            crew_snapshots = await vessel_repo.get_crew_snapshots(db, campaign.yacht_id)

        betas          = await repo.get_active_model_betas(db)
        status_map     = await repo.get_applications_status_map(db, campaign_id)
        weight_config  = await repo.get_active_job_weight_config(db)

        # Format attendu par pipeline.run_batch()
        candidates_for_engine = [
            {
                "snapshot":         c["snapshot"] or {},
                "crew_profile_id":  c["crew_profile_id"],
                "experience_years": c.get("experience_years", 0),
                "position_key":     str(c.get("position_targeted", "")),
            }
            for c in candidates_data
        ]

        # ── Pipeline DNRE → MLPSM ─────────────────────────────────────────────
        results: List[PipelineResult] = pipeline.run_batch(
            candidates=candidates_for_engine,
            current_crew_snapshots=crew_snapshots,
            vessel_params=vessel_params,
            captain_vector=captain_vector,
            betas=betas,
            sme_weights_override=weight_config.get("sme_weights") if weight_config else None,
            p_ind_omegas=weight_config.get("p_ind_omegas") if weight_config else None,
        )

        # ── Fusion avec statuts candidature ───────────────────────────────────
        matching = []
        cand_by_id = {str(c["crew_profile_id"]): c for c in candidates_data}

        for result in results:
            cid  = result.crew_profile_id
            cand = cand_by_id.get(cid, {})
            app  = status_map.get(cid, {})

            row = result.to_matching_row()
            row.update({
                "name":          cand.get("name"),
                "avatar_url":    cand.get("avatar_url"),
                "location":      cand.get("location"),
                "experience_years": cand.get("experience_years", 0),
                "test_status":   "completed" if cand.get("snapshot") else "pending",
                # Statuts candidature
                "is_hired":            app.get("is_hired", False),
                "is_rejected":         app.get("is_rejected", False),
                "application_status":  str(app.get("status", "pending")),
                "rejected_reason":     app.get("rejected_reason"),
            })
            matching.append(row)

        # ── Tri ───────────────────────────────────────────────────────────────
        return self._sort_matching(matching, sort_by)

    async def get_candidate_impact(
        self,
        db: AsyncSession,
        campaign_id: int,
        crew_profile_id: str,
        employer: EmployerProfile,
    ) -> Dict:
        """
        Rapport What-If détaillé à deux étages pour un candidat.
        Utilise le pool des autres candidats pour le centile DNRE.
        """
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Accès refusé.")

        candidate_snapshot = await repo.get_candidate_snapshot(db, crew_profile_id)
        if not candidate_snapshot:
            raise ValueError("Candidat sans données psychométriques.")

        # Construction du pool_context pour le centile DNRE
        all_candidates = await repo.get_candidates_with_snapshots(db, campaign_id)
        pool_context   = _build_pool_context(all_candidates)

        vessel_params, captain_vector, crew_snapshots = await self._get_yacht_context(
            db, campaign.yacht_id
        )
        betas         = await repo.get_active_model_betas(db)
        weight_config = await repo.get_active_job_weight_config(db)

        # Trouver les métadonnées du candidat
        cand_meta = next((c for c in all_candidates if str(c["crew_profile_id"]) == str(crew_profile_id)), {})

        result = pipeline.run_single(
            candidate_snapshot=candidate_snapshot,
            current_crew_snapshots=crew_snapshots,
            vessel_params=vessel_params,
            captain_vector=captain_vector,
            betas=betas,
            pool_context=pool_context,
            sme_weights_override=weight_config.get("sme_weights") if weight_config else None,
            position_key=str(cand_meta.get("position_targeted", "")),
            experience_years=cand_meta.get("experience_years", 0),
            crew_profile_id=crew_profile_id,
            p_ind_omegas=weight_config.get("p_ind_omegas") if weight_config else None,
        )

        return result.to_impact_report()

    # ── Décisions ─────────────────────────────────────────────────────────────

    async def hire_candidate(
        self, db: AsyncSession, campaign_id: int,
        crew_profile_id: str, employer: EmployerProfile,
    ) -> Dict:
        """
        Embauche + création RecruitmentEvent avec snapshot pipeline.
        """
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Accès refusé.")

        link = await repo.hire_candidate(db, campaign_id, crew_profile_id)
        if not link:
            raise ValueError("Candidature introuvable.")

        # Calcul pipeline pour l'event ML
        await self._create_recruitment_event(db, campaign, crew_profile_id)

        return {"message": "Candidat recruté.", "crew_profile_id": crew_profile_id}

    async def reject_candidate(
        self, db: AsyncSession, campaign_id: int,
        crew_profile_id: str, reason: str, employer: EmployerProfile,
    ) -> Dict:
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        link = await repo.reject_candidate(db, campaign_id, crew_profile_id, reason)
        if not link:
            raise ValueError("Candidature introuvable.")
        return {"message": "Candidat rejeté."}

    async def get_campaign_statistics(
        self, db: AsyncSession, campaign_id: int, employer: EmployerProfile
    ) -> Dict:
        campaign = await repo.get_campaign_secure(db, campaign_id, employer.id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        return await repo.get_campaign_statistics(db, campaign_id)

    # ── Internals ─────────────────────────────────────────────────────────────

    def _sort_matching(self, matching: List[Dict], sort_by: str) -> List[Dict]:
        """
        Tri configurable selon la dimension que l'employeur veut prioriser.

        "g_fit"           : candidats les plus adaptés au poste en tête
        "y_success"       : candidats les mieux intégrés à cet équipage en tête
        "dnre_then_mlpsm" : filtre DNRE d'abord, départage par MLPSM
                            (les DISQUALIFIED toujours en bas)
        """
        def dnre_score(row: Dict) -> float:
            return row.get("profile_fit", {}).get("g_fit", 0.0)

        def mlpsm_score(row: Dict) -> float:
            ti = row.get("team_integration", {})
            if not ti.get("available"):
                return -1.0
            return ti.get("y_success", 0.0)

        def is_pass(row: Dict) -> int:
            return 0 if row.get("is_pipeline_pass", True) else 1  # filtrés en bas

        if sort_by == "g_fit":
            return sorted(matching, key=lambda r: (is_pass(r), -dnre_score(r)))
        elif sort_by == "y_success":
            return sorted(matching, key=lambda r: (is_pass(r), -mlpsm_score(r)))
        else:  # dnre_then_mlpsm (default recommandé)
            return sorted(matching, key=lambda r: (is_pass(r), -dnre_score(r), -mlpsm_score(r)))

    async def _get_yacht_context(
        self, db: AsyncSession, yacht_id: Optional[int]
    ):
        if not yacht_id:
            return {}, {}, []
        vs = await vessel_repo.get_vessel_snapshot(db, yacht_id)
        vessel_params  = (vs or {}).get("jdr_params", {})
        captain_vector = await vessel_repo.get_captain_vector(db, yacht_id) or {}
        crew_snapshots = await vessel_repo.get_crew_snapshots(db, yacht_id)
        return vessel_params, captain_vector, crew_snapshots

    async def _create_recruitment_event(
        self, db: AsyncSession, campaign, crew_profile_id: str
    ) -> None:
        """Calcule le pipeline et persiste un RecruitmentEvent compact (audit ML)."""
        if not campaign.yacht_id:
            return

        snapshot = await repo.get_candidate_snapshot(db, crew_profile_id) or {}
        vessel_params, captain_vector, crew_snaps = await self._get_yacht_context(
            db, campaign.yacht_id
        )
        betas         = await repo.get_active_model_betas(db)
        weight_config = await repo.get_active_job_weight_config(db)

        result = pipeline.run_single(
            candidate_snapshot=snapshot,
            current_crew_snapshots=crew_snaps,
            vessel_params=vessel_params,
            captain_vector=captain_vector,
            betas=betas,
            sme_weights_override=weight_config.get("sme_weights") if weight_config else None,
            crew_profile_id=crew_profile_id,
            p_ind_omegas=weight_config.get("p_ind_omegas") if weight_config else None,
        )

        snap = result.to_event_snapshot()
        await repo.create_recruitment_event(db, {
            "crew_profile_id":     crew_profile_id,
            "campaign_id":         campaign.id,
            "yacht_id":            campaign.yacht_id,
            "y_success_predicted": snap["mlpsm"]["y_success"] if snap.get("mlpsm") else None,
            "dnre_g_fit":          snap["dnre"]["g_fit"],
            "dnre_centile":        snap["dnre"]["overall_centile"],
            "beta_weights_snapshot": betas,
            "engine_snapshot":     snap,
            "model_version":       "v2.0",
            "outcome":             "hired",
        })


# ── Helper pool_context ────────────────────────────────────────────────────────

def _build_pool_context(candidates_data: List[Dict]) -> Dict[str, Dict[str, float]]:
    """
    Construit le pool_context pour compute_single() à partir de la liste
    des candidats de la campagne.

    Format de sortie : {competency_key: {crew_profile_id: s_ic}}
    Calculé une seule fois en amont pour éviter de recalculer le DNRE batch.

    Note : Cette fonction n'est appelée que pour le rapport What-If individuel.
    Pour le batch, le centile est calculé directement dans pipeline.run_batch().
    """
    from engine.recruitment.DNRE import sme_score as _sme_score
    from engine.recruitment.DNRE.sme_score import ALL_COMPETENCIES

    pool_context: Dict[str, Dict[str, float]] = {c: {} for c in ALL_COMPETENCIES}

    for cand in candidates_data:
        cid      = str(cand.get("crew_profile_id", ""))
        snapshot = cand.get("snapshot") or {}

        sme_results = _sme_score.compute_all_competencies(snapshot)
        for competency_key, result in sme_results.items():
            pool_context[competency_key][cid] = result.score

    return pool_context