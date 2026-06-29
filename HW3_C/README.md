# HW3_C — Kubernetes on k3s (12 hours)

Deploy your HW3_B container to a real k3s cluster and demonstrate 12 production MLOps scenarios.

## What you got

From Quera: `hw03_c_handout.zip` containing:
- `kubeconfig.yaml` — scoped to your namespace, pointed at `https://185.50.38.163:6443`
- `node-port.txt` — your assigned NodePort (one line, e.g. `30090`)

## What you need

- Your HW3_B code (the FastAPI embedder from HW3_B)
- The design doc: `../HW3_06_hw3_c_k8s.md` — read this first, it has the HOW
- Docker (to build and push images)
- kubectl (configured with your handout kubeconfig)
- curl and a load testing tool (hey, wrk, or similar)

## Quick start

1. Unzip your handout. Copy `kubeconfig.yaml` here. Read `node-port.txt`.
2. Pull the shared base image from the registry: `185.50.38.163:35000`
3. Patch your `app/main.py` with health check endpoints + `state.loaded` flag
4. Build your image on top of the base and push to the registry
5. Work through the 7 task folders in order: `01` → `07`
6. Capture evidence screenshots in `EVIDENCE/`
7. Submit your `EVIDENCE/` folder + `k8s/*.yaml` manifests to Quera

## Folder structure

```
HW3_C/
├── README.md
├── .env.example
├── 01_first_deployment/      # init container + 3 probes + state.loaded + resources
├── 02_failure_modes/         # OOMKilled + self-healing
├── 03_rolling_update/        # rolling update + ConfigMap rotation
├── 04_blue_green/            # blue/green atomic cutover
├── 05_hpa/                   # Horizontal Pod Autoscaler
├── 06_pdb/                   # PodDisruptionBudget
├── 07_prestop_and_eval/      # preStop hook + verification + scale-to-zero
├── templates/                # starter YAML manifests with TODO comments
└── EVIDENCE/                 # your screenshots go here
```

Each task folder has a `README.md` describing the goal. There are no scripts — you write the commands.

## Submission (13 screenshots)

| # | File | Task |
|---|------|------|
| 1 | `task1_pods_running.png` | Pod 1/1 Ready |
| 2 | `task1_three_probes.png` | 3-probe demonstration |
| 3 | `task2a_oomkilled_describe.png` | OOMKilled describe output |
| 4 | `task2a_oomkilled_recovery.png` | Recovery after restoring limit |
| 5 | `task2b_self_healing.png` | Self-healing with 0 5xx |
| 6 | `task3a_rolling_update.png` | Rolling update with 0 5xx |
| 7 | `task3b_configmap_rotation.png` | ConfigMap rotation verified |
| 8 | `task4_blue_green.png` | Blue/green cutover (3 curl outputs) |
| 9 | `task5_hpa_scaling.png` | HPA scaling 1→3→1 |
| 10 | `task6_pdb.png` | PDB blocks drain |
| 11 | `task7a_prestop.png` | PreStop hook in action |
| 12 | `task7b_verification.png` | All 6 verification checks pass |
| 13 | `task7c_scale_to_zero.png` | Scale-to-zero state |

Also submit your `k8s/*.yaml` manifest files.

## Grading (35 points)

| Task | Points |
|------|--------|
| 01 — First deployment (init + probes + state.loaded + resources) | 7 |
| 02 — OOMKilled + self-healing | 6 |
| 03 — Rolling update + ConfigMap | 5 |
| 04 — Blue/green | 5 |
| 05 — HPA | 4 |
| 06 — PDB | 2 |
| 07 — PreStop + verification + scale-to-zero | 6 |
| **Total** | **35** |

Grading is screenshot-based. No leaderboard. No PG submission. No `submit_results.py`.

## Important cluster constraints

- Your namespace has a ResourceQuota: 4 vCPU / 8 GB requests, 8 vCPU / 16 GB limits, 10 pods, 2 NodePorts
- Cluster-wide: 24 vCPU / 117 GB total. Keep HPA max at 3 replicas, not 10
- **Scale to zero when you walk away** — free resources for classmates
- You do NOT SSH to the server. Everything is via kubectl + curl + docker push
- Your kubeconfig is scoped — you cannot see other students' pods

## Common pitfalls

1. **OOMKilled** — memory limit too low. Restore to 1Gi after task 2a.
2. **ImagePullBackOff** — image not pushed to the registry. Push again and verify.
3. **Service selector mismatch** — labels must match exactly between Service and Pod template.
4. **Cluster is full** — scale to zero when done, retry later if another student is hogging resources.
