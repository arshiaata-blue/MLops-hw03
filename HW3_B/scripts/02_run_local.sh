#!/usr/bin/env bash
# 02_run_local.sh — start the API with docker compose (Qdrant + PG + API).
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ ! -f .env ]]; then
  echo "ERROR: .env not found. Copy .env.example to .env and fill in your values."
  exit 1
fi

# Make sure the bundle is in place for the build context
rm -rf bundle
cp -R ../HW3_A/bundle bundle

echo "Starting Qdrant + Postgres + API…"
docker compose up -d

echo
echo "Waiting for API to become healthy (max 60s)…"
for i in {1..30}; do
  status=$(docker inspect -f '{{.State.Health.Status}}' qbc12-hw03-b-api-local 2>/dev/null || echo unknown)
  if [[ "$status" == "healthy" ]]; then
    echo "API is healthy."
    break
  fi
  echo "  ($i) health=$status — waiting 2s…"
  sleep 2
done

echo
echo "API logs (last 20 lines):"
docker compose logs --tail=20 api
