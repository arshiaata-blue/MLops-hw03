# HW3_C — Kubernetes on k3s (12 hours, 12 scenarios)

## The MLOps K8s playbook you will learn

This sub-assignment is where MLOps engineering actually lives. HW3_A taught you the artifact contract (bundle), HW3_B taught you immutable deployment (container). HW3_C teaches you the things production breaks on: **lifecycle, scale, failure, traffic, secrets, and recovery**.

By the end of HW3_C you will have demonstrated — on a real Linux k3s cluster, with your hands on `kubectl` — twelve scenarios that an MLOps platform engineer sees in their first 90 days on the job.

| # | Scenario | Production question it answers |
|---|---|---|
| 1 | **Init container for model download** | "How do I decouple my model from my image so I can roll the model without rebuilding the image?" |
| 2 | **Three distinct probes (startup + liveness + readiness)** | "How does my app tell K8s when it is TRULY ready, vs just process-up?" |
| 3 | **`state.loaded` flag (custom readiness signal)** | "How do I prevent the service from sending requests to a pod whose model is not yet in memory?" |
| 4 | **Resource requests AND limits (CPU + memory)** | "How do I prevent one bad pod from eating the whole node?" |
| 5 | **Deliberate OOMKilled** | "What does the kernel say when my pod is over budget? Can I read its verdict?" |
| 6 | **Self-healing** | "What happens when I delete a pod? Why is desired state a fact, not a request?" |
| 7 | **Rolling update with `maxSurge: 1, maxUnavailable: 0`** | "How do I ship a new image with zero dropped requests?" |
| 8 | **Blue/Green atomic cutover** | "How do I roll back in 1 second if the new version is broken?" |
| 9 | **Horizontal Pod Autoscaler (HPA)** | "How do I scale based on load, not just static replicas?" |
| 10 | **PodDisruptionBudget (PDB)** | "How do I guarantee a minimum available during node maintenance?" |
| 11 | **ConfigMap rotation (no rebuild)** | "How do I change a threshold or a URL without a CI/CD pipeline?" |
| 12 | **PreStop hook (graceful shutdown)** | "How do I drain in-flight requests before SIGTERM kills the process?" |

You will also do, as part of the verification pipeline:

- **6-check deployment verification** (pod ready, 3 endpoints via NodePort, 384-dim vectors, search hits, no OOMKilled)
- **Scale-to-zero** (release cluster resources when walking away)

---

## 0. The hard constraints (read this before starting)

### 0.1 You do not SSH to the main server

The bootcamp server at `185.50.38.163` is **TA-only**. You interact with it exclusively through HTTP APIs (Qdrant, MinIO, model registry, MLflow, the k3s API). You never log in.

This is non-negotiable: the server runs other services (HW2 postgres, Airflow, Metabase, MLflow) that must stay up.

### 0.2 You push your image to a local Docker registry (not the laptop, not the server's local Docker)

There is a **local Docker registry** running on the server at `185.50.38.163:35000`. The registry has a single pre-loaded **base image** (`qbc12-hw03-base:v1`) containing python 3.10-slim + torch 2.5.1+cpu + transformers + fastapi + all prod dependencies.

You pull the base, build your HW3_B code on top (using `HW3_B/Dockerfile.hw3c`, a 3-line file: `FROM base` + `COPY app/` + `USER app`), tag the result as `185.50.38.163:35000/qbc12-embedder-<username>:v1`, and `docker push` it back to the registry.

k3s pods reference this image with `imagePullPolicy: Always` and pull directly from the registry.

**You do NOT:**
- Push from the server's local Docker
- `docker save` + `docker load` tarballs
- Rely on the server's local Docker to host your image

If you change the image (e.g., for the rolling update task, or for blue/green), you `docker build` + `docker push` again. k3s rolls the new image automatically (you bump the version label or change the tag).

### 0.3 You have a personal kubeconfig, not a shared one

Each student gets a **kubeconfig file scoped to their namespace**. The TA generated it with a service account + Role + RoleBinding. The file lives in your handout zip (you received it alongside the credential CSV). It contains:

- A cluster entry pointing to `https://185.50.38.163:6443` (the k3s API)
- A user entry with a personal token (32 random bytes, base64)
- A context that namespaces everything to `qbc12-hw03-c-<username>`

When you `kubectl apply`, the API server checks: do you have a Role in `qbc12-hw03-c-<username>` that grants this verb? If yes, OK. If no, 403.

**You cannot see, list, or modify resources in any other student's namespace.** Try it once to prove it (`kubectl get pods -n qbc12-hw03-c-someone-else` → 403 Forbidden), then move on.

### 0.4 Your namespace is hard-constrained

The TA applied a `ResourceQuota` to your namespace:

```
requests.cpu: 4
requests.memory: 8Gi
limits.cpu: 8
limits.memory: 16Gi
pods: 10
```

You cannot exceed these. If you try to deploy a 4-replica deployment with `limits.cpu: 4` each (16 total), the API server rejects the manifest at apply time with `exceeded quota`. **This is a feature, not a bug.** It is teaching you that multi-tenant clusters require explicit capacity planning.

### 0.5 Scale-to-zero is the deal — not a nice-to-have

