# HW3_B — Containerize the bundle (FastAPI + Docker + compose)

## Goal

Take the frozen bundle from HW3_A, package it into a Docker image, expose it
through a FastAPI service with **6 endpoints**, and verify end-to-end with
`docker compose`.

## What you'll build

You will write the FastAPI service that wraps your HW3_A bundle. The code files
in `app/` have `# TODO:` markers where you need to write implementation.

## Your workspace

```bash
cp .env.example .env
# Fill in your 7 values from hw03_credentials_handout.csv + SHARED.txt
```

**Time: 18h** | **Points: 35**

## Endpoints you must implement

| Method | Path          | What it does |
|--------|---------------|--------------|
| GET    | `/`           | Service banner |
| GET    | `/health`     | Bundle + Qdrant + PG reachability |
| GET    | `/model-info` | Bundle metadata + Qdrant vector count |
| POST   | `/embed`      | texts → 384-dim L2-normalized vectors |
| POST   | `/predict`    | Single text → predicted emotion label (nearest neighbor in corpus) |
| POST   | `/search`     | Query → Qdrant ANN + PG audit, with filters |

## TODOs

Search for `# TODO:` in each file:

- `app/config.py` — env var contract (BUNDLE_DIR, QDRANT_URL, DATABASE_URL, etc.)
- `app/schemas.py` — Pydantic request/response models (extra="forbid")
- `app/model_loader.py` — bundle discovery, import, MANIFEST verification
- `app/predictor.py` — thin wrapper over BundlePredictor.embed()
- `app/client_qdrant.py` — Qdrant read-only client + search
- `app/client_pg.py` — Postgres read-only client + fetch_corpus_hits
- `app/client_minio.py` — MinIO client (for MODEL_SOURCE=s3)
- `app/search.py` — hybrid search orchestration (Qdrant + PG)
- `app/main.py` — FastAPI app, lifespan, all 6 endpoints

## How to run locally

```bash
make build      # build the Docker image (bundle baked in)
make run        # start Qdrant + Postgres + API via compose
make smoke      # curl-based smoke test
make test       # run pytest
```
Open http://127.0.0.1:8000/docs for the Swagger UI.

## How to test

```bash
make test       # pytest tests/ -v (unit tests, no compose needed)
make load       # concurrent /embed load test (compose must be up)
```

## Submission

- Paste the last 20 lines of `make all` output.
- Paste the pytest summary from `make test`.
- Screenshot of Swagger UI with `/embed` and `/search` tested.
- Output of `docker images | grep qbc12-hw03-b-encoder` showing image size.

## Hard penalties

- `.env` committed (instant zero) — use `.gitignore`
- Image > 2 GB (did not use multi-stage build)
- `extra` not set to `"forbid"` on request models (leakage firewall)
- Container runs as root
- `/health` returns 5xx when bundle/Qdrant/PG are merely degraded
