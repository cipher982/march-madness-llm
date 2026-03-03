FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    UV_LINK_MODE=copy

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl bash \
    && curl -1sLf 'https://artifacts.infisical.com/setup.deb.sh' | bash \
    && apt-get install -y infisical \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir uv

COPY pyproject.toml uv.lock ./
COPY mm_ai ./mm_ai
COPY data ./data

RUN uv sync --frozen --no-dev

ARG FRONTEND_PORT=3000
ENV FRONTEND_PORT=${FRONTEND_PORT}

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
  CMD curl -f http://localhost:8000/health || exit 1

CMD ["infisical", "run", "--env", "prod", "--", "uv", "run", "uvicorn", "mm_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
