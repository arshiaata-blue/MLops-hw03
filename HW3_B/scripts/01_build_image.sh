#!/usr/bin/env bash
# 01_build_image.sh — build the HW3_B image.
set -euo pipefail

cd "$(dirname "$0")/.."

# We COPY ../HW3_A/bundle/ into the image during build. The path is relative
# to the build context (this folder). So we copy the bundle into ./bundle/
# as a build prep step (idempotent).
BUNDLE_SRC="../HW3_A/bundle"
if [[ ! -d "$BUNDLE_SRC/model" ]]; then
  echo "ERROR: $BUNDLE_SRC/model/ does not exist. Run 'make all' in HW3_A first."
  exit 1
fi
rm -rf bundle
cp -R "$BUNDLE_SRC" bundle

IMAGE="${IMAGE:-qbc12-hw03-b-encoder:dev}"
echo "Building ${IMAGE}…"
docker build -t "${IMAGE}" .

echo
echo "Built: ${IMAGE}"
echo "Run:   bash scripts/02_run_local.sh"
