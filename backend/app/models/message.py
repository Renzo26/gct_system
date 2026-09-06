import enum
import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class MessageType(str, enum.Enum):
    TEXT = "TEXT"
    IMAGE = "IMAGE"
    AUDIO = "AUDIO"
    DOCUMENT = "DOCUMENT"


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    conversation_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("conversations.id"), nullable=False, index=True
    )
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    type: Mapped[MessageType] = mapped_column(
        Enum(MessageType, name="message_type"),
        nullable=False,
        default=MessageType.TEXT,
    )
    sender_name: Mapped[str] = mapped_column(String(200), nullable=False)
    is_from_lead: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    media_url: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    waha_message_id: Mapped[Optional[str]] = mapped_column(
        String(200), unique=True, nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    conversation: Mapped["Conversation"] = relationship(  # noqa: F821
        "Conversation", back_populates="messages"
    )
