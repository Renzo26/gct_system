import uuid
from typing import AsyncGenerator

from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError
from redis.asyncio import Redis
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.services.auth_service import AuthError, auth_service, decode_token
from app.services.redis_service import RedisService

_bearer = HTTPBearer()

_UNAUTHORIZED = HTTPException(
    status_code=status.HTTP_401_UNAUTHORIZED,
    detail="Token inválido ou expirado",
    headers={"WWW-Authenticate": "Bearer"},
)


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async for session in get_db():
        yield session


async def get_redis_service(request: Request) -> RedisService:
    redis: Redis = request.app.state.redis
    return RedisService(redis)


async def get_access_payload(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise AuthError("Token inválido")
        return payload
    except (JWTError, AuthError, ValueError, KeyError):
        raise _UNAUTHORIZED


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(_bearer),
    db: AsyncSession = Depends(get_session),
) -> User:
    try:
        return await auth_service.get_current_user(db, credentials.credentials)
    except AuthError:
        raise _UNAUTHORIZED


async def require_superadmin(user: User = Depends(get_current_user)) -> User:
    if not user.is_superadmin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Ação restrita a administradores do GCT",
        )
    return user


async def get_workshop_id(payload: dict = Depends(get_access_payload)) -> uuid.UUID:
    raw = payload.get("workshop_id")
    # Token válido, porém sem cliente escolhido: 403 (e não 401) para que o
    # frontend leve à tela de seleção em vez de encerrar a sessão.
    if not raw:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Nenhum cliente selecionado",
        )
    try:
        return uuid.UUID(raw)
    except ValueError:
        raise _UNAUTHORIZED
