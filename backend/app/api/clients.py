import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_workshop_id
from app.models.client import Client
from app.schemas.client import ClientIn, ClientOut

router = APIRouter(prefix="/clients", tags=["clients"])


async def _get_or_404(client_id: uuid.UUID, workshop_id: uuid.UUID, db: AsyncSession) -> Client:
    client = await db.scalar(
        select(Client).where(Client.id == client_id, Client.workshop_id == workshop_id)
    )
    if not client:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Cliente não encontrado")
    return client


@router.get("", response_model=list[ClientOut])
async def list_clients(
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    result = await db.scalars(select(Client).where(Client.workshop_id == workshop_id))
    return result.all()


@router.post("", response_model=ClientOut, status_code=status.HTTP_201_CREATED)
async def create_client(
    body: ClientIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    client = Client(workshop_id=workshop_id, **body.model_dump())
    db.add(client)
    await db.commit()
    await db.refresh(client)
    return client


@router.put("/{client_id}", response_model=ClientOut)
async def update_client(
    client_id: uuid.UUID,
    body: ClientIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    client = await _get_or_404(client_id, workshop_id, db)
    for field, value in body.model_dump().items():
        setattr(client, field, value)
    await db.commit()
    await db.refresh(client)
    return client


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_client(
    client_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    client = await _get_or_404(client_id, workshop_id, db)
    await db.delete(client)
    await db.commit()
