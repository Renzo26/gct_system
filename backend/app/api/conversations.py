import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_redis_service, get_session, get_workshop_id
from app.schemas.conversation import AssignIn, ConversationDetail, ConversationSummary
from app.schemas.label import LabelIn, LabelOut
from app.schemas.message import MessagePage, MessageOut, SendMessageIn
from app.services.conversation_service import conversation_service
from app.services.redis_service import RedisService

router = APIRouter(prefix="/conversations", tags=["conversations"])


async def _get_or_404(
    conv_id: uuid.UUID, workshop_id: uuid.UUID, db: AsyncSession
):
    conv = await conversation_service.get_conversation(db, conv_id, workshop_id)
    if not conv:
        raise HTTPException(status_code=404, detail="Conversa não encontrada")
    return conv


@router.get("", response_model=list[ConversationSummary])
async def list_conversations(
    tab: str = Query("ALL", regex="^(ALL|MINE|UNASSIGNED|RESOLVED)$"),
    agent_id: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    return await conversation_service.list_conversations(
        db, workshop_id=workshop_id, tab=tab, agent_id=agent_id
    )


@router.get("/{conv_id}", response_model=ConversationDetail)
async def get_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    return await _get_or_404(conv_id, workshop_id, db)


@router.get("/{conv_id}/messages", response_model=MessagePage)
async def list_messages(
    conv_id: uuid.UUID,
    page: int = Query(0, ge=0),
    size: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    await _get_or_404(conv_id, workshop_id, db)
    msgs, total = await conversation_service.list_messages(db, conv_id, page, size)
    return MessagePage(
        items=[MessageOut.model_validate(m) for m in msgs],
        total=total,
        page=page,
        size=size,
    )


@router.post("/{conv_id}/messages", response_model=MessageOut, status_code=status.HTTP_201_CREATED)
async def send_message(
    conv_id: uuid.UUID,
    body: SendMessageIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
    redis: RedisService = Depends(get_redis_service),
):
    from app.models.conversation import ConversationStatus
    conv = await _get_or_404(conv_id, workshop_id, db)
    agent_name = conv.assigned_agent_name or "Agente"
    if conv.status != ConversationStatus.HUMAN:
        await conversation_service.set_human(db, conv, redis)
    msg = await conversation_service.send_message(db, conv, body.content, agent_name)
    return MessageOut.model_validate(msg)


@router.patch("/{conv_id}/read", status_code=status.HTTP_204_NO_CONTENT)
async def mark_as_read(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    await conversation_service.mark_as_read(db, conv)


@router.patch("/{conv_id}/reopen", response_model=ConversationDetail)
async def reopen(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    return await conversation_service.reopen(db, conv)


@router.patch("/{conv_id}/name", response_model=ConversationDetail)
async def update_name(
    conv_id: uuid.UUID,
    body: dict,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    name = (body.get("lead_name") or "").strip()
    if not name:
        raise HTTPException(status_code=422, detail="Nome inválido")
    return await conversation_service.update_name(db, conv, name)


@router.patch("/{conv_id}/resolve", response_model=ConversationDetail)
async def resolve(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    return await conversation_service.resolve(db, conv)


@router.patch("/{conv_id}/assign", response_model=ConversationDetail)
async def assign(
    conv_id: uuid.UUID,
    body: AssignIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    return await conversation_service.assign(db, conv, body.agent_id, body.agent_name)


@router.patch("/{conv_id}/human", response_model=ConversationDetail)
async def set_human(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
    redis: RedisService = Depends(get_redis_service),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    return await conversation_service.set_human(db, conv, redis)


@router.patch("/{conv_id}/bot", response_model=ConversationDetail)
async def set_bot(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
    redis: RedisService = Depends(get_redis_service),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    return await conversation_service.set_bot(db, conv, redis)


@router.post("/{conv_id}/labels", response_model=LabelOut, status_code=status.HTTP_201_CREATED)
async def add_label(
    conv_id: uuid.UUID,
    body: LabelIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    label = await conversation_service.add_label(db, conv, body.name, body.color)
    return LabelOut.model_validate(label)


@router.delete("/{conv_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conv_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    conv = await _get_or_404(conv_id, workshop_id, db)
    await conversation_service.delete_conversation(db, conv)


@router.delete("/{conv_id}/labels/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_label(
    conv_id: uuid.UUID,
    label_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    await _get_or_404(conv_id, workshop_id, db)
    removed = await conversation_service.remove_label(db, conv_id, label_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Etiqueta não encontrada")
