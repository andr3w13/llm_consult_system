"""
bot_service/app/core/config.py

Настройки Bot Service через pydantic-settings.

Ключевое: JWT_SECRET должен совпадать с Auth Service.
  Это единственная конфигурационная связь между сервисами.
  Bot Service не обращается к Auth Service во время работы —
  он валидирует JWT локально, используя тот же секретный ключ.

TELEGRAM_BOT_TOKEN: обязательное поле без дефолта —
  приложение не запустится без него, что является правильным поведением.
"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    APP_NAME: str = "bot-service"
    ENV: str = "local"

    # ── Telegram ─────────────────────────────────────────────────────────────
    TELEGRAM_BOT_TOKEN: str  # обязательно — без токена бот не запустится

    # ── JWT (должен совпадать с Auth Service) ────────────────────────────────
    JWT_SECRET: str = "change_me_super_secret"
    JWT_ALG: str = "HS256"

    # ── OpenRouter ───────────────────────────────────────────────────────────
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_MODEL: str = "stepfun/step-3.5-flash:free"
    OPENROUTER_SITE_URL: str = "https://example.com"
    OPENROUTER_APP_NAME: str = "bot-service"

    # ── Инфраструктура (не используется в базовой версии) ────────────────────
    REDIS_URL: str = "redis://redis:6379/0"
    RABBITMQ_URL: str = "amqp://guest:guest@rabbitmq:5672//"


settings = Settings()