"""
Configurazione del backend letta da environment/.env (pydantic-settings).
Le chiavi dei provider AI sono qui, lato server, e non vengono mai esposte
al frontend: è il prodotto stesso a fornire l'accesso all'AI, non l'utente.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Auth
    jwt_secret: str = "insecure-dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60 * 24 * 7  # 7 giorni

    # Database
    database_url: str = "sqlite:///./analyzer.db"

    # Chiavi piattaforma per i provider AI (opzionali: un provider senza
    # chiave configurata non compare nel selettore frontend, vedi
    # core.ai_providers.registry.list_available_providers)
    gemini_api_key: str | None = None
    openai_api_key: str | None = None
    anthropic_api_key: str | None = None

    # Piani/quota (nessun pagamento reale collegato in questa fase)
    free_plan_monthly_limit: int = 10
    pro_plan_monthly_limit: int = 500

    # Hardening
    max_upload_chars: int = 5_000_000  # ~5MB di testo
    cors_origins_raw: str = "http://localhost:5173,http://127.0.0.1:5173"
    rate_limit_analyze: str = "20/minute"

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins_raw.split(",") if origin.strip()]

    @property
    def provider_keys(self) -> dict[str, str | None]:
        return {
            "gemini": self.gemini_api_key,
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }


@lru_cache
def get_settings() -> Settings:
    return Settings()
