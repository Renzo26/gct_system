import uuid
from typing import Optional
from pydantic import BaseModel


class LabelOut(BaseModel):
    id: uuid.UUID
    name: str
    color: Optional[str] = None

    model_config = {"from_attributes": True}


class LabelIn(BaseModel):
    name: str
    color: Optional[str] = None
