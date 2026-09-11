import logging
from typing import Optional

import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)

# JIDs que nao sao conversa enderecavel de uma pessoa: um sendText para
# "status@broadcast" PUBLICA um status na conta do cliente em vez de responder
# alguem, e canais (@newsletter) / listas de transmissao nao aceitam resposta.
# E blocklist, e nao allowlist de "@c.us", porque contatos legitimos tambem
# chegam como "<numero>@lid".
NON_CHAT_JID_SUFFIXES = ("@broadcast", "@newsletter")


class UnsendableChatError(Exception):
    """chatId nao corresponde a uma conversa para a qual se possa responder."""


def is_sendable_chat_id(chat_id: str) -> bool:
    return bool(chat_id) and not chat_id.strip().lower().endswith(NON_CHAT_JID_SUFFIXES)


class WahaService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.waha_base_url
        self._default_session = settings.waha_session
        self._headers = {"X-Api-Key": settings.waha_api_key}

    async def send_text(
        self, chat_id: str, text: str, session: Optional[str] = None
    ) -> Optional[str]:
        # Cinto de seguranca: mesmo que uma conversa suja exista no banco ou que
        # um agente clique "responder" nela, nunca publicamos um status.
        if not is_sendable_chat_id(chat_id):
            logger.error("WAHA sendText BLOQUEADO para JID nao enderecavel: %r", chat_id)
            raise UnsendableChatError(chat_id)

        # Cada cliente tem sua propria sessao WAHA; a do .env e apenas fallback
        # para clientes ainda sem sessao configurada.
        payload = {
            "session": session or self._default_session,
            "chatId": chat_id,
            "text": text,
        }
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                f"{self._base_url}/api/sendText",
                json=payload,
                headers=self._headers,
            )
            resp.raise_for_status()
            try:
                data = resp.json()
            except Exception:
                logger.warning("WAHA sendText response is not JSON")
                return None
        # WAHA pode retornar id em diferentes lugares dependendo da versão
        return (
            data.get("id")
            or (data.get("_data") or {}).get("id", {}).get("_serialized")
            or (data.get("key") or {}).get("id")
        )


waha_service = WahaService()
