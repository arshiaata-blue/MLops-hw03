#!/usr/bin/env bash
# 05_load_test.sh — concurrent /embed against the running API. Useful for
# verifying that the request rate matches the model card (MiniLM-L6-v2
# should do ~1000 req/s single-threaded on a modern x86).
set -euo pipefail

URL="${API_URL:-http://127.0.0.1:8000}"
N="${N:-200}"
CONCURRENCY="${CONCURRENCY:-8}"

echo "Load test: ${N} requests, ${CONCURRENCY} concurrent workers → ${URL}/embed"

cat > /tmp/load_body.json <<'JSON'
{"texts": ["hello world"]}
JSON

python - <<PY
import concurrent.futures, json, statistics, time, urllib.request

URL = "${URL}/embed"
N = ${N}
C = ${CONCURRENCY}
body = json.dumps({"texts": ["hello world"]}).encode()

def one_call(_):
    t0 = time.perf_counter()
    req = urllib.request.Request(URL, data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as r:
        r.read()
    return (time.perf_counter() - t0) * 1000.0

t0 = time.perf_counter()
with concurrent.futures.ThreadPoolExecutor(max_workers=C) as ex:
    latencies = list(ex.map(one_call, range(N)))
elapsed = time.perf_counter() - t0
latencies.sort()
p50 = latencies[len(latencies)//2]
p95 = latencies[int(len(latencies)*0.95)]
p99 = latencies[int(len(latencies)*0.99)]
print(f"  total:   {elapsed:.2f}s")
print(f"  rate:    {N/elapsed:.1f} req/s")
print(f"  p50:     {p50:.1f}ms")
print(f"  p95:     {p95:.1f}ms")
print(f"  p99:     {p99:.1f}ms")
PY
