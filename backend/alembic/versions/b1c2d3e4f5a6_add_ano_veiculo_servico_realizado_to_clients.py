"""add_ano_veiculo_servico_realizado_to_clients

Revision ID: b1c2d3e4f5a6
Revises: a8f9b2c3d4e5
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = 'a8f9b2c3d4e5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLS = [
    ("ano_veiculo",       sa.String(4)),
    ("servico_realizado", sa.Text()),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("clients")}
    for col_name, col_type in _NEW_COLS:
        if col_name not in existing:
            op.add_column("clients", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("clients")}
    for col_name, _ in _NEW_COLS:
        if col_name in existing:
            op.drop_column("clients", col_name)
