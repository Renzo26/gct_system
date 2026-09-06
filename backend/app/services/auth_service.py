import uuid
from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import get_settings
from app.models.user import User, UserRole
from app.models.workshop import Workshop

_pwd = CryptContext(schemes=["bcrypt"], deprecated="auto")
_settings = get_settings()

ALGORITHM = "HS256"


class ConflictError(Exception):
    """Recurso já existe (HTTP 409)."""


class AuthError(Exception):
    """Credenciais inválidas ou token expirado (HTTP 401)."""


class ForbiddenError(Exception):
    """Usuário autenticado sem permissão para o recurso (HTTP 403)."""


class ValidationError(Exception):
    """Entrada inválida (HTTP 422)."""


def hash_password(plain: str) -> str:
    if len(plain.encode("utf-8")) > 72:
        raise ValidationError("A senha não pode ter mais de 72 caracteres.")
    return _pwd.hash(plain)


def verify_password(plain: str, hashed: str) -> bool:
    return _pwd.verify(plain, hashed)


def _make_token(data: dict, ttl_ms: int) -> str:
    expire = datetime.now(timezone.utc) + timedelta(milliseconds=ttl_ms)
    return jwt.encode({**data, "exp": expire}, _settings.jwt_secret, algorithm=ALGORITHM)


def create_access_token(user: User, workshop_id: Optional[uuid.UUID] = None) -> str:
    payload = {
        "sub": str(user.id),
        "role": user.role.value,
        "name": user.name,
        "type": "access",
    }
    if workshop_id is not None:
        payload["workshop_id"] = str(workshop_id)
    return _make_token(payload, _settings.jwt_access_ttl_ms)


def create_refresh_token(user: User, workshop_id: Optional[uuid.UUID] = None) -> str:
    payload = {"sub": str(user.id), "type": "refresh"}
    if workshop_id is not None:
        payload["workshop_id"] = str(workshop_id)
    return _make_token(payload, _settings.jwt_refresh_ttl_ms)


def decode_token(token: str) -> dict:
    return jwt.decode(token, _settings.jwt_secret, algorithms=[ALGORITHM])


class AuthService:
    async def login(self, db: AsyncSession, email: str, password: str) -> User:
        user = await db.scalar(
            select(User)
            .where(User.email == email, User.is_active == True)  # noqa: E712
            .options(selectinload(User.workshop))
        )
        if not user or not verify_password(password, user.password_hash):
            raise AuthError("E-mail ou senha inválidos")
        return user

    async def refresh(self, db: AsyncSession, refresh_token: str) -> tuple[User, Optional[uuid.UUID]]:
        try:
            payload = decode_token(refresh_token)
            if payload.get("type") != "refresh":
                raise ValueError()
            user_id = uuid.UUID(payload["sub"])
            raw_workshop = payload.get("workshop_id")
            workshop_id = uuid.UUID(raw_workshop) if raw_workshop else None
        except (JWTError, ValueError, KeyError):
            raise AuthError("Token inválido")

        user = await db.scalar(
            select(User)
            .where(User.id == user_id, User.is_active == True)  # noqa: E712
            .options(selectinload(User.workshop))
        )
        if not user:
            raise AuthError("Usuário não encontrado")

        # Uma seleção antiga não pode sobreviver à perda de acesso do usuário.
        if workshop_id is not None and not await self.can_access(db, user, workshop_id):
            workshop_id = None
        return user, workshop_id

    async def get_current_user(self, db: AsyncSession, token: str) -> User:
        try:
            payload = decode_token(token)
            if payload.get("type") != "access":
                raise AuthError("Token inválido")
            user_id = uuid.UUID(payload["sub"])
        except (JWTError, ValueError, KeyError):
            raise AuthError("Token inválido")

        user = await db.scalar(
            select(User)
            .where(User.id == user_id, User.is_active == True)  # noqa: E712
            .options(selectinload(User.workshop))
        )
        if not user:
            raise AuthError("Usuário não encontrado")
        return user

    async def list_accessible_workshops(self, db: AsyncSession, user: User) -> list[Workshop]:
        stmt = select(Workshop).order_by(Workshop.name)
        if not user.is_superadmin:
            if user.workshop_id is None:
                return []
            stmt = stmt.where(Workshop.id == user.workshop_id)
        result = await db.scalars(stmt)
        return list(result.all())

    async def can_access(self, db: AsyncSession, user: User, workshop_id: uuid.UUID) -> bool:
        if not user.is_superadmin and user.workshop_id != workshop_id:
            return False
        exists = await db.scalar(select(Workshop.id).where(Workshop.id == workshop_id))
        return exists is not None

    async def select_workshop(
        self, db: AsyncSession, user: User, workshop_id: uuid.UUID
    ) -> Workshop:
        workshop = await db.scalar(select(Workshop).where(Workshop.id == workshop_id))
        if not workshop:
            raise ForbiddenError("Cliente não encontrado")
        if not user.is_superadmin and user.workshop_id != workshop_id:
            raise ForbiddenError("Você não tem acesso a este cliente")
        return workshop


auth_service = AuthService()
