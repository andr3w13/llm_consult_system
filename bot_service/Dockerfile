FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir aiogram httpx pydantic-settings \
    "python-jose[cryptography]" redis celery fastapi uvicorn[standard]

COPY . .

CMD ["python", "-m", "app.bot_run"]