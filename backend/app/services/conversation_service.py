import logging
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation, ConversationStatus
from app.models.label import ConversationLabel
from app.models.message import Message, MessageType
from app.models.workshop import Workshop
from app.schemas.webhook import WahaWebhookRequest
from app.services.sse_service import broadcaster
from app.services.waha_service import is_sendable_chat_id, waha_service

logger = logging.getLogger(__name__)


def _normalize_chat_id(raw: str) -> str:
    return raw.replace("@s.whatsapp.net", "@c.us")


def _detect_type(payload) -> MessageType:
    if not payload.hasMedia or payload.media is None:
        return MessageType.TEXT
    mime = (payload.media.mimetype or "").lower()
    if mime.startswith("image"):
        return MessageType.IMAGE
    if mime.startswith("audio"):
        return MessageType.AUDIO
    return MessageType.DOCUMENT


class ConversationService:

    async def process_webhook(self, db: AsyncSession, body: WahaWebhookRequest) -> None:
        p = body.payload
        is_from_me = bool(p.fromMe)

        # Resolve a oficina pela sessão WAHA do payload. Sem oficina vinculada,
        # ignoramos o evento (evita criar conversas órfãs sem dono).
        session_name = (body.session or "").strip()
        if not session_name:
            logger.warning("WAHA webhook sem 'session' — ignorando")
            return
        workshop = await db.scalar(
            select(Workshop).where(Workshop.waha_session == session_name)
        )
        if workshop is None:
            logger.warning(
                "WAHA webhook | sessão %r não vinculada a nenhuma oficina — ignorando",
                session_name,
            )
            return

        # chatId é o identificador canônico do WAHA (funciona para mensagens enviadas e recebidas).
        # Para mensagens enviadas via API externa (ex: n8n), "to" pode estar ausente — chatId resolve isso.
        if p.chat_id:
            raw_chat_id = p.chat_id
        elif is_from_me:
            raw_chat_id = p.to or p.from_field or ""
        else:
            raw_chat_id = p.from_field or ""

        waha_chat_id = _normalize_chat_id(raw_chat_id)
        if not waha_chat_id:
            return

        # Status/stories de contatos chegam como evento de mensagem comum, com
        # chatId "status@broadcast". Criar conversa a partir disso faz o bot
        # "responder" o status — e essa resposta sai publicada como status na
        # conta do cliente, visivel para todos os contatos dele.
        if not is_sendable_chat_id(waha_chat_id):
            logger.info(
                "WAHA webhook | chat=%s nao e conversa enderecavel — ignorando",
                waha_chat_id,
            )
            return

        existing_msg = await db.scalar(
            select(Message).where(Message.waha_message_id == p.id)
        )
        if existing_msg:
            return

        conv = await db.scalar(
            select(Conversation)
            .where(Conversation.waha_chat_id == waha_chat_id)
            .where(Conversation.workshop_id == workshop.id)
            .options(selectinload(Conversation.labels))
        )

        # Se não existe conversa e é mensagem do bot, ignora (não cria conversa sem lead)
        if conv is None and is_from_me:
            return

        d = p.inner_data
        info = d.info if d else None
        # Nome: tenta _data.Info.PushName, _data.PushName, notifyName
        push_in_info = info.pushName if info else None
        push_in_data = d.pushName if d else None
        display_name = (
            push_in_info
            or push_in_data
            or p.notifyName
            or (d.notifyName if d else None)
            or ""
        )
        # Telefone real: _data.Info.SenderAlt → strip ":<device>@<server>"
        raw_alt = info.senderAlt if info else None
        if raw_alt:
            lead_phone = raw_alt.split(":")[0].split("@")[0]
        else:
            lead_phone = waha_chat_id.split("@")[0]

        lead_name = display_name or lead_phone

        logger.info(
            "WAHA webhook | chat=%s fromMe=%s push_info=%r push_data=%r notify=%r senderAlt=%r → name=%r phone=%s",
            waha_chat_id, is_from_me, push_in_info, push_in_data,
            p.notifyName, raw_alt, lead_name, lead_phone
        )

        if conv is None:
            try:
                conv = Conversation(
                    workshop_id=workshop.id,
                    waha_chat_id=waha_chat_id,
                    lead_name=lead_name,
                    lead_phone=lead_phone,
                    session=session_name,
                    status=ConversationStatus.UNASSIGNED,
                )
                db.add(conv)
                await db.flush()
            except Exception:
                await db.rollback()
                conv = await db.scalar(
                    select(Conversation)
                    .where(Conversation.waha_chat_id == waha_chat_id)
                    .where(Conversation.workshop_id == workshop.id)
                    .options(selectinload(Conversation.labels))
                )
                if conv is None:
                    return
        else:
            # Atualiza nome se o atual parece número (LID ou telefone) e chegou nome real
            name_is_number = conv.lead_name.replace("+", "").replace(" ", "").isdigit()
            if display_name and name_is_number:
                conv.lead_name = lead_name
            if raw_alt and conv.lead_phone != lead_phone:
                conv.lead_phone = lead_phone

        sender_name = "Bot" if is_from_me else lead_name

        # Persiste atualizações de lead_name/lead_phone na transação principal
        await db.flush()

        # Insert da mensagem em savepoint — duplicate não derruba updates anteriores
        from sqlalchemy.exc import IntegrityError
        try:
            async with db.begin_nested():
                msg = Message(
                    conversation_id=conv.id,
                    content=p.body,
                    type=_detect_type(p),
                    sender_name=sender_name,
                    is_from_lead=not is_from_me,
                    media_url=p.media.url if p.media else None,
                    waha_message_id=p.id,
                )
                db.add(msg)
                conv.last_message = p.body or ""
                conv.last_message_at = datetime.now(timezone.utc)
                if not is_from_me:
                    conv.unread_count = (conv.unread_count or 0) + 1
                await db.flush()
        except IntegrityError:
            logger.warning("WAHA mensagem duplicada %s — ignorando", p.id)
            return

        await broadcaster.publish("message", {
            "workshopId": str(conv.workshop_id),
            "conversationId": str(conv.id),
            "messageId": str(msg.id),
            "content": msg.content,
            "type": msg.type.value,
            "senderName": msg.sender_name,
            "isFromLead": msg.is_from_lead,
            "createdAt": msg.created_at.isoformat() if msg.created_at else None,
        }, workshop_id=str(conv.workshop_id))
        await broadcaster.publish("conversation", {
            "workshopId": str(conv.workshop_id),
            "id": str(conv.id),
            "leadName": conv.lead_name,
            "status": conv.status.value,
            "unreadCount": conv.unread_count,
            "lastMessage": conv.last_message,
        }, workshop_id=str(conv.workshop_id))

    async def list_conversations(
        self,
        db: AsyncSession,
        workshop_id: uuid.UUID,
        tab: str = "ALL",
        agent_id: Optional[str] = None,
    ) -> list[Conversation]:
        q = (
            select(Conversation)
            .where(Conversation.workshop_id == workshop_id)
            .options(selectinload(Conversation.labels))
        )

        if tab == "RESOLVED":
            q = q.where(Conversation.status == ConversationStatus.RESOLVED)
        elif tab == "UNASSIGNED":
            q = q.where(Conversation.status == ConversationStatus.UNASSIGNED)
        elif tab == "MINE" and agent_id:
            q = q.where(Conversation.assigned_agent_id == agent_id)
        else:
            q = q.where(Conversation.status != ConversationStatus.RESOLVED)

        q = q.order_by(Conversation.last_message_at.desc().nullslast())
        result = await db.scalars(q)
        return list(result.all())

    async def get_conversation(
        self,
        db: AsyncSession,
        conv_id: uuid.UUID,
        workshop_id: uuid.UUID,
    ) -> Optional[Conversation]:
        return await db.scalar(
            select(Conversation)
            .where(Conversation.id == conv_id)
            .where(Conversation.workshop_id == workshop_id)
            .options(selectinload(Conversation.labels))
        )

    async def list_messages(
        self, db: AsyncSession, conv_id: uuid.UUID, page: int = 0, size: int = 50
    ) -> tuple[list[Message], int]:
        total = await db.scalar(
            select(func.count(Message.id)).where(Message.conversation_id == conv_id)
        )
        total = total or 0
        # página 0 = últimas `size` mensagens; página 1 = anteriores; etc.
        offset = max(0, total - size * (page + 1))
        msgs = await db.scalars(
            select(Message)
            .where(Message.conversation_id == conv_id)
            .order_by(Message.created_at.asc())
            .offset(offset)
            .limit(size)
        )
        return list(msgs.all()), total

    async def send_message(
        self,
        db: AsyncSession,
        conv: Conversation,
        content: str,
        agent_name: str = "Agente",
    ) -> Message:
        waha_msg_id = await waha_service.send_text(
            conv.waha_chat_id, content, session=conv.session
        )

        msg = Message(
            conversation_id=conv.id,
            content=content,
            type=MessageType.TEXT,
            sender_name=agent_name,
            is_from_lead=False,
            waha_message_id=waha_msg_id,
        )
        db.add(msg)

        conv.last_message = content
        conv.last_message_at = datetime.now(timezone.utc)
        await db.flush()

        wid = str(conv.workshop_id)
        await broadcaster.publish("message", {
            "workshopId": wid,
            "conversationId": str(conv.id),
            "messageId": str(msg.id),
            "content": msg.content,
            "type": msg.type.value,
            "senderName": msg.sender_name,
            "isFromLead": False,
            "createdAt": msg.created_at.isoformat() if msg.created_at else None,
        }, workshop_id=wid)
        return msg

    async def mark_as_read(self, db: AsyncSession, conv: Conversation) -> None:
        conv.unread_count = 0
        await db.flush()
        wid = str(conv.workshop_id)
        await broadcaster.publish(
            "conversation",
            {"workshopId": wid, "id": str(conv.id), "unreadCount": 0},
            workshop_id=wid,
        )

    async def reopen(
        self, db: AsyncSession, conv: Conversation, redis_service
    ) -> Conversation:
        # Volta para a fila do bot: a pausa nao expira sozinha, entao reabrir
        # tem que liberar o bot explicitamente.
        await redis_service.del_human_block(conv.waha_chat_id)
        conv.status = ConversationStatus.UNASSIGNED
        conv.assigned_agent_id = None
        conv.assigned_agent_name = None
        await db.flush()
        await db.refresh(conv)
        wid = str(conv.workshop_id)
        await broadcaster.publish(
            "conversation",
            {"workshopId": wid, "id": str(conv.id), "status": conv.status.value},
            workshop_id=wid,
        )
        return conv

    async def update_name(self, db: AsyncSession, conv: Conversation, lead_name: str) -> Conversation:
        conv.lead_name = lead_name.strip()
        await db.flush()
        await db.refresh(conv)
        wid = str(conv.workshop_id)
        await broadcaster.publish(
            "conversation",
            {"workshopId": wid, "id": str(conv.id), "leadName": conv.lead_name},
            workshop_id=wid,
        )
        return conv

    async def resolve(
        self, db: AsyncSession, conv: Conversation, redis_service
    ) -> Conversation:
        # Atendimento encerrado: libera o bot para atender a proxima duvida
        # desse contato, senao ele ficaria calado para sempre.
        await redis_service.del_human_block(conv.waha_chat_id)
        conv.status = ConversationStatus.RESOLVED
        conv.unread_count = 0
        await db.flush()
        await db.refresh(conv)
        wid = str(conv.workshop_id)
        await broadcaster.publish(
            "conversation",
            {"workshopId": wid, "id": str(conv.id), "status": conv.status.value},
            workshop_id=wid,
        )
        return conv

    async def assign(
        self, db: AsyncSession, conv: Conversation, agent_id: str, agent_name: str
    ) -> Conversation:
        conv.assigned_agent_id = agent_id
        conv.assigned_agent_name = agent_name
        conv.status = ConversationStatus.HUMAN
        await db.flush()
        await db.refresh(conv)
        wid = str(conv.workshop_id)
        await broadcaster.publish("conversation", {
            "workshopId": wid,
            "id": str(conv.id),
            "status": conv.status.value,
            "assignedAgentId": agent_id,
            "assignedAgentName": agent_name,
        }, workshop_id=wid)
        return conv

    async def set_human(
        self, db: AsyncSession, conv: Conversation, redis_service
    ) -> Conversation:
        await redis_service.set_human_block(conv.waha_chat_id)
        logger.info(
            "set_human | chat=%s redis_key=%s",
            conv.waha_chat_id, redis_service._key(conv.waha_chat_id),
        )
        conv.status = ConversationStatus.HUMAN
        await db.flush()
        await db.refresh(conv)
        wid = str(conv.workshop_id)
        await broadcaster.publish(
            "conversation",
            {"workshopId": wid, "id": str(conv.id), "status": conv.status.value},
            workshop_id=wid,
        )
        return conv

    async def set_bot(
        self, db: AsyncSession, conv: Conversation, redis_service
    ) -> Conversation:
        await redis_service.del_human_block(conv.waha_chat_id)
        conv.status = ConversationStatus.BOT
        await db.flush()
        await db.refresh(conv)
        wid = str(conv.workshop_id)
        await broadcaster.publish(
            "conversation",
            {"workshopId": wid, "id": str(conv.id), "status": conv.status.value},
            workshop_id=wid,
        )
        return conv

    async def add_label(
        self, db: AsyncSession, conv: Conversation, name: str, color: Optional[str]
    ) -> ConversationLabel:
        label = ConversationLabel(conversation_id=conv.id, name=name, color=color)
        db.add(label)
        await db.flush()
        return label

    async def remove_label(
        self, db: AsyncSession, conv_id: uuid.UUID, label_id: uuid.UUID
    ) -> bool:
        label = await db.scalar(
            select(ConversationLabel).where(
                ConversationLabel.id == label_id,
                ConversationLabel.conversation_id == conv_id,
            )
        )
        if not label:
            return False
        await db.delete(label)
        await db.flush()
        return True

    async def delete_conversation(self, db: AsyncSession, conv: Conversation) -> None:
        from sqlalchemy import delete as sa_delete
        from app.models.message import Message
        await db.execute(sa_delete(Message).where(Message.conversation_id == conv.id))
        await db.delete(conv)
        await db.flush()


conversation_service = ConversationService()
