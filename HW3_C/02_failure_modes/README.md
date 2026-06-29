# Task 2 — Failure modes: OOMKilled + self-healing (1.5 h)

**Scenarios:** OOMKilled (#5), Self-healing (#6).

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 2.

## What you must do

### Part A: Deliberate OOMKilled

The model + framework together need ~500 MB. If you set the memory limit below that, the kernel will kill the container.

1. **Lower the memory limit** on your Deployment to 256Mi.
2. **Send requests** to the service to trigger model loading under tight memory.
3. **Observe** the pod get OOMKilled — check the pod's events and status for `Reason: OOMKilled` and `Exit Code: 137`.
4. **Restore the memory limit** to 1Gi and verify the pod recovers to `1/1 Ready`.

### Part B: Self-healing

Prove that a single-pod service survives pod deletion with zero 5xx errors.

1. **Delete the running pod.**
2. **Watch** a new pod appear (the ReplicaSet recreates it).
3. **Hit the service in a loop** (curl in a tight loop) from the moment you delete the pod until the new pod is ready.
4. **Count 5xx errors** — the count must be **0**. If you see any 5xx, your readiness probe is not gating traffic correctly.

## Evidence

- `../EVIDENCE/task2a_oomkilled_describe.png` — `kubectl describe pod` showing `Reason: OOMKilled`, `Exit Code: 137`
- `../EVIDENCE/task2a_oomkilled_recovery.png` — rollout status + `kubectl get pods` showing `1/1 Ready` after restoring to 1Gi
- `../EVIDENCE/task2b_self_healing.png` — pod delete event + new pod starting + curl log showing `5xx count = 0`

## Pitfalls

- OOMKilled may take 1-2 minutes to trigger (kubelet gives a grace period on first boot before enforcing). Be patient.
- `5xx count > 0` during self-healing → readiness probe is not gating on `state.loaded`. Re-check task 1.
- If pod gets stuck in `CrashLoopBackOff` after the OOM test, that's expected — restore to 1Gi and it will recover.
