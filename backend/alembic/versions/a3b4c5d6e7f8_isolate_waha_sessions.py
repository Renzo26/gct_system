"""isola clientes com sessoes WAHA diferentes

Revision ID: a3b4c5d6e7f8
Revises: f2a3b4c5d6e7
Create Date: 2026-09-15

- conversations.waha_chat_id deixa de ser unico globalmente e passa a ser
  unico por cliente: o mesmo contato falando com dois clientes derrubava as
  mensagens do segundo.
- messages.waha_message_id passa a ser unico por conversa.
- workshops.bot_name guarda o prefixo da chave de pausa do bot no Redis. Os
  clientes existentes recebem "CloudSolutions", o valor que ja estava fixo no
  codigo, para nao mudar o comportamento dos fluxos n8n atuais.
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "a3b4c5d6e7f8"
down_revision: Union[str, None] = "f2a3b4c5d6e7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # IF EXISTS: o banco pode ter nascido de create_all em vez das migracoes,
    # e ai a unicidade existe como constraint em vez de indice.
    op.execute("ALTER TABLE conversations DROP CONSTRAINT IF EXISTS conversations_waha_chat_id_key")
    op.execute("DROP INDEX IF EXISTS ix_conversations_waha_chat_id")
    op.create_index("ix_conversations_waha_chat_id", "conversations", ["waha_chat_id"])
    op.create_unique_constraint(
        "uq_conversations_workshop_chat", "conversations", ["workshop_id", "waha_chat_id"]
    )

    op.execute("ALTER TABLE messages DROP CONSTRAINT IF EXISTS messages_waha_message_id_key")
    op.execute("DROP INDEX IF EXISTS ix_messages_waha_message_id")
    op.create_index("ix_messages_waha_message_id", "messages", ["waha_message_id"])
    op.create_unique_constraint(
        "uq_messages_conversation_waha_id", "messages", ["conversation_id", "waha_message_id"]
    )

    op.add_column("workshops", sa.Column("bot_name", sa.String(length=100), nullable=True))
    op.execute("UPDATE workshops SET bot_name = 'CloudSolutions'")


def downgrade() -> None:
    op.drop_column("workshops", "bot_name")

    op.drop_constraint("uq_messages_conversation_waha_id", "messages", type_="unique")
    op.drop_index("ix_messages_waha_message_id", table_name="messages")
    op.create_index("ix_messages_waha_message_id", "messages", ["waha_message_id"], unique=True)

    op.drop_constraint("uq_conversations_workshop_chat", "conversations", type_="unique")
    op.drop_index("ix_conversations_waha_chat_id", table_name="conversations")
    op.create_index("ix_conversations_waha_chat_id", "conversations", ["waha_chat_id"], unique=True)
