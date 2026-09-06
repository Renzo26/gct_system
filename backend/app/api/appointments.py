import re
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_workshop_id
from app.models.appointment import Appointment
from app.models.conversation import Conversation
from app.models.workshop import Workshop
from app.schemas.appointment import AppointmentIn, AppointmentOut
from app.services.conversation_service import conversation_service
from app.services.waha_service import waha_service

router = APIRouter(prefix="/appointments", tags=["appointments"])


async def _get_or_404(
    appointment_id: uuid.UUID, workshop_id: uuid.UUID, db: AsyncSession
) -> Appointment:
    appointment = await db.scalar(
        select(Appointment).where(
            Appointment.id == appointment_id, Appointment.workshop_id == workshop_id
        )
    )
    if not appointment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Agendamento não encontrado"
        )
    return appointment


@router.get("", response_model=list[AppointmentOut])
async def list_appointments(
    data: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    stmt = select(Appointment).where(Appointment.workshop_id == workshop_id)
    if data:
        stmt = stmt.where(Appointment.data == data)
    result = await db.scalars(stmt)
    return result.all()


@router.post("", response_model=AppointmentOut, status_code=status.HTTP_201_CREATED)
async def create_appointment(
    body: AppointmentIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    appointment = Appointment(workshop_id=workshop_id, **body.model_dump())
    db.add(appointment)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.put("/{appointment_id}", response_model=AppointmentOut)
async def update_appointment(
    appointment_id: uuid.UUID,
    body: AppointmentIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    appointment = await _get_or_404(appointment_id, workshop_id, db)
    for field, value in body.model_dump().items():
        setattr(appointment, field, value)
    await db.commit()
    await db.refresh(appointment)
    return appointment


@router.delete("/{appointment_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_appointment(
    appointment_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    appointment = await _get_or_404(appointment_id, workshop_id, db)

    telefone = appointment.telefone
    cliente = appointment.cliente
    titulo = appointment.titulo
    data = appointment.data
    hora = appointment.hora

    await db.delete(appointment)
    await db.commit()

    if not telefone:
        return

    digits = re.sub(r"\D", "", telefone.split("@")[0])
    if not digits:
        return

    waha_chat_id = f"{digits}@c.us"

    workshop = await db.scalar(select(Workshop).where(Workshop.id == workshop_id))
    workshop_name = workshop.name if workshop else "Oficina"

    msg_text = (
        f"Olá, {cliente}! 👋 Passando para informar que seu agendamento de "
        f"{titulo} - {cliente} marcado para o dia {data} às {hora} foi cancelado.  "
        f"Caso queira remarcar, é só nos chamar aqui! 😊 — {workshop_name}"
    )

    conv = await db.scalar(
        select(Conversation)
        .where(Conversation.waha_chat_id == waha_chat_id)
        .where(Conversation.workshop_id == workshop_id)
    )
    if conv:
        # Conversa encontrada: envia pelo send_message (salva no DB + manda pelo WAHA)
        await conversation_service.send_message(db, conv, msg_text, "Bot")
        await db.commit()
    else:
        # Conversa não encontrada: envia pelo WAHA diretamente para o cliente receber a msg
        await waha_service.send_text(
            waha_chat_id, msg_text, session=workshop.waha_session if workshop else None
        )
