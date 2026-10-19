# syntax=docker/dockerfile:1
FROM python:3.12-slim-bookworm AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PIP_NO_CACHE_DIR=1 \
    CONTAMATE_HOME=/data CONTAMATE_DOCKER=1 CONTAMATE_OLLAMA_URL=http://ollama:11434
WORKDIR /app
RUN groupadd --gid 10001 contamate && useradd --uid 10001 --gid 10001 --create-home contamate
COPY pyproject.toml README.md ./
COPY src ./src
RUN python -m pip install --no-cache-dir . 'fastapi>=0.115,<1' 'uvicorn>=0.34,<1' 'python-multipart>=0.0.20,<1' && \
    mkdir -p /data /imports /samples && chown -R contamate:contamate /data /app
COPY web ./web
COPY scripts ./scripts
USER contamate
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=4s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/healthz', timeout=3)"
CMD ["uvicorn", "contamate.api:app", "--host", "0.0.0.0", "--port", "8765", "--workers", "1", "--proxy-headers", "false"]
