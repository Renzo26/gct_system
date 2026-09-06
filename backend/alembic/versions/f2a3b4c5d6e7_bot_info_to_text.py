"""bot_info: String(2000) -> Text

Revision ID: f2a3b4c5d6e7
Revises: e1f2a3b4c5d6
Create Date: 2026-09-06

O prompt do bot de um cliente passa facilmente de 2000 caracteres
(o script do Dr. Heberth tem ~15 mil), então o campo precisa ser TEXT.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "f2a3b4c5d6e7"
down_revision: Union[str, None] = "e1f2a3b4c5d6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column(
        "workshops",
        "bot_info",
        existing_type=sa.String(length=2000),
        type_=sa.Text(),
        existing_nullable=True,
    )


def downgrade() -> None:
    op.execute("UPDATE workshops SET bot_info = left(bot_info, 2000)")
    op.alter_column(
        "workshops",
        "bot_info",
        existing_type=sa.Text(),
        type_=sa.String(length=2000),
        existing_nullable=True,
    )
