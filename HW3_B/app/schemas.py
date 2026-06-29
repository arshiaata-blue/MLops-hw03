"""app.schemas — Pydantic request/response models.

extra="forbid" everywhere so Swagger rejects typos and unknown fields loudly
instead of silently dropping them (a real production incident class).
"""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


# ============================================================================
# Service — health + model-info + root
# ============================================================================

# TODO: define HealthResponse model with fields:
#   - status: Literal["ok", "degraded", "error"]
#   - bundle_loaded: bool
#   - bundle_dir: str
#   - qdrant_reachable: bool
#   - pg_reachable: bool
#   - error: Optional[str] = None
# HINT: use ConfigDict(extra="forbid") for all models so extra fields are rejected
class HealthResponse(BaseModel):
    status: Literal["ok", "degraded", "error"]
    bundle_loaded: bool
    bundle_dir: str
    qdrant_reachable: bool
    pg_reachable: bool
    error: Optional[str] = None

    model_config = ConfigDict(extra="forbid")


# TODO: define ModelInfoResponse model with fields:
#   - bundle_version: str
#   - model_id: str
#   - model_revision: str
#   - device: str
#   - max_seq_len: int
#   - embedding_dim: int
#   - bundle_dir: str
#   - qdrant_collection: str
#   - qdrant_vector_count: Optional[int] = None
# HINT: model_config = ConfigDict(extra="forbid")
class ModelInfoResponse(BaseModel):
    bundle_version: str
    model_id: str
    model_revision: str
    device: str
    max_seq_len: int
    embedding_dim: int
    bundle_dir: str
    qdrant_collection: str
    qdrant_vector_count: Optional[int] = None

    model_config = ConfigDict(extra="forbid")


# TODO: define RootResponse model with fields:
#   - message: str
#   - docs: str
#   - health: str
#   - version: str
# HINT: this is returned by the GET / endpoint
class RootResponse(BaseModel):
    message: str
    docs: str
    health: str
    version: str

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# /embed
# ============================================================================

# TODO: define EmbedRequest model:
#   - texts: List[str] = Field(..., min_length=1, max_length=256)
#   - Include extra="forbid" to reject unknown fields
# HINT: model_config = ConfigDict(
#     extra="forbid",
#     json_schema_extra={"example": {"texts": ["I love this so much"]}}
# )
class EmbedRequest(BaseModel):
    texts: List[str] = Field(..., min_length=1, max_length=256)

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={"example": {"texts": ["I love this so much"]}}
    )


# TODO: define EmbedResponse model:
#   - count: int          (number of embedded texts)
#   - dim: int            (embedding dimension, always 384)
#   - embeddings: List[List[float]]
# HINT: model_config = ConfigDict(extra="forbid")
class EmbedResponse(BaseModel):
    count: int
    dim: int
    embeddings: List[List[float]]

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# /search
# ============================================================================

# TODO: define SearchRequest model:
#   - query: str = Field(..., min_length=1, max_length=4096)
#   - top_k: int = Field(10, ge=1, le=100)   (default 10)
#   - lang: Optional[Literal["en"]] = None     (optional language filter)
#   - primary: Optional[str] = Field(None, max_length=64)  (filter by emotion)
#   - exclude_neutral: bool = Field(True)     (drop docs with only "neutral" label)
# HINT: model_config = ConfigDict(extra="forbid")
class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=4096)
    top_k: int = Field(10, ge=1, le=100)
    lang: Optional[Literal["en"]] = None
    primary: Optional[str] = Field(None, max_length=64)
    exclude_neutral: bool = Field(True)

    model_config = ConfigDict(extra="forbid")


# TODO: define SearchHit model:
#   - id: str
#   - score: float
#   - text: str
#   - primary: str
#   - labels: List[str]
#   - lang: str
#   - source: str
# HINT: model_config = ConfigDict(extra="forbid")
class SearchHit(BaseModel):
    id: str
    score: float
    text: str
    primary: str
    labels: List[str]
    lang: str
    source: str

    model_config = ConfigDict(extra="forbid")


# TODO: define SearchResponse model:
#   - query: str
#   - count: int
#   - top_k: int
#   - took_ms: float
#   - hits: List[SearchHit]
# HINT: model_config = ConfigDict(extra="forbid")
class SearchResponse(BaseModel):
    query: str
    count: int
    top_k: int
    took_ms: float
    hits: List[SearchHit]

    model_config = ConfigDict(extra="forbid")


# ============================================================================
# /predict — single text → predicted emotion label via nearest neighbor
# ============================================================================

# TODO: define PredictRequest model:
#   - text: str = Field(..., min_length=1, max_length=4096)  (single text)
# HINT: model_config = ConfigDict(extra="forbid")
class PredictRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4096)

    model_config = ConfigDict(extra="forbid")


# TODO: define PredictResponse model:
#   - text: str
#   - predicted_label: str   (emotion label from the closest corpus match)
#   - confidence: float      (cosine score of the top match)
#   - matched_text: str      (the corpus text that matched)
#   - elapsed_ms: float      (time in ms)
# HINT: model_config = ConfigDict(extra="forbid")
class PredictResponse(BaseModel):
    text: str
    predicted_label: str
    confidence: float
    matched_text: str
    elapsed_ms: float

    model_config = ConfigDict(extra="forbid")