from redis.asyncio import Redis

# Formato lido pelos fluxos n8n: "{Botname}_{telefone}_block", com o Botname do
# no "Configuração Global" de cada fluxo. Cada cliente precisa de um Botname
# proprio, senao pausar o bot de um contato cala o bot dos outros clientes.
_BLOCK_KEY = "{bot_name}_{chat_id}_block"

# A pausa NAO tem prazo: quando um humano assume, o bot fica calado naquele
# contato ate alguem reativa-lo (botao "bot" no painel, ou resolver/reabrir a
# conversa). Antes havia um TTL de 15 min, e ele criava divergencia de estado:
# a conversa seguia marcada como HUMAN no banco, a chave expirava sozinha e o
# bot voltava a responder por cima do atendente.


class RedisService:
    def __init__(self, redis: Redis) -> None:
        self._redis = redis

    def key(self, bot_name: str, waha_chat_id: str) -> str:
        return _BLOCK_KEY.format(bot_name=bot_name, chat_id=waha_chat_id)

    async def set_human_block(self, bot_name: str, waha_chat_id: str) -> None:
        await self._redis.set(self.key(bot_name, waha_chat_id), "true")

    async def del_human_block(self, bot_name: str, waha_chat_id: str) -> None:
        await self._redis.delete(self.key(bot_name, waha_chat_id))
