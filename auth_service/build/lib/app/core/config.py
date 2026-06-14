"""
auth_service/app/core/config.py

Единственное место, где читаются переменные окружения.
Все остальные модули импортируют готовый объект `settings`.
"""
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Метаинформация ──────────────────────────────────────────────────────
    APP_NAME: str = "auth-service"
    ENV: str = "local"

    # ── JWT ─────────────────────────────────────────────────────────────────
    # JWT_SECRET должен совпадать с Bot Service — это единственная "точка
    # соединения" двух сервисов. Меняйте только через .env, никогда в коде.
    JWT_SECRET: str = "change_me_super_secret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    # ── База данных ──────────────────────────────────────────────────────────
    SQLITE_PATH: str = "./auth.db"

    @property
    def DATABASE_URL(self) -> str:
        """Асинхронная строка подключения для SQLAlchemy + aiosqlite."""
        return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """
    Фабрика с кэшированием. Используй её вместо прямого импорта `settings`
    в тестах — lru_cache позволяет вызвать get_settings.cache_clear() для
    подмены настроек в изолированных тестах.
    """
    return Settings()


# Модульный синглтон — удобен для импорта в продовом коде
settings: Settings = get_settings()
