"""
auth_service/app/schemas/auth.py

Pydantic-схемы для эндпоинтов аутентификации.

RegisterRequest — тело POST /auth/register.
TokenResponse   — ответ POST /auth/login.

Почему нет LoginRequest?
  Для /auth/login используется OAuth2PasswordRequestForm (стандарт OAuth2).
  Форма принимает поля username (мы используем его как email) и password
  в формате application/x-www-form-urlencoded. Это позволяет FastAPI
  автоматически показывать кнопку "Authorize" в Swagger UI.
"""
from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    username: str = Field(..., min_length=3, max_length=100, examples=["john_doe"])
    email: EmailStr = Field(..., examples=["john@example.com"])
    password: str = Field(..., min_length=6, examples=["secret123"])


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