At rest, the cohort uses ~2 vCPU and ~4 GB RAM (HW2/HW3 services included). Your pod at rest uses 0.5 vCPU and 1 GB RAM. With 3 replicas, you consume 1.5 vCPU and 3 GB. With 42 students × 1.5 vCPU at rest = 63 vCPU at rest — over budget.

The k3s cluster has 24 vCPU and 117 GB RAM total. The math does not work if all 42 students run a 3-replica HPA at the same time.

**The deal:**
- The HPA demo uses `minReplicas: 1, maxReplicas: 3` (NOT 10). At rest you run 1 replica.
- When you scale up to 3 for the load test, the cluster can absorb ~14 students scaling simultaneously.
- If you scale up and see `Pending` pods, the cluster is full — wait a minute or scale back down.
- **When you walk away from the keyboard, scale to zero** (`kubectl scale deployment embedder --replicas=0`). This frees the cluster for your classmates.
- You can scale back to 1 any time: `kubectl scale deployment embedder --replicas=1`.
- Task 7c **grades** scale-to-zero as part of the final cleanup (1 pt of 6). It is not optional.

### 0.6 What the instructor did before you started (you do not redo this)

In Phase 0.6 (instructor pre-flight, ~45 min), the TA:

1. Installed k3s on the main server (`curl -sfL https://get.k3s.io | sh -` with `--disable=traefik --disable=servicelb`)
2. Installed `metrics-server` (for HPA)
3. Started a local Docker registry on port 35000 (with `/opt/qbc12-hw03/registry-data` as persistent volume)
4. Built the **base image** `qbc12-hw03-base:v1` (python 3.10-slim + torch 2.5.1+cpu + transformers + fastapi + all prod deps) and pushed it to the local registry
5. Created 42 namespaces (`qbc12-hw03-c-<username>`)
6. Created 42 service accounts (one per namespace)
7. Created 42 Roles + RoleBindings (read/write on own namespace, deny on others)
8. Created 42 ResourceQuotas (per 0.4 above)
9. Created 42 NetworkPolicies (default-deny + allow DNS + allow ingress from anywhere + allow egress to Qdrant/MinIO/registry)
10. Generated 42 kubeconfig files (token auth, scoped to each namespace)
11. Assigned 42 NodePorts (30090-30131, one per student)
12. Packaged everything into `hw03_c_handout.zip` and distributed via Quera

You start at task 1 by unzipping your handout, pulling the base image, and building/pushing your own image on top.

---

## 1. The 7 student tasks (12 hours total)

### Task 1: First deployment — init container + 3 probes + state.loaded + resources (2.5 h)

**The aha:** *Image contains code; init container fetches model. App signals when it is truly ready.*

You will write a 9-resource manifest bundle that runs your HW3_B service in your namespace. The interesting part is not the main container — it is the **init container** that runs BEFORE the main container starts and downloads the model + bundle into a shared `emptyDir` volume.

**Files you write:**

```
k8s/
├── 02_deployment.yaml        # main work
├── 03_service.yaml           # ClusterIP, exposes port 80 → 8000
├── 04_configmap.yaml         # log_level, threshold
├── 05_secret.yaml            # minio creds, qdrant key
└── kustomization.yaml        # (optional) one-shot apply
```

**What goes in `02_deployment.yaml` (key sections, not full file — you write the rest):**

> **§1.0 Why `init-bundle:v1` instead of `minio/mc:latest`?**
> Two reasons:
> 1. `minio/mc:latest` is built **FROM scratch** — it has only the `mc` binary, no shell tools, no `tar`. Your init script does `tar -xzf /tmp/bundle.tar.gz -C /bundle/`, so you need `tar`.
> 2. k3s in Iran cannot pull from `docker.io` (HTTP 403 on blobs). The instructor pre-pushes a custom 2-stage image `185.50.38.163:35000/init-bundle:v1` (alpine + tar + the `mc` binary copied from the pre-pushed `minio/mc`). The image is ~13 MB compressed.
> The Dockerfile is in `HW3_C_instructor_scripts/init-bundle.Dockerfile` and is built by `09b_preload_init_bundle.sh`. **Do not** use `minio/mc:latest` in your manifest — the init container will fail with `tar: command not found`.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: embedder
  namespace: qbc12-hw03-c-<username>     # your namespace
  labels: {app: embedder, version: v1}
