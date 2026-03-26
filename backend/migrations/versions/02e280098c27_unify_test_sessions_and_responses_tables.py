"""unify test sessions and responses tables

Revision ID: 02e280098c27
Revises: c454ce1ca221
Create Date: 2026-03-26 10:04:55.954057

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '02e280098c27'
down_revision: Union[str, None] = 'c454ce1ca221'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── 1. Créer test_sessions ────────────────────────────────────────────────
    op.create_table(
        'test_sessions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('catalogue_id', sa.Integer(), nullable=False),
        sa.Column('crew_profile_id', sa.Integer(), nullable=True),
        sa.Column('calibrator_id', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('device_info', sa.JSON(), nullable=True),
        sa.CheckConstraint(
            '(crew_profile_id IS NOT NULL)::int + (calibrator_id IS NOT NULL)::int = 1',
            name='check_xor_user_session',
        ),
        sa.ForeignKeyConstraint(['calibrator_id'],   ['calib_users.id']),
        sa.ForeignKeyConstraint(['catalogue_id'],     ['test_catalogues.id']),
        sa.ForeignKeyConstraint(['crew_profile_id'],  ['crew_profiles.id']),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_test_sessions_calib_catalogue', 'test_sessions', ['calibrator_id', 'catalogue_id'], unique=False)
    op.create_index('ix_test_sessions_crew_catalogue',  'test_sessions', ['crew_profile_id', 'catalogue_id'], unique=False)
    op.create_index(op.f('ix_test_sessions_id'), 'test_sessions', ['id'], unique=False)

    # ── 2. Index partiel unique pour calibrateurs (PostgreSQL) ───────────────
    op.execute("""
        CREATE UNIQUE INDEX uq_calib_session_catalogue
        ON test_sessions(calibrator_id, catalogue_id)
        WHERE calibrator_id IS NOT NULL
    """)

    # ── 3. Data migration : calib_sessions → test_sessions ───────────────────
    op.execute("""
        INSERT INTO test_sessions (id, catalogue_id, calibrator_id, started_at, completed_at, device_info)
        SELECT id, catalogue_id, calibrator_id, started_at, completed_at, device_info
        FROM calib_sessions
    """)

    # ── 4. Créer test_responses ───────────────────────────────────────────────
    op.create_table(
        'test_responses',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('session_id', sa.Integer(), nullable=False),
        sa.Column('catalogue_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('response_value', sa.String(length=50), nullable=False),
        sa.Column('seconds_spent', sa.Float(), nullable=True),
        sa.CheckConstraint(
            'seconds_spent IS NULL OR (seconds_spent >= 0 AND seconds_spent <= 3600)',
            name='check_seconds_spent_range',
        ),
        sa.ForeignKeyConstraint(['catalogue_id'], ['test_catalogues.id']),
        sa.ForeignKeyConstraint(['question_id'],  ['questions.id'],      ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['session_id'],   ['test_sessions.id'],  ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_test_responses_catalogue_question', 'test_responses', ['catalogue_id', 'question_id'], unique=False)
    op.create_index(op.f('ix_test_responses_id'),         'test_responses', ['id'],         unique=False)
    op.create_index(op.f('ix_test_responses_session_id'), 'test_responses', ['session_id'], unique=False)

    # ── 5. Data migration : calib_responses → test_responses ─────────────────
    # value (int) → response_value (str), catalogue_id dérivé depuis la session
    op.execute("""
        INSERT INTO test_responses (session_id, catalogue_id, question_id, response_value, seconds_spent)
        SELECT cr.session_id, cs.catalogue_id, cr.question_id,
               CAST(cr.value AS VARCHAR), cr.seconds_spent
        FROM calib_responses cr
        JOIN calib_sessions cs ON cr.session_id = cs.id
    """)

    # ── 6. Mettre à jour la séquence test_sessions (évite les collisions PK) ─
    op.execute(
        "SELECT setval('test_sessions_id_seq', COALESCE((SELECT MAX(id) FROM test_sessions), 1))"
    )

    # ── 7. Supprimer les anciennes tables (après data migration) ──────────────
    op.drop_table('calib_responses')
    op.drop_table('calib_sessions')

    # ── 8. Colonnes supplémentaires sur test_results ──────────────────────────
    # Créer le type enum PostgreSQL avant de l'utiliser
    user_type_enum = sa.Enum('candidate', 'calibrator', name='usertypeenum')
    user_type_enum.create(op.get_bind(), checkfirst=True)

    op.add_column('test_results', sa.Column('calibrator_id', sa.Integer(), nullable=True))
    op.add_column('test_results', sa.Column('session_id',    sa.Integer(), nullable=True))
    op.add_column('test_results', sa.Column(
        'user_type',
        sa.Enum('candidate', 'calibrator', name='usertypeenum'),
        server_default='candidate',
        nullable=False,
    ))
    op.alter_column('test_results', 'crew_profile_id', existing_type=sa.INTEGER(), nullable=True)
    op.create_foreign_key(
        'fk_test_results_session_id', 'test_results', 'test_sessions', ['session_id'], ['id']
    )
    op.create_foreign_key(
        'fk_test_results_calibrator_id', 'test_results', 'calib_users', ['calibrator_id'], ['id']
    )


def downgrade() -> None:
    # Migration non-reversible : la suppression de calib_sessions/calib_responses
    # avec data migration ne peut pas être annulée sans risque de perte de données.
    # Pour revenir en arrière, restaurer depuis un backup.
    raise NotImplementedError(
        "Cette migration est non-reversible. "
        "Pour revenir en arrière, restaurer la base depuis un backup pre-migration."
    )
