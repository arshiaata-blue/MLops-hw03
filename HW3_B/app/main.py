from __future__ import annotations

import logging
import os
import time
from contextlib import asynccontextmanager

import numpy as np
from fastapi import FastAPI, HTTPException, status, Response

import client_pg
import client_qdrant
import config
import predictor as predictor_mod
from model_loader import ModelService
from schemas import (
    EmbedRequest,
    EmbedResponse,
    HealthResponse,
    ModelInfoResponse,
    PredictRequest,
    PredictResponse,
    RootResponse,
    SearchRequest,
    SearchResponse,
)
from search import hybrid_search

log = logging.getLogger("hw3_b")
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO").upper())


model_service = ModelService()


@asynccontextmanager
async def lifespan(app: FastAPI):
    log.info("HW3_B starting. BUNDLE_DIR=%s", config.BUNDLE_DIR)
    app.state.loaded = False
    model_service.load()
    if model_service.state.loaded:
        log.info("Bundle loaded: %s", model_service.state.bundle_dir)
        app.state.loaded = True
    else:
        log.error("Bundle load FAILED: %s", model_service.state.error)
        app.state.loaded = False
    yield
    log.info("HW3_B shutting down.")
    app.state.loaded = False


app = FastAPI(title=config.APP_TITLE, version=config.APP_VERSION, lifespan=lifespan)


# ---------------------------------------------------------------------------
# Root
# ---------------------------------------------------------------------------


@app.get("/", response_model=RootResponse, tags=["service"])
async def root():
    return RootResponse(
        message="QBC12 HW3 Encoder API", 
        docs="/docs", 
        health="/health", 
        version=config.APP_VERSION
    )


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse, tags=["service"])
async def health():
    bundle_ok = model_service.state.loaded
    qdrant_ok = client_qdrant.ping()
    pg_ok = client_pg.ping()
    
    status_code = "ok" if (bundle_ok and qdrant_ok and pg_ok) else "degraded"
    
    return HealthResponse(
        status=status_code,
        bundle_loaded=bundle_ok,
        bundle_dir=str(model_service.state.bundle_dir) if model_service.state.bundle_dir else "",
        qdrant_reachable=qdrant_ok,
        pg_reachable=pg_ok,
        error=model_service.state.error
    )


# K8s Liveness Probe: Just checks if app is running
@app.get("/healthz/live", tags=["service"])
async def live():
    return {"status": "live"}


# K8s Readiness Probe: Checks if model is actually loaded and ready to serve
@app.get("/healthz/ready", tags=["service"])
async def ready(response: Response):
    if not getattr(app.state, "loaded", False):
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
        return {"status": "not_ready", "model_loaded": False}
    return {"status": "ready", "model_loaded": True}


# ---------------------------------------------------------------------------
# Model info
# ---------------------------------------------------------------------------


@app.get("/model-info", response_model=ModelInfoResponse, tags=["model"])
async def model_info():
    if not model_service.state.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    vector_count = client_qdrant.vector_count(config.QDRANT_COLLECTION)
    
    return ModelInfoResponse(
        bundle_version=model_service.metadata.get("bundle_version", "0.1.0"),
        model_id=model_service.metadata.get("model_id", model_service.metadata.get("model_name", "unknown")),
        model_revision=model_service.metadata.get("model_revision", "main"),
        device=config.BUNDLE_DEVICE,
        max_seq_len=int(model_service.metadata.get("max_seq_len", config.EMBED_MAX_SEQ_LEN)),
        embedding_dim=int(model_service.metadata.get("embedding_dim", config.EMBED_DIM)),
        bundle_dir=str(model_service.state.bundle_dir) if model_service.state.bundle_dir else "",
        qdrant_collection=config.QDRANT_COLLECTION,
        qdrant_vector_count=vector_count
    )


# ---------------------------------------------------------------------------
# Embed
# ---------------------------------------------------------------------------


@app.post("/embed", response_model=EmbedResponse, tags=["embedding"])
async def embed(req: EmbedRequest):
    if not model_service.state.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
    
    if len(req.texts) > config.EMBED_BATCH_HARD_CAP:
        raise HTTPException(status_code=413, detail="Batch size exceeds hard cap")
        
    predictor = model_service.require_predictor()
    vectors = predictor_mod.embed_texts(predictor, req.texts)
    embeddings_list = vectors.tolist()
    
    return EmbedResponse(
        count=len(req.texts),
        dim=vectors.shape[1],
        embeddings=embeddings_list
    )


# ---------------------------------------------------------------------------
# /predict — single text → emotion label via nearest neighbor
# ---------------------------------------------------------------------------


@app.post("/predict", response_model=PredictResponse, tags=["embedding"])
async def predict(req: PredictRequest):
    if not model_service.state.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    t0 = time.perf_counter()
    
    predictor = model_service.require_predictor()
    vectors = predictor_mod.embed_texts(predictor, [req.text])
    query_vec_list = vectors[0].tolist()
    
    hits = client_qdrant.search(
        collection=config.QDRANT_COLLECTION,
        vector=query_vec_list,
        top_k=1,
        lang=None,
        primary=None,
        exclude_neutral=False
    )
    
    if not hits:
        raise HTTPException(status_code=404, detail="no match found in corpus")
        
    best = hits[0]
    payload = best.payload or {}
    label = payload.get("primary", payload.get("primary_label", "unknown"))
    matched_text = payload.get("text", "")
    
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    
    return PredictResponse(
        text=req.text,
        predicted_label=label,
        confidence=float(best.score),
        matched_text=matched_text,
        elapsed_ms=elapsed_ms
    )


# ---------------------------------------------------------------------------
# Search
# ---------------------------------------------------------------------------


@app.post("/search", response_model=SearchResponse, tags=["search"])
async def search(req: SearchRequest):
    if not model_service.state.loaded:
        raise HTTPException(status_code=503, detail="Model not loaded")
        
    predictor = model_service.require_predictor()
    query_vec = predictor_mod.embed_texts(predictor, [req.query])
    query_vec_list = query_vec[0].tolist()
    
    hits, took_ms = hybrid_search(
        query_vector=query_vec_list,
        top_k=req.top_k,
        lang=req.lang,
        primary=req.primary,
        exclude_neutral=req.exclude_neutral
    )
    
    return SearchResponse(
        query=req.query,
        count=len(hits),
        top_k=req.top_k,
        took_ms=took_ms,
        hits=hits
    )