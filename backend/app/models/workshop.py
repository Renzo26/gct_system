import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Workshop(Base):
    __tablename__ = "workshops"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    cnpj: Mapped[Optional[str]] = mapped_column(String(20), nullable=True, unique=True)
    phone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    email: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    address: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    city: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(2), nullable=True)
    cep: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    business_hours: Mapped[Optional[str]] = mapped_column(String(300), nullable=True)
    services: Mapped[Optional[str]] = mapped_column(String(2000), nullable=True)
    bot_info: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    waha_session: Mapped[Optional[str]] = mapped_column(String(50), nullable=True, unique=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    users: Mapped[list["User"]] = relationship(  # noqa: F821
        "User", back_populates="workshop", cascade="all, delete-orphan"
    )
    clients: Mapped[list["Client"]] = relationship(  # noqa: F821
        "Client", back_populates="workshop", cascade="all, delete-orphan"
    )
    appointments: Mapped[list["Appointment"]] = relationship(  # noqa: F821
        "Appointment", back_populates="workshop", cascade="all, delete-orphan"
    )
    labels: Mapped[list["WorkshopLabel"]] = relationship(  # noqa: F821
        "WorkshopLabel", back_populates="workshop", cascade="all, delete-orphan"
    )
    conversations: Mapped[list["Conversation"]] = relationship(  # noqa: F821
        "Conversation", back_populates="workshop", cascade="all, delete-orphan"
    )
