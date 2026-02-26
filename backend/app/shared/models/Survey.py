# app/models/survey.py
"""
Pipeline ML :
Survey → SurveyResponse → mise à jour RecruitmentEvent.y_actual
n > 150 events → régression → nouveau ModelVersion actif
"""
from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, JSON, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.core.database import Base


class Survey(Base):
    __tablename__ = "surveys"

    id                  = Column(Integer, primary_key=True, index=True)
    title               = Column(String, nullable=True)
    yacht_id            = Column(Integer, ForeignKey("yachts.id"), nullable=False, index=True)
    triggered_by_id     = Column(Integer, ForeignKey("employer_profiles.id"), nullable=False)

    trigger_type    = Column(String, nullable=False)
    # post_charter | post_season | monthly_pulse | conflict_event | exit_interview

    target_crew_ids = Column(JSON, nullable=False, default=list)   # [crew_profile_id, ...]

    is_open    = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at  = Column(DateTime(timezone=True), nullable=True)

    yacht        = relationship("Yacht", back_populates="surveys")
    triggered_by = relationship("EmployerProfile", back_populates="surveys_triggered", foreign_keys=[triggered_by_id])
    responses    = relationship("SurveyResponse", back_populates="survey", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Survey id={self.id} type={self.trigger_type} open={self.is_open}>"


class SurveyResponse(Base):
    __tablename__ = "survey_responses"

    id              = Column(Integer, primary_key=True, index=True)
    survey_id       = Column(Integer, ForeignKey("surveys.id"), nullable=False, index=True)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"), nullable=False, index=True)
    yacht_id        = Column(Integer, ForeignKey("yachts.id"), nullable=False)
    trigger_type    = Column(String, nullable=False)

    # ── Dimensions observées (0–100) — valident les prédictions algo
    team_cohesion_observed      = Column(Float, nullable=True)   # proxy F_team
    workload_felt               = Column(Float, nullable=True)   # proxy F_env
    leadership_fit_felt         = Column(Float, nullable=True)   # proxy F_lmx
    individual_performance_self = Column(Float, nullable=True)

    # Variable dépendante principale — proxy Y_actual continu
    # 0 = "je pars" / 100 = "je reste longtemps"
    intent_to_stay = Column(Float, nullable=False)

    free_text    = Column(String, nullable=True)
    submitted_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        UniqueConstraint("survey_id", "crew_profile_id", name="uq_survey_crew"),
    )

    survey       = relationship("Survey", back_populates="responses")
    crew_profile = relationship("CrewProfile")

    def __repr__(self):
        return f"<SurveyResponse id={self.id} crew={self.crew_profile_id} intent={self.intent_to_stay}>"


class RecruitmentEvent(Base):
    """
    Snapshot de chaque décision d'embauche avec les scores prédits.
    Mis à jour progressivement par les SurveyResponses via y_actual.
    Paires (Ŷ_predicted, Y_actual) → régression → ajustement β₁…β₄.
    """
    __tablename__ = "recruitment_events"

    id              = Column(Integer, primary_key=True, index=True)
    crew_profile_id = Column(Integer, ForeignKey("crew_profiles.id"), nullable=False, index=True)
    campaign_id     = Column(Integer, ForeignKey("campaigns.id"), nullable=True)
    yacht_id        = Column(Integer, ForeignKey("yachts.id"), nullable=True, index=True)

    y_success_predicted   = Column(Float, nullable=True)
    p_ind_score           = Column(Float, nullable=True)
    f_team_score          = Column(Float, nullable=True)
    f_env_score           = Column(Float, nullable=True)
    f_lmx_score           = Column(Float, nullable=True)
    beta_weights_snapshot = Column(JSON,  nullable=True)
    model_version         = Column(String, default="v1.0")

    outcome            = Column(String, nullable=True, default="hired")
    y_actual           = Column(Float, nullable=True)   # Rempli par les surveys
    actual_tenure_days = Column(Integer, nullable=True)
    departure_reason   = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    crew_profile = relationship("CrewProfile")

    def __repr__(self):
        return f"<RecruitmentEvent id={self.id} Ŷ={self.y_success_predicted} Y={self.y_actual}>"


class ModelVersion(Base):
    """
    Versioning des betas β₁…β₄.
    v1.0 seedé à l'init (priors littérature).
    Remplacé par régression dès n > 150 events avec y_actual.
    """
    __tablename__ = "model_versions"

    id        = Column(Integer, primary_key=True, index=True)
    version   = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=False)

    b1_p_ind  = Column(Float, default=0.25)
    b2_f_team = Column(Float, default=0.35)
    b3_f_env  = Column(Float, default=0.20)
    b4_f_lmx  = Column(Float, default=0.20)

    n_samples  = Column(Integer, nullable=True)
    r_squared  = Column(Float, nullable=True)
    trained_at = Column(DateTime(timezone=True), nullable=True)
    notes      = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<ModelVersion {self.version} active={self.is_active} R²={self.r_squared}>"


class JobWeightConfig(Base):
    """
    Versioning des poids SME (DNRE) et omegas P_ind (MLPSM).

    Analogue à ModelVersion pour les betas MLPSM — permet à un script ML
    de mettre à jour les poids la nuit sans toucher au code Python.

    SKILL.md DIRECTIVE V1 : les poids w_t ne doivent jamais être hardcodés
    dans les fonctions. Ce modèle les stocke en DB pour injection dynamique.

    Colonnes :
        sme_weights       : JSON {competency_key: {trait_key: weight}}
                            None = utiliser DEFAULT_SME_WEIGHTS de sme_score.py
        omega_gca/c/inter : omegas P_ind (SKILL.md V1 : ω₁=0.55, ω₂=0.35, ω₃=0.10)
                            Permettront ajustements par poste en Temps 2.
    """
    __tablename__ = "job_weight_configs"

    id        = Column(Integer, primary_key=True, index=True)
    version   = Column(String, unique=True, nullable=False)
    is_active = Column(Boolean, default=False)

    # Poids SME par compétence : {competency_key: {trait_key: weight}}
    # None = utiliser DEFAULT_SME_WEIGHTS du module sme_score.py
    sme_weights = Column(JSON, nullable=True)

    # Omegas P_ind (SKILL.md V1 — calibrables par régression Temps 2)
    omega_gca               = Column(Float, default=0.55)
    omega_conscientiousness = Column(Float, default=0.35)
    omega_interaction       = Column(Float, default=0.10)

    n_samples  = Column(Integer, nullable=True)
    trained_at = Column(DateTime(timezone=True), nullable=True)
    notes      = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    def __repr__(self):
        return f"<JobWeightConfig {self.version} active={self.is_active}>"