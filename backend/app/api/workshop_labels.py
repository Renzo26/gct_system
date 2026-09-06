import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_workshop_id
from app.models.workshop_label import WorkshopLabel
from app.schemas.workshop_label import WorkshopLabelIn, WorkshopLabelOut

router = APIRouter(prefix="/labels", tags=["labels"])


async def _get_or_404(
    label_id: uuid.UUID, workshop_id: uuid.UUID, db: AsyncSession
) -> WorkshopLabel:
    label = await db.scalar(
        select(WorkshopLabel).where(
            WorkshopLabel.id == label_id, WorkshopLabel.workshop_id == workshop_id
        )
    )
    if not label:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Etiqueta não encontrada")
    return label


@router.get("", response_model=list[WorkshopLabelOut])
async def list_labels(
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    result = await db.scalars(
        select(WorkshopLabel).where(WorkshopLabel.workshop_id == workshop_id)
    )
    return result.all()


@router.post("", response_model=WorkshopLabelOut, status_code=status.HTTP_201_CREATED)
async def create_label(
    body: WorkshopLabelIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    label = WorkshopLabel(workshop_id=workshop_id, **body.model_dump())
    db.add(label)
    await db.commit()
    await db.refresh(label)
    return label


@router.put("/{label_id}", response_model=WorkshopLabelOut)
async def update_label(
    label_id: uuid.UUID,
    body: WorkshopLabelIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    label = await _get_or_404(label_id, workshop_id, db)
    for field, value in body.model_dump().items():
        setattr(label, field, value)
    await db.commit()
    await db.refresh(label)
    return label


@router.delete("/{label_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_label(
    label_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    label = await _get_or_404(label_id, workshop_id, db)
    await db.delete(label)
    await db.commit()
