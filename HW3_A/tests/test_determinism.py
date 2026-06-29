"""test_determinism.py — verify that embeddings are reproducible.

The bundle MUST produce identical embeddings for the same input across
multiple calls. This is enforced by:
   - torch.manual_seed(0)
   - model.eval()
   - torch.use_deterministic_algorithms(True)

Run from HW3_A/:
    PYTHONPATH=bundle python -m pytest tests/test_determinism.py -v
"""
from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bundle"))

from predict import embed


# ---------------------------------------------------------------------------
# Test: Determinism
# ---------------------------------------------------------------------------
def test_embed_deterministic():
    """Same input called twice must produce identical embeddings."""
    texts = [
        "I love this so much",
        "I hate this so much",
        "This is the best day of my life",
        "I am so angry right now",
    ]
    emb1 = embed(texts)
    emb2 = embed(texts)

    # Must be bit-identical
    np.testing.assert_array_equal(
        emb1, emb2,
        err_msg="Embeddings are NOT deterministic! Check torch.manual_seed(0) and model.eval()."
    )

    # Also check first call produces valid shape
    assert emb1.shape == (4, 384), f"Unexpected shape: {emb1.shape}"
    print("Determinism confirmed: 2 calls produced identical output.")
    print(f"First value: {emb1[0, 0]:.10f}")
