# syntax=docker/dockerfile:1.7
# ============================================================================
# HW3_B Dockerfile — multi-stage, CPU-only torch, bundle baked in.
# ============================================================================

# --- Stage 1: builder ------------------------------------------------------
# We need a builder because the install of torch+transformers is large and
# we don't want the cache layers (or .pip cache) in the final image.
FROM python:3.11-slim AS builder

ENV PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /build

# Install CPU-only torch FIRST (the heaviest dep; ~700 MB).
# We pin to match bundle/requirements.txt exactly.
COPY requirements.txt /build/requirements.txt
RUN pip install --prefix=/install \
        torch==2.5.1 \
        --index-url https://download.pytorch.org/whl/cpu && \
    pip install --prefix=/install -r /build/requirements.txt


# --- Stage 2: runtime -------------------------------------------------------
FROM python:3.11-slim AS runtime

LABEL org.opencontainers.image.title="qbc12-hw03-b-encoder" \
      org.opencontainers.image.description="Encoder embedding + hybrid search" \
      org.opencontainers.image.source="HW3_B" \
      org.opencontainers.image.licenses="Apache-2.0"

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create non-root user (security: never run as root in prod)
RUN groupadd --gid 1001 qbc12 && \
    useradd  --uid 1001 --gid qbc12 --shell /bin/bash --create-home qbc12

WORKDIR /app

# Copy installed Python packages from builder
COPY --from=builder /install /usr/local

# Install bundle runtime deps NOT included in /install (transformers, tokenizers, safetensors).
# This runs in the runtime stage to avoid invalidating the builder's heavy torch cache layer.
# These are light packages (~30 MB total) and take ~1 min to download.
COPY bundle/requirements.txt /tmp/bundle-requirements.txt
RUN grep -E -v "torch|numpy" /tmp/bundle-requirements.txt > /tmp/filtered-requirements.txt && \
    pip install --no-cache-dir -r /tmp/filtered-requirements.txt && \
    rm /tmp/bundle-requirements.txt /tmp/filtered-requirements.txt
    
    # Copy the FastAPI app
COPY app/ /app/app/
RUN chmod +x /app/app/entrypoint.sh && \
    chown -R qbc12:qbc12 /app

# === Bundle baked in (MODEL_SOURCE=baked mode) ===
# For MODEL_SOURCE=local or =s3, replace this with:
#   VOLUME ["/bundle"]
# or remove entirely (the image becomes a "loader" that pulls from MinIO on boot).
COPY bundle/ /app/bundle/
RUN chown -R qbc12:qbc12 /app/bundle

# Switch to non-root
USER qbc12

# Expose port (FastAPI)
EXPOSE 8000

# Healthcheck — the /health endpoint must return 200 AND bundle_loaded=true
HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python -c "import urllib.request, sys; \
        r = urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3); \
        j = __import__('json').loads(r.read()); \
        sys.exit(0 if (j.get('status') == 'ok' and j.get('bundle_loaded')) else 1)"

# Default env
ENV BUNDLE_DIR=/app/bundle \
    BUNDLE_DEVICE=cpu \
    PORT=8000 \
    UVICORN_WORKERS=1 \
    LOG_LEVEL=info \
    PYTHONPATH=/app

# Entrypoint: sets the runtime contract, then execs uvicorn
ENTRYPOINT ["/app/app/entrypoint.sh"]
