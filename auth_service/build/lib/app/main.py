"""
auth_service/app/main.py

Точка входа Auth Service. Только конфигурация приложения:
  - создание FastAPI-экземпляра
  - lifespan (startup / shutdown)
  - middleware логирования запросов
  - обработчик исключений
  - подключение роутеров
  - healthcheck endpoint

Бизнес-логика здесь отсутствует — она живёт в usecases/.

Примечание о lifespan vs on_event:
  on_event deprecated в FastAPI 0.93+. lifespan-паттерн через
  @asynccontextmanager является современной заменой.
"""
import logging
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import BaseHTTPException
from app.db.base import Base
from app.db.session import engine
from app.db import models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)


# ── Жизненный цикл приложения ────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup: создаём таблицы (в production используйте Alembic-миграции).
    Shutdown: освобождаем пул соединений.
    """
    logger.info("Starting %s [env=%s]", settings.APP_NAME, settings.ENV)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created / verified")
    yield
    logger.info("Shutting down %s", settings.APP_NAME)
    await engine.dispose()


# ── Приложение ───────────────────────────────────────────────────────────────

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Auth Service: registration, login, JWT issuing",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── Middleware ───────────────────────────────────────────────────────────────

@app.middleware("http")
async def logging_middleware(request: Request, call_next):
    """Логирует каждый HTTP-запрос с методом, путём, статусом и временем."""
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s → %d  (%.1f ms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Обработчики исключений ───────────────────────────────────────────────────

@app.exception_handler(BaseHTTPException)
async def base_http_exception_handler(
    request: Request, exc: BaseHTTPException
) -> JSONResponse:
    """
    Перехватывает наши кастомные HTTP-исключения и возвращает
    стандартный JSON-ответ {"detail": "..."}.
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )


# ── Роуты ────────────────────────────────────────────────────────────────────

app.include_router(api_router)


@app.get("/health", tags=["System"], summary="Health check")
async def health() -> dict:
    return {
        "status": "ok",
        "service": settings.APP_NAME,
        "env": settings.ENV,
    }
