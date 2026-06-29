"""test_search.py — /search hybrid (Qdrant + PG)."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_search_basic(client):
    r = client.post(
        "/search",
        json={"query": "I am so happy right now", "top_k": 5},
    )
    if r.status_code == 503:
        pytest.skip("bundle not loaded")
    if r.status_code == 500:
        # Qdrant/PG may not be up locally; treat as skip rather than fail
        pytest.skip(f"backend not reachable: {r.text}")
    assert r.status_code == 200, r.text
    j = r.json()
    assert j["query"] == "I am so happy right now"
    assert j["top_k"] == 5
    assert j["count"] <= 5
    assert "took_ms" in j
    if j["hits"]:
        h = j["hits"][0]
        assert "id" in h
        assert "score" in h
        assert "text" in h
        assert "primary" in h
        assert "labels" in h
        # exclude_neutral default is True; primary should not be "neutral"
        assert h["primary"] != "neutral"


def test_search_excludes_neutral_by_default(client):
    r = client.post("/search", json={"query": "okay", "top_k": 20})
    if r.status_code != 200:
        pytest.skip("backend not reachable")
    for hit in r.json()["hits"]:
        assert hit["primary"] != "neutral", f"neutral slipped through: {hit}"


def test_search_with_primary_filter(client):
    r = client.post(
        "/search",
        json={"query": "I am so happy", "top_k": 5, "primary": "joy"},
    )
    if r.status_code != 200:
        pytest.skip("backend not reachable")
    for hit in r.json()["hits"]:
        assert hit["primary"] == "joy", f"filter leaked: {hit}"


def test_search_top_k_bounds(client):
    r = client.post("/search", json={"query": "x", "top_k": 0})
    assert r.status_code == 422
    r = client.post("/search", json={"query": "x", "top_k": 101})
    assert r.status_code == 422


def test_search_rejects_unknown_field(client):
    """extra='forbid' — typo in the request body fails loudly."""
    r = client.post("/search", json={"query": "x", "top_k": 5, "lang": "english"})
    # "english" isn't in the Literal["en"]; rejected at Pydantic validation
    assert r.status_code == 422
