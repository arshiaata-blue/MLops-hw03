"""app.model_loader — wraps the HW3_A bundle's predict.py.

The bundle is the unit of truth. This module:
  1. Discovers the bundle on disk (env BUNDLE_DIR or ../HW3_A/bundle).
  2. Imports the BundlePredictor class.
  3. Verifies the MANIFEST.json SHAs at startup (fail-fast on corruption).
  4. Holds one global predictor instance (lifespan-managed by main.py).
"""
from __future__ import annotations

import hashlib
import json
import os
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


# --- Bundle discovery constants ---
# When the image is built with the bundle baked in, the structure is:
#   /app/
#     app/                    <-- this FastAPI service
#     bundle/                 <-- the bundle
#       model/                <-- model.safetensors + tokenizer files
#       predict.py            <-- BundlePredictor class
#       MANIFEST.json
#       metadata.json
#       requirements.txt

_DEFAULT_BUNDLE_IN_IMAGE = "/app/bundle"
_DEV_BUNDLE = str(
    Path(__file__).resolve().parent.parent.parent / "HW3_A" / "bundle"
)


# TODO: implement _resolve_bundle_dir() -> Path
# Resolve the bundle directory using this priority:
#   1. BUNDLE_DIR env var (if set and non-empty)
#   2. _DEFAULT_BUNDLE_IN_IMAGE (container path) if it exists
#   3. _DEV_BUNDLE (local dev path) if it exists
#   4. Raise FileNotFoundError with helpful message
# HINT: env = os.getenv("BUNDLE_DIR", "").strip()
# HINT: Path(env).resolve() if env else ...
# HINT: use Path.exists() to check if a path exists
def _resolve_bundle_dir() -> Path:
    env = os.getenv("BUNDLE_DIR", "").strip()
    if env:
        p = Path(env).resolve()
        if p.exists():
            return p
            
    p_image = Path(_DEFAULT_BUNDLE_IN_IMAGE).resolve()
    if p_image.exists():
        return p_image
        
    p_dev = Path(_DEV_BUNDLE).resolve()
    if p_dev.exists():
        return p_dev
        
    raise FileNotFoundError("Could not resolve bundle directory in any of the specified locations.")


# TODO: implement _sha256(path: Path) -> str
# Compute SHA-256 hash of a file, reading in 1MB chunks.
# HINT: h = hashlib.sha256()
# HINT: with path.open("rb") as f:
# HINT:     for chunk in iter(lambda: f.read(1 << 20), b""):
# HINT:         h.update(chunk)
# HINT: return h.hexdigest()
def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


# TODO: implement _verify_manifest(bundle_dir: Path) -> tuple[bool, str]
# Verify that MANIFEST.json contains all files and their SHAs match.
# 1. Check manifest_path = bundle_dir / "MANIFEST.json" exists
# 2. Parse it as JSON
# 3. For each (rel, expected) in manifest["files"].items():
#    - Reject if expected starts with "REPLACE" (placeholder not filled)
#    - Check file exists at bundle_dir / rel
#    - Compute SHA-256 and compare to expected
# 4. Return (True, f"{N} files OK") on success, (False, reason) on failure
# HINT: manifest = json.loads(manifest_path.read_text())
# HINT: check manifest.get("files", {})
def _verify_manifest(bundle_dir: Path) -> tuple[bool, str]:
    manifest_path = bundle_dir / "MANIFEST.json"
    if not manifest_path.exists():
        return False, "MANIFEST.json does not exist"
        
    try:
        manifest = json.loads(manifest_path.read_text())
    except Exception as e:
        return False, f"Failed to parse MANIFEST.json: {str(e)}"
        
    files = manifest.get("files", {})
    if not files:
        return False, "No files section in MANIFEST.json"
        
    file_count = 0
    for rel, expected in files.items():
        if expected.startswith("REPLACE"):
            return False, f"Placeholder detected for {rel}"
            
        target_file = bundle_dir / rel
        if not target_file.exists():
            return False, f"File missing on disk: {rel}"
            
        if _sha256(target_file) != expected:
            return False, f"SHA-256 mismatch for file: {rel}"
            
        file_count += 1
        
    return True, f"{file_count} files OK"