spec:
  replicas: 1                            # start at 1; HPA scales later
  selector: {matchLabels: {app: embedder}}
  template:
    metadata: {labels: {app: embedder, version: v1}}
    spec:
      initContainers:
      - name: bundle-pull
        image: 185.50.38.163:35000/init-bundle:v1     # custom: mc + tar (NOT minio/mc!)
        command: ["/bin/sh", "-c"]
        args:
        - |
          set -e
          mc alias set s3 http://185.50.38.163:33333 \
            $MINIO_ACCESS_KEY $MINIO_SECRET_KEY
          mc cp -r s3/hw03-bundles/<username>/hw03_bundle_v1.tar.gz /bundle/
          tar -xzf /bundle/hw03_bundle_v1.tar.gz -C /bundle/
          # Fetch model files (shared registry, same 6 files for everyone)
          for f in config.json model.safetensors tokenizer.json \
                   tokenizer_config.json special_tokens_map.json vocab.txt; do
            curl -fsSL -o /bundle/$f \
              http://185.50.38.163:33200/$f
          done
        env:
        - name: MINIO_ACCESS_KEY
          valueFrom: {secretKeyRef: {name: minio-credentials, key: access_key}}
        - name: MINIO_SECRET_KEY
          valueFrom: {secretKeyRef: {name: minio-credentials, key: secret_key}}
        volumeMounts:
        - {name: bundle, mountPath: /bundle}
        resources:
          requests: {cpu: 50m, memory: 64Mi}
          limits:   {cpu: 200m, memory: 256Mi}

      containers:
      - name: api
        image: 185.50.38.163:35000/qbc12-embedder-<username>:v1   # your image, in the local registry
        imagePullPolicy: Always                                   # k3s pulls from the registry
        ports: [{name: http, containerPort: 8000}]
        env:
        - {name: MODEL_SOURCE, value: "local"}
        - {name: BUNDLE_DIR,  value: "/bundle"}
        - {name: QDRANT_URL,  value: "http://185.50.38.163:6333"}
        - {name: QDRANT_API_KEY, valueFrom: {secretKeyRef: {name: qdrant-credentials, key: api_key}}}
        - {name: QDRANT_COLLECTION, value: "qbc12_corpus"}
        - {name: OMP_NUM_THREADS, value: "2"}
        - {name: LOG_LEVEL, valueFrom: {configMapKeyRef: {name: app-config, key: log_level}}
        - {name: PREDICTION_THRESHOLD, valueFrom: {configMapKeyRef: {name: app-config, key: threshold}}}

        # --- THREE distinct probes ---
        startupProbe:
          httpGet: {path: /healthz/live, port: http}
          initialDelaySeconds: 0
          periodSeconds: 5
          failureThreshold: 24         # 24 * 5s = 120s for slow model load
        livenessProbe:
          httpGet: {path: /healthz/live, port: http}
          periodSeconds: 10
          timeoutSeconds: 3
          failureThreshold: 3
        readinessProbe:
          httpGet: {path: /healthz/ready, port: http}
          periodSeconds: 5
          timeoutSeconds: 3
          failureThreshold: 2

        resources:
          requests: {cpu: 250m, memory: 512Mi}
          limits:   {cpu: 500m, memory: 1Gi}
        securityContext:
          runAsNonRoot: true
          runAsUser: 10001
          readOnlyRootFilesystem: true
          allowPrivilegeEscalation: false
          capabilities: {drop: [ALL]}
        volumeMounts:
        - {name: bundle, mountPath: /bundle, readOnly: true}

      volumes:
      - name: bundle
        emptyDir: {sizeLimit: 500Mi}
```

**You must also add 2 endpoints to your FastAPI app** (HW3_B did not have them):

- `GET /healthz/live` — returns 200 always, as long as the process is up. Cheap.
- `GET /healthz/ready` — returns 200 only when `state.loaded == True`. Returns 503 otherwise.

Add to `app/main.py`:

```python
from fastapi import Response, status

@app.get("/healthz/live")
def healthz_live():
    return {"status": "live"}

@app.get("/healthz/ready")
def healthz_ready(response: Response):
    if getattr(app.state, "loaded", False):
        return {"status": "ready", "model_loaded": True}
    response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return {"status": "not_ready", "model_loaded": False}
```

And in your startup event, set `app.state.loaded = True` AFTER the model is loaded into memory (after the `from_pretrained()` call returns).

**Apply and verify:**

```bash
export KUBECONFIG=~/kubeconfigs/qbc12-hw03-c-<username>.yaml
kubectl get nodes                  # 1 node expected (single control-plane)
kubectl -n qbc12-hw03-c-<username> get all
kubectl apply -f k8s/
kubectl -n qbc12-hw03-c-<username> get pods -w
# Expect: 1 pod, 0/1 → 1/1 Ready, in ~30-60s
```

**The 3-probe demonstration (you must capture evidence):**

```bash
# 1. Delete and re-apply
kubectl -n qbc12-hw03-c-<username> delete deployment embedder
kubectl apply -f k8s/

# 2. IMMEDIATELY port-forward (within 2 seconds)
kubectl -n qbc12-hw03-c-<username> port-forward svc/embedder 8000:80 &
PF=$!
sleep 2

# 3. /live is 200 (process up) — but /ready is 503 (model not loaded)
curl -i http://localhost:8000/healthz/live    # HTTP 200
curl -i http://localhost:8000/healthz/ready   # HTTP 503

# 4. Wait 45s, try /ready again
sleep 45
curl -i http://localhost:8000/healthz/ready   # HTTP 200

kill $PF
```

**Capture this in EVIDENCE/task1_three_probes.png** — three curls, three status codes.

**Save:** `EVIDENCE/task1_pods_running.png`, `EVIDENCE/task1_three_probes.png`, write a 1-paragraph note on what each probe caught.

---

### Task 2: Failure modes — OOMKilled + self-healing (1.5 h)

**The aha:** *Limits are enforced by the kernel OOM killer, not by your app. You can read the kernel's verdict in pod events. And desired state is a fact, not a request.*

#### Subtask 2a: Deliberate OOMKilled (45 min)

You will halve the memory limit, send a request that exceeds it, watch the kubelet kill the container, read the event, then restore.

```bash
# Patch the memory limit to 256Mi (model alone is 80MB; framework 400MB; this WILL OOM)
kubectl -n qbc12-hw03-c-<username> patch deployment embedder \
  --type json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"256Mi"}]'

