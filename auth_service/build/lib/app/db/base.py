"""
auth_service/app/db/base.py

Единственный источник Base для всех ORM-моделей проекта.

Почему отдельный файл?
  Alembic и session.py оба импортируют Base для создания таблиц.
  Если Base объявить в models.py, возникают циклические импорты.
  Отдельный модуль db/base.py разрывает этот цикл.
"""
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """Базовый класс для всех SQLAlchemy-моделей Auth Service."""
    pass
