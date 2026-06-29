#!/usr/bin/env bash
# 03_push_image.sh — tag and push your HW3_C image to the local registry.
# Run this AFTER building with Dockerfile.hw3c and BEFORE deploying to k3s.
#
# Usage:
#   REGISTRY=185.50.38.163:35000 USERNAME=nazanin_hesari bash scripts/03_push_image.sh
set -euo pipefail

cd "$(dirname "$0")/.."

REGISTRY="${REGISTRY:?Set REGISTRY to 185.50.38.163:35000}"
USERNAME="${USERNAME:?Set USERNAME to your Quera username}"
IMAGE_TAG="${REGISTRY}/qbc12-embedder-${USERNAME}:v1"

docker tag qbc12-hw03-b-encoder:dev "${IMAGE_TAG}"
docker push "${IMAGE_TAG}"

echo
echo "Pushed: ${IMAGE_TAG}"
echo "The k3s cluster will pull this image on pod start."
