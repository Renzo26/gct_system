import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Appointment(Base):
    __tablename__ = "appointments"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workshops.id"), nullable=False, index=True
    )
    data: Mapped[str] = mapped_column(String(10), nullable=False)
    hora: Mapped[str] = mapped_column(String(5), nullable=False)
    titulo: Mapped[str] = mapped_column(String(200), nullable=False)
    cliente: Mapped[str] = mapped_column(String(200), nullable=False)
    veiculo: Mapped[str | None] = mapped_column(String(200), nullable=True)
    telefone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workshop: Mapped["Workshop"] = relationship(  # noqa: F821
        "Workshop", back_populates="appointments"
    )
