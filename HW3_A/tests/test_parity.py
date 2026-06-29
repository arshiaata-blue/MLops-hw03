"""test_parity.py — verify the bundle produces correct embeddings.

7 tests that validate the bundle works correctly. All must pass before
you can register in MLflow or upload to MinIO.

Run from HW3_A/:
    PYTHONPATH=bundle python -m pytest tests/test_parity.py -v
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

# Ensure bundle/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bundle"))

from predict import load_bundle, embed, similarity, info, EMBEDDING_DIM, BUNDLE_DIR


# ---------------------------------------------------------------------------
# Test 1: Bundle can be loaded
# ---------------------------------------------------------------------------
def test_predictor_loads():
    """info() returns correct metadata after load_bundle()."""
    model, tokenizer = load_bundle()
    assert model is not None, "load_bundle() returned None for model"
    assert tokenizer is not None, "load_bundle() returned None for tokenizer"

    meta = info()
    assert isinstance(meta, dict), "info() must return a dict"
    assert meta["embedding_dim"] == EMBEDDING_DIM, f"Expected dim {EMBEDDING_DIM}"
    assert meta["device"] in ("cpu", "cuda"), f"Unexpected device: {meta['device']}"
    print("info:", meta)


# ---------------------------------------------------------------------------
# Test 2: Single text produces correct shape
# ---------------------------------------------------------------------------
def test_embed_single_text():
    """embed() on one text returns shape (1, 384)."""
    emb = embed(["I love this so much"])
    assert emb.shape == (1, EMBEDDING_DIM), f"Expected (1, {EMBEDDING_DIM}), got {emb.shape}"
    assert emb.dtype == np.float32, f"Expected float32, got {emb.dtype}"


# ---------------------------------------------------------------------------
# Test 3: Multiple texts
# ---------------------------------------------------------------------------
def test_embed_multiple_texts():
    """embed() on 3 texts returns shape (3, 384)."""
    texts = ["I love this", "I hate this", "The food was okay"]
    emb = embed(texts)
    assert emb.shape == (3, EMBEDDING_DIM), f"Expected (3, {EMBEDDING_DIM}), got {emb.shape}"
    assert emb.dtype == np.float32


# ---------------------------------------------------------------------------
# Test 4: L2 unit norm
# ---------------------------------------------------------------------------
def test_l2_unit_norm():
    """Every output vector must have L2 norm ≈ 1.0 (normalized)."""
    texts = ["I love this so much", "I hate this so much", "This is the best day of my life"]
    emb = embed(texts)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5), f"Non-unit norms: {norms}"
    print(f"L2 norms: {norms}")


# ---------------------------------------------------------------------------
# Test 5: Empty input
# ---------------------------------------------------------------------------
def test_empty_input_returns_empty():
    """embed([]) returns (0, 384) float32 array."""
    arr = embed([])
    assert arr.shape == (0, EMBEDDING_DIM), f"Expected (0, {EMBEDDING_DIM}), got {arr.shape}"
    assert arr.dtype == np.float32


# ---------------------------------------------------------------------------
# Test 6: Similarity — opposite sentiment
# ---------------------------------------------------------------------------
def test_similarity_opposite():
    """Semantically opposite sentences should have low cosine similarity."""
    emb = embed(["I love this so much", "I hate this so much"])
    sim = similarity(emb[0], emb[1])
    assert -1.0 <= sim <= 1.0, f"Similarity {sim} out of range"
    # Opposite sentiments: similarity should be < 0.8 (not too close)
    assert sim < 0.9, f"Opposite sentences too similar: {sim:.4f}"
    print(f"Similarity (opposite): {sim:.4f}")


# ---------------------------------------------------------------------------
# Test 7: Similarity — identical
# ---------------------------------------------------------------------------
def test_similarity_identical():
    """Identical text should have cosine ≈ 1.0."""
    emb = embed(["I love this so much", "I love this so much"])
    sim = similarity(emb[0], emb[1])
    assert np.isclose(sim, 1.0, atol=1e-4), f"Identical text not similar enough: {sim:.6f}"
    print(f"Similarity (identical): {sim:.6f}")
