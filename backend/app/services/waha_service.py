import logging
from typing import Optional

import httpx
from app.core.config import get_settings

logger = logging.getLogger(__name__)


class WahaService:
    def __init__(self) -> None:
        settings = get_settings()
        self._base_url = settings.waha_base_url
        self._default_session = settings.waha_session
        self._headers = {"X-Api-Key": settings.waha_api_key}

    async def send_text(
        self, chat_id: str, text: str, session: Optional[str] = None
    ) -> Optional[str]:
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
