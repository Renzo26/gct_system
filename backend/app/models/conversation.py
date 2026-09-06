import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class ConversationStatus(str, enum.Enum):
    BOT = "BOT"
    HUMAN = "HUMAN"
    UNASSIGNED = "UNASSIGNED"
    RESOLVED = "RESOLVED"


class Conversation(Base):
    __tablename__ = "conversations"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("workshops.id", name="fk_conversations_workshop_id"),
        nullable=False,
        index=True,
    )
    waha_chat_id: Mapped[str] = mapped_column(
        String(100), unique=True, nullable=False, index=True
    )
    lead_name: Mapped[str] = mapped_column(String(200), nullable=False)
    lead_phone: Mapped[str] = mapped_column(String(20), nullable=False)
    session: Mapped[str] = mapped_column(String(50), nullable=False, default="Cloudy")
    status: Mapped[ConversationStatus] = mapped_column(
        Enum(ConversationStatus, name="conversation_status"),
        nullable=False,
        default=ConversationStatus.UNASSIGNED,
    )
    assigned_agent_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    assigned_agent_name: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    unread_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    last_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    last_message_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    workshop: Mapped["Workshop"] = relationship(  # noqa: F821
        "Workshop", back_populates="conversations"
    )
    messages: Mapped[list["Message"]] = relationship(  # noqa: F821
        "Message", back_populates="conversation", lazy="select"
    )
    labels: Mapped[list["ConversationLabel"]] = relationship(  # noqa: F821
        "ConversationLabel", back_populates="conversation", cascade="all, delete-orphan"
    )
