import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, EmailStr
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_session, get_workshop_id, _bearer
from fastapi.security import HTTPAuthorizationCredentials
from jose import JWTError

from app.models.user import User, UserRole
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


@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_session),
    workshop_id: uuid.UUID = Depends(get_workshop_id),
):
    result = await db.scalars(
        select(User).where(User.workshop_id == workshop_id, User.is_active == True)  # noqa: E712
    )
    return result.all()


@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
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
    return user


@router.put("/{user_id}", response_model=UserOut)
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
    return user


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
    user = await _get_or_404(user_id, workshop_id, db)
    user.is_active = False
    await db.commit()
