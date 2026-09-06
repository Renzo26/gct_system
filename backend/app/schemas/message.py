import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.message import MessageType


class MessageOut(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    content: Optional[str] = None
    type: MessageType
    sender_name: str
    is_from_lead: bool
    media_url: Optional[str] = None
    waha_message_id: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class SendMessageIn(BaseModel):
    content: str


class MessagePage(BaseModel):
    items: list[MessageOut]
    total: int
    page: int
    size: int
