"""
auth_service/app/schemas/user.py

Публичное представление пользователя для API-ответов.

ВАЖНО: поля password_hash здесь нет — оно никогда не должно покидать
сервер. Pydantic V2 с from_attributes=True умеет читать данные из
SQLAlchemy-объектов через .model_validate(user_orm_obj).
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserPublic(BaseModel):
    id: int
    username: str
    email: EmailStr
    role: str
    created_at: datetime

    model_config = {"from_attributes": True}
