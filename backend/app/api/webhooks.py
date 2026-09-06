import json
import logging

from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session
from app.schemas.webhook import WahaWebhookRequest
from app.services.conversation_service import conversation_service

router = APIRouter(tags=["webhooks"])
logger = logging.getLogger(__name__)


@router.post("/webhooks/waha", status_code=status.HTTP_204_NO_CONTENT)
async def waha_webhook(
    request: Request,
    body: WahaWebhookRequest,
    db: AsyncSession = Depends(get_session),
) -> None:
    raw = await request.body()
    logger.warning("WAHA_RAW_PAYLOAD: %s", raw.decode("utf-8", errors="replace"))
    await conversation_service.process_webhook(db, body)
