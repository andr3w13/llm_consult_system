"""
auth_service/app/db/session.py

Асинхронный движок SQLAlchemy и фабрика сессий.

Зачем expire_on_commit=False?
  В асинхронном коде после commit() атрибуты объекта "ленивы" — SQLAlchemy
  пытается сделать lazy-load в синхронном режиме, что невозможно.
  expire_on_commit=False отключает этот механизм: атрибуты остаются
  доступными после коммита без дополнительного SELECT.

Зачем echo=True только в ENV=local?
  SQL-лог удобен при разработке, но засоряет продовые логи.
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=(settings.ENV == "local"),  # логировать SQL только в dev-режиме
    future=True,
)

# Фабрика сессий — не создаёт соединение сразу, только описывает параметры
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)
