import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from tests.mock.conftest import make_valid_token, make_expired_token


def _make_message(text: str, user_id: int = 123, chat_id: int = 456) -> MagicMock:
    """
    Фабрика мок-сообщений aiogram.

    answer() — async метод, поэтому AsyncMock.
    from_user.id и chat.id — синхронные атрибуты.
    """
    msg = MagicMock()
    msg.text = text
    msg.from_user = MagicMock()
    msg.from_user.id = user_id
    msg.chat = MagicMock()
    msg.chat.id = chat_id
    msg.answer = AsyncMock()
    return msg


# ── /token handler ────────────────────────────────────────────────────────────

class TestTokenHandler:
    async def test_valid_token_saves_to_storage(self, token_storage, router):
        """
        При валидном JWT токен должен сохраниться в storage под ключом
        tg_token:<user_id> и бот должен ответить об успехе.
        """
        token = make_valid_token(sub="42")
        msg = _make_message(f"/token {token}", user_id=100)

        # Извлекаем token_handler — второй зарегистрированный хэндлер
        # (первый — start_handler)
        token_handler = router.message.handlers[1].callback
        await token_handler(msg)

        # Токен сохранён в storage
        saved = await token_storage.get_token(100)
        assert saved == token

        # Бот ответил успехом
        msg.answer.assert_called_once()
        response_text = msg.answer.call_args[0][0]
        assert "Авторизация успешна" in response_text

    async def test_invalid_token_not_saved(self, token_storage, router):
        """Невалидный JWT не должен сохраняться."""
        msg = _make_message("/token garbage.token.here", user_id=200)

        token_handler = router.message.handlers[1].callback
        await token_handler(msg)

        saved = await token_storage.get_token(200)
        assert saved is None
        msg.answer.assert_called_once()
        assert "неверный" in msg.answer.call_args[0][0].lower()

    async def test_expired_token_not_saved(self, token_storage, router):
        """Просроченный JWT не должен сохраняться."""
        token = make_expired_token()
        msg = _make_message(f"/token {token}", user_id=300)

        token_handler = router.message.handlers[1].callback
        await token_handler(msg)

        saved = await token_storage.get_token(300)
        assert saved is None
        msg.answer.assert_called_once()
        assert "истёк" in msg.answer.call_args[0][0].lower()

    async def test_token_command_without_argument(self, router):
        """/token без аргумента должен вернуть инструкцию."""
        msg = _make_message("/token", user_id=400)

        token_handler = router.message.handlers[1].callback
        await token_handler(msg)

        msg.answer.assert_called_once()
        assert "Использование" in msg.answer.call_args[0][0]


# ── LLM handler ──────────────────────────────────────────────────────────────

class TestLLMHandler:
    async def test_no_token_returns_auth_prompt(self, token_storage, router):
        """
        Если токена нет в storage — бот должен попросить авторизоваться
        и НЕ вызывать llm_request.delay.
        """
        msg = _make_message("Расскажи про Python", user_id=500)

        llm_handler = router.message.handlers[2].callback
        with patch("app.bot.handlers.llm_request") as mock_task:
            await llm_handler(msg)

        mock_task.delay.assert_not_called()
        msg.answer.assert_called_once()
        assert "авторизуйтесь" in msg.answer.call_args[0][0].lower()

    async def test_valid_token_calls_celery_task(self, token_storage, router):
        """
        Если токен валиден — должна вызваться llm_request.delay с правильными
        аргументами (tg_chat_id, prompt).
        """
        token = make_valid_token(sub="42")
        await token_storage.set_token(600, token)

        msg = _make_message("Что такое FastAPI?", user_id=600, chat_id=789)

        llm_handler = router.message.handlers[2].callback
        with patch("app.bot.handlers.llm_request") as mock_task:
            await llm_handler(msg)

        mock_task.delay.assert_called_once_with(
            tg_chat_id=789,
            prompt="Что такое FastAPI?",
        )
        msg.answer.assert_called_once()
        assert "Запрос принят" in msg.answer.call_args[0][0]

    async def test_expired_token_clears_storage_and_prompts(self, token_storage, router):
        """
        Просроченный токен должен быть удалён из storage и
        пользователь должен получить сообщение о необходимости переавторизации.
        """
        expired = make_expired_token()
        await token_storage.set_token(700, expired)

        msg = _make_message("Вопрос к LLM", user_id=700)

        llm_handler = router.message.handlers[2].callback
        with patch("app.bot.handlers.llm_request") as mock_task:
            await llm_handler(msg)

        mock_task.delay.assert_not_called()
        # Токен должен быть удалён из storage
        assert await token_storage.get_token(700) is None
        msg.answer.assert_called_once()
        assert "истёк" in msg.answer.call_args[0][0].lower()