# Wait for the new pod to roll out
kubectl -n qbc12-hw03-c-<username> rollout status deployment embedder
# Pod restarts after OOMKilled, then OOMKills again, then enters CrashLoopBackOff

# Watch
kubectl -n qbc12-hw03-c-<username> get pods -w
# Expect: Running → OOMKilled → CrashLoopBackOff (back-off increasing)

# Read the verdict
POD=$(kubectl -n qbc12-hw03-c-<username> get pods -l app=embedder -o name | head -1)
kubectl -n qbc12-hw03-c-<username> describe $POD
# Look for:
#   Containers:
#     api:
#       State:          Waiting (Reason: CrashLoopBackOff)
#       Last State:     Terminated
#       Reason:         OOMKilled
#       Exit Code:      137
#       Started:        ...
#       Finished:       ...
#       Ready:          False

# Capture: EVIDENCE/task2a_oomkilled_describe.png
```

**The lesson:** the OOMKilled reason comes from the kernel cgroup OOM killer, not from Kubernetes. The kubelet just observes the cgroup event and translates it to a pod status. Exit code 137 = 128 + 9 (SIGKILL), the signal the OOM killer sends.

**Fix it:**

```bash
# Restore 1Gi
kubectl -n qbc12-hw03-c-<username> patch deployment embedder \
  --type json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"1Gi"}]'

kubectl -n qbc12-hw03-c-<username> rollout status deployment embedder
kubectl -n qbc12-hw03-c-<username> get pods    # 1/1 Ready
```

**Capture:** `EVIDENCE/task2a_oomkilled_recovery.png` (3 status transitions, side by side).

#### Subtask 2b: Self-healing (45 min)

```bash
# Port-forward in the background
kubectl -n qbc12-hw03-c-<username> port-forward svc/embedder 8000:80 &
PF=$!
sleep 2

# Get the pod name
POD=$(kubectl -n qbc12-hw03-c-<username> get pods -l app=embedder -o jsonpath='{.items[0].metadata.name}')
echo "Killing $POD"

# In one terminal: watch the pod get recreated
kubectl -n qbc12-hw03-c-<username> get pods -w &
WATCH=$!

# In another terminal: hit the service 60 times (one per second)
ERRORS=0
for i in $(seq 1 60); do
  CODE=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/healthz/live)
  if [ "$CODE" -ge 500 ]; then ERRORS=$((ERRORS+1)); fi
  sleep 1
done
echo "5xx count during self-healing: $ERRORS"   # MUST be 0

# Now kill the pod
kubectl -n qbc12-hw03-c-<username> delete pod $POD
# Watch the new pod come up (within ~30s)

kill $PF $WATCH
```

**The lesson:** the service never went down because (a) the Deployment had `replicas: 1` and the controller noticed the pod was deleted, (b) the new pod passed its readiness probe before the Service added it as an endpoint. **Zero 5xx is the contract of self-healing.**

**Capture:** `EVIDENCE/task2b_self_healing.png` (delete event + new pod starting + curl loop showing 0 errors).

---

### Task 3: Rolling update + ConfigMap rotation (1.5 h)

**The aha:** *A rolling update with `maxSurge: 1, maxUnavailable: 0` replaces pods one at a time while the service keeps serving 100% of traffic. And you can change a config value WITHOUT rebuilding the image.*

#### Subtask 3a: Rolling update with zero downtime (45 min)

```bash
# Bump the version label (this is the standard "trigger a rollout" trick)
kubectl -n qbc12-hw03-c-<username> patch deployment embedder \
  --type json -p='[{"op":"replace","path":"/spec/template/metadata/labels/version","value":"v2"}]'

# Port-forward in background
kubectl -n qbc12-hw03-c-<username> port-forward svc/embedder 8000:80 &
PF=$!
sleep 2

# Start a curl loop hitting the service every 200ms
( while true; do
    curl -s -o /dev/null -w "%{http_code}\n" http://localhost:8000/healthz/live
    sleep 0.2
  done ) > /tmp/curl_log.txt &
CURL=$!

# Watch the rollout
kubectl -n qbc12-hw03-c-<username> rollout status deployment embedder
# Expect: "deployment 'embedder' successfully rolled out"

# Watch pods individually
kubectl -n qbc12-hw03-c-<username> get pods -w
# Expect: old pod Terminating, new pod Pending → ContainerCreating → Running → Ready

# Stop the curl loop
kill $CURL

# Count the 5xx
echo "5xx count during rolling update:"
grep -c '^5' /tmp/curl_log.txt    # MUST be 0
echo "Total requests:"
wc -l < /tmp/curl_log.txt

kill $PF
```

**The lesson:** `maxSurge: 1, maxUnavailable: 0` means at most 1 extra pod exists during the rollout, and 0 pods are unavailable. The old pod serves traffic until the new pod is Ready, then the old pod is terminated. **The service is available the entire time.**

**Capture:** `EVIDENCE/task3a_rolling_update.png` (rollout status + curl log + pod list).

#### Subtask 3b: ConfigMap rotation, no rebuild (45 min)

```bash
# Bump the threshold from 0.5 to 0.7
kubectl -n qbc12-hw03-c-<username> patch configmap app-config \
  --type merge -p '{"data":{"threshold":"0.7"}}'

