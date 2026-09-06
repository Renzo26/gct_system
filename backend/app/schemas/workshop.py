import uuid
from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class WorkshopCreateIn(BaseModel):
    name: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    waha_session: Optional[str] = None


class WorkshopUpdateIn(BaseModel):
    name: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    waha_session: Optional[str] = None


class WorkshopAdminOut(BaseModel):
    id: uuid.UUID
    name: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    waha_session: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}
