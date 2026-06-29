# Task 1 — First deployment (2.5 h)

**Scenarios:** Init container (#1), 3 distinct probes (#2), `state.loaded` flag (#3), resource requests/limits (#4).

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 1.

## What you must do

1. **Patch `app/main.py`** with health check endpoints and a model-loaded flag:
   - `GET /healthz/live` — always returns 200 (used by startup + liveness probes)
   - `GET /healthz/ready` — returns 200 only when `app.state.loaded = True`, 503 otherwise (used by readiness probe)
   - Set `app.state.loaded = True` after the model + tokenizer finish loading
   - Reference: `state_loaded_patch.py` in this folder

2. **Rebuild your image** with the new endpoints and push to the registry at `185.50.38.163:35000`.

3. **Write 4 Kubernetes manifests** in a `k8s/` subfolder:
   - `deployment.yaml` — Deployment with:
     - An init container that downloads the bundle + model from MinIO
     - 3 distinct probes: startup, liveness, and readiness (each hitting different endpoints/paths)
     - Resource requests AND limits (CPU + memory)
   - `service.yaml` — **NodePort** service (not ClusterIP) using your assigned node port
   - `configmap.yaml` — `log_level: INFO`, `threshold: "0.5"`
   - `secret.yaml` — your MinIO credentials (from handout CSV) + Qdrant read key (from SHARED.txt)

4. **Apply and verify** — the pod must reach `1/1 Ready` and your NodePort must respond.

5. **Demonstrate the 3 probes:**
   - `/healthz/live` → 200 immediately (even during model load)
   - `/healthz/ready` → 503 early (model not loaded yet)
   - `/healthz/ready` → 200 after the model finishes loading

## Evidence

- `../EVIDENCE/task1_pods_running.png` — `kubectl get pods` showing `1/1 Ready`
- `../EVIDENCE/task1_three_probes.png` — 3 timed curl calls demonstrating all 3 probe behaviors above

Push your manifest files to your `k8s/` subfolder (they are part of the submission).

## Pitfalls

- `/healthz/ready` never returns 200 → `app.state.loaded = True` is in the wrong place. It must fire AFTER model load.
- `ImagePullBackOff` → image was not pushed to the registry. Push again and verify the tag.
- Pod stuck in `Init:Error` → init container could not download from MinIO. Check your Secret values.
- `curl` to your NodePort refuses connection → Service is type ClusterIP, not NodePort. Fix the Service spec.