# This does NOT trigger a rollout (ConfigMap is mounted as env, not as volume).
# We need to restart the pods to pick up the new value. The K8s-idiomatic way:
kubectl -n qbc12-hw03-c-<username> rollout restart deployment embedder

# Watch
kubectl -n qbc12-hw03-c-<username> rollout status deployment embedder

# Verify the new value is in effect
kubectl -n qbc12-hw03-c-<username> port-forward svc/embedder 8000:80 &
PF=$!
sleep 2
curl -s http://localhost:8000/model-info | grep threshold
# Expect: "threshold": 0.7

kill $PF
```

**The lesson:** env vars from ConfigMap are baked into the container at start. To rotate, you need a `rollout restart`. K8s treats this as a "trigger" — it updates the pod template hash, the Deployment controller creates new pods, the old ones terminate. Same rolling update machinery, but the IMAGE hasn't changed.

**The alternative** is to mount the ConfigMap as a file and have the app hot-reload it (more code, more failure modes). For a config that changes <1×/day, restart is simpler and safer.

**Capture:** `EVIDENCE/task3b_configmap_rotation.png` (patch command + rollout status + curl response with new threshold).

---

### Task 4: Blue/Green atomic cutover (2 h)

**The aha:** *Two versions live, only one receives traffic. The cutover is atomic. Rollback is one command.*

```bash
# You already have a Deployment called "embedder" with label version=v2 (from task 3).
# Rename it conceptually: it's the "blue" deployment now.
# Add a new "green" deployment with version=v3 and a different image tag.

# First, build v3 locally (any change — e.g., add a /version endpoint to FastAPI)
# In app/main.py:
@app.get("/version")
def version():
    return {"image_tag": "v3", "git_sha": "abc123"}

# Rebuild + push to the local registry
docker build -t 185.50.38.163:35000/qbc12-embedder-<username>:v3 -f HW3_B/Dockerfile.hw3c HW3_B/
docker push 185.50.38.163:35000/qbc12-embedder-<username>:v3
# (k3s will pull v3 on the next pod start)
```

Now write the green deployment:

```yaml
# k8s/06_deployment_green.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: embedder-green
  namespace: qbc12-hw03-c-<username>
  labels: {app: embedder, track: green, version: v3}
spec:
  replicas: 1
  selector: {matchLabels: {app: embedder, track: green}}
  template:
    metadata: {labels: {app: embedder, track: green, version: v3}}
    spec:
      containers:
      - name: api
        image: 185.50.38.163:35000/qbc12-embedder-<username>:v3
        imagePullPolicy: Always
      # ... rest same as blue
```

```bash
# Apply green
kubectl apply -f k8s/06_deployment_green.yaml
kubectl -n qbc12-hw03-c-<username> get pods -l track=green -w
# Wait for 1/1 Ready

# Test green directly via its OWN service (we need to expose it for testing)
cat <<EOF | kubectl apply -f -
apiVersion: v1
kind: Service
metadata:
  name: embedder-green-test
  namespace: qbc12-hw03-c-<username>
spec:
  type: ClusterIP
  selector: {app: embedder, track: green}
  ports: [{port: 80, targetPort: http}]
EOF

kubectl -n qbc12-hw03-c-<username> port-forward svc/embedder-green-test 8001:80 &
PF_GREEN=$!
sleep 2

# Hit green directly
curl -s http://localhost:8001/version
# Expect: {"image_tag":"v3", ...}

# Now the moment of truth: atomically switch the MAIN service
kubectl -n qbc12-hw03-c-<username> patch service embedder \
  --type json -p='[{"op":"replace","path":"/spec/selector","value":{"app":"embedder","track":"green"}}]'

# The main service now points to green. Blue is still running but receives no traffic.
curl -s http://localhost:8000/version     # port-forward to MAIN svc on 8000
# Expect: {"image_tag":"v3", ...}    -- served by green

# Rollback: switch back to blue
kubectl -n qbc12-hw03-c-<username> patch service embedder \
  --type json -p='[{"op":"replace","path":"/spec/selector","value":{"app":"embedder","track":"blue"}}]'

curl -s http://localhost:8000/version     # back to v2 (blue)

kill $PF_GREEN
```

**The lesson:** the Service selector is the switch. Changing it is an atomic operation (one API call, the kube-proxy updates iptables on all nodes within ~1 second). You can roll back in 1 second by reverting the selector. Blue keeps running, you pay for it, but you have **zero-downtime rollback**.

**Capture:** `EVIDENCE/task4_blue_green.png` (3 curl responses: blue / green / after switch).

---

### Task 5: Horizontal Pod Autoscaler (1.5 h)

**The aha:** *Scaling is reactive, not predictive. K8s watches metrics, not your gut.*

**Write `k8s/07_hpa.yaml`:**

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: embedder-hpa
  namespace: qbc12-hw03-c-<username>
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: embedder
  minReplicas: 1
  maxReplicas: 3
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 50
  behavior:
    scaleDown:
      stabilizationWindowSeconds: 60
    scaleUp:
      stabilizationWindowSeconds: 0
      policies:
      - type: Percent
        value: 100
        periodSeconds: 30
```

