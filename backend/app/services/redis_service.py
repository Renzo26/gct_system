from redis.asyncio import Redis

# Nome herdado do fluxo n8n do Cloudy/Mecaflow, que le exatamente esta chave
# para saber se deve silenciar o bot. Mudar o formato aqui exige mudar o n8n
# junto, senao o bot responde por cima do atendente humano.
# Efeito colateral aceito: o Redis e compartilhado com o Mecaflow, entao um
# mesmo numero atendido nos dois sistemas compartilha o bloqueio.
_BLOCK_KEY = "CloudSolutions_{chat_id}_block"

_TTL_SEGUNDOS = 900


class RedisService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, waha_chat_id: str) -> str:
        return _BLOCK_KEY.format(chat_id=waha_chat_id)

    async def set_human_block(self, waha_chat_id: str) -> None:
        await self._redis.set(self._key(waha_chat_id), "true", ex=_TTL_SEGUNDOS)

    async def del_human_block(self, waha_chat_id: str) -> None:
        await self._redis.delete(self._key(waha_chat_id))
