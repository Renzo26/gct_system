"""add_workshop_id_to_conversations

Revision ID: c7f1a9b2d3e4
Revises: a1b2c3d4e5f6
Create Date: 2026-05-22 00:00:00.000000

Adiciona `waha_session` em workshops e `workshop_id` em conversations.
Backfill: atribui todas as conversas existentes à oficina mais antiga
(CloudySolutions) e define a `waha_session = 'Cloudy'` nela.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c7f1a9b2d3e4'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    workshop_cols = {c["name"] for c in inspector.get_columns("workshops")}
    if "waha_session" not in workshop_cols:
        op.add_column(
            "workshops",
            sa.Column("waha_session", sa.String(length=50), nullable=True),
        )
        op.create_unique_constraint(
            "uq_workshops_waha_session", "workshops", ["waha_session"]
        )

    conv_cols = {c["name"] for c in inspector.get_columns("conversations")}
    if "workshop_id" not in conv_cols:
        op.add_column(
            "conversations",
            sa.Column("workshop_id", sa.UUID(), nullable=True),
        )

    # Backfill: pega a oficina mais antiga como destino das conversas existentes
    oldest_id = conn.execute(
        sa.text("SELECT id FROM workshops ORDER BY created_at ASC LIMIT 1")
    ).scalar()

    if oldest_id is not None:
        # define waha_session = 'Cloudy' na oficina mais antiga, se ainda não estiver definida
        conn.execute(
            sa.text(
                "UPDATE workshops SET waha_session = 'Cloudy' "
                "WHERE id = :wid AND waha_session IS NULL"
            ),
            {"wid": oldest_id},
        )
        # atribui todas as conversas órfãs à oficina mais antiga
        conn.execute(
            sa.text(
                "UPDATE conversations SET workshop_id = :wid "
                "WHERE workshop_id IS NULL"
            ),
            {"wid": oldest_id},
        )

    # Aplica NOT NULL + FK + índice somente se houver conversas (ou se a coluna foi recém-criada)
    # Se não existir oficina ainda, pula NOT NULL (cenário de banco vazio)
    has_rows = conn.execute(sa.text("SELECT COUNT(*) FROM conversations")).scalar()
    if oldest_id is not None or not has_rows:
        op.alter_column("conversations", "workshop_id", nullable=False)

    fks = {fk["name"] for fk in inspector.get_foreign_keys("conversations")}
    if "fk_conversations_workshop_id" not in fks:
        op.create_foreign_key(
            "fk_conversations_workshop_id",
            "conversations",
            "workshops",
            ["workshop_id"],
            ["id"],
        )

    idx = {i["name"] for i in inspector.get_indexes("conversations")}
    if "ix_conversations_workshop_id" not in idx:
        op.create_index(
            "ix_conversations_workshop_id",
            "conversations",
            ["workshop_id"],
        )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    idx = {i["name"] for i in inspector.get_indexes("conversations")}
    if "ix_conversations_workshop_id" in idx:
        op.drop_index("ix_conversations_workshop_id", table_name="conversations")

    fks = {fk["name"] for fk in inspector.get_foreign_keys("conversations")}
    if "fk_conversations_workshop_id" in fks:
        op.drop_constraint(
            "fk_conversations_workshop_id", "conversations", type_="foreignkey"
        )

    conv_cols = {c["name"] for c in inspector.get_columns("conversations")}
    if "workshop_id" in conv_cols:
        op.drop_column("conversations", "workshop_id")

    uqs = {u["name"] for u in inspector.get_unique_constraints("workshops")}
    if "uq_workshops_waha_session" in uqs:
        op.drop_constraint(
            "uq_workshops_waha_session", "workshops", type_="unique"
        )

    workshop_cols = {c["name"] for c in inspector.get_columns("workshops")}
    if "waha_session" in workshop_cols:
        op.drop_column("workshops", "waha_session")
