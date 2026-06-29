#!/usr/bin/env python
"""
download_model.py — Download all-MiniLM-L6-v2 from HuggingFace.

Saves 6 files to bundle/model/:
    config.json
    tokenizer_config.json
    tokenizer.json
    vocab.txt
    special_tokens_map.json
    model.safetensors

Usage:
    python scripts/download_model.py

Environment variables:
    MODEL_ID     — HuggingFace model ID (default: sentence-transformers/all-MiniLM-L6-v2)
    BUNDLE_DIR   — where to save (default: ./bundle/model)
    MODEL_REVISION — git revision (default: main)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

MODEL_ID = os.getenv("EMBEDDING_MODEL_ID", "sentence-transformers/all-MiniLM-L6-v2")
BUNDLE_DIR = os.getenv("BUNDLE_DIR", "./bundle/model")
REVISION = os.getenv("MODEL_REVISION", "main")

REQUIRED_FILES = [
    "config.json",
    "tokenizer_config.json",
    "tokenizer.json",
    "vocab.txt",
    "special_tokens_map.json",
    "model.safetensors",
]


def download():
    from huggingface_hub import snapshot_download, HfApi

    dest = Path(BUNDLE_DIR).resolve()
    dest.mkdir(parents=True, exist_ok=True)

    # Check if already downloaded
    missing = [f for f in REQUIRED_FILES if not (dest / f).exists()]
    if not missing:
        print(f"All {len(REQUIRED_FILES)} files already present in {dest}")
        print(f"Skipping download. Delete {dest}/ to re-download.")
        return

    print(f"Downloading {MODEL_ID} @ {REVISION}")
    print(f"Missing files: {missing}")
    print(f"Destination: {dest}")

    snapshot_path = snapshot_download(
        repo_id=MODEL_ID,
        revision=REVISION,
        local_dir=str(dest),
        allow_patterns=REQUIRED_FILES,
    )
    print(f"Snapshot downloaded to: {snapshot_path}")

    # Save the actual git commit hash
    try:
        commit = HfApi().model_info(MODEL_ID, revision=REVISION).sha
        (dest / ".commit").write_text(commit)
        print(f"Resolved commit: {commit}")
    except Exception as e:
        print(f"Warning: could not resolve commit hash: {e}")

    # Verify all files exist
    for fname in REQUIRED_FILES:
        if not (dest / fname).exists():
            print(f"ERROR: {fname} missing after download!", file=sys.stderr)
            sys.exit(1)

    print(f"Done. {len(REQUIRED_FILES)} files saved to {dest}/")
    for fname in sorted(REQUIRED_FILES):
        fpath = dest / fname
        size_mb = fpath.stat().st_size / (1024 * 1024)
        print(f"  {fname:35s}  {size_mb:.1f} MB")


if __name__ == "__main__":
    download()
