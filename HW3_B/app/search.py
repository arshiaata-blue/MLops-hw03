"""app.search — hybrid (Qdrant ANN + PG audit) search orchestration."""
from __future__ import annotations

import time
from typing import List, Optional

from . import client_pg, client_qdrant
from . import config
from .schemas import SearchHit


# TODO: implement hybrid_search(query_vector, top_k, lang, primary, exclude_neutral) -> tuple[List[SearchHit], float]
# This function orchestrates a hybrid search:
#   1. Call client_qdrant.search() to get Qdrant ANN hits
#   2. Extract IDs from Qdrant results
#   3. Call client_pg.fetch_corpus_hits() to get the source-of-truth rows from Postgres
#   4. Zip Qdrant hits with PG rows to build SearchHit objects
#   5. Return (hits, took_ms) where took_ms is elapsed time in milliseconds
#
# HINT: qdr_hits = client_qdrant.search(collection=config.QDRANT_COLLECTION, vector=query_vector, top_k=top_k, lang=lang, primary=primary, exclude_neutral=exclude_neutral)
# HINT: ids = [str(h.id) for h in qdr_hits]
# HINT: pg_rows = client_pg.fetch_corpus_hits(ids)
# HINT: SearchHit(id=str(h.id), score=float(h.score), text=row["text"], primary=row["primary_label"], labels=list(row["labels"]), lang=row["lang"], source=row["source"])
# HINT: use time.perf_counter() to measure elapsed time
# HINT: return empty list if no Qdrant hits: [], (time.perf_counter() - t0) * 1000.0
def hybrid_search(
    query_vector: List[float], 
    top_k: int, 
    lang: Optional[str], 
    primary: Optional[str], 
    exclude_neutral: bool
) -> tuple[List[SearchHit], float]:
    t0 = time.perf_counter()
    
    qdr_hits = client_qdrant.search(
        collection=config.QDRANT_COLLECTION, 
        vector=query_vector, 
        top_k=top_k, 
        lang=lang, 
        primary=primary, 
        exclude_neutral=exclude_neutral
    )
    
    if not qdr_hits:
        took_ms = (time.perf_counter() - t0) * 1000.0
        return [], took_ms
        
    ids = [str(h.id) for h in qdr_hits]
    pg_rows = client_pg.fetch_corpus_hits(ids)
    
    # ساختن یک دیکشنری برای دسترسی سریع به سطرهای دیتابیس بر اساس آیدی
    pg_map = {row["id"]: row for row in pg_rows}
    
    hits = []
    for h in qdr_hits:
        h_id = str(h.id)
        if h_id in pg_map:
            row = pg_map[h_id]
            hit = SearchHit(
                id=h_id,
                score=float(h.score),
                text=row["text"],
                primary=row["primary_label"],
                labels=list(row["labels"]),
                lang=row["lang"],
                source=row["source"]
            )
            hits.append(hit)
            
    took_ms = (time.perf_counter() - t0) * 1000.0
    return hits, took_ms