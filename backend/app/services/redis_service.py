from typing import Optional

from redis.asyncio import Redis

# O Redis da VPS e compartilhado com outros projetos/clientes, entao a chave
# leva o prefixo do projeto e a sessao WAHA do cliente. O fluxo do n8n precisa
# ler exatamente este mesmo formato.
_BLOCK_KEY = "gct_{session}_{chat_id}_block"


class RedisService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, waha_chat_id: str, session: Optional[str]) -> str:
        return _BLOCK_KEY.format(session=session or "default", chat_id=waha_chat_id)

    async def set_human_block(
        self, waha_chat_id: str, session: Optional[str] = None
    ) -> None:
        await self._redis.set(self._key(waha_chat_id, session), "true", ex=900)

    async def del_human_block(
        self, waha_chat_id: str, session: Optional[str] = None
    ) -> None:
        await self._redis.delete(self._key(waha_chat_id, session))
