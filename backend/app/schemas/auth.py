import uuid
from typing import Optional

from pydantic import BaseModel, EmailStr


class LoginIn(BaseModel):
    email: EmailStr
    password: str


class RefreshIn(BaseModel):
    refresh_token: str


class SelectWorkshopIn(BaseModel):
    workshop_id: uuid.UUID


class WorkshopOut(BaseModel):
    id: uuid.UUID
    name: str

    model_config = {"from_attributes": True}


class WorkshopListItemOut(BaseModel):
    id: uuid.UUID
    name: str
    city: Optional[str] = None
    state: Optional[str] = None

    model_config = {"from_attributes": True}


class UserOut(BaseModel):
    id: uuid.UUID
    name: str
    email: str
    role: str
    workshop_id: Optional[uuid.UUID] = None

    model_config = {"from_attributes": True}


class TokenOut(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut
    workshop: Optional[WorkshopOut] = None
