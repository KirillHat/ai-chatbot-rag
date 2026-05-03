# syntax=docker/dockerfile:1.7

# ----- Builder -----
FROM python:3.11-slim AS builder
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential gcc \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# ----- Runtime -----
FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 \
    PATH=/home/app/.local/bin:$PATH \
    PORT=8000

# gosu lets the entrypoint drop from root → app *after* fixing volume
# ownership. Tiny (~2 MB), trusted (used by 100+ official Docker images),
# and properly handles signal forwarding so SIGTERM reaches uvicorn.
RUN apt-get update \
 && apt-get install -y --no-install-recommends gosu \
 && rm -rf /var/lib/apt/lists/*

# Non-root user — chromadb writes into ./data which we mount as a volume
RUN addgroup --system app && adduser --system --ingroup app --home /home/app app

COPY --from=builder --chown=app:app /root/.local /home/app/.local

WORKDIR /app
COPY --chown=app:app app/ ./app/
COPY --chown=app:app widget/ ./widget/
COPY --chown=app:app demo/ ./demo/
COPY --chown=app:app scripts/ ./scripts/
COPY --chown=app:app data/knowledge_base/ ./data/knowledge_base/
COPY docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN chmod +x /usr/local/bin/docker-entrypoint.sh \
 && mkdir -p /app/data/chroma /app/data/uploads && chown -R app:app /app/data

# We do NOT set USER app here — the entrypoint runs as root just long
# enough to chown the persistent volume mount, then drops to `app`.
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{p}/health',timeout=3).status==200 else 1)" || exit 1

ENTRYPOINT ["docker-entrypoint.sh"]
# Shell form so the host platform's $PORT is honoured at runtime (Railway,
# Cloud Run and Heroku all inject a dynamic port). Locally $PORT is unset
# and the default 8000 is used. `exec` keeps uvicorn as PID 1.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1"]
