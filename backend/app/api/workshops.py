import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, require_superadmin
from app.models.user import User
from app.models.workshop import Workshop
from app.schemas.workshop import WorkshopAdminOut, WorkshopCreateIn, WorkshopUpdateIn

router = APIRouter(prefix="/workshops", tags=["workshops"])


async def _get_or_404(workshop_id: uuid.UUID, db: AsyncSession) -> Workshop:
    workshop = await db.scalar(select(Workshop).where(Workshop.id == workshop_id))
    if not workshop:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado"
        )
    return workshop


async def _ensure_unique(
    db: AsyncSession, body, current_id: uuid.UUID | None = None
) -> None:
    for field in ("cnpj", "waha_session"):
        value = getattr(body, field)
        if not value:
            continue
        stmt = select(Workshop.id).where(getattr(Workshop, field) == value)
        if current_id is not None:
            stmt = stmt.where(Workshop.id != current_id)
        if await db.scalar(stmt) is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Já existe um cliente com este {field}",
            )


@router.get("", response_model=list[WorkshopAdminOut])
async def list_workshops(
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_superadmin),
):
    result = await db.scalars(select(Workshop).order_by(Workshop.name))
    return result.all()


@router.post("", response_model=WorkshopAdminOut, status_code=status.HTTP_201_CREATED)
async def create_workshop(
    body: WorkshopCreateIn,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_superadmin),
):
    await _ensure_unique(db, body)
    workshop = Workshop(**body.model_dump())
    db.add(workshop)
    await db.commit()
    await db.refresh(workshop)
    return workshop


@router.put("/{workshop_id}", response_model=WorkshopAdminOut)
async def update_workshop(
    workshop_id: uuid.UUID,
    body: WorkshopUpdateIn,
    db: AsyncSession = Depends(get_session),
    _: User = Depends(require_superadmin),
):
    workshop = await _get_or_404(workshop_id, db)
    await _ensure_unique(db, body, current_id=workshop_id)
    for field, value in body.model_dump().items():
        setattr(workshop, field, value)
    await db.commit()
    await db.refresh(workshop)
    return workshop
