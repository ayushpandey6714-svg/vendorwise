FROM python:3.14-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PORT=7860 \
    VENDORWISE_MODE=live \
    VENDORWISE_PUBLIC_DEMO=false \
    LLM_PROVIDER=openrouter \
    OPENROUTER_MODEL=openrouter/free \
    EMBEDDING_BACKEND=tfidf \
    VENDORWISE_DATA_DIR=/app/data \
    VENDORWISE_API_URL=http://127.0.0.1:8000 \
    OMP_NUM_THREADS=1 \
    OPENBLAS_NUM_THREADS=1

RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 appuser
WORKDIR /app
COPY requirements-docker.txt ./
RUN python -m pip install -r requirements-docker.txt && python -m pip check
COPY --chown=appuser:appuser . .
RUN mkdir -p /app/data && chown appuser:appuser /app/data
USER appuser
EXPOSE 7860
HEALTHCHECK --interval=30s --timeout=5s --start-period=90s \
    CMD python -c "import os,urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health',timeout=2); urllib.request.urlopen('http://127.0.0.1:'+os.getenv('PORT','7860')+'/_stcore/health',timeout=2)"
CMD ["python", "-m", "scripts.serve_container"]
