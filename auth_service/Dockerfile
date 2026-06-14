FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir fastapi uvicorn[standard] sqlalchemy aiosqlite \
    "pydantic[email]" pydantic-settings "python-jose[cryptography]" \
    "passlib[bcrypt]" python-multipart greenlet "bcrypt==4.3.0"

COPY . .

RUN mkdir -p /app/data

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
