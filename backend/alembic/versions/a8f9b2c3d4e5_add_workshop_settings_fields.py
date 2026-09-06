"""add_workshop_settings_fields

Revision ID: a8f9b2c3d4e5
Revises: 65d080f796d0
Create Date: 2026-05-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a8f9b2c3d4e5'
down_revision: Union[str, None] = '65d080f796d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

_NEW_COLS = [
    ("address",        sa.String(300)),
    ("city",           sa.String(100)),
    ("state",          sa.String(2)),
    ("cep",            sa.String(10)),
    ("business_hours", sa.String(300)),
    ("services",       sa.String(2000)),
    ("bot_info",       sa.String(2000)),
]


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("workshops")}
    for col_name, col_type in _NEW_COLS:
        if col_name not in existing:
            op.add_column("workshops", sa.Column(col_name, col_type, nullable=True))


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing = {c["name"] for c in inspector.get_columns("workshops")}
    for col_name, _ in _NEW_COLS:
        if col_name in existing:
            op.drop_column("workshops", col_name)
