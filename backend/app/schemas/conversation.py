import uuid
from datetime import datetime
from typing import Optional
from pydantic import BaseModel

from app.models.conversation import ConversationStatus
from app.schemas.label import LabelOut


class ConversationSummary(BaseModel):
    id: uuid.UUID
    waha_chat_id: str
    lead_name: str
    lead_phone: str
    session: str
    status: ConversationStatus
    assigned_agent_id: Optional[str] = None
    assigned_agent_name: Optional[str] = None
    unread_count: int
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime
    labels: list[LabelOut] = []

    model_config = {"from_attributes": True}


class ConversationDetail(ConversationSummary):
    updated_at: datetime


class AssignIn(BaseModel):
    agent_id: str
    agent_name: str
