"""add superadmin role and make users.workshop_id nullable

Revision ID: e1f2a3b4c5d6
Revises: c7f1a9b2d3e4
Create Date: 2026-09-06

Permite usuários do grupo GCT que não pertencem a um cliente específico
(workshop_id nulo) e enxergam todos os clientes cadastrados.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "e1f2a3b4c5d6"
down_revision: Union[str, None] = "c7f1a9b2d3e4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ALTER TYPE ... ADD VALUE não pode rodar dentro do bloco transacional do Alembic.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'SUPERADMIN'")

    op.alter_column(
        "users",
        "workshop_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=True,
    )


def downgrade() -> None:
    op.execute("DELETE FROM users WHERE workshop_id IS NULL")
    op.alter_column(
        "users",
        "workshop_id",
        existing_type=sa.dialects.postgresql.UUID(as_uuid=True),
        nullable=False,
    )
    op.execute("ALTER TYPE user_role RENAME TO user_role_old")
    op.execute("CREATE TYPE user_role AS ENUM ('ADMIN', 'AGENT')")
    op.execute(
        "ALTER TABLE users ALTER COLUMN role TYPE user_role "
        "USING role::text::user_role"
    )
    op.execute("DROP TYPE user_role_old")
