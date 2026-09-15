import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_session, get_workshop_id, _bearer
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.models.user import User, UserRole
from app.models.user_workshop_access import UserWorkshopAccess
from app.schemas.auth import UserOut
from app.services.auth_service import AuthError, decode_token, hash_password

router = APIRouter(prefix="/users", tags=["users"])


class UserCreateIn(BaseModel):
    nome: str
    email: EmailStr
    password: str
    role: Optional[str] = "AGENT"


class UserUpdateIn(BaseModel):
    nome: str
    role: str


class GrantAccessIn(BaseModel):
    email: EmailStr


class WorkshopUserOut(UserOut):
    # Usuário de outro cliente com acesso concedido a este.
    is_guest: bool = False


def _out(user: User, workshop_id: uuid.UUID) -> WorkshopUserOut:
    out = WorkshopUserOut.model_validate(user)
    out.is_guest = user.workshop_id != workshop_id
    return out


async def _get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> uuid.UUID:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthError("Token inválido")
        return uuid.UUID(payload["sub"])
    except (JWTError, AuthError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )


def _parse_role(raw: str) -> UserRole:
    try:
        role = UserRole(raw.upper())
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Role inválida"
        )
    # SUPERADMIN é do grupo GCT e não pode ser concedido de dentro de um cliente.
    if role == UserRole.SUPERADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Não é permitido atribuir a role SUPERADMIN",
        )
    return role


async def _get_or_404(user_id: uuid.UUID, workshop_id: uuid.UUID, db: AsyncSession) -> User:
    user = await db.scalar(
        select(User).where(User.id == user_id, User.workshop_id == workshop_id)
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuário não encontrado")
    return user


@router.get("", response_model=list[WorkshopUserOut])
async def list_users(
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    guests = select(UserWorkshopAccess.user_id).where(
        UserWorkshopAccess.workshop_id == workshop_id
    )
    result = await db.scalars(
        select(User)
        .where(or_(User.workshop_id == workshop_id, User.id.in_(guests)))
        .where(User.is_active == True)  # noqa: E712
        .order_by(User.name)
    )
    return [_out(u, workshop_id) for u in result.all()]


@router.post("/access", response_model=WorkshopUserOut, status_code=status.HTTP_201_CREATED)
async def grant_access(
    body: GrantAccessIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.AGENT:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem dar acesso a este cliente",
        )
    user = await db.scalar(
        select(User).where(User.email == body.email, User.is_active == True)  # noqa: E712
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhum usuário com este e-mail. Use \"Novo usuário\" para criar.",
        )
    if user.is_superadmin or user.workshop_id == workshop_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este usuário já tem acesso a este cliente"
        )
    exists = await db.scalar(
        select(UserWorkshopAccess).where(
            UserWorkshopAccess.user_id == user.id,
            UserWorkshopAccess.workshop_id == workshop_id,
        )
    )
    if exists:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Este usuário já tem acesso a este cliente"
        )
    db.add(UserWorkshopAccess(user_id=user.id, workshop_id=workshop_id))
    await db.commit()
    return _out(user, workshop_id)


@router.post("", response_model=WorkshopUserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreateIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    existing = await db.scalar(select(User).where(User.email == body.email))
    if existing:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="E-mail já cadastrado")

    role = _parse_role(body.role)

    user = User(
        workshop_id=workshop_id,
        name=body.nome,
        email=body.email,
        password_hash=hash_password(body.password),
        role=role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return _out(user, workshop_id)


@router.put("/{user_id}", response_model=WorkshopUserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdateIn,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    user = await _get_or_404(user_id, workshop_id, db)
    role = _parse_role(body.role)

    user.name = body.nome
    user.role = role
    await db.commit()
    await db.refresh(user)
    return _out(user, workshop_id)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: uuid.UUID,
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
    current_user_id: uuid.UUID = Depends(_get_current_user_id),
):
    if user_id == current_user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é possível remover seu próprio usuário",
        )
    # Convidado de outro cliente: só perde o acesso a este, o usuário continua ativo.
    access = await db.scalar(
        select(UserWorkshopAccess).where(
            UserWorkshopAccess.user_id == user_id,
            UserWorkshopAccess.workshop_id == workshop_id,
        )
    )
    if access:
        await db.delete(access)
        await db.commit()
        return
    user = await _get_or_404(user_id, workshop_id, db)
    user.is_active = False
    await db.commit()
