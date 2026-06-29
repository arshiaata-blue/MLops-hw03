# Task 5 — Horizontal Pod Autoscaler (1.5 h)

**Scenario:** HPA (#9).

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 5.

## What you must do

Write a `HorizontalPodAutoscaler` that scales your `embedder` Deployment based on CPU utilization, generate load, and watch it scale up and back down.

### Step 1: Write the HPA manifest

Create `k8s/hpa.yaml`:
- `minReplicas: 1`, `maxReplicas: 3`
- Target: 50% CPU utilization
- `scaleUp.stabilizationWindowSeconds: 0` (react immediately)
- `scaleDown.stabilizationWindowSeconds: 60` (wait before scaling down)

### Step 2: Apply and wait for metrics

Apply the HPA. Wait 60-90 seconds for the metrics-server to gather initial CPU data. Verify `kubectl get hpa` shows a current utilization number (not `<unknown>`).

### Step 3: Generate load

Use a load testing tool (hey, wrk, or similar) to hit your `/embed` endpoint. Run enough concurrent requests to push CPU above 50%. Watch the HPA in real time:

```
kubectl get hpa -w
kubectl get pods -w
```

### Step 4: Verify scaling up AND down

1. Watch the replica count climb from 1 → 2 → 3 under load.
2. Stop the load. Wait. Watch the replica count drop back to 1 after the 60-second stabilization window.

## Evidence

- `../EVIDENCE/task5_hpa_scaling.png` — 3 HPA snapshots:
  1. Idle: `1/1`, ~0% CPU
  2. Peak: `3/3`, ~80% CPU
  3. Scaledown: `1/1`, ~0% CPU

## Pitfalls

- `TARGETS: <unknown>/50%` for more than 2 minutes → metrics-server is not running. Check `kubectl -n kube-system get pods`.
- HPA never scales up → your container has no `resources.requests.cpu` set. Add `requests.cpu: 250m`.
- Load tool returns all 5xx → load is too high. Drop concurrency and retry.
