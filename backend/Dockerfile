# ── Backend Dockerfile ──────────────────────────────────────────────────────────
#
# Design decisions:
#
# 1. python:3.12-slim — slim variant drops documentation and package indexes,
#    saving ~100MB image size vs the full image. We don't need them at runtime.
#
# 2. Non-root user — running as root in a container is a security risk. If the
#    container is compromised, the attacker would have root inside it. We create
#    a dedicated "appuser" instead.
#
# 3. PYTHONDONTWRITEBYTECODE=1 — prevents Python from writing .pyc files.
#    We don't need them in containers (startup time is a non-issue at build time).
#
# 4. PYTHONUNBUFFERED=1 — forces Python to flush stdout/stderr immediately.
#    Without this, logs may not appear in `docker compose logs` in real time.

FROM python:3.12-slim

# ── System dependencies ────────────────────────────────────────────────────────
# gcc and libpq-dev are needed to compile asyncpg (C extension).
# We install and use them in the same RUN layer to minimize image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# ── Python environment ─────────────────────────────────────────────────────────
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

# ── Working directory ──────────────────────────────────────────────────────────
WORKDIR /app

# ── Install dependencies ───────────────────────────────────────────────────────
# Copy requirements first (before app code) so Docker can cache this layer.
# Changing app code won't re-run pip install — only changing requirements.txt will.
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ── Copy application code ──────────────────────────────────────────────────────
COPY . .

# ── Non-root user ─────────────────────────────────────────────────────────────
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app
USER appuser

# ── Health check ──────────────────────────────────────────────────────────────
# Docker will call this every 30s. If it fails 3 times, the container is
# marked unhealthy and docker-compose can restart it.
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# ── Default command ────────────────────────────────────────────────────────────
# --reload: auto-restart on code changes (development only).
# In production, remove --reload and add --workers 4.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