**Apply and verify:**

```bash
kubectl apply -f k8s/07_hpa.yaml

# Wait 60s for metrics-server to gather 1 data point
sleep 60
kubectl -n qbc12-hw03-c-<username> get hpa
# Expect: TARGETS: <unknown>/50% initially, then 0%/50% (idle CPU)
```

**Load test:**

```bash
# Port-forward
kubectl -n qbc12-hw03-c-<username> port-forward svc/embedder 8000:80 &
PF=$!
sleep 2

# Install hey (one-time)
curl -L https://github.com/rakyll/hey/releases/download/v0.1.4/hey_linux_amd64 -o /usr/local/bin/hey
chmod +x /usr/local/bin/hey

# Generate load: 10000 requests, 50 concurrent, POST to /embed with batch of 8 texts
hey -n 10000 -c 50 -m POST -T "application/json" \
  -d '{"texts":["hello world","good morning","I love this","this is terrible","thank you","great job","oh no","really?"]}' \
  http://localhost:8000/embed &

# Watch HPA in another terminal
kubectl -n qbc12-hw03-c-<username> get hpa -w
# Expect: REPLICAS go from 1 → 2 → 3 over ~2-3 minutes

# Watch pods
kubectl -n qbc12-hw03-c-<username> get pods -w
# Expect: new pods Pending → ContainerCreating → Running → Ready

# When load test ends, watch HPA scale DOWN (after 60s stabilization)
# REPLICAS: 3 → 1

kill $PF
```

**The lesson:** HPA reads CPU from cAdvisor (via metrics-server) every 15s, computes the desired replica count, and the Deployment controller reconciles. You did NOT tell it to scale. You told it the **policy** (target 50% CPU, min 1, max 3) and the **controller** did the work.

**Capture:** `EVIDENCE/task5_hpa_scaling.png` (3 HPA snapshots: idle, peak, scaledown).

---

### Task 6: PodDisruptionBudget (1 h)

**The aha:** *Voluntary disruption (node drain) is rate-limited by your PDB. Without it, a node drain could take down your service.*

```bash
# Scale back to 3 replicas (PDB needs >= minAvailable to make sense)
kubectl -n qbc12-hw03-c-<username> scale deployment embedder --replicas=3

# Write the PDB
cat <<EOF | kubectl apply -f -
apiVersion: policy/v1
kind: PodDisruptionBudget
metadata:
  name: embedder-pdb
  namespace: qbc12-hw03-c-<username>
spec:
  minAvailable: 2
  selector:
    matchLabels:
      app: embedder
EOF

# Verify
kubectl -n qbc12-hw03-c-<username> get pdb
# Expect: MIN AVAILABLE = 2

# Try to drain (simulated, dry-run)
# Note: in a 1-node cluster, draining the only node will evict ALL pods.
# We use --dry-run=server to see what would happen.
kubectl drain 185.50.38.163 --dry-run=server --ignore-daemonsets --delete-emptydir-data
# Expect: "error: cannot evict pod as it would violate the pod's disruption budget"
# (or a similar message about 1 of 3 pods being evictable)

# Demonstrate: with 1 node, you cannot fully drain. The PDB holds.
# This is correct behavior. In a multi-node cluster, the drain would proceed
# but respect the PDB (only 1 pod evicted at a time).
```

**The lesson:** PDB does NOT prevent voluntary disruption. It **rate-limits** it. A node drain is "I'd like to remove N pods"; the PDB says "you can remove at most (replicas - minAvailable) at a time." Without a PDB, `kubectl drain` evicts all pods immediately — your service goes down.

**Capture:** `EVIDENCE/task6_pdb.png` (PDB definition + drain dry-run output).

---

### Task 7: PreStop hook + 6-check verification + scale-to-zero (2 h)

**The aha:** *SIGTERM alone doesn't wait for in-flight requests. A preStop hook buys you a graceful shutdown window. And sharing a cluster means releasing resources when you're done.*

#### Subtask 7a: PreStop hook (45 min)

```bash
# Add a preStop hook to the deployment
# In k8s/02_deployment.yaml, in spec.template.spec.containers[0], add:
#   lifecycle:
#     preStop:
#       exec:
#         command: ["/bin/sh", "-c", "sleep 10"]
# This gives the pod 10s to drain in-flight requests before SIGTERM.

kubectl -n qbc12-hw03-c-<username> apply -f k8s/02_deployment.yaml
# (apply with the new field)

# Demonstrate: trigger a rolling update, watch the preStop fire
kubectl -n qbc12-hw03-c-<username> patch deployment embedder \
  --type json -p='[{"op":"replace","path":"/spec/template/metadata/labels/version","value":"v4"}]'

# In one terminal, watch pod termination
kubectl -n qbc12-hw03-c-<username> get pods -w
# Expect: old pod has TerminationGracePeriodSeconds: 30, but the preStop
# sleep 10 fires FIRST. The pod stays in "Running" for 10s after the
# rolling update starts, then SIGTERM is sent.

# Verify with describe
POD=$(kubectl -n qbc12-hw03-c-<username> get pods -l app=embedder,version=v3 -o name | head -1)
kubectl -n qbc12-hw03-c-<username> describe $POD
# Look for:
#   Containers:
#     api:
#       State:          Terminated (after the rolling update)
#       Reason:         Completed
#   Events:
#     ... preStop hook executed ...
```

