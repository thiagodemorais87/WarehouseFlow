FROM python:3.12-slim

ARG APP_VERSION=dev

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    APP_VERSION=${APP_VERSION} \
    FRONTEND_DIR=/app/frontend

LABEL org.opencontainers.image.title="WarehouseFlow" \
      org.opencontainers.image.version="${APP_VERSION}"

RUN groupadd --system appuser \
    && useradd --system --gid appuser --home-dir /app --shell /usr/sbin/nologin appuser

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY backend ./backend
COPY frontend ./frontend

RUN chown -R appuser:appuser /app

USER appuser

EXPOSE 8000

# Produção: sem --reload. Dev sobrescreve o command no docker-compose.yml.
CMD ["uvicorn", "app.main:app", "--app-dir", "backend", "--host", "0.0.0.0", "--port", "8000"]
