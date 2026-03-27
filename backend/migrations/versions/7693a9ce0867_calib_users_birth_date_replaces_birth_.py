"""calib_users birth_date replaces birth_year

Revision ID: 7693a9ce0867
Revises: 2895301cf6d8
Create Date: 2026-03-27 19:12:18.388907

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7693a9ce0867'
down_revision: Union[str, None] = '2895301cf6d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # calib_users: remplace birth_year (Integer) par birth_date (Date)
    op.add_column('calib_users', sa.Column('birth_date', sa.Date(), nullable=True))
    op.drop_column('calib_users', 'birth_year')
    # Supprime l'index partiel obsolète sur test_sessions (renommé lors d'une migration précédente)
    op.drop_index('uq_calib_session_catalogue', table_name='test_sessions', postgresql_where='(calibrator_id IS NOT NULL)')


def downgrade() -> None:
    # Recréer l'index partiel (best-effort, peut échouer si la contrainte existe déjà)
    op.create_index(
        'uq_calib_session_catalogue', 'test_sessions',
        ['calibrator_id', 'catalogue_id'], unique=True,
        postgresql_where='(calibrator_id IS NOT NULL)',
    )
    op.add_column('calib_users', sa.Column('birth_year', sa.INTEGER(), autoincrement=False, nullable=True))
    op.drop_column('calib_users', 'birth_date')
