"""app.client_qdrant — Qdrant client (read-only API key)."""
from __future__ import annotations

import time
from typing import List, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models

from . import config


# TODO: create a singleton QdrantClient instance
# HINT: use a module-level variable _client: Optional[QdrantClient] = None
# HINT: implement get_client() -> QdrantClient that lazily creates the client
# HINT: QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY or None, timeout=10.0)
_client: Optional[QdrantClient] = None

def get_client() -> QdrantClient:
    global _client
    if _client is None:
        _client = QdrantClient(
            url=config.QDRANT_URL, 
            api_key=config.QDRANT_API_KEY or None, 
            timeout=10
        )
    return _client


# TODO: implement ping() -> bool
# Try to list collections to verify connectivity. Return True if reachable, False otherwise.
# HINT: call get_client().get_collections()
def ping() -> bool:
    try:
        get_client().get_collections()
        return True
    except Exception:
        return False


# TODO: implement vector_count(collection: str) -> Optional[int]
# Return the number of vectors in a collection, or None on error.
# HINT: get_client().get_collection(collection_name=collection).vectors_count
def vector_count(collection: str) -> Optional[int]:
    try:
        return get_client().get_collection(collection_name=collection).vectors_count
    except Exception:
        return None


# TODO: implement search(collection, vector, top_k, lang, primary, exclude_neutral) -> List[models.ScoredPoint]
# Run an ANN search with optional payload filters.
# HINT: build a qdrant_client.http.models.Filter with must/must_not conditions
# HINT: must conditions for lang and primary (if provided)
# HINT: must_not condition for primary="neutral" if exclude_neutral is True
# HINT: call get_client().search(collection_name=..., query_vector=..., limit=..., query_filter=..., with_payload=True, with_vectors=False)
def search(
    collection: str, 
    vector: List[float], 
    top_k: int, 
    lang: Optional[str], 
    primary: Optional[str], 
    exclude_neutral: bool
) -> List[models.ScoredPoint]:
    must_conditions = []
    must_not_conditions = []

    if lang is not None:
        must_conditions.append(
            models.FieldCondition(
                key="lang", 
                match=models.MatchValue(value=lang)
            )
        )

    if primary is not None:
        must_conditions.append(
            models.FieldCondition(
                key="primary", 
                match=models.MatchValue(value=primary)
            )
        )

    if exclude_neutral:
        must_not_conditions.append(
            models.FieldCondition(
                key="primary", 
                match=models.MatchValue(value="neutral")
            )
        )

    query_filter = None
    if must_conditions or must_not_conditions:
        query_filter = models.Filter(
            must=must_conditions if must_conditions else None,
            must_not=must_not_conditions if must_not_conditions else None
        )

    return get_client().search(
        collection_name=collection,
        query_vector=vector,
        limit=top_k,
        query_filter=query_filter,
        with_payload=True,
        with_vectors=False
    )