from pydantic_settings import BaseSettings, SettingsConfigDict
from functools import lru_cache


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Banco de dados
    database_url: str

    # WAHA
    waha_base_url: str
    waha_api_key: str
    waha_session: str = "Cloudy"

    # Redis
    redis_url: str

    # JWT
    jwt_secret: str
    jwt_access_ttl_ms: int = 28800000
    jwt_refresh_ttl_ms: int = 604800000

    # IA
    anthropic_api_key: str = ""

    # App
    app_env: str = "development"
    app_port: int = 8080

    # CORS
    cors_origins: str = "http://localhost:5173"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",")]


@lru_cache
def get_settings() -> Settings:
    return Settings()