**The lesson:** `terminationGracePeriodSeconds: 30` is the upper bound. The preStop hook runs INSIDE that window. Without preStop, the kubelet sends SIGTERM immediately, and your app has 30s to handle it. With `sleep 10`, your app has 10s of "drain mode" before SIGTERM, plus 20s after SIGTERM to finish. **For HTTP services, this means in-flight requests complete before the connection is severed.**

**Capture:** `EVIDENCE/task7a_prestop.png` (pod describe showing preStop + Terminated state).

#### Subtask 7b: 6-check verification (30 min)

You must pass ALL 6 of these before submission is accepted. The checks are codified in `07_prestop_and_eval/verification.sh` — run it.

```bash
# Set your kubeconfig
export KUBECONFIG=$(pwd)/kubeconfig.yaml
# Make sure your .env is filled in
source .env

# Run the verification
bash 07_prestop_and_eval/verification.sh
# Expect: 6 passed, 0 failed
```

The 6 checks:

| # | Check | What it tests |
|---|---|---|
| V1 | Pod is `1/1 Ready` | Basic scheduling + readiness probe |
| V2 | `GET http://185.50.38.163:<your-nodeport>/healthz/live` returns 200 | Process up, **via NodePort** (not port-forward) |
| V3 | `GET http://185.50.38.163:<your-nodeport>/healthz/ready` returns 200 | Model loaded, via NodePort |
| V4 | `POST /embed` returns 200 with **384-dim vectors** | Model serving + correct shape |
| V5 | `POST /search` returns 200 with **at least 1 hit** | End-to-end Qdrant roundtrip |
| V6 | No OOMKilled in pod's lastState | Memory limit is healthy |

If any check fails, fix it. The 3 most common failures:
- V1 fails: your readiness probe is misconfigured. Check `state.loaded = True` is set after `from_pretrained()`.
- V2/V3 fails (connection refused): your Service is `ClusterIP` not `NodePort`. Re-apply with `type: NodePort`.
- V4 fails: your model is the wrong dim. Check it's `all-MiniLM-L6-v2` (384-dim), not e.g. `all-mpnet-base-v2` (768-dim).

**Capture:** `EVIDENCE/task7b_verification.png` (the script output: "6 passed, 0 failed").

#### Subtask 7c: Scale to zero (15 min)

When you are done with HW3_C, release the cluster resources for your classmates.

```bash
# Scale main deployment to zero
kubectl scale deployment embedder --replicas=0
# If you have a green deployment from task 4, scale that too
kubectl scale deployment embedder-green --replicas=0 2>/dev/null || true

# Verify
kubectl get pods
# Expected: No resources found in your namespace

# Watch resources free up
kubectl -n qbc12-hw03-c-<username> get all
# Expected: deployments with 0/0 replicas, services still defined, no pods
```

**Why this matters:** the cluster has 24 vCPU and 117 GB. 42 students × 1 GB idle pod = 42 GB. If even half of the class forgets to scale down, the cluster is full and the next student's HPA demo will hang on `Pending` pods. **You are a good cluster citizen if you scale to zero.**

**Capture:** `EVIDENCE/task7c_scale_to_zero.png` (the `kubectl get all` output showing 0 pods).

**When you come back tomorrow (to demo to the TA, or to fix a bug):**
```bash
kubectl scale deployment embedder --replicas=1
# 30s later, the pod is back
```

---

## 2. Submission

```
qbc12_hw03_<username>/
├── k8s/                                # this sub-assignment
│   ├── 02_deployment.yaml              # task 1
│   ├── 03_service.yaml                 # task 1
│   ├── 04_configmap.yaml               # task 1
│   ├── 05_secret.yaml                  # task 1
│   ├── 06_deployment_green.yaml        # task 4
│   ├── 07_hpa.yaml                     # task 5
│   ├── 08_pdb.yaml                     # task 6
│   └── README.md                       # apply commands + verified outputs
└── EVIDENCE/
    ├── task1_pods_running.png
    ├── task1_three_probes.png
    ├── task2a_oomkilled_describe.png
    ├── task2a_oomkilled_recovery.png
    ├── task2b_self_healing.png
    ├── task3a_rolling_update.png
    ├── task3b_configmap_rotation.png
    ├── task4_blue_green.png
    ├── task5_hpa_scaling.png
    ├── task6_pdb.png
    ├── task7a_prestop.png
    ├── task7b_verification.png         # the 6-check output
    └── task7c_scale_to_zero.png        # the 0-pod final state
```

## 3. Time check (12 hours)

| Task | Subtasks | Time |
|---|---|---|
| Task 1: First deployment (init + 3 probes + state.loaded + resources) | 2.5 h | 2.5 h |
| Task 2: Failure modes | OOMKilled + self-healing | 1.5 h |
| Task 3: Rolling + ConfigMap | rolling + rotation | 1.5 h |
| Task 4: Blue/Green | build v3 + atomic cutover | 2.0 h |
| Task 5: HPA | load test + scale up/down | 1.5 h |
| Task 6: PDB | dry-run drain | 1.0 h |
| Task 7: PreStop + verification + scale-to-zero | 3 subtasks | 2.0 h |
| **Total** | | **12.0 h** |

