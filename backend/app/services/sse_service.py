import asyncio
import json
from typing import AsyncGenerator, Optional


class SSEBroadcaster:
    """Broadcaster com filtro opcional por workshop_id.

    Cada assinante registra a oficina que deseja receber. Eventos publicados sem
    workshop_id são entregues a todos (uso interno/diagnóstico). Eventos com
    workshop_id são entregues apenas a assinantes da mesma oficina.
    """

    def __init__(self) -> None:
        # cada item: (queue, workshop_id_or_None)
        self._subs: set[tuple[asyncio.Queue, Optional[str]]] = set()

    def _format(self, event: str, data: dict) -> str:
        return f"event: {event}\ndata: {json.dumps(data)}\n\n"

    async def publish(
        self, event: str, data: dict, workshop_id: Optional[str] = None
    ) -> None:
        payload = self._format(event, data)
        dead: set = set()
        for entry in self._subs:
            q, sub_wid = entry
            if workshop_id is not None and sub_wid is not None and sub_wid != workshop_id:
                continue
            try:
                q.put_nowait(payload)
            except asyncio.QueueFull:
                dead.add(entry)
        self._subs -= dead

    async def subscribe(
        self, workshop_id: Optional[str] = None
    ) -> AsyncGenerator[str, None]:
        queue: asyncio.Queue = asyncio.Queue(maxsize=100)
        entry = (queue, workshop_id)
        self._subs.add(entry)
        try:
            while True:
                payload = await queue.get()
                yield payload
        finally:
            self._subs.discard(entry)


broadcaster = SSEBroadcaster()
