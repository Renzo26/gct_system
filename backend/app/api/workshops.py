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


def _normalize(body) -> dict:
    data = body.model_dump()
    for field in ("waha_session", "bot_name"):
        data[field] = (data[field] or "").strip() or None
    # Sem Botname explicito, o fluxo n8n do cliente deve usar a propria sessao.
    data["bot_name"] = data["bot_name"] or data["waha_session"]
    return data


async def _ensure_unique(
    db: AsyncSession, data: dict, current: Workshop | None = None
) -> None:
    for field in ("cnpj", "waha_session", "bot_name"):
        value = data[field]
        if not value or (current is not None and getattr(current, field) == value):
            continue
        stmt = select(Workshop.id).where(getattr(Workshop, field) == value)
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
    data = _normalize(body)
    await _ensure_unique(db, data)
    workshop = Workshop(**data)
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
    data = _normalize(body)
    await _ensure_unique(db, data, current=workshop)
    for field, value in data.items():
        setattr(workshop, field, value)
    await db.commit()
    await db.refresh(workshop)
    return workshop