## 4. Common pitfalls

| Pitfall | Symptom | Fix |
|---|---|---|
| Image not pushed to registry | `ImagePullBackOff` | `docker push 185.50.38.163:35000/qbc12-embedder-<username>:v1` and verify with `curl http://185.50.38.163:35000/v2/_catalog` |
| Init container fails | Pod stuck in `Init:Error` | `kubectl describe pod` → look at init container's exit reason (usually `mc` not finding the bundle path) |
| `/healthz/ready` always 503 | Readiness never flips | Check `app.state.loaded = True` is set AFTER `from_pretrained()` returns |
| Memory too low | `OOMKilled` | 80 MB model + 400 MB framework + 200 MB buffer = 700 MB minimum. Use 1Gi. |
| HPA not scaling | `kubectl top pods` returns empty | metrics-server is installed by TA, not by you. If empty, ping TA. |
| Service selector mismatch | 503 from curl | Selector must match pod labels EXACTLY. `app=embedder` ≠ `app=Embedder`. |
| PDB drain "succeeds" | All pods evicted | PDB only rate-limits, doesn't block. With 1 node, drain removes all. This is correct. |
| PreStop hook infinite | Pod stuck in Terminating | Check `terminationGracePeriodSeconds` is ≥ preStop duration. Default 30s is fine. |
| Service is ClusterIP, not NodePort | `curl http://185.50.38.163:30090/...` refuses | Service must be `type: NodePort` with `nodePort: 30090` (your assigned port). |
| Forgot to scale to zero | Cluster fills up, classmates see Pending | `kubectl scale deployment embedder --replicas=0` |

## 5. Grading (see HW3_08 for full rubric)

HW3_C is 35 points (out of 100 total for HW3):

| Component | Points |
|---|---|
| Task 1: Init container + 3 probes + state.loaded + resources | 7 |
| Task 2: OOMKilled + self-healing | 6 |
| Task 3: Rolling + ConfigMap | 5 |
| Task 4: Blue/Green | 5 |
| Task 5: HPA | 4 |
| Task 6: PDB | 2 |
| Task 7: PreStop + 6-check verification + scale-to-zero | 6 (prestop 2 + verification 3 + scale-to-zero 1) |
| **Total** | **35** |

The remaining 65 points come from HW3_A (30) and HW3_B (35).

> **Note:** HW3_C is graded entirely by inspecting the **13 PNG screenshots** in your `EVIDENCE/` folder plus your **YAML manifests** in `k8s/`. There is no leaderboard, no automated scoring, no PG submission. The TA opens each student's submission, looks at the screenshots, and applies the rubric above.

## 6. Why we chose k3s (not kind, not minikube, not EKS)

| Option | Pros | Cons | Verdict |
|---|---|---|---|
| **kind** | Mature, multi-node | Brittle on Windows, no real systemd | ❌ |
| **minikube** | Single binary | Hypervisor-dependent, slow on Windows | ❌ |
| **EKS / GKE** | Production-realistic | Costs money, we have 1 server | ❌ |
| **k3d (k3s in Docker)** | No systemd, easy reset | Single-node by default, less realistic | △ |
| **k3s (real)** | Real CNCF K8s, multi-node, 700 MB binary, runs on Ubuntu | Needs systemd + root | ✅ chosen |

K3s is the best fit because:
- **Real K8s**, not a simulation. Students see real `crictl`, real CNI, real iptables.
- **700 MB control plane** — fits on our 24-vCPU server with room for 42 students' pods.
- **Traefik disabled** (port 80/443 conflict with Apache). We use NodePort services instead.
- **Single-node cluster** is fine for this assignment (no need to demonstrate node affinity in 12h).

## 7. FAQ

**Q: Can I run `kubectl exec` into my pod to debug?**
A: Yes. `kubectl -n qbc12-hw03-c-<username> exec -it <pod> -- /bin/sh` works. Use it to check `ps`, `env`, `/proc/1/cmdline`, `ls /bundle`.

**Q: Can I see other students' pods?**
A: No. Your Role grants read/write only in your namespace. `kubectl get pods -A` returns 403 for non-system namespaces. Try once to confirm, then move on.

**Q: My HPA shows `<unknown>/50%` — is it broken?**
A: No, that's normal for the first 60s (metrics-server needs 2 data points). Wait, then `kubectl -n <ns> describe hpa` to see why.

**Q: My pod got OOMKilled and won't recover. What do I do?**
A: Restore the memory limit. `kubectl -n <ns> patch deployment embedder --type json -p='[{"op":"replace","path":"/spec/template/spec/containers/0/resources/limits/memory","value":"1Gi"}]'`.

**Q: Can I deploy MORE than 3 replicas?**
A: Your ResourceQuota allows 8 vCPU and 16 GB. With each pod at 500m / 1Gi, you could deploy 8. But: (1) you'd be a noisy neighbor, (2) HPA max is 3 anyway, (3) the cluster is shared. Don't.

**Q: Can I use Helm or Kustomize?**
A: Optional. Kustomize is built into `kubectl` (`kubectl apply -k k8s/`). Helm is overkill for 7 manifests.

**Q: What happens if the k3s API goes down?**
A: Your pods keep running (the kubelet doesn't need the API for that), but you can't apply new manifests. TA will fix.
