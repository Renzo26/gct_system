from typing import Optional
from pydantic import BaseModel


class WorkshopSettingsIn(BaseModel):
    name: str
    cnpj: Optional[str] = None
    phone: Optional[str] = None
    email: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    cep: Optional[str] = None
    business_hours: Optional[str] = None
    services: Optional[str] = None
    bot_info: Optional[str] = None


class WorkshopSettingsOut(WorkshopSettingsIn):
    model_config = {"from_attributes": True}
