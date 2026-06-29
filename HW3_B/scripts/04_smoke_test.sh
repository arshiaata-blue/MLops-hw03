#!/usr/bin/env bash
# 04_smoke_test.sh — minimal curl-based smoke test against a running API.
# Use after `02_run_local.sh`.
set -euo pipefail

URL="${API_URL:-http://127.0.0.1:8000}"

echo "=== / ==="
curl -s "${URL}/" | python -m json.tool

echo
echo "=== /health ==="
curl -s "${URL}/health" | python -m json.tool

echo
echo "=== /model-info ==="
curl -s "${URL}/model-info" | python -m json.tool

echo
echo "=== /embed ==="
curl -s -X POST "${URL}/embed" \
  -H "Content-Type: application/json" \
  -d @data/valid_embed_request.json | python -m json.tool | head -30

echo
echo "Smoke OK. Open ${URL}/docs in a browser for the full Swagger."
