import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_workshop_id
from app.models.workshop import Workshop
from app.schemas.workshop_settings import WorkshopSettingsIn, WorkshopSettingsOut

router = APIRouter(prefix="/workshop", tags=["workshop"])


@router.get("", response_model=WorkshopSettingsOut)
async def get_settings(
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    workshop = await db.scalar(select(Workshop).where(Workshop.id == workshop_id))
    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oficina não encontrada")
    return workshop


@router.put("", response_model=WorkshopSettingsOut)
async def update_settings(
    body: WorkshopSettingsIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    workshop = await db.scalar(select(Workshop).where(Workshop.id == workshop_id))
    if not workshop:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Oficina não encontrada")
    for field, value in body.model_dump().items():
        setattr(workshop, field, value)
    await db.commit()
    await db.refresh(workshop)
    return workshop
