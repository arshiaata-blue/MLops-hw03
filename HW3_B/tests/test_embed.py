"""test_embed.py — /embed and /predict end-to-end."""
from __future__ import annotations

import numpy as np
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_embed_basic(client):
    r = client.post("/embed", json={"texts": ["hello world", "goodbye world"]})
    if r.status_code == 503:
        pytest.skip("bundle not loaded — run HW3_A 'make all' first")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["count"] == 2
    assert j["dim"] == 384
    assert len(j["embeddings"]) == 2
    assert len(j["embeddings"][0]) == 384


def test_embed_l2_normalized(client):
    r = client.post("/embed", json={"texts": ["I love this", "I hate this"]})
    if r.status_code == 503:
        pytest.skip("bundle not loaded")
    arr = np.array(r.json()["embeddings"])
    norms = np.linalg.norm(arr, axis=1)
    assert np.allclose(norms, 1.0, atol=1e-4), f"non-unit norms: {norms}"


def test_embed_rejects_empty(client):
    r = client.post("/embed", json={"texts": []})
    assert r.status_code == 422  # Pydantic min_length=1


def test_embed_rejects_extra_field(client):
    """extra='forbid' — leakage field is rejected loudly, not silently dropped."""
    r = client.post("/embed", json={"texts": ["x"], "leakage_target": "joy"})
    assert r.status_code == 422


def test_embed_rejects_oversize_batch(client):
    big = ["x"] * 300
    r = client.post("/embed", json={"texts": big})
    # Either 422 (Pydantic max_length=256) or 413 (our hard cap)
    assert r.status_code in (413, 422)


def test_predict_returns_label(client):
    """Predict embeds a single text, searches Qdrant, returns a label."""
    r = client.post("/predict", json={"text": "I love this so much"})
    if r.status_code == 503:
        pytest.skip("bundle not loaded")
    assert r.status_code == 200, r.text
    j = r.json()
    assert "text" in j and j["text"] == "I love this so much"
    assert "predicted_label" in j and isinstance(j["predicted_label"], str) and len(j["predicted_label"]) > 0
    assert "confidence" in j and 0 <= j["confidence"] <= 1
    assert "matched_text" in j and isinstance(j["matched_text"], str) and len(j["matched_text"]) > 0
    assert "elapsed_ms" in j

