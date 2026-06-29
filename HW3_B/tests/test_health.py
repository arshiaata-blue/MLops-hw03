"""test_health.py — /, /health, /model-info smoke tests."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture(scope="module")
def client() -> TestClient:
    return TestClient(app)


def test_root(client):
    r = client.get("/")
    assert r.status_code == 200
    j = r.json()
    assert j["docs"] == "/docs"
    assert j["health"] == "/health"


def test_health_payload_shape(client):
    r = client.get("/health")
    assert r.status_code == 200
    j = r.json()
    assert "status" in j
    assert "bundle_loaded" in j
    assert "qdrant_reachable" in j
    assert "pg_reachable" in j
    # When run locally without Qdrant/PG, status should be "ok" or "degraded", not 5xx


def test_model_info_requires_bundle(client):
    """If the bundle fails to load, /model-info should 503, not 500."""
    r = client.get("/model-info")
    # Either 200 (bundle loaded) or 503 (bundle not loaded). Never 500.
    assert r.status_code in (200, 503)
