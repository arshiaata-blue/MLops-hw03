# Task 7 — PreStop hook + verification + scale-to-zero (2 h)

**Scenario:** PreStop hook (#12), deployment verification, scale-to-zero.

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 7.

## What you must do

### Part A: PreStop hook

Give your container a 10-second drain window before receiving SIGTERM during a rollout or pod deletion.

1. **Add a `preStop` lifecycle hook** to your main container:
   - `sleep 10` — gives the Service 10 seconds to stop routing traffic to this pod before it terminates
2. **Trigger a rolling update** (e.g., bump a label).
3. **Watch the old pod** — it should hold in `Terminating` state for ~10 seconds before the container exits.
4. **Check `kubectl describe pod`** to confirm the preStop hook is present.

### Part B: Run the verification script

Run `verification.sh` from this folder. It checks all 6 criteria via your NodePort:

1. Pod is running and `1/1 Ready`
2. `/healthz/live` returns 200
3. `/healthz/ready` returns 200
4. `/embed` returns 200 with 384-dimensional vectors
5. `/search` returns 200 with at least 1 hit
6. No OOMKilled in recent pod history

If any check fails, fix it before proceeding.

### Part C: Scale to zero

Free cluster resources for your classmates:

```bash
kubectl scale deployment embedder --replicas=0
kubectl scale deployment embedder-green --replicas=0   # if green exists
```

Verify no pods remain in your namespace. When you return, scale back to 1 and wait for the init container + model load.

### Reminder

Grading is screenshot-based. No leaderboard. No PG submission.

## Evidence

- `../EVIDENCE/task7a_prestop.png` — `kubectl describe pod` showing the preStop hook + the pod holding in `Terminating` state
- `../EVIDENCE/task7b_verification.png` — output of `verification.sh` showing all 6 checks pass
- `../EVIDENCE/task7c_scale_to_zero.png` — `kubectl get pods` showing `No resources found` (or empty pod list)

## Pitfalls

- preStop never fires → the patch did not update the Deployment spec. Verify the `lifecycle` block is present in `kubectl describe deployment`.
- preStop sleep exceeds `terminationGracePeriodSeconds` (default 30s) → pod gets stuck. `sleep 10` is fine with the default.
- A verification check fails → read the specific error and fix the underlying issue.
