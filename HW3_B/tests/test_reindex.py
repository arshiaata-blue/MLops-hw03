"""test_reindex.py — bonus CLI smoke test (offline-safe)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parent.parent


def test_reindex_dry_run_help():
    """`python -m app.reindex --help` should exit 0 and list options."""
    r = subprocess.run(
        [sys.executable, "-m", "app.reindex", "--help"],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
    )
    assert r.returncode == 0
    assert "--source" in r.stdout
    assert "--limit" in r.stdout
    assert "--dry-run" in r.stdout
