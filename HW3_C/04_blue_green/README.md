# Task 4 — Blue/Green atomic cutover (2 h)

**Scenario:** Blue/Green (#8).

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 4.

## What you must do

Your current Deployment (`track: blue`, image `v1` or `v2`) is the "blue" version. You will deploy a parallel "green" version and atomically switch traffic via the Service selector.

### Step 1: Build a v3 image with a `/version` endpoint

Add to `app/main.py`:

```python
@app.get("/version")
def version():
    return {"image_tag": "v3"}
```

Rebuild and push as tag `v3` to the registry.

### Step 2: Deploy the green version

1. **Write a second Deployment** (`deployment_green.yaml`) — same shape as your blue Deployment but with `track: green`, `version: v3`, and the `v3` image tag. Store it in your `k8s/` folder.
2. **Create a temporary test service** (`embedder-green-test`) that targets only green pods (selector: `{app: embedder, track: green}`). This lets you curl green without affecting production.
3. **Verify** green is healthy via the test service — call `/version` and `/healthz/ready`.

### Step 3: Atomic cutover

1. **Patch the main `embedder` Service selector** from `{app: embedder}` to `{app: embedder, track: green}`.
2. **Verify the cutover** — curl `/version` on the main NodePort. It should now return `v3`.
3. Blue pods are still running but receive no traffic (the Service no longer matches them).

### Step 4: Rollback (optional)

Patch the main Service selector back to `{app: embedder, track: blue}` to reverse the cutover.

## Evidence

- `../EVIDENCE/task4_blue_green.png` — 3 curl responses:
  1. Blue `v2` (via main service before cutover)
  2. Green `v3` (via green test service)
  3. Main service AFTER cutover returns `v3`

## Pitfalls

- Green pod in `ImagePullBackOff` → `v3` image was not pushed. Push and verify the tag in the registry.
- Main service still returns `v2` after cutover → you patched the wrong service or the selector still matches blue pods.
- Cutover is "atomic" at the K8s Service level — in-flight TCP connections to blue pods will complete. New connections go to green.
