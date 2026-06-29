"""test_tokenization.py — verify tokenizer behavior in the bundle.

5 tests that validate tokenization is correct and consistent.

Run from HW3_A/:
    PYTHONPATH=bundle python -m pytest tests/test_tokenization.py -v
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bundle"))

from predict import load_bundle, info, EMBEDDING_DIM


@pytest.fixture(scope="module")
def tokenizer():
    """Load tokenizer once for all tests."""
    model, tok = load_bundle()
    return tok


# ---------------------------------------------------------------------------
# Test 1: Tokenizer loads and produces expected keys
# ---------------------------------------------------------------------------
def test_tokenizer_output_has_required_keys(tokenizer):
    """Tokenization output must contain input_ids and attention_mask."""
    encoded = tokenizer("Hello world", return_tensors="pt")
    assert "input_ids" in encoded, "Missing input_ids"
    assert "attention_mask" in encoded, "Missing attention_mask"


# ---------------------------------------------------------------------------
# Test 2: input_ids shape is (batch, seq_len), seq_len respects max_length
# ---------------------------------------------------------------------------
def test_seq_len_respects_max(tokenizer):
    """All tokenized sequences must be <= max_seq_len from info()."""
    max_len = info()["max_seq_len"]
    texts = ["Hello world", "The quick brown fox jumps over the lazy dog " * 9]  # ~360 words
    encoded = tokenizer(texts, padding=True, truncation=True, max_length=max_len, return_tensors="pt")
    seq_len = encoded["input_ids"].shape[1]
    assert seq_len <= max_len, f"Sequence length {seq_len} exceeds max {max_len}"


# ---------------------------------------------------------------------------
# Test 3: Padding produces equal-length sequences
# ---------------------------------------------------------------------------
def test_padding_equal_lengths(tokenizer):
    """Padded sequences must all have the same length."""
    texts = ["Hi", "A much longer sentence that should be padded or truncated to match"]
    encoded = tokenizer(texts, padding=True, truncation=True, max_length=256, return_tensors="pt")
    # Both sequences should have same length
    shape = encoded["input_ids"].shape
    assert shape[0] == 2, f"Expected batch size 2, got {shape[0]}"
    # The seq_len should be determined by the longer text
    print(f"Batch shape: {shape}")


# ---------------------------------------------------------------------------
# Test 4: Special tokens exist (CLS, SEP, PAD)
# ---------------------------------------------------------------------------
def test_special_tokens_exist(tokenizer):
    """Tokenizer must have CLS, SEP, and PAD tokens defined."""
    assert tokenizer.cls_token is not None, "CLS token not defined"
    assert tokenizer.sep_token is not None, "SEP token not defined"
    assert tokenizer.pad_token is not None, "PAD token not defined"
    print(f"CLS='{tokenizer.cls_token}', SEP='{tokenizer.sep_token}', PAD='{tokenizer.pad_token}'")


# ---------------------------------------------------------------------------
# Test 5: Tokenizer round-trip
# ---------------------------------------------------------------------------
def test_tokenizer_roundtrip(tokenizer):
    """decode(encode(text)) should produce similar output (ignoring case/spaces)."""
    text = "I love this so much"
    encoded = tokenizer(text, return_tensors="pt")
    decoded = tokenizer.decode(encoded["input_ids"][0], skip_special_tokens=True, clean_up_tokenization_spaces=True)
    # Decoded text should contain the original words (ignoring case and trailing punctuation)
    for word in text.lower().split():
        assert word in decoded.lower(), f"Word '{word}' not found in decoded: '{decoded}'"
    print(f"Original: '{text}'")
    print(f"Decoded:  '{decoded}'")
