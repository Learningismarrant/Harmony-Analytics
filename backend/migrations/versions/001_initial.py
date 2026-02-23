"""initial schema — harmony v2 — Full System

Revision ID: 001_initial
Create Date: 23/02/2026
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial'
down_revision = None

# Valeurs des Enums
USER_ROLE = ('candidate', 'client', 'admin')
YACHT_POSITION = ('Captain', 'First Mate', 'Bosun', 'Deckhand', 'Chief Engineer', '2nd Engineer', 'Chief Stewardess', 'Stewardess', 'Chef')
AVAILABILITY_STATUS = ('available', 'on_board', 'unavailable', 'soon')
CAMPAIGN_STATUS = ('open', 'closed', 'draft')
APPLICATION_STATUS = ('pending', 'hired', 'rejected', 'joined')
SURVEY_TRIGGER = ('post_charter', 'post_season', 'monthly_pulse', 'conflict_event', 'exit_interview')
DEPARTURE_REASON = ('performance', 'team_conflict', 'environment', 'leadership', 'external', 'unknown')

def upgrade() -> None:
    # ── 1. CREATION MANUELLE DES TYPES ENUM (SÉCURISÉE) ──
    enums = {
        "userrole": USER_ROLE,
        "yachtposition": YACHT_POSITION,
        "availabilitystatus": AVAILABILITY_STATUS,
        "campaignstatus": CAMPAIGN_STATUS,
        "applicationstatus": APPLICATION_STATUS,
        "surveytriggertype": SURVEY_TRIGGER,
        "departurereason": DEPARTURE_REASON,
    }

    for name, values in enums.items():
        vals_str = ", ".join([f"'{v}'" for v in values])
        op.execute(f"""
            DO $$ 
            BEGIN 
                IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = '{name}') THEN
                    CREATE TYPE {name} AS ENUM ({vals_str});
                END IF;
            END $$;
        """)

    # ── 2. CREATION DES TABLES ──
    # Note : On utilise postgresql.ENUM(..., create_type=False) 
    # pour empêcher SQLAlchemy de tenter une double création.

    op.create_table("users",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("email", sa.String, nullable=False, unique=True),
        sa.Column("phone", sa.String, nullable=True),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("avatar_url", sa.String, nullable=True),
        sa.Column("hashed_password", sa.String, nullable=False),
        sa.Column("is_harmony_verified", sa.Boolean, default=False),
        sa.Column("role", postgresql.ENUM(*USER_ROLE, name='userrole', create_type=False), nullable=False, server_default="candidate"),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("location", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    op.create_table("crew_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("position_targeted", postgresql.ENUM(*YACHT_POSITION, name='yachtposition', create_type=False), nullable=False, server_default="Deckhand"),
        sa.Column("experience_years", sa.Integer, default=0),
        sa.Column("availability_status", postgresql.ENUM(*AVAILABILITY_STATUS, name='availabilitystatus', create_type=False), server_default="available"),
        sa.Column("psychometric_snapshot", sa.JSON, nullable=True),
        sa.Column("snapshot_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("trust_score", sa.Integer, nullable=True),
    )

    op.create_table("employer_profiles",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), unique=True, nullable=False),
        sa.Column("company_name", sa.String, nullable=True),
        sa.Column("is_billing_active", sa.Boolean, default=False),
        sa.Column("fleet_snapshot", sa.JSON, nullable=True),
        sa.Column("fleet_updated_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table("user_documents",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("user_id", sa.Integer, sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("title", sa.String, nullable=False, default="Document"),
        sa.Column("document_type", sa.String, nullable=True),
        sa.Column("file_url", sa.String, nullable=False),
        sa.Column("expiry_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_verified", sa.Boolean, default=False),
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("official_id", sa.String, nullable=True),
        sa.Column("official_brevet", sa.String, nullable=True),
        sa.Column("num_titulaire_officiel", sa.String, nullable=True),
        sa.Column("official_name", sa.String, nullable=True),
        sa.Column("verification_metadata", sa.JSON, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("yachts",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employer_profile_id", sa.Integer, sa.ForeignKey("employer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String, nullable=False),
        sa.Column("type", sa.String, nullable=False),
        sa.Column("length", sa.Integer, nullable=True),
        sa.Column("boarding_token", sa.String, unique=True, nullable=False),
        sa.Column("vessel_snapshot", sa.JSON, nullable=True),
        sa.Column("snapshot_updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("captain_leadership_vector", sa.JSON, nullable=True),
        sa.Column("toxicity_flag", sa.Boolean, default=False),
        sa.Column("required_es_minimum", sa.Float, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("crew_assignments",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("crew_profile_id", sa.Integer, sa.ForeignKey("crew_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("yacht_id", sa.Integer, sa.ForeignKey("yachts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("role", postgresql.ENUM(*YACHT_POSITION, name='yachtposition', create_type=False), nullable=False),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("start_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("end_date", sa.DateTime(timezone=True), nullable=True),
        sa.Column("external_yacht_name", sa.String, nullable=True),
        sa.Column("contract_type", sa.String, nullable=True),
        sa.Column("candidate_comment", sa.String, nullable=True),
        sa.Column("reference_comment", sa.String, nullable=True),
        sa.Column("is_harmony_approved", sa.Boolean, default=False),
        sa.Column("reference_contact_email", sa.String, nullable=True),
        sa.Column("verification_token", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("test_catalogues",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("nom_du_test", sa.String, nullable=False),
        sa.Column("description_courte", sa.String, nullable=True),
        sa.Column("instructions", sa.Text, nullable=True),
        sa.Column("test_type", sa.String, nullable=False),
        sa.Column("max_score_per_question", sa.Integer, default=5),
        sa.Column("is_active", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("questions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("test_id", sa.Integer, sa.ForeignKey("test_catalogues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("text", sa.Text, nullable=False),
        sa.Column("question_type", sa.String, nullable=False),
        sa.Column("options", sa.JSON, nullable=True),
        sa.Column("trait", sa.String, nullable=True),
        sa.Column("correct_answer", sa.String, nullable=True),
        sa.Column("reverse", sa.Boolean, default=False),
        sa.Column("order", sa.Integer, default=0),
    )

    op.create_table("test_results",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("crew_profile_id", sa.Integer, sa.ForeignKey("crew_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("test_id", sa.Integer, sa.ForeignKey("test_catalogues.id"), nullable=False),
        sa.Column("global_score", sa.Float, nullable=False),
        sa.Column("scores", sa.JSON, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("campaigns",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("employer_profile_id", sa.Integer, sa.ForeignKey("employer_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("yacht_id", sa.Integer, sa.ForeignKey("yachts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String, nullable=False),
        sa.Column("position", postgresql.ENUM(*YACHT_POSITION, name='yachtposition', create_type=False), nullable=False),
        sa.Column("description", sa.String, nullable=True),
        sa.Column("status", postgresql.ENUM(*CAMPAIGN_STATUS, name='campaignstatus', create_type=False), server_default="open"),
        sa.Column("is_archived", sa.Boolean, default=False),
        sa.Column("invite_token", sa.String, unique=True, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    op.create_table("campaign_candidates",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crew_profile_id", sa.Integer, sa.ForeignKey("crew_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", postgresql.ENUM(*APPLICATION_STATUS, name='applicationstatus', create_type=False), server_default="pending"),
        sa.Column("is_hired", sa.Boolean, default=False),
        sa.Column("is_rejected", sa.Boolean, default=False),
        sa.Column("rejected_reason", sa.String, nullable=True),
        sa.Column("joined_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("campaign_id", "crew_profile_id", name="uq_campaign_crew"),
    )

    op.create_table("daily_pulses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("crew_profile_id", sa.Integer, sa.ForeignKey("crew_profiles.id", ondelete="CASCADE"), nullable=False),
        sa.Column("yacht_id", sa.Integer, sa.ForeignKey("yachts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Integer, nullable=False),
        sa.Column("comment", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.create_table("surveys",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("yacht_id", sa.Integer, sa.ForeignKey("yachts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("triggered_by_id", sa.Integer, sa.ForeignKey("employer_profiles.id"), nullable=False),
        sa.Column("trigger_type", postgresql.ENUM(*SURVEY_TRIGGER, name='surveytriggertype', create_type=False), nullable=False),
        sa.Column("target_crew_ids", sa.JSON, nullable=False),
        sa.Column("is_open", sa.Boolean, default=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("closed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table("survey_responses",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("survey_id", sa.Integer, sa.ForeignKey("surveys.id", ondelete="CASCADE"), nullable=False),
        sa.Column("crew_profile_id", sa.Integer, sa.ForeignKey("crew_profiles.id"), nullable=False),
        sa.Column("yacht_id", sa.Integer, sa.ForeignKey("yachts.id"), nullable=False),
        sa.Column("trigger_type", postgresql.ENUM(*SURVEY_TRIGGER, name='surveytriggertype', create_type=False), nullable=False),
        sa.Column("team_cohesion_observed", sa.Float, nullable=True),
        sa.Column("workload_felt", sa.Float, nullable=True),
        sa.Column("leadership_fit_felt", sa.Float, nullable=True),
        sa.Column("individual_performance_self", sa.Float, nullable=True),
        sa.Column("intent_to_stay", sa.Float, nullable=False),
        sa.Column("free_text", sa.String, nullable=True),
        sa.Column("submitted_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.UniqueConstraint("survey_id", "crew_profile_id", name="uq_survey_crew"),
    )

    op.create_table("recruitment_events",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("crew_profile_id", sa.Integer, sa.ForeignKey("crew_profiles.id"), nullable=False),
        sa.Column("campaign_id", sa.Integer, sa.ForeignKey("campaigns.id", ondelete="SET NULL"), nullable=True),
        sa.Column("yacht_id", sa.Integer, sa.ForeignKey("yachts.id", ondelete="SET NULL"), nullable=True),
        sa.Column("y_success_predicted", sa.Float, nullable=True),
        sa.Column("p_ind_score", sa.Float, nullable=True),
        sa.Column("f_team_score", sa.Float, nullable=True),
        sa.Column("f_env_score", sa.Float, nullable=True),
        sa.Column("f_lmx_score", sa.Float, nullable=True),
        sa.Column("beta_weights_snapshot", sa.JSON, nullable=True),
        sa.Column("model_version", sa.String, server_default="v1.0"),
        sa.Column("outcome", postgresql.ENUM(*APPLICATION_STATUS, name='applicationstatus', create_type=False), server_default="hired"),
        sa.Column("y_actual", sa.Float, nullable=True),
        sa.Column("actual_tenure_days", sa.Integer, nullable=True),
        sa.Column("departure_reason", postgresql.ENUM(*DEPARTURE_REASON, name='departurereason', create_type=False), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), onupdate=sa.func.now()),
    )

    op.create_table("model_versions",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("version", sa.String, unique=True, nullable=False),
        sa.Column("is_active", sa.Boolean, default=False),
        sa.Column("b1_p_ind", sa.Float, default=0.25),
        sa.Column("b2_f_team", sa.Float, default=0.35),
        sa.Column("b3_f_env", sa.Float, default=0.20),
        sa.Column("b4_f_lmx", sa.Float, default=0.20),
        sa.Column("n_samples", sa.Integer, nullable=True),
        sa.Column("r_squared", sa.Float, nullable=True),
        sa.Column("trained_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("notes", sa.String, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    op.execute("""
        INSERT INTO model_versions (version, is_active, b1_p_ind, b2_f_team, b3_f_env, b4_f_lmx, notes)
        VALUES ('v1.0', true, 0.25, 0.35, 0.20, 0.20,
                'Priors littérature — Schmidt & Hunter 1998, Hackman 2002, Graen & Uhl-Bien 1995')
    """)

def downgrade() -> None:
    tables = [
        "model_versions", "recruitment_events", "survey_responses", "surveys",
        "daily_pulses", "campaign_candidates", "campaigns",
        "test_results", "questions", "test_catalogues",
        "crew_assignments", "yachts",
        "user_documents", "employer_profiles", "crew_profiles", "users",
    ]
    for table in tables:
        op.drop_table(table)

    enums = [
        "userrole", "yachtposition", "availabilitystatus", 
        "campaignstatus", "applicationstatus", "surveytriggertype", "departurereason"
    ]
    for e in enums:
        op.execute(f"DROP TYPE IF EXISTS {e}")