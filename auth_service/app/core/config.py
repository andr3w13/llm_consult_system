from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )
    APP_NAME: str = "auth-service"
    ENV: str = "local"

    JWT_SECRET: str = "change_me_super_secret"
    JWT_ALG: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    SQLITE_PATH: str = "./auth.db"

    @property
    def DATABASE_URL(self) -> str:
        """Асинхронная строка подключения для SQLAlchemy + aiosqlite."""
        return f"sqlite+aiosqlite:///{self.SQLITE_PATH}"


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()

settings: Settings = get_settings()
