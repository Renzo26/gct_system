import uuid
from typing import Optional

from fastapi import APIRouter, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from jose import JWTError

from app.services.auth_service import AuthError, decode_token
from app.services.sse_service import broadcaster

router = APIRouter(tags=["sse"])


def _resolve_workshop_id(token: Optional[str]) -> uuid.UUID:
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token ausente"
        )
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise AuthError("Token inválido")
        return uuid.UUID(payload["workshop_id"])
    except (JWTError, AuthError, ValueError, KeyError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
        )


@router.get("/sse/events")
async def sse_events(token: Optional[str] = Query(None)):
    workshop_id = _resolve_workshop_id(token)
    wid = str(workshop_id)

    async def event_stream():
        async for chunk in broadcaster.subscribe(workshop_id=wid):
            yield chunk

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
