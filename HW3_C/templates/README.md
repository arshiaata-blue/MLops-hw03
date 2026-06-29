# Starter templates

This folder contains skeleton YAML manifests for each K8s resource you need. Copy the file you need into your `k8s/` folder, then replace every placeholder.

## What's in this folder

| File | Purpose |
|---|---|
| `01_deployment.yaml` | Starter Deployment with TODO comments marking every Task 1 requirement (init container, 3 probes, resources, securityContext, preStop) |
| `02_service.yaml` | Starter Service — `type: NodePort` with placeholder for your assigned port |
| `03_configmap.yaml` | Starter ConfigMap (log_level + threshold) |
| `04_secret.yaml` | Starter Secret with placeholder values for MinIO + Qdrant |
| `05_hpa.yaml` | Starter HPA (min 1, max 3, target 50% CPU) |
| `06_pdb.yaml` | Starter PodDisruptionBudget (minAvailable 2) |

## How to use

1. Copy the file you need into your `k8s/` folder
2. Replace every `<username>` with your actual username
3. Replace every `<your-nodeport>` with the value from your `node-port.txt`
4. Replace every `REPLACE_*` placeholder with your real per-student credential
5. Read the TODO comments — they call out exactly what each task requires

## What's in the design doc (more complete)

- §1 Task 1: full Deployment (with init container + 3 probes + resources + securityContext) and Service
- §1 Task 4: green Deployment for blue/green
- §1 Task 5: HPA (inline)
- §1 Task 6: PDB (inline)
- §1 Task 7: preStop (inline patch)


# Warning
though your USERNAME is "<first-name>_<last-name>", you kuber name space should be "<first-name>-<last-name>", in the image name aswell.