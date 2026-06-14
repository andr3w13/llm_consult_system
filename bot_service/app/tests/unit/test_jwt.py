import pytest
from httpx import AsyncClient


# ── Вспомогательные данные ───────────────────────────────────────────────────

VALID_USER = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "secret123",
}


async def register_and_login(client: AsyncClient) -> str:
    """
    Вспомогательная функция: регистрирует пользователя и возвращает JWT.
    Используется в нескольких тестах.
    """
    await client.post("/auth/register", json=VALID_USER)
    resp = await client.post(
        "/auth/login",
        data={"username": VALID_USER["email"], "password": VALID_USER["password"]},
    )
    return resp.json()["access_token"]


# ── Позитивные тесты ─────────────────────────────────────────────────────────

class TestRegister:
    async def test_register_success(self, client: AsyncClient):
        """Регистрация должна возвращать 201 и данные пользователя."""
        resp = await client.post("/auth/register", json=VALID_USER)
        assert resp.status_code == 201

        data = resp.json()
        assert data["email"] == VALID_USER["email"]
        assert data["username"] == VALID_USER["username"]
        assert data["role"] == "user"
        assert "id" in data
        assert "created_at" in data
        # Пароль никогда не должен возвращаться в ответе
        assert "password" not in data
        assert "password_hash" not in data


class TestLogin:
    async def test_login_success_returns_token(self, client: AsyncClient):
        """Логин с корректными данными должен возвращать JWT."""
        await client.post("/auth/register", json=VALID_USER)

        resp = await client.post(
            "/auth/login",
            data={"username": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Токен должен быть непустым
        assert len(data["access_token"]) > 10


class TestMe:
    async def test_me_returns_current_user(self, client: AsyncClient):
        """GET /auth/me с валидным токеном должен возвращать профиль."""
        token = await register_and_login(client)

        resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200

        data = resp.json()
        assert data["email"] == VALID_USER["email"]
        assert data["username"] == VALID_USER["username"]


class TestFullFlow:
    async def test_register_login_me_full_flow(self, client: AsyncClient):
        """
        Полный пользовательский сценарий:
          1. Регистрация
          2. Логин → получение токена
          3. /me → получение профиля через токен
        """
        # 1. Регистрация
        reg_resp = await client.post("/auth/register", json=VALID_USER)
        assert reg_resp.status_code == 201
        user_id = reg_resp.json()["id"]

        # 2. Логин
        login_resp = await client.post(
            "/auth/login",
            data={"username": VALID_USER["email"], "password": VALID_USER["password"]},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]

        # 3. /me
        me_resp = await client.get(
            "/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert me_resp.status_code == 200
        assert me_resp.json()["id"] == user_id


# ── Негативные тесты ─────────────────────────────────────────────────────────

class TestNegativeCases:
    async def test_register_duplicate_email_returns_409(self, client: AsyncClient):
        """Повторная регистрация с тем же email → 409 Conflict."""
        await client.post("/auth/register", json=VALID_USER)
        resp = await client.post("/auth/register", json=VALID_USER)
        assert resp.status_code == 409

    async def test_login_wrong_password_returns_401(self, client: AsyncClient):
        """Логин с неверным паролем → 401."""
        await client.post("/auth/register", json=VALID_USER)
        resp = await client.post(
            "/auth/login",
            data={"username": VALID_USER["email"], "password": "wrongpassword"},
        )
        assert resp.status_code == 401

    async def test_login_unknown_email_returns_401(self, client: AsyncClient):
        """Логин с несуществующим email → 401 (не раскрываем, есть ли пользователь)."""
        resp = await client.post(
            "/auth/login",
            data={"username": "nobody@example.com", "password": "anything"},
        )
        assert resp.status_code == 401

    async def test_me_without_token_returns_401(self, client: AsyncClient):
        """GET /auth/me без токена → 401."""
        resp = await client.get("/auth/me")
        assert resp.status_code == 401

    async def test_me_with_invalid_token_returns_401(self, client: AsyncClient):
        """GET /auth/me с мусорным токеном → 401."""
        resp = await client.get(
            "/auth/me",
            headers={"Authorization": "Bearer this.is.garbage"},
        )
        assert resp.status_code == 401

    async def test_register_short_password_returns_422(self, client: AsyncClient):
        """Пароль короче 6 символов → 422 Unprocessable Entity (Pydantic validation)."""
        resp = await client.post(
            "/auth/register",
            json={**VALID_USER, "password": "123"},
        )
        assert resp.status_code == 422

    async def test_register_invalid_email_returns_422(self, client: AsyncClient):
        """Невалидный email → 422."""
        resp = await client.post(
            "/auth/register",
            json={**VALID_USER, "email": "not-an-email"},
        )
        assert resp.status_code == 422