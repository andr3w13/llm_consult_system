import pytest
import respx
import httpx

from app.services.openrouter_client import OpenRouterClient, OpenRouterError, LLMResponse


MOCK_RESPONSE = {
    "id": "gen-test-123",
    "model": "stepfun/step-3.5-flash:free",
    "choices": [
        {
            "message": {
                "role": "assistant",
                "content": "FastAPI — современный веб-фреймворк для Python.",
            }
        }
    ],
    "usage": {
        "prompt_tokens": 10,
        "completion_tokens": 20,
        "total_tokens": 30,
    },
}


class TestOpenRouterClientSuccess:
    @respx.mock
    async def test_chat_returns_llm_response(self):
        """
        Успешный запрос должен вернуть LLMResponse с content из choices[0].
        """
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        client = OpenRouterClient()
        result = await client.chat("Что такое FastAPI?")

        assert isinstance(result, LLMResponse)
        assert result.content == "FastAPI — современный веб-фреймворк для Python."

    @respx.mock
    async def test_chat_passes_correct_model(self):
        """Клиент должен передавать модель из настроек."""
        route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        client = OpenRouterClient()
        await client.chat("test")

        request_body = route.calls[0].request
        import json
        body = json.loads(request_body.content)
        assert "model" in body
        assert "messages" in body

    @respx.mock
    async def test_chat_includes_system_prompt(self):
        """При передаче system_prompt он должен быть первым сообщением."""
        route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        client = OpenRouterClient()
        await client.chat("user question", system_prompt="Ты полезный ассистент.")

        import json
        body = json.loads(route.calls[0].request.content)
        messages = body["messages"]

        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "Ты полезный ассистент."
        assert messages[1]["role"] == "user"

    @respx.mock
    async def test_chat_returns_usage_stats(self):
        """Статистика использования токенов должна возвращаться."""
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        client = OpenRouterClient()
        result = await client.chat("test")

        assert result.usage.get("total_tokens") == 30

    @respx.mock
    async def test_http_request_is_actually_made(self):
        """
        Подтверждаем, что HTTP-вызов действительно происходит.
        respx отслеживает вызовы — если вызова не было, тест упадёт.
        """
        route = respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json=MOCK_RESPONSE)
        )

        client = OpenRouterClient()
        await client.chat("ping")

        assert route.called
        assert route.call_count == 1


class TestOpenRouterClientErrors:
    @respx.mock
    async def test_http_500_raises_openrouter_error(self):
        """HTTP 500 от API → OpenRouterError."""
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(500, json={"error": "Internal Server Error"})
        )

        client = OpenRouterClient()
        with pytest.raises(OpenRouterError):
            await client.chat("test")

    @respx.mock
    async def test_http_401_raises_openrouter_error(self):
        """HTTP 401 (неверный API ключ) → OpenRouterError."""
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(401, json={"error": "Unauthorized"})
        )

        client = OpenRouterClient()
        with pytest.raises(OpenRouterError):
            await client.chat("test")

    @respx.mock
    async def test_malformed_response_raises_openrouter_error(self):
        """Ответ без ожидаемых полей → OpenRouterError."""
        respx.post("https://openrouter.ai/api/v1/chat/completions").mock(
            return_value=httpx.Response(200, json={"unexpected": "structure"})
        )

        client = OpenRouterClient()
        with pytest.raises(OpenRouterError):
            await client.chat("test")