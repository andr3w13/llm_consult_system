"""
bot_service/app/services/openrouter.py

Клиент OpenRouter API для обращения к языковым моделям.

OpenRouter — это прокси-сервис с OpenAI-совместимым API, который
предоставляет доступ к моделям разных провайдеров через единый endpoint.

Почему отдельный сервис-класс, а не httpx-вызовы прямо в хэндлерах?
  - Единственное место для настройки timeout, headers, retry-логики.
  - Легко заменить OpenRouter на другой провайдер.
  - Легко тестировать: мокаем OpenRouterClient, не HTTP-сессию.
  - Хэндлеры остаются тонкими — они не знают деталей HTTP-взаимодействия.

Почему async httpx, а не requests?
  Бот работает на asyncio event loop. Синхронный requests заблокировал бы
  loop на время HTTP-запроса, что недопустимо.

Почему создаём клиент на каждый запрос (не глобальный httpx.AsyncClient)?
  httpx.AsyncClient с контекстным менеджером гарантирует закрытие
  соединений. Глобальный клиент сложнее в управлении (graceful shutdown).
  Для высоких нагрузок стоит перейти на connection pool.
"""
import logging
from dataclasses import dataclass, field

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


class OpenRouterError(Exception):
    """Базовое исключение ошибок OpenRouter API."""


@dataclass
class LLMResponse:
    """Ответ языковой модели."""
    content: str
    model: str
    usage: dict = field(default_factory=dict)


class OpenRouterClient:
    """
    Асинхронный клиент OpenRouter API.

    Для каждого запроса создаётся новый httpx.AsyncClient.
    Настройки читаются из Settings один раз при инициализации.
    """

    def __init__(self) -> None:
        self._base_url = settings.OPENROUTER_BASE_URL
        self._api_key = settings.OPENROUTER_API_KEY
        self._model = settings.OPENROUTER_MODEL
        self._site_url = settings.OPENROUTER_SITE_URL
        self._app_name = settings.OPENROUTER_APP_NAME

        # Разные таймауты для разных операций
        self._timeout = httpx.Timeout(
            connect=10.0,   # установка соединения
            read=60.0,      # чтение ответа (LLM может отвечать долго)
            write=10.0,
            pool=5.0,
        )

    async def chat(
        self,
        user_message: str,
        system_prompt: str | None = None,
    ) -> LLMResponse:
        """
        Отправляет сообщение в LLM и возвращает ответ.

        Args:
            user_message: текст от пользователя Telegram
            system_prompt: опциональный системный промпт

        Returns:
            LLMResponse с полем content

        Raises:
            OpenRouterError: при timeout или ошибке API
        """
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": user_message})

        payload = {"model": self._model, "messages": messages}
        headers = {
            "Authorization": f"Bearer {self._api_key}",
            "HTTP-Referer": self._site_url,
            "X-Title": self._app_name,
            "Content-Type": "application/json",
        }

        logger.info("OpenRouter request: model=%s len=%d", self._model, len(user_message))

        async with httpx.AsyncClient(timeout=self._timeout) as client:
            try:
                response = await client.post(
                    f"{self._base_url}/chat/completions",
                    json=payload,
                    headers=headers,
                )
                response.raise_for_status()
            except httpx.TimeoutException as exc:
                logger.error("OpenRouter timeout: %s", exc)
                raise OpenRouterError(
                    "Запрос к LLM превысил таймаут. Попробуйте позже."
                ) from exc
            except httpx.HTTPStatusError as exc:
                logger.error(
                    "OpenRouter HTTP error: status=%d body=%s",
                    exc.response.status_code,
                    exc.response.text[:500],
                )
                raise OpenRouterError(
                    f"LLM API вернул ошибку {exc.response.status_code}."
                ) from exc

        data = response.json()

        try:
            content = data["choices"][0]["message"]["content"]
            model = data.get("model", self._model)
            usage = data.get("usage", {})
        except (KeyError, IndexError) as exc:
            logger.error("Unexpected OpenRouter response: %s", data)
            raise OpenRouterError("Неожиданная структура ответа от LLM API.") from exc

        logger.info(
            "OpenRouter response: model=%s tokens=%s",
            model,
            usage.get("total_tokens", "?"),
        )
        return LLMResponse(content=content, model=model, usage=usage)