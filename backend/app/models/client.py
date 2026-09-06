import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class Client(Base):
    __tablename__ = "clients"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    workshop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workshops.id"), nullable=False, index=True
    )
    nome: Mapped[str] = mapped_column(String(200), nullable=False)
    telefone: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    veiculo: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    placa: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ultimo_atendimento: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    ano_veiculo: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    servico_realizado: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    resumo: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    workshop: Mapped["Workshop"] = relationship(  # noqa: F821
        "Workshop", back_populates="clients"
    )
