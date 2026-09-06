from dotenv import load_dotenv
load_dotenv()  # garante que .env é carregado no os.environ antes de qualquer import

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.api import auth, conversations, webhooks, sse, clients, appointments, workshop_labels, workshop_users, workshop_settings, workshops, assistant

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    from app.core.redis import get_redis
    redis = await get_redis()
    app.state.redis = redis
    yield
    await redis.aclose()


app = FastAPI(
    title="GCT API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_origin_regex=r"https?://.*\.easypanel\.host",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(webhooks.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(sse.router, prefix="/api")
app.include_router(clients.router, prefix="/api")
app.include_router(appointments.router, prefix="/api")
app.include_router(workshop_labels.router, prefix="/api")
app.include_router(workshop_users.router, prefix="/api")
app.include_router(workshop_settings.router, prefix="/api")
app.include_router(workshops.router, prefix="/api")
app.include_router(assistant.router, prefix="/api")


@app.get("/health")
async def health():
    return {"status": "ok"}
