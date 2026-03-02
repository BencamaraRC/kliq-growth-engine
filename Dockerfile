# Stage 1: Builder
FROM python:3.11-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --prefix=/install .

# Stage 2: Runtime
FROM python:3.11-slim

ARG INSTALL_PLAYWRIGHT=false

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Install Playwright + Chromium only for worker image
RUN if [ "$INSTALL_PLAYWRIGHT" = "true" ]; then \
        playwright install chromium && playwright install-deps chromium; \
    fi

# Create non-root user
RUN groupadd -r appuser && useradd -r -g appuser -d /app -s /sbin/nologin appuser

COPY . .

RUN chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

CMD ["gunicorn", "app.main:app", "-w", "2", "-k", "uvicorn.workers.UvicornWorker", "--bind", "0.0.0.0:8000", "--timeout", "120"]
