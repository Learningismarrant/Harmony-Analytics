"""extend_yachtposition_enum

Revision ID: d4f8a1b2c3e9
Revises: 2923d36c72e5
Create Date: 2026-03-18 12:00:00.000000

Ajoute 7 nouvelles valeurs à l'enum PostgreSQL 'yachtposition'.

IMPORTANT : PostgreSQL ne supporte pas la suppression de valeurs d'un type ENUM.
Cette migration est irréversible (downgrade est un no-op).
Alembic autogenerate ne gère pas les types ENUM nommés — migration manuelle requise.

Nouvelles valeurs :
    Second Officer, 3rd Engineer, ETO, Butler, Sous Chef, Dive Instructor, Medic
"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d4f8a1b2c3e9"
down_revision: Union[str, None] = "2923d36c72e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


NEW_VALUES = [
    "Second Officer",
    "3rd Engineer",
    "ETO",
    "Butler",
    "Sous Chef",
    "Dive Instructor",
    "Medic",
]


def upgrade() -> None:
    # ADD VALUE IF NOT EXISTS est idempotent (PostgreSQL 9.3+)
    for value in NEW_VALUES:
        op.execute(
            f"ALTER TYPE yachtposition ADD VALUE IF NOT EXISTS '{value}'"
        )


def downgrade() -> None:
    # PostgreSQL ne supporte pas la suppression de valeurs ENUM.
    # Downgrade est intentionnellement un no-op.
    pass
