from redis.asyncio import Redis

# Nome herdado do fluxo n8n do Cloudy/Mecaflow, que le exatamente esta chave
# para saber se deve silenciar o bot. Mudar o formato aqui exige mudar o n8n
# junto, senao o bot responde por cima do atendente humano.
# Efeito colateral aceito: o Redis e compartilhado com o Mecaflow, entao um
# mesmo numero atendido nos dois sistemas compartilha o bloqueio.
_BLOCK_KEY = "CloudSolutions_{chat_id}_block"

# A pausa NAO tem prazo: quando um humano assume, o bot fica calado naquele
# contato ate alguem reativa-lo (botao "bot" no painel, ou resolver/reabrir a
# conversa). Antes havia um TTL de 15 min, e ele criava divergencia de estado:
# a conversa seguia marcada como HUMAN no banco, a chave expirava sozinha e o
# bot voltava a responder por cima do atendente.


class RedisService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def _key(self, waha_chat_id: str) -> str:
        return _BLOCK_KEY.format(chat_id=waha_chat_id)

    async def set_human_block(self, waha_chat_id: str) -> None:
        await self._redis.set(self._key(waha_chat_id), "true")

    async def del_human_block(self, waha_chat_id: str) -> None:
        await self._redis.delete(self._key(waha_chat_id))