# TODO: define LoadState dataclass
# @dataclass
# class LoadState:
#     loaded: bool = False
#     error: Optional[str] = None
#     bundle_dir: Optional[Path] = None
#     manifest_ok: Optional[bool] = None
#     manifest_msg: Optional[str] = None
@dataclass
class LoadState:
    loaded: bool = False
    error: Optional[str] = None
    bundle_dir: Optional[Path] = None
    manifest_ok: Optional[bool] = None
    manifest_msg: Optional[str] = None


# TODO: define ModelService dataclass
# @dataclass
# class ModelService:
#     state: LoadState = field(default_factory=LoadState)
#     predictor: Optional[object] = None  # BundlePredictor instance from bundle
#     metadata: dict = field(default_factory=dict)
@dataclass
class ModelService:
    state: LoadState = field(default_factory=LoadState)
    predictor: Optional[object] = None  # BundlePredictor instance from bundle
    metadata: dict = field(default_factory=dict)

#     # TODO: implement load(self) -> None
#     # This method:
#     #   1. Calls _resolve_bundle_dir() to find the bundle
#     #   2. Calls _verify_manifest() and stores the result in state
#     #   3. Locates bundle_dir / "model" subdirectory (must exist)
#     #   4. Adds bundle_dir to sys.path so we can `from predict import BundlePredictor`
#     #   5. Imports BundlePredictor and creates instance: BundlePredictor(bundle_dir=model_dir)
#     #   6. Reads metadata.json from bundle_dir if it exists
#     #   7. Sets state.loaded = True on success, or captures error on failure
#     # HINT: model_dir = bundle_dir / "model"
#     # HINT: if str(bundle_dir) not in sys.path: sys.path.insert(0, str(bundle_dir))
#     # HINT: from predict import BundlePredictor  # type: ignore  # noqa: E402
#     # HINT: self.predictor = BundlePredictor(bundle_dir=model_dir)
#     # HINT: meta_path = bundle_dir / "metadata.json"
#     # HINT: if meta_path.exists(): self.metadata = json.loads(meta_path.read_text())
#     #
    def load(self) -> None:
        try:
            bundle_dir = _resolve_bundle_dir()
            self.state.bundle_dir = bundle_dir
            
            ok, msg = _verify_manifest(bundle_dir)
            self.state.manifest_ok = ok
            self.state.manifest_msg = msg
            if not ok:
                raise ValueError(f"Manifest verification failed: {msg}")
                
            model_dir = bundle_dir / "model"
            if not model_dir.exists():
                raise FileNotFoundError(f"Model subdirectory missing: {model_dir}")
                
            if str(bundle_dir) not in sys.path:
                sys.path.insert(0, str(bundle_dir))
                
            from predict import BundlePredictor  # type: ignore  # noqa: E402
            
            self.predictor = BundlePredictor(bundle_dir=model_dir)
            
            meta_path = bundle_dir / "metadata.json"
            if meta_path.exists():
                self.metadata = json.loads(meta_path.read_text())
                
            self.state.loaded = True
        except Exception as e:
            self.state.loaded = False
            self.state.error = str(e)

#     # TODO: implement require_predictor(self) -> object
#     # Return the predictor instance. Raise RuntimeError if not loaded.
#     # HINT: if not self.state.loaded or self.predictor is None: raise RuntimeError(...)
    def require_predictor(self) -> object:
        if not self.state.loaded or self.predictor is None:
            raise RuntimeError(f"Predictor is not loaded. Error state: {self.state.error}")
        return self.predictor

#     # TODO: implement info(self) -> dict
#     # Return a dict with bundle status for debugging /model-info
#     # HINT: return {"bundle_loaded": self.state.loaded, "bundle_dir": ..., "metadata": self.metadata, ...}
    def info(self) -> dict:
        return {
            "bundle_loaded": self.state.loaded,
            "bundle_dir": str(self.state.bundle_dir) if self.state.bundle_dir else None,
            "metadata": self.metadata,
            "manifest_ok": self.state.manifest_ok,
            "manifest_msg": self.state.manifest_msg,
            "error": self.state.error
        }