from typing import Optional
from pydantic import BaseModel, Field


class WahaMediaPayload(BaseModel):
    url: Optional[str] = None
    mimetype: Optional[str] = None


class WahaInnerInfo(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}

    senderAlt: Optional[str] = Field(None, alias="SenderAlt")
    pushName: Optional[str] = Field(None, alias="PushName")


class WahaInnerData(BaseModel):
    model_config = {"extra": "allow", "populate_by_name": True}

    notifyName: Optional[str] = None
    pushName: Optional[str] = Field(None, alias="PushName")
    info: Optional[WahaInnerInfo] = Field(None, alias="Info")


class WahaMessagePayload(BaseModel):
    model_config = {"populate_by_name": True, "extra": "allow"}

    id: str
    from_field: Optional[str] = Field(None, alias="from")
    to: Optional[str] = None
    chat_id: Optional[str] = Field(None, alias="chatId")
    body: Optional[str] = None
    fromMe: bool = False
    hasMedia: bool = False
    notifyName: Optional[str] = None
    media: Optional[WahaMediaPayload] = None
    inner_data: Optional[WahaInnerData] = Field(None, alias="_data")


class WahaWebhookRequest(BaseModel):
    model_config = {"extra": "allow"}

    event: Optional[str] = None
    session: Optional[str] = None
    payload: WahaMessagePayload
