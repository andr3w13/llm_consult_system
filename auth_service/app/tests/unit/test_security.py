import pytest
from jose import jwt

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_token,
    hash_password,
    verify_password,
)


# ── Тесты паролей ────────────────────────────────────────────────────────────

class TestPasswordHashing:
    def test_hash_is_not_plain_text(self):
        """Хэш пароля не должен совпадать с исходным паролем."""
        plain = "supersecret"
        hashed = hash_password(plain)
        assert hashed != plain

    def test_hash_is_bcrypt(self):
        """Хэш должен начинаться с префикса bcrypt."""
        hashed = hash_password("anypassword")
        assert hashed.startswith("$2")

    def test_verify_correct_password(self):
        """Правильный пароль должен проходить верификацию."""
        plain = "correctpassword"
        hashed = hash_password(plain)
        assert verify_password(plain, hashed) is True

    def test_verify_wrong_password(self):
        """Неправильный пароль не должен проходить верификацию."""
        hashed = hash_password("correctpassword")
        assert verify_password("wrongpassword", hashed) is False

    def test_two_hashes_of_same_password_differ(self):
        """
        Два хэша одного пароля должны быть разными (bcrypt использует соль).
        Оба должны проходить верификацию.
        """
        plain = "samepassword"
        h1 = hash_password(plain)
        h2 = hash_password(plain)
        assert h1 != h2
        assert verify_password(plain, h1)
        assert verify_password(plain, h2)


# ── Тесты JWT ────────────────────────────────────────────────────────────────

class TestJWT:
    def test_token_contains_required_claims(self):
        """Токен должен содержать sub, role, iat, exp."""
        token = create_access_token(subject=42, role="user")
        payload = decode_token(token)

        assert "sub" in payload
        assert "role" in payload
        assert "iat" in payload
        assert "exp" in payload

    def test_sub_matches_subject(self):
        """sub в токене должен совпадать с переданным subject."""
        token = create_access_token(subject=99, role="admin")
        payload = decode_token(token)
        # sub по стандарту JWT — строка
        assert payload["sub"] == "99"

    def test_role_matches(self):
        """role в токене должен совпадать с переданным значением."""
        token = create_access_token(subject=1, role="admin")
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_decode_returns_dict(self):
        """decode_token должен возвращать словарь."""
        token = create_access_token(subject=1, role="user")
        payload = decode_token(token)
        assert isinstance(payload, dict)

    def test_invalid_token_raises(self):
        """Мусорная строка должна вызывать JWTError."""
        from jose import JWTError
        with pytest.raises(JWTError):
            decode_token("this.is.not.a.valid.jwt")

    def test_wrong_secret_raises(self):
        """Токен, подписанный другим секретом, должен отклоняться."""
        from jose import JWTError, jwt as jose_jwt
        fake_token = jose_jwt.encode(
            {"sub": "1", "role": "user"},
            "wrong_secret",
            algorithm="HS256",
        )
        with pytest.raises(JWTError):
            decode_token(fake_token)

    def test_expired_token_raises(self):
        """Истёкший токен должен вызывать ExpiredSignatureError."""
        from datetime import datetime, timedelta, timezone
        from jose import ExpiredSignatureError, jwt as jose_jwt

        payload = {
            "sub": "1",
            "role": "user",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        expired_token = jose_jwt.encode(
            payload, settings.JWT_SECRET, algorithm=settings.JWT_ALG
        )
        with pytest.raises(ExpiredSignatureError):
            decode_token(expired_token)