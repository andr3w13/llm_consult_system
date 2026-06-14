import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.infra.redis import get_redis

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Startup / shutdown lifecycle.

    На startup:
      - создаём Redis connection pool

    На shutdown:
      - корректно закрываем Redis
    """
    logger.info(
        "Starting %s [env=%s]",
        settings.APP_NAME,
        settings.ENV,
    )

    redis = get_redis()

    try:
        await redis.ping()
        logger.info("Redis connection established")
    except Exception as exc:
        logger.exception("Redis unavailable: %s", exc)

    yield

    logger.info("Shutting down %s", settings.APP_NAME)

    await redis.close()


app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    description="Bot Service API",
    lifespan=lifespan,
)


@app.get(
    "/health",
    tags=["System"],
    summary="Health check",
)
async def health() -> JSONResponse:
    """
    Используется:
      - docker healthcheck
      - Kubernetes probes
      - monitoring systems
    """
    return JSONResponse(
        content={
            "status": "ok",
            "service": settings.APP_NAME,
            "env": settings.ENV,
        }
    )