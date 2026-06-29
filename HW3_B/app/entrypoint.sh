#!/usr/bin/env bash
# entrypoint.sh — runtime contract for the HW3_B container.
# Sets the env vars that test_env_contract.py requires, then execs uvicorn.

set -euo pipefail

export OMP_NUM_THREADS="${OMP_NUM_THREADS:-2}"
export MKL_NUM_THREADS="${MKL_NUM_THREADS:-2}"
export TOKENIZERS_PARALLELISM=false
export BUNDLE_DEVICE="${BUNDLE_DEVICE:-cpu}"
export PYTHONHASHSEED=0

echo "[entrypoint] BUNDLE_DIR=${BUNDLE_DIR:-/app/bundle}"
echo "[entrypoint] BUNDLE_DEVICE=${BUNDLE_DEVICE}"
echo "[entrypoint] OMP_NUM_THREADS=${OMP_NUM_THREADS}"
echo "[entrypoint] MKL_NUM_THREADS=${MKL_NUM_THREADS}"
echo "[entrypoint] TOKENIZERS_PARALLELISM=${TOKENIZERS_PARALLELISM}"

trap 'echo "[entrypoint] SIGTERM received, draining…"; kill -TERM "$PID" 2>/dev/null || true; wait "$PID" || true' TERM INT

exec uvicorn main:app \
  --host 0.0.0.0 \
  --port "${PORT:-8000}" \
  --workers "${UVICORN_WORKERS:-1}" \
  --log-level "${LOG_LEVEL:-info}"