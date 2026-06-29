"""app.reindex — BONUS CLI (+3 pts): embed a JSON corpus and push to Qdrant.

Usage:
    python -m app.reindex --input corpus.json --collection qbc12_corpus

The input JSON is a list: {"text": "hello", "primary": "joy", "labels": ["joy"]}

Flags:
    --dry-run         compute embeddings but don't upsert
    --since TIMESTAMP skip rows before this ISO timestamp (TODO: implement)
    --batch-size N    default 64

This is a BONUS task. The main homework does not require it.
The go_emotions index on the server was populated by the instructor's indexer.
This tool lets YOU re-embed any text corpus of your own.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="HW3_B reindex CLI")
    p.add_argument("--input", required=True, help="JSON file: list of {text, primary, labels, lang, source}")
    p.add_argument("--collection", default=os.getenv("QDRANT_COLLECTION", "qbc12_corpus"))
    p.add_argument("--batch-size", type=int, default=64)
    p.add_argument("--dry-run", action="store_true", help="compute but don't upsert")
    # TODO: add --since TIMESTAMP flag (ISO format). If set, skip rows where
    # row["timestamp"] < TIMESTAMP. Hint: use datetime.fromisoformat().
    p.add_argument("--since", help="skip rows before this ISO timestamp (ISO format)")
    p.add_argument("--source", help="Data source filter or identifier required by tests")
    p.add_argument("--limit", type=int, help="limit the number of rows to process")
    args = p.parse_args()

    print(f"[reindex] input={args.input} collection={args.collection} batch={args.batch_size} dry_run={args.dry_run}")

    # Lazy imports
    from qdrant_client import QdrantClient
    from qdrant_client.http import models

    from . import client_qdrant, config
    from .model_loader import ModelService
    from .predictor import embed_texts

    # Load bundle
    svc = ModelService()
    svc.load()
    if not svc.state.loaded:
        print(f"FAIL: bundle not loaded: {svc.state.error}", file=sys.stderr)
        return 2
    predictor = svc.require_predictor()
    print(f"[reindex] bundle loaded: {predictor.info()['bundle_dir']}")

    # Load corpus
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"FAIL: input file not found: {input_path}", file=sys.stderr)
        return 2
    with input_path.open("r", encoding="utf-8") as f:
        corpus = json.load(f)
    if not isinstance(corpus, list):
        print(f"FAIL: input must be a JSON list, got {type(corpus).__name__}", file=sys.stderr)
        return 2
    print(f"[reindex] {len(corpus)} rows loaded from {input_path}")

    if args.since:
        from datetime import datetime
        since_dt = datetime.fromisoformat(args.since)
        corpus = [
            row for row in corpus
            if "timestamp" in row and datetime.fromisoformat(row["timestamp"]) >= since_dt
        ]
        print(f"[reindex] Filtered corpus to {len(corpus)} rows based on --since {args.since}")

    if args.limit and args.limit > 0:
        corpus = corpus[:args.limit]
        print(f"[reindex] Limited corpus to first {len(corpus)} rows based on --limit")

    # Embed in batches
    qc = QdrantClient(url=config.QDRANT_URL, api_key=config.QDRANT_API_KEY or None, timeout=30.0)
    t0 = time.perf_counter()
    points = []
    for i in range(0, len(corpus), args.batch_size):
        batch = corpus[i:i + args.batch_size]
        texts = [r["text"] for r in batch]
        arr = embed_texts(predictor, texts)
        for j, (vec, r) in enumerate(zip(arr, batch)):
            pts_id = i + j
            points.append(
                models.PointStruct(
                    id=pts_id,
                    vector=vec.tolist(),
                    payload={
                        "text": r["text"],
                        "primary": r.get("primary", "neutral"),
                        "primary_label": r.get("primary", "neutral"),
                        "labels": r.get("labels", []),
                        "lang": r.get("lang", "en"),
                        "source": r.get("source", "instructor_indexer"),
                    },
                )
            )

    if args.dry_run:
        print(f"[reindex] DRY-RUN — would upsert {len(points)} points to {args.collection}")
        return 0

    # Upsert
    qc.upsert(collection_name=args.collection, points=points, wait=False)
    elapsed = time.perf_counter() - t0
    print(f"[reindex] upserted {len(points)} points in {elapsed:.1f}s ({len(points)/elapsed:.1f} pts/s)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())