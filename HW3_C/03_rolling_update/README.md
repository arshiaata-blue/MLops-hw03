# Task 3 — Rolling update + ConfigMap rotation (1.5 h)

**Scenarios:** Rolling update with `maxSurge: 1, maxUnavailable: 0` (#7), ConfigMap rotation (#11).

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 3.

## What you must do

### Part A: Rolling update with zero downtime

Trigger a Deployment update and verify the service never drops a request.

1. **Bump the version label** on your Deployment pod template (the standard trick to trigger a rolling update without rebuilding the image).
2. **Start a curl loop** hitting your NodePort endpoint before the rollout begins.
3. **Trigger the rollout** and watch `kubectl rollout status`.
4. **Count 5xx errors** in the curl log — must be **0**. If non-zero, your `maxSurge`/`maxUnavailable` settings need fixing.

> **HINT:** Set `strategy.rollingUpdate.maxSurge: 1` and `maxUnavailable: 0`. The default (25%) can cause brief 5xx.

### Part B: ConfigMap rotation (no rebuild)

Update a runtime config value without rebuilding the image.

1. **Patch the ConfigMap** — change `threshold` from `0.5` to `0.7`.
2. **Trigger a rollout restart** so the new value takes effect (env-var-mounted ConfigMaps need a pod restart).
3. **Verify** via the `/model-info` endpoint that the running pod sees `threshold: 0.7`.

## Evidence

- `../EVIDENCE/task3a_rolling_update.png` — rollout status + curl log with `5xx count = 0` + pod transitions (old Terminating, new Running)
- `../EVIDENCE/task3b_configmap_rotation.png` — ConfigMap patch command + rollout status + `/model-info` showing `"threshold": 0.7`

## Pitfalls

- ConfigMap patched but `/model-info` shows the old threshold → forgot to `rollout restart`. Env-var ConfigMaps need a pod restart.
- `5xx count > 0` during rolling → your readiness probe is not gating on `state.loaded`.
- `0/1 nodes are available` during rollout → cluster is full. Withdraw replicas, wait, retry.
