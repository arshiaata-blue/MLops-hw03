#!/usr/bin/env bash
# 01_upload_to_minio.sh — Upload the bundle to MinIO.
# Uses mc (MinIO client). Must be configured first.
#
# Prerequisites:
#   1. Install mc: https://min.io/docs/minio/linux/reference/minio-mc.html
#   2. source .env (sets MINIO_ENDPOINT, MINIO_ACCESS_KEY, MINIO_SECRET_KEY, etc.)
#
# Usage:
#   source .env && bash scripts/01_upload_to_minio.sh
set -euo pipefail

cd "$(dirname "$0")/.."

: "${MINIO_ENDPOINT:?MINIO_ENDPOINT must be set in .env}"
: "${MINIO_ACCESS_KEY:?MINIO_ACCESS_KEY must be set}"
: "${MINIO_SECRET_KEY:?MINIO_SECRET_KEY must be set}"
: "${MINIO_BUCKET:=hw03-bundles}"
: "${STUDENT_USERNAME:?STUDENT_USERNAME must be set}"
: "${MINIO_PREFIX:=${STUDENT_USERNAME}/}"

# Configure mc alias (one-time per session)
echo "Configuring MinIO alias 'qbc12'..."
mc alias set qbc12 "http://${MINIO_ENDPOINT}" "${MINIO_ACCESS_KEY}" "${MINIO_SECRET_KEY}" >/dev/null 2>&1 || {
    echo "ERROR: Failed to configure mc alias. Check your credentials."
    exit 1
}

# Create bucket if missing (idempotent)
mc mb "qbc12/${MINIO_BUCKET}" 2>/dev/null || true
echo "Bucket: ${MINIO_BUCKET}"

# Upload the bundle (exclude git metadata, the .commit marker, etc.)
echo "Uploading bundle/ → s3://${MINIO_BUCKET}/${MINIO_PREFIX}"
mc cp --recursive \
    --exclude "*.git*" \
    --exclude "*.commit" \
    "bundle/" \
    "qbc12/${MINIO_BUCKET}/${MINIO_PREFIX}"

echo ""
echo "=== Verification ==="
echo "Files on MinIO:"
mc ls --recursive "qbc12/${MINIO_BUCKET}/${MINIO_PREFIX}" | head -30
echo ""
echo "Done. Your bundle is at: s3://${MINIO_BUCKET}/${MINIO_PREFIX}"
