#!/usr/bin/env bash
# verification.sh - Run the 6 checks the instructor requires before submission.
# This is the evidence-capture script for EVIDENCE/task7b_verification.png
#
# All 6 checks must PASS before you scale to zero and submit.
#
# V1: pod 1/1 Ready (in-cluster)
# V2: /healthz/live returns 200 (via NodePort from outside the cluster)
# V3: /healthz/ready returns 200 (via NodePort)
# V4: /embed returns 200 with 384-dim vectors
# V5: /search returns 200 with hits
# V6: no OOMKilled in last 10 minutes

set -euo pipefail

if [ -f ../.env ]; then
    source ../.env
fi

USERNAME="${USERNAME:?Set USERNAME in .env}"
NODEPORT="${NODEPORT:?Set NODEPORT in .env (from your handout zip)}"
export KUBECONFIG="${KUBECONFIG_PATH:-./kubeconfig.yaml}"
NS="${NAMESPACE:-qbc12-hw03-c-${USERNAME}}"
SERVICE_URL="http://185.50.38.163:${NODEPORT}"

echo "=== Deployment verification (6 checks) ==="
echo "Namespace:    $NS"
echo "Service URL:  $SERVICE_URL"
echo ""

PASS=0
FAIL=0

check() {
    local NAME="$1"
    local EXPECTED="$2"
    local ACTUAL="$3"
    if [ "$ACTUAL" = "$EXPECTED" ]; then
        echo "  ✓ $NAME = $ACTUAL"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $NAME = $ACTUAL  (expected $EXPECTED)"
        FAIL=$((FAIL + 1))
    fi
}

# ============== V1: Pod is running and ready ==============
echo "## V1: Pod is running and 1/1 Ready"
PODS=$(kubectl -n "$NS" get pods -l app=embedder --no-headers 2>/dev/null || true)
if [ -z "$PODS" ]; then
    echo "  ✗ no pods found"
    FAIL=$((FAIL + 1))
else
    echo "$PODS"
    NOT_READY=$(echo "$PODS" | awk '{print $2}' | grep -v '^1/1$' | wc -l)
    if [ "$NOT_READY" -eq 0 ]; then
        echo "  ✓ all pods are 1/1 Ready"
        PASS=$((PASS + 1))
    else
        echo "  ✗ $NOT_READY pod(s) are not 1/1 Ready"
        FAIL=$((FAIL + 1))
    fi
fi
echo ""

# ============== V2: /healthz/live via NodePort ==============
echo "## V2: /healthz/live (via NodePort ${NODEPORT})"
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${SERVICE_URL}/healthz/live")
check "/healthz/live"  "200" "$CODE"
echo ""

# ============== V3: /healthz/ready via NodePort ==============
echo "## V3: /healthz/ready (via NodePort ${NODEPORT})"
CODE=$(curl -s -o /dev/null -w "%{http_code}" --max-time 5 "${SERVICE_URL}/healthz/ready")
check "/healthz/ready" "200" "$CODE"
echo ""

# ============== V4: /embed returns 200 with 384-dim vectors ==============
echo "## V4: /embed returns 200 with 384-dim vectors"
EMBED_BODY=$(curl -s -w "\n%{http_code}" --max-time 30 -X POST "${SERVICE_URL}/embed" \
    -H "Content-Type: application/json" \
    -d '{"texts":["hello world"]}')
EMBED_CODE=$(echo "$EMBED_BODY" | tail -1)
EMBED_JSON=$(echo "$EMBED_BODY" | sed '$d')
check "/embed" "200" "$EMBED_CODE"
if [ "$EMBED_CODE" = "200" ]; then
    DIM=$(echo "$EMBED_JSON" | python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    vecs = d.get('vectors') or d.get('embeddings') or []
    if vecs and isinstance(vecs, list):
        print(len(vecs[0]) if isinstance(vecs[0], list) else len(vecs))
    else:
        print('unknown')
except Exception as e:
    print('parse_error')
" 2>/dev/null || echo "parse_error")
    if [ "$DIM" = "384" ]; then
        echo "  ✓ vector dim = 384"
        PASS=$((PASS + 1))
    else
        echo "  ✗ vector dim = $DIM (expected 384)"
        FAIL=$((FAIL + 1))
    fi
else
    FAIL=$((FAIL + 1))
    echo "  (skipped dim check — /embed did not return 200)"
fi
echo ""

# ============== V5: /search returns 200 with hits ==============
echo "## V5: /search returns 200 with hits"
SEARCH_BODY=$(curl -s -w "\n%{http_code}" --max-time 30 -X POST "${SERVICE_URL}/search" \
    -H "Content-Type: application/json" \
    -d '{"query":"thank you so much", "top_k":3}')
SEARCH_CODE=$(echo "$SEARCH_BODY" | tail -1)
SEARCH_JSON=$(echo "$SEARCH_BODY" | sed '$d')
check "/search" "200" "$SEARCH_CODE"
if [ "$SEARCH_CODE" = "200" ]; then
    HITS=$(echo "$SEARCH_JSON" | python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    h = d.get('hits') or d.get('results') or []
    print(len(h))
except Exception as e:
    print('parse_error')
" 2>/dev/null || echo "parse_error")
    if [ "$HITS" -ge 1 ] 2>/dev/null; then
        echo "  ✓ hits = $HITS"
        PASS=$((PASS + 1))
    else
        echo "  ✗ hits = $HITS (expected >= 1)"
        FAIL=$((FAIL + 1))
    fi
else
    FAIL=$((FAIL + 1))
    echo "  (skipped hits check — /search did not return 200)"
fi
echo ""

# ============== V6: No OOMKilled in last 10 minutes ==============
echo "## V6: No OOMKilled in recent pod history"
OOM_COUNT=$(kubectl -n "$NS" get pods -o json 2>/dev/null | \
    python3 -c "
import json, sys
try:
    d = json.loads(sys.stdin.read())
    count = 0
    for item in d.get('items', []):
        for cs in item.get('status', {}).get('containerStatuses', []) or []:
            term = (cs.get('lastState') or {}).get('terminated') or {}
            if term.get('reason') == 'OOMKilled':
                count += 1
    print(count)
except Exception:
    print(0)
" 2>/dev/null || echo 0)
check "OOMKilled count" "0" "$OOM_COUNT"
echo ""

# ============== Summary ==============
echo "## Summary: $PASS passed, $FAIL failed"
if [ "$FAIL" -eq 0 ]; then
    echo ""
    echo "=== All checks PASSED — capture the screenshot, then scale to zero ==="
    exit 0
else
    echo ""
    echo "=== Verification FAILED — fix the failing checks ==="
    exit 1
fi
