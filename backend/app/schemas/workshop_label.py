import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WorkshopLabelIn(BaseModel):
    nome: str
    cor: Optional[str] = None
    descricao: Optional[str] = None


class WorkshopLabelOut(WorkshopLabelIn):
    id: uuid.UUID
    workshop_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}
