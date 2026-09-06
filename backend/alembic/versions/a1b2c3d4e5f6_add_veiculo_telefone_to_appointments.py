"""add_veiculo_telefone_to_appointments

Revision ID: a1b2c3d4e5f6
Revises: 65d080f796d0
Create Date: 2026-05-11 00:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "b1c2d3e4f5a6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("appointments")}

    if "veiculo" not in existing:
        op.add_column("appointments", sa.Column("veiculo", sa.String(200), nullable=True))
    if "telefone" not in existing:
        op.add_column("appointments", sa.Column("telefone", sa.String(20), nullable=True))


def downgrade() -> None:
    op.drop_column("appointments", "telefone")
    op.drop_column("appointments", "veiculo")
