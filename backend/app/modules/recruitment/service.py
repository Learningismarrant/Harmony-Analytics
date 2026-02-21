# modules/recruitment/service.py
"""
Orchestration du cycle de vie des campagnes de recrutement.

Responsabilités :
- CRUD campagnes + cycle de vie (statuts, archivage)
- Matching psychométrique (SME + pool + impact équipe)
- Décisions candidats (hire, reject, unhire)
- Simulation What-If (engine/recruitment/simulator.py)
- Enregistrement RecruitmentEvent (alimentation future régression)
"""
from sqlalchemy.orm import Session
from typing import List, Optional, Dict

from engine.matching.sme import get_bulk_matching_results
from engine.recruitment.simulator import simulate_impact
from modules.recruitment.repository import RecruitmentRepository
from modules.vessel.repository import VesselRepository
from backend.app.shared.enums import CampaignStatus, ApplicationStatus

repo = RecruitmentRepository()
vessel_repo = VesselRepository()


class RecruitmentService:

    # ─────────────────────────────────────────────
    # CRUD CAMPAGNES
    # ─────────────────────────────────────────────

    def create_campaign(self, db: Session, payload, client_id: int):
        if payload.yacht_id:
            if not vessel_repo.is_owner(db, payload.yacht_id, client_id):
                raise ValueError("Ce yacht ne vous appartient pas.")
            existing = repo.get_active_campaign_for_yacht(db, payload.yacht_id, payload.position)
            if existing:
                raise ValueError("Une campagne active existe déjà pour ce poste sur ce yacht.")
        return repo.create_campaign(db, payload, client_id)

    def list_campaigns(
        self, db: Session, client_id: int,
        campaign_status=None, is_archived: bool = False
    ) -> List:
        return repo.get_campaigns_for_client(db, client_id, campaign_status, is_archived)

    def get_campaign(self, db: Session, campaign_id: int, client_id: int):
        return repo.get_campaign_secure(db, campaign_id, client_id)

    def update_campaign(self, db: Session, campaign_id: int, payload, client_id: int):
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        return repo.update_campaign(db, campaign, payload)

    def delete_campaign(self, db: Session, campaign_id: int, client_id: int):
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        hired = repo.count_hired_candidates(db, campaign_id)
        if hired > 0:
            raise ValueError("Impossible de supprimer une campagne avec des candidats embauchés.")
        repo.soft_delete_campaign(db, campaign)

    def change_status(self, db: Session, campaign_id: int, new_status: CampaignStatus, client_id: int):
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        return repo.update_status(db, campaign, new_status)

    def archive_campaign(self, db: Session, campaign_id: int, client_id: int):
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        # Rejet automatique des candidats non embauchés
        repo.reject_pending_candidates(db, campaign_id, reason="Campagne archivée")
        return repo.archive_campaign(db, campaign)

    # ─────────────────────────────────────────────
    # MATCHING PSYCHOMÉTRIQUE
    # ─────────────────────────────────────────────

    def get_matching(
        self, db: Session, campaign_id: int, client_id: int
    ) -> List[Dict]:
        """
        Matching sur 3 axes :
        1. Candidat vs profil SME (normative)
        2. Candidat vs pool (relative percentile)
        3. Impact sur l'équipe existante (F_team delta) — si yacht assigné
        """
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")

        candidates_data = repo.get_candidates_with_snapshots(db, campaign_id)

        # Axe 1 + 2 : SME + pool matching (votre engine existant)
        sme_results = get_bulk_matching_results(
            all_candidates_data=candidates_data,
            job_title=campaign.position,
            is_client_view=True,
        )

        # Axe 3 : Impact équipe (si yacht assigné avec équipage)
        team_impacts = {}
        if campaign.yacht_id:
            current_crew_snapshots = vessel_repo.get_crew_snapshots(db, campaign.yacht_id)
            vessel_snapshot = vessel_repo.get_vessel_snapshot(db, campaign.yacht_id)
            captain_vector = vessel_repo.get_captain_vector(db, campaign.yacht_id)

            if current_crew_snapshots and vessel_snapshot:
                vessel_params = vessel_snapshot.get("jdr_params", {})
                for cand in candidates_data:
                    if cand.get("snapshot"):
                        impact = simulate_impact(
                            candidate_snapshot=cand["snapshot"],
                            current_crew_snapshots=current_crew_snapshots,
                            vessel_params=vessel_params,
                            captain_vector=captain_vector or {},
                        )
                        team_impacts[cand["id"]] = {
                            "y_success": impact.y_success_predicted,
                            "f_team_delta": impact.f_team_delta,
                            "flags": impact.flags,
                            "confidence": impact.confidence_label,
                        }

        # Fusion des résultats
        return self._merge_matching_results(sme_results, team_impacts, campaign_id, db)

    def simulate_recruitment_impact(
        self, db: Session, campaign_id: int, candidate_id: int, client_id: int
    ) -> Optional[Dict]:
        """Simulation What-If détaillée pour un candidat spécifique."""
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign or not campaign.yacht_id:
            return None

        candidate_snapshot = repo.get_candidate_snapshot(db, candidate_id)
        if not candidate_snapshot:
            return None

        current_crew_snapshots = vessel_repo.get_crew_snapshots(db, campaign.yacht_id)
        vessel_snapshot = vessel_repo.get_vessel_snapshot(db, campaign.yacht_id)
        captain_vector = vessel_repo.get_captain_vector(db, campaign.yacht_id)

        impact = simulate_impact(
            candidate_snapshot=candidate_snapshot,
            current_crew_snapshots=current_crew_snapshots or [],
            vessel_params=vessel_snapshot.get("jdr_params", {}) if vessel_snapshot else {},
            captain_vector=captain_vector or {},
        )

        return {
            "y_success_predicted": impact.y_success_predicted,
            "p_ind": impact.p_ind,
            "f_team": impact.f_team,
            "f_env": impact.f_env,
            "f_lmx": impact.f_lmx,
            "f_team_delta": impact.f_team_delta,
            "jerk_filter_delta": impact.jerk_filter_delta,
            "faultline_risk_delta": impact.faultline_risk_delta,
            "emotional_buffer_delta": impact.emotional_buffer_delta,
            "flags": impact.flags,
            "data_completeness": impact.data_completeness,
            "confidence_label": impact.confidence_label,
        }

    def get_statistics(self, db: Session, campaign_id: int, client_id: int):
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        return repo.get_campaign_statistics(db, campaign_id)

    # ─────────────────────────────────────────────
    # DÉCISIONS CANDIDATS
    # ─────────────────────────────────────────────

    def process_joined_onboarding(self, db: Session, campaign_id: int, candidate_id: int, client_id: int):
        self._check_access(db, campaign_id, client_id)
        return repo.update_candidate_status(db, campaign_id, candidate_id, ApplicationStatus.JOINED)

    def process_hiring(self, db: Session, campaign_id: int, candidate_id: int, client_id: int):
        self._check_access(db, campaign_id, client_id)
        result = repo.hire_candidate(db, campaign_id, candidate_id)
        # Enregistrement RecruitmentEvent pour alimenter la régression future
        self._record_recruitment_event(db, campaign_id, candidate_id)
        return result

    def process_unhire(self, db: Session, campaign_id: int, candidate_id: int, client_id: int):
        self._check_access(db, campaign_id, client_id)
        return repo.update_candidate_status(db, campaign_id, candidate_id, ApplicationStatus.PENDING)

    def process_rejection(self, db: Session, campaign_id: int, candidate_id: int, reason: str, client_id: int):
        self._check_access(db, campaign_id, client_id)
        return repo.reject_candidate(db, campaign_id, candidate_id, reason)

    def bulk_reject(self, db: Session, campaign_id: int, candidate_ids: List[int], reason: str, client_id: int) -> int:
        self._check_access(db, campaign_id, client_id)
        return repo.bulk_reject_candidates(db, campaign_id, candidate_ids, reason)

    # ─────────────────────────────────────────────
    # VUE CANDIDAT
    # ─────────────────────────────────────────────

    def get_candidate_applications(self, db: Session, candidate_id: int) -> List:
        return repo.get_applications_for_candidate(db, candidate_id)

    # ─────────────────────────────────────────────
    # ENDPOINTS PUBLICS
    # ─────────────────────────────────────────────

    def get_public_campaign(self, db: Session, invite_token: str) -> Optional[Dict]:
        campaign = repo.get_by_invite_token(db, invite_token)
        if not campaign:
            return None
        return {
            "id": campaign.id,
            "title": campaign.title,
            "position": campaign.position,
            "description": campaign.description,
            "yacht_name": campaign.yacht.name if campaign.yacht else None,
            "status": campaign.status,
            "is_archived": campaign.is_archived,
        }

    def join_campaign(self, db: Session, invite_token: str, candidate_id: int) -> Dict:
        campaign = repo.get_by_invite_token(db, invite_token)
        if not campaign:
            raise ValueError("CAMPAIGN_NOT_FOUND")
        if campaign.is_archived or campaign.status == CampaignStatus.CLOSED:
            raise ValueError("CAMPAIGN_CLOSED")

        existing = repo.get_application(db, campaign.id, candidate_id)
        if existing:
            raise ValueError("ALREADY_APPLIED")

        repo.create_application(db, campaign.id, candidate_id)
        return {"message": "Candidature enregistrée.", "campaign_id": campaign.id}

    # ─────────────────────────────────────────────
    # INTERNALS
    # ─────────────────────────────────────────────

    def _check_access(self, db: Session, campaign_id: int, client_id: int):
        campaign = repo.get_campaign_secure(db, campaign_id, client_id)
        if not campaign:
            raise PermissionError("Accès refusé.")
        return campaign

    def _record_recruitment_event(self, db: Session, campaign_id: int, candidate_id: int):
        """
        Enregistre l'événement de recrutement avec les scores prédits.
        Ces données alimenteront la régression multiple au Temps 2.
        """
        try:
            campaign = repo.get_campaign_by_id(db, campaign_id)
            candidate_snapshot = repo.get_candidate_snapshot(db, candidate_id)
            if not candidate_snapshot or not campaign.yacht_id:
                return

            current_crew = vessel_repo.get_crew_snapshots(db, campaign.yacht_id)
            vessel_snapshot = vessel_repo.get_vessel_snapshot(db, campaign.yacht_id)
            captain_vector = vessel_repo.get_captain_vector(db, campaign.yacht_id)
            betas = repo.get_active_model_betas(db)

            from engine.recruitment.master import compute_y_success
            score = compute_y_success(
                candidate_snapshot=candidate_snapshot,
                current_crew_snapshots=current_crew or [],
                vessel_params=vessel_snapshot.get("jdr_params", {}) if vessel_snapshot else {},
                captain_vector=captain_vector or {},
                betas=betas,
            )

            repo.create_recruitment_event(db, {
                "candidate_id": candidate_id,
                "campaign_id": campaign_id,
                "yacht_id": campaign.yacht_id,
                "y_success_predicted": score.y_success,
                "p_ind_score": score.p_ind,
                "f_team_score": score.f_team,
                "f_env_score": score.f_env,
                "f_lmx_score": score.f_lmx,
                "beta_weights_snapshot": score.betas_used,
                "outcome": "hired",
                "y_actual": None,  # Rempli par les surveys + exit interview
            })
        except Exception as e:
            print(f"[RECRUITMENT_EVENT] Erreur enregistrement: {e}")

    def _merge_matching_results(
        self, sme_results: List, team_impacts: Dict, campaign_id: int, db: Session
    ) -> List[Dict]:
        """Fusionne les résultats SME/pool avec les impacts équipe."""
        applications = repo.get_applications_status_map(db, campaign_id)

        merged = []
        for r in sme_results:
            cand_id = r["candidate_id"]
            impact = team_impacts.get(cand_id, {})
            app_status = applications.get(cand_id, {})

            merged.append({
                **r,
                "y_success": impact.get("y_success"),
                "f_team_delta": impact.get("f_team_delta"),
                "impact_flags": impact.get("flags", []),
                "confidence": impact.get("confidence"),
                "is_hired": app_status.get("is_hired", False),
                "is_rejected": app_status.get("is_rejected", False),
                "application_status": app_status.get("status"),
            })

        # Tri : Hired → Score Ŷ décroissant → Rejected
        return sorted(
            merged,
            key=lambda x: (
                not x.get("is_hired", False),
                -(x.get("y_success") or x.get("global_fit") or 0),
                x.get("is_rejected", False),
            )
        )