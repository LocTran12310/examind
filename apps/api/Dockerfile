FROM python:3.12-slim AS base
RUN apt-get update \
 && apt-get install -y --no-install-recommends pandoc tesseract-ocr tesseract-ocr-vie tesseract-ocr-eng fonts-dejavu-core \
 && rm -rf /var/lib/apt/lists/*
COPY --from=ghcr.io/astral-sh/uv:0.8 /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/opt/venv PATH="/opt/venv/bin:$PATH" PYTHONUNBUFFERED=1
WORKDIR /app
COPY pyproject.toml uv.lock ./

FROM base AS test
RUN uv sync --frozen --no-install-project
# source is bind-mounted by the api-test service
CMD ["pytest", "-q"]

FROM base AS runtime
RUN uv sync --frozen --no-dev --no-install-project
COPY . .
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && python -m app.seed.bootstrap && exec uvicorn app.main:app --host 0.0.0.0 --port 8000 --proxy-headers --forwarded-allow-ips='*'"]
