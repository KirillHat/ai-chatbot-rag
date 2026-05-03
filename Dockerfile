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

# Non-root user — chromadb writes into ./data which we mount as a volume
RUN addgroup --system app && adduser --system --ingroup app --home /home/app app

COPY --from=builder --chown=app:app /root/.local /home/app/.local

WORKDIR /app
COPY --chown=app:app app/ ./app/
COPY --chown=app:app widget/ ./widget/
COPY --chown=app:app demo/ ./demo/
COPY --chown=app:app scripts/ ./scripts/
COPY --chown=app:app data/knowledge_base/ ./data/knowledge_base/
RUN mkdir -p /app/data/chroma /app/data/uploads && chown -R app:app /app/data

USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "import os,urllib.request,sys; p=os.environ.get('PORT','8000'); sys.exit(0 if urllib.request.urlopen(f'http://127.0.0.1:{p}/health',timeout=3).status==200 else 1)" || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
