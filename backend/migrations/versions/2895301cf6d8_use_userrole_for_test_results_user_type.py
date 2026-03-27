"""use_userrole_for_test_results_user_type

Revision ID: 2895301cf6d8
Revises: 02e280098c27
Create Date: 2026-03-26 10:51:41.574717

Consolidation : supprime l'enum redondant `usertypeenum` et réutilise `userrole`.
- Ajoute la valeur 'calibrator' au type PG `userrole` (irreversible en PG)
- Migre test_results.user_type de usertypeenum → userrole
- Supprime usertypeenum
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '2895301cf6d8'
down_revision: Union[str, None] = '02e280098c27'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Ajouter 'calibrator' au type PG userrole (ADD VALUE est irreversible en PG)
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'calibrator'")

    # 2. Supprimer le server_default typé usertypeenum avant le USING cast
    op.execute(
        "ALTER TABLE test_results ALTER COLUMN user_type DROP DEFAULT"
    )

    # 3. Migrer la colonne user_type : usertypeenum → userrole
    #    USING cast text puis cast vers userrole pour traverser les deux types
    op.execute(
        "ALTER TABLE test_results "
        "ALTER COLUMN user_type TYPE userrole "
        "USING user_type::text::userrole"
    )

    # 4. Remettre le server_default avec le bon type
    op.execute(
        "ALTER TABLE test_results "
        "ALTER COLUMN user_type SET DEFAULT 'candidate'::userrole"
    )

    # 5. Supprimer l'ancien type redondant
    op.execute("DROP TYPE IF EXISTS usertypeenum")


def downgrade() -> None:
    # Recréer usertypeenum et remettre la colonne dessus
    # Note: 'calibrator' reste dans userrole (impossible à supprimer en PG)
    op.execute("CREATE TYPE usertypeenum AS ENUM ('candidate', 'calibrator')")
    op.execute(
        "ALTER TABLE test_results "
        "ALTER COLUMN user_type TYPE usertypeenum "
        "USING user_type::text::usertypeenum"
    )
