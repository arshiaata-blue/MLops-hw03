"""test_adversarial.py — edge cases and error handling.

10 tests that stress the bundle with unusual inputs. Every test must pass.

Run from HW3_A/:
    PYTHONPATH=bundle python -m pytest tests/test_adversarial.py -v
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bundle"))

from predict import load_bundle, embed, similarity, info


# ---------------------------------------------------------------------------
# Test 1: Missing bundle directory
# ---------------------------------------------------------------------------
def test_missing_bundle_dir():
    """load_bundle() on nonexistent path must raise error."""
    with pytest.raises(Exception):
        load_bundle("/nonexistent/path/to/model")


# ---------------------------------------------------------------------------
# Test 2: Very long text (truncation works)
# ---------------------------------------------------------------------------
def test_very_long_text():
    """A text exceeding max_seq_len must still produce a valid embedding."""
    long_text = "the quick brown fox " * 1000  # way over 256 tokens
    emb = embed([long_text])
    assert emb.shape == (1, 384), f"Long text shape: {emb.shape}"
    # Must still be normalized
    norm = np.linalg.norm(emb[0])
    assert np.isclose(norm, 1.0, atol=1e-5), f"Long text norm: {norm}"


# ---------------------------------------------------------------------------
# Test 3: Unicode / non-English
# ---------------------------------------------------------------------------
def test_unicode_text():
    """Embeddings must work with emoji, Persian, Chinese, etc."""
    texts = [
        "I love this 🎉 so much",
        "این یک متن فارسی است",
        "这是一个中文句子",
        "Café naïve résumé",
    ]
    emb = embed(texts)
    assert emb.shape == (4, 384)
    assert emb.dtype == np.float32
    # All norms should be 1
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5), f"Unicode text norms: {norms}"


# ---------------------------------------------------------------------------
# Test 4: Numeric-only text
# ---------------------------------------------------------------------------
def test_numeric_text():
    """Purely numeric strings must produce valid embeddings."""
    texts = ["12345", "3.14159", "0", "-9999.99"]
    emb = embed(texts)
    assert emb.shape == (4, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 5: Single token text
# ---------------------------------------------------------------------------
def test_single_token_text():
    """A string that tokenizes to a single token must work."""
    text = ["."]
    emb = embed(text)
    assert emb.shape == (1, 384)
    assert np.isclose(np.linalg.norm(emb[0]), 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 6: Duplicate inputs produce identical outputs
# ---------------------------------------------------------------------------
def test_duplicate_texts():
    """The same text repeated must produce identical embeddings."""
    emb = embed(["Hello world", "Hello world", "Hello world"])
    assert emb.shape == (3, 384)
    sim01 = similarity(emb[0], emb[1])
    sim02 = similarity(emb[0], emb[2])
    assert np.isclose(sim01, 1.0, atol=1e-5), f"Duplicates not identical: {sim01}"
    assert np.isclose(sim02, 1.0, atol=1e-5), f"Duplicates not identical: {sim02}"


# ---------------------------------------------------------------------------
# Test 7: Batch of size 1
# ---------------------------------------------------------------------------
def test_batch_of_one():
    """Batch size 1 must still return a 2D array, not 1D."""
    emb = embed(["A single sentence"])
    assert emb.ndim == 2, f"Expected 2D, got {emb.ndim}D: shape {emb.shape}"
    assert emb.shape == (1, 384)


# ---------------------------------------------------------------------------
# Test 8: Large batch
# ---------------------------------------------------------------------------
def test_large_batch():
    """Batch of 100 texts must work without error."""
    texts = [f"This is sentence number {i}." for i in range(100)]
    emb = embed(texts)
    assert emb.shape == (100, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 9: Punctuation-only text
# ---------------------------------------------------------------------------
def test_punctuation_only():
    """Strings containing only punctuation must not crash."""
    texts = ["!!!", "???", "...", ".,!?;:"]
    emb = embed(texts)
    assert emb.shape == (4, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)


# ---------------------------------------------------------------------------
# Test 10: Whitespace-only text
# ---------------------------------------------------------------------------
def test_whitespace_only():
    """Whitespace strings must not crash and must return valid embeddings."""
    texts = [" ", "\t", "\n\n", "   "]
    emb = embed(texts)
    assert emb.shape == (4, 384)
    norms = np.linalg.norm(emb, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-5)
