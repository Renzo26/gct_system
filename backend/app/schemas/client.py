import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class ClientIn(BaseModel):
    nome: str
    telefone: Optional[str] = None
    veiculo: Optional[str] = None
    placa: Optional[str] = None
    ultimo_atendimento: Optional[str] = None
    ano_veiculo: Optional[str] = None
    servico_realizado: Optional[str] = None
    resumo: Optional[str] = None


class ClientOut(ClientIn):
    id: uuid.UUID
    workshop_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
