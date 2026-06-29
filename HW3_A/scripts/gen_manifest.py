#!/usr/bin/env python
"""
gen_manifest.py — Generate MANIFEST.json with SHA-256 hashes.

Recursively hashes every file under bundle/ (excluding MANIFEST.json itself)
and writes bundle/MANIFEST.json.

Usage:
    python scripts/gen_manifest.py

The student can use this as a reference, but must implement their own
version in the notebook (Cell 6 — Step 3).
"""
from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


def sha256(filepath: Path) -> str:
    """Compute SHA-256 hex digest of a file."""
    h = hashlib.sha256()
    with filepath.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def generate(bundle_root: str | None = None) -> dict:
    """Generate manifest dict for all files under bundle_root."""
    root = Path(bundle_root or os.path.join(os.path.dirname(__file__), "..", "bundle"))
    root = root.resolve()

    if not root.exists():
        raise FileNotFoundError(f"Bundle directory not found: {root}")

    files = {}
    for p in sorted(root.rglob("*")):
        if p.is_file() and p.name != "MANIFEST.json":
            rel = str(p.relative_to(root))
            files[rel] = sha256(p)

    manifest = {
        "format_version": 1,
        "schema_version": "1.0",
        "bundle_version": "1.0.0",
        "files": files,
        "generated_at_utc": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "generator": "scripts/gen_manifest.py",
    }
    return manifest


def main():
    root = os.path.join(os.path.dirname(__file__), "..", "bundle")
    manifest = generate(root)

    out_path = Path(root) / "MANIFEST.json"
    out_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    print(f"MANIFEST.json written with {len(manifest['files'])} files:")
    for rel, h in sorted(manifest["files"].items()):
        print(f"  {h[:16]}…  {rel}")


if __name__ == "__main__":
    main()
