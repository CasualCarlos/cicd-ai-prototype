# Multi-stage build: builder installs dependencies, runtime runs the app.

# ── Stage 1: builder ────────────────────────────────────────────────────────
FROM python:3.11-slim AS builder

WORKDIR /build

# Install build tools needed for some packages
RUN apt-get update && apt-get install -y --no-install-recommends gcc && \
    rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && \
    pip install --prefix=/install --no-cache-dir -r requirements.txt


# ── Stage 2: runtime ────────────────────────────────────────────────────────
FROM python:3.11-slim AS runtime

WORKDIR /app

# Copy installed packages from builder
COPY --from=builder /install /usr/local

# Non-root user
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser

# Copy application source
COPY app/ ./app/
COPY requirements.txt .

# Create writable directory for SQLite database
RUN mkdir -p /app/data && chown appuser:appgroup /app/data

USER appuser

EXPOSE 5000

ENV FLASK_APP=app.main
ENV FLASK_RUN_HOST=0.0.0.0
ENV DATABASE=/app/data/app.db

CMD ["python", "-m", "flask", "run"]
