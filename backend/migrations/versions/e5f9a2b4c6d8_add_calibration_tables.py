"""add_calibration_tables

Revision ID: e5f9a2b4c6d8
Revises: d4f8a1b2c3e9
Create Date: 2026-03-21

Crée 3 tables isolées pour le système d'étalonnage psychométrique (préfixe calib_).
Ces tables sont totalement indépendantes des tables de production.

Tables :
  - calib_users      : calibrateurs (n=200-300 par instrument)
  - calib_sessions   : sessions de passation (1 session = 1 calibrateur + 1 catalogue)
  - calib_responses  : réponses individuelles aux items

Contraintes notables :
  - calib_sessions : UNIQUE (calibrator_id, catalogue_id) — un calibrateur passe
                     chaque catalogue une seule fois
"""
from alembic import op
import sqlalchemy as sa


revision = 'e5f9a2b4c6d8'
down_revision = 'd4f8a1b2c3e9'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── calib_users ────────────────────────────────────────────────────────────
    op.create_table(
        "calib_users",
        sa.Column("id",              sa.Integer,      primary_key=True),
        sa.Column("email",           sa.String(255),  nullable=False),
        sa.Column("name",            sa.String(255),  nullable=False),
        sa.Column("hashed_password", sa.String,       nullable=False),
        sa.Column("cohort",          sa.String(100),  nullable=True),
        sa.Column("is_active",       sa.Boolean,      nullable=False, server_default=sa.text("true")),
        sa.Column("created_at",      sa.DateTime(timezone=True), server_default=sa.func.now()),
        # Démographiques — analyse DIF (Differential Item Functioning)
        sa.Column("gender",          sa.String(50),   nullable=True),
        sa.Column("birth_year",      sa.Integer,      nullable=True),
        sa.Column("education_level", sa.String(50),   nullable=True),
        sa.Column("native_language", sa.String(50),   nullable=True),
        sa.Column("years_at_sea",    sa.Integer,      nullable=True),
        sa.Column("maritime_role",   sa.String(100),  nullable=True),
        sa.Column("nationality",     sa.String(100),  nullable=True),
    )
    op.create_index("ix_calib_users_id",    "calib_users", ["id"],    unique=False)
    op.create_index("ix_calib_users_email", "calib_users", ["email"], unique=True)

    # ── calib_sessions ─────────────────────────────────────────────────────────
    op.create_table(
        "calib_sessions",
        sa.Column("id",            sa.Integer, primary_key=True),
        sa.Column("calibrator_id", sa.Integer, sa.ForeignKey("calib_users.id",     ondelete="CASCADE"), nullable=False),
        sa.Column("catalogue_id",  sa.Integer, sa.ForeignKey("test_catalogues.id", ondelete="CASCADE"), nullable=False),
        sa.Column("started_at",    sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("completed_at",  sa.DateTime(timezone=True), nullable=True),
        sa.Column("device_info",   sa.JSON, nullable=True),
        sa.UniqueConstraint("calibrator_id", "catalogue_id", name="uq_calib_session_calibrator_catalogue"),
    )
    op.create_index("ix_calib_sessions_id",            "calib_sessions", ["id"],           unique=False)
    op.create_index("ix_calib_sessions_calibrator_id", "calib_sessions", ["calibrator_id"], unique=False)
    op.create_index("ix_calib_sessions_catalogue_id",  "calib_sessions", ["catalogue_id"],  unique=False)

    # ── calib_responses ────────────────────────────────────────────────────────
    op.create_table(
        "calib_responses",
        sa.Column("id",            sa.Integer, primary_key=True),
        sa.Column("session_id",    sa.Integer, sa.ForeignKey("calib_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("question_id",   sa.Integer, sa.ForeignKey("questions.id",      ondelete="CASCADE"), nullable=False),
        sa.Column("value",         sa.Integer, nullable=False),
        sa.Column("seconds_spent", sa.Float,   nullable=True),
    )
    op.create_index("ix_calib_responses_id",         "calib_responses", ["id"],          unique=False)
    op.create_index("ix_calib_responses_session_id", "calib_responses", ["session_id"],  unique=False)
    op.create_index("ix_calib_responses_question_id","calib_responses", ["question_id"], unique=False)


def downgrade() -> None:
    op.drop_table("calib_responses")
    op.drop_table("calib_sessions")
    op.drop_table("calib_users")
