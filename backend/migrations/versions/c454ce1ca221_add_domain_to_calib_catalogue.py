"""add domain to calib_catalogue

Revision ID: c454ce1ca221
Revises: e5f9a2b4c6d8
Create Date: 2026-03-23 14:23:13.391147

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c454ce1ca221'
down_revision: Union[str, None] = 'e5f9a2b4c6d8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

catalogue_domain_enum = sa.Enum(
    'personality', 'cognitive', 'motivation', 'person_job', 'person_org', 'person_team', 'physical',
    name='cataloguedomain'
)


def upgrade() -> None:
    catalogue_domain_enum.create(op.get_bind(), checkfirst=True)
    op.alter_column('calib_users', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=True,
               existing_server_default=sa.text('true'))
    op.add_column('test_catalogues', sa.Column('domain', catalogue_domain_enum, server_default='personality', nullable=False))


def downgrade() -> None:
    op.drop_column('test_catalogues', 'domain')
    op.alter_column('calib_users', 'is_active',
               existing_type=sa.BOOLEAN(),
               nullable=False,
               existing_server_default=sa.text('true'))
    catalogue_domain_enum.drop(op.get_bind(), checkfirst=True)
