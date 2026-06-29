# HW3_A — Build a Versioned Encoder Bundle

## Goal

Produce a **frozen, hash-pinned bundle** of `sentence-transformers/all-MiniLM-L6-v2`
plus a self-contained `predict.py`. The bundle is the **unit of truth** for every
later step: HW3_B imports it, HW3_C packages it.

## What you will do

| Step | What | File |
|------|------|------|
| 1 | Download the model from HuggingFace | `encoder_bundle.ipynb` cell 2 |
| 2 | Write `metadata.json` | `encoder_bundle.ipynb` cell 4 |
| 3 | Write `MANIFEST.json` with SHA-256 hashes | `encoder_bundle.ipynb` cell 6 |
| 4 | Write `predict.py` (4 functions) | `encoder_bundle.ipynb` cell 8 |
| 5 | Run tests — all must pass | `encoder_bundle.ipynb` cell 10 |
| 6 | Register the bundle in MLflow | `encoder_bundle.ipynb` cell 12 |
| 7 | Upload bundle to MinIO | `encoder_bundle.ipynb` cell 14 |

## Workflow

```
1. Open encoder_bundle.ipynb in Jupyter
2. Complete each TODO cell (read the HINT comments)
3. After each step, the next cell depends on it — don't skip
4. Run the test cell — fix anything that fails
5. Register in MLflow
6. Upload to MinIO with the provided upload script
```

## Folder layout

```
HW3_A/
├── README.md
├── .env.example                      ← fill in credentials, rename to .env
├── encoder_bundle.ipynb              ← ⬅ YOU WORK HERE
│
├── bundle/                           ← what you ship
│   ├── predict.py                    ← ⬅ YOU IMPLEMENT THIS (4 functions)
│   ├── metadata.json                 ← ⬅ YOU FILL THIS
│   ├── MANIFEST.json                 ← ⬅ YOU GENERATE THIS
│   ├── requirements.txt              ← ⬅ YOU WRITE THIS
│   └── model/                        ← ⬅ YOU DOWNLOAD 6 FILES HERE
│
├── tests/                            ← provided, DO NOT MODIFY
│   ├── test_parity.py                ← 7 tests for embedding correctness
│   ├── test_tokenization.py          ← 5 tests for tokenizer behavior
│   ├── test_determinism.py           ← 1 test for reproducibility
│   └── test_adversarial.py           ← 10 tests for edge cases
│
└── scripts/                          ← provided, READ but DO NOT MODIFY
    ├── download_model.py             ← helper: download from HuggingFace
    ├── gen_manifest.py               ← helper: generate SHA-256 manifest
    └── 01_upload_to_minio.sh         ← uploader (uses mc client)
```

## The predict.py contract

You must implement exactly 4 functions:

| Function | Signature | Returns |
|----------|-----------|---------|
| `load_bundle()` | no args | (model, tokenizer) tuple |
| `embed(texts)` | List[str] | `np.ndarray` shape `(N, 384)`, dtype `float32` |
| `similarity(a, b)` | two `np.ndarray` | `float` (cosine similarity) |
| `info()` | no args | `dict` with model_name, embedding_dim, max_seq_len, device |

The 7-step pipeline inside `embed()`:
1. Tokenize (padding=True, truncation=True, max_length=256)
2. Move tensors to device
3. Forward pass under `torch.no_grad()`
4. Mean-pool weighted by attention mask
5. L2-normalize
6. Move to CPU, convert to float32 numpy
7. Return

## Running tests

```bash
cd HW3_A
pip install -r bundle/requirements.txt
PYTHONPATH=bundle pytest tests/ -v
```

All tests must pass before you submit.

## Time and points

- **Time**: 18 hours
- **Points**: 30

## What you submit

1. `encoder_bundle.ipynb` — your completed notebook with all outputs
2. `bundle/` — complete with predict.py, metadata.json, MANIFEST.json, requirements.txt, model/ (6 files)
3. `EVIDENCE/` folder with screenshots:
   - `EVIDENCE/pytest_pass.png` — all tests passing
   - `EVIDENCE/mlflow_registered.png` — MLflow showing registered model
   - `EVIDENCE/minio_upload.png` — MinIO upload confirmation

## Hard penalties

| Penalty | Condition |
|---------|-----------|
| **-20** | `test_parity.py` does not pass |
| **-10** | Missing model files in `bundle/model/` |
| **-10** | Missing `MANIFEST.json` or contains placeholder `REPLACE_*` values |
| **-10** | `predict.py` calls `sentence-transformers` instead of raw `transformers` |
| **-10** | Missing `EVIDENCE/` screenshots |
| **-5** | Embeddings not L2-normalized |
| **-5** | Missing `metadata.json` |
| **-5** | Missing `requirements.txt` |
| **-5** | Notebook cells not executed (no outputs visible) |


# Warning 
Before running the upload cell, either:
1. start Jupyter from a terminal where you already ran `source .env`, or
2. run the upload script directly from terminal:
   source .env && bash scripts/01_upload_to_minio.sh