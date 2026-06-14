"""
auth_service/app/db/models.py

ORM-модели Auth Service.

Здесь только описание структуры данных — никакой бизнес-логики.
Бизнес-логика живёт в usecases/auth.py, доступ к данным — в repositories/.

Почему уникальный индекс по email?
  Уникальность должна гарантироваться на уровне БД, а не только в коде.
  Если два параллельных запроса пройдут проверку в usecase одновременно,
  база выбросит IntegrityError — репозиторий или usecase поймают его.
"""
from datetime import datetime

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,  # быстрый поиск по email при логине
    )
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # устанавливается базой, не Python-кодом
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} email={self.email!r} role={self.role!r}>"
