# Task 6 — PodDisruptionBudget (1 h)

**Scenario:** PDB (#10).

**Read:** `../../HW3_06_hw3_c_k8s.md` §1 Task 6.

## What you must do

A PodDisruptionBudget prevents voluntary disruptions from taking down too many pods at once. In a 1-node cluster, a PDB with `minAvailable: 2` will block a node drain entirely when you have 3 replicas.

### Step 1: Scale to 3 replicas

```bash
kubectl scale deployment embedder --replicas=3
```

Wait for all 3 pods to reach `1/1 Ready`.

### Step 2: Write and apply the PDB

Create `k8s/pdb.yaml` with `minAvailable: 2`, targeting pods with label `app: embedder`. Apply it.

### Step 3: Demonstrate the PDB holds

Run `kubectl drain --dry-run=server` against the node. With 1 node and 3 pods, ALL pods would be evicted during a drain — but the PDB says at least 2 must remain available. The drain should be **rejected** with: `would violate disruption budget`.

## Evidence

- `../EVIDENCE/task6_pdb.png` — PDB definition + `kubectl get pdb` showing `MIN AVAILABLE = 2` + drain rejection output

## Pitfalls

- `kubectl drain` says "node already cordoned" → run `kubectl uncordon` on the node first.
- Drain succeeds and evicts all pods → your PDB selector is wrong or the PDB was never applied. Check with `kubectl get pdb`.
- `--dry-run=server` is used because your Role does not have `nodes/drain` permission — but it still validates the PDB check before the permission check.
