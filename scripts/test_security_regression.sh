#!/usr/bin/env bash
# =============================================================================
# test_security_regression.sh — Tests de régression sécurité IACA backend
# =============================================================================
#
# Usage:
#   bash scripts/test_security_regression.sh
#
# Ce script :
#   1) Démarre l'API FastAPI sur un port dynamique (8099+RANDOM) avec :
#        API_AUTH_TOKEN=test-secret
#        RATE_LIMIT_ENABLED=true
#        RATE_LIMIT_REQUESTS=30  (marge pour tests 1-4, burst test5=40 déclenche 429)
#        RATE_LIMIT_WINDOW_SECONDS=60
#   2) Teste POST /api/matieres sans token          → attend 401
#   3) Teste POST /api/matieres avec token valide   → attend 201 ou 409
#   4) Teste WS /api/vocal/ws sans token            → attend 1008 ou 403/InvalidStatus
#   5) Teste WS /api/vocal/ws avec ?token=test-secret → attend connexion acceptée
#   6) Burst de requêtes GET /api/vocal/status      → attend au moins un 429
#   7) Arrête l'API et retourne exit 0 (tout OK) ou exit 1 (au moins un échec)
#
# Prérequis : curl, backend/.venv (uvicorn + websockets déjà installés)
# =============================================================================

set -euo pipefail

# Dynamic port: 8100–8599 to avoid stale-server conflicts
PORT=$(( 8100 + (RANDOM % 500) ))
# Kill any stale process already on this port
fuser -k "${PORT}/tcp" 2>/dev/null || true
BASE_URL="http://127.0.0.1:${PORT}"
TOKEN="test-secret"
BACKEND_DIR="$(cd "$(dirname "$0")/../backend" && pwd)"
PYTHON="${BACKEND_DIR}/.venv/bin/python3"
UVICORN="${BACKEND_DIR}/.venv/bin/uvicorn"
LOG="/tmp/iaca_security_test_$$.log"
SERVER_PID=""
FAILURES=0

# ── Colors ───────────────────────────────────────────────────────────────────
RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
pass() { echo -e "${GREEN}  PASS${NC} $1"; }
fail() { echo -e "${RED}  FAIL${NC} $1"; FAILURES=$((FAILURES+1)); }
info() { echo -e "${YELLOW}  ....${NC} $1"; }

# ── Cleanup ──────────────────────────────────────────────────────────────────
cleanup() {
    if [[ -n "$SERVER_PID" ]] && kill -0 "$SERVER_PID" 2>/dev/null; then
        info "Arrêt du serveur (PID $SERVER_PID)…"
        kill "$SERVER_PID" 2>/dev/null || true
        wait "$SERVER_PID" 2>/dev/null || true
    fi
    rm -f "$LOG"
}
trap cleanup EXIT

# ── Start server ─────────────────────────────────────────────────────────────
echo "=== Démarrage API sur 127.0.0.1:${PORT} ==="
(
  cd "$BACKEND_DIR"
  API_AUTH_TOKEN="$TOKEN" \
  RATE_LIMIT_ENABLED="true" \
  RATE_LIMIT_REQUESTS="30" \
  RATE_LIMIT_WINDOW_SECONDS="60" \
  "$UVICORN" app.main:app \
    --host 127.0.0.1 --port "$PORT" \
    --log-level warning \
    > "$LOG" 2>&1
) &
SERVER_PID=$!

# Wait for server to be ready (up to 60s)
info "Attente démarrage serveur…"
for i in $(seq 1 120); do
    if curl -sf "${BASE_URL}/health" > /dev/null 2>&1; then
        pass "Serveur prêt (tentative ${i})"
        break
    fi
    sleep 0.5
    if [[ $i -eq 120 ]]; then
        echo "--- LOG SERVEUR ---"
        cat "$LOG"
        fail "Serveur non démarré après 60s"
        exit 1
    fi
done

echo ""
echo "=== TEST 1: POST /api/matieres sans token → 401 ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}/api/matieres" \
    -H "Content-Type: application/json" \
    -d '{"nom":"TestRegression","description":"regression"}')
if [[ "$STATUS" == "401" ]]; then
    pass "POST sans token → 401 (obtenu: $STATUS)"
else
    fail "POST sans token → attendu 401, obtenu $STATUS"
fi

echo ""
echo "=== TEST 2: POST /api/matieres avec token valide → 201 ou 409 ==="
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
    -X POST "${BASE_URL}/api/matieres" \
    -H "Content-Type: application/json" \
    -H "Authorization: Bearer ${TOKEN}" \
    -d '{"nom":"TestRegression","description":"regression"}')
if [[ "$STATUS" == "201" || "$STATUS" == "409" ]]; then
    pass "POST avec token → $STATUS (201 créé ou 409 déjà existant)"
else
    fail "POST avec token → attendu 201/409, obtenu $STATUS"
fi

echo ""
echo "=== TEST 3: WebSocket sans token → close 1008 ==="
WS_NO_TOKEN=$("$PYTHON" - <<PYEOF
import asyncio, sys
try:
    import websockets
except ImportError:
    print("NO_WEBSOCKETS")
    sys.exit(0)

async def test():
    try:
        async with websockets.connect("ws://127.0.0.1:${PORT}/api/vocal/ws") as ws:
            await ws.recv()
            print("ACCEPTED")
    except websockets.exceptions.ConnectionClosedError as e:
        code = e.rcvd.code if e.rcvd else 0
        print(f"CLOSED_{code}")
    except websockets.exceptions.InvalidStatus as e:
        # websockets v16: HTTP rejection before upgrade (e.g. 403)
        print(f"REJECTED_{e.response.status_code}")
    except Exception as e:
        print(f"ERROR:{type(e).__name__}:{e}")

asyncio.run(test())
PYEOF
)
if [[ "$WS_NO_TOKEN" == "CLOSED_1008" || "$WS_NO_TOKEN" == "REJECTED_HTTP" || "$WS_NO_TOKEN" =~ ^REJECTED_ ]]; then
    pass "WS sans token → rejeté ($WS_NO_TOKEN)"
elif [[ "$WS_NO_TOKEN" == "NO_WEBSOCKETS" ]]; then
    info "SKIP WS tests — websockets non installé dans le venv"
else
    fail "WS sans token → attendu rejet (1008/403), obtenu $WS_NO_TOKEN"
fi

echo ""
echo "=== TEST 4: WebSocket avec ?token=test-secret → connexion acceptée ==="
WS_WITH_TOKEN=$("$PYTHON" - <<PYEOF
import asyncio, sys
try:
    import websockets
except ImportError:
    print("NO_WEBSOCKETS")
    sys.exit(0)

async def test():
    try:
        async with websockets.connect(
            "ws://127.0.0.1:${PORT}/api/vocal/ws?token=${TOKEN}",
            open_timeout=5,
        ) as ws:
            await ws.send('{"type":"pong"}')
            print("ACCEPTED")
    except websockets.exceptions.ConnectionClosedError as e:
        code = e.rcvd.code if e.rcvd else 0
        print(f"CLOSED_{code}")
    except Exception as e:
        print(f"ERROR:{e}")

asyncio.run(test())
PYEOF
)
if [[ "$WS_WITH_TOKEN" == "ACCEPTED" ]]; then
    pass "WS avec token → connexion acceptée"
elif [[ "$WS_WITH_TOKEN" == "NO_WEBSOCKETS" ]]; then
    info "SKIP — websockets non installé dans le venv"
else
    fail "WS avec token → attendu ACCEPTED, obtenu $WS_WITH_TOKEN"
fi

echo ""
echo "=== TEST 5: Burst GET /api/vocal/status → au moins un 429 ==="
# Rate limit: 30 req/60s. Burst 40 requests, expect ≥1 × 429.
GOT_429=0
for i in $(seq 1 40); do
    S=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer ${TOKEN}" \
        "${BASE_URL}/api/vocal/status")
    if [[ "$S" == "429" ]]; then
        GOT_429=$((GOT_429+1))
    fi
done
if [[ $GOT_429 -ge 1 ]]; then
    pass "Burst → $GOT_429 réponse(s) 429 reçues"
else
    fail "Burst → aucun 429 reçu (rate-limit non déclenché ?)"
fi

# ── Summary ──────────────────────────────────────────────────────────────────
echo ""
echo "==========================================="
if [[ $FAILURES -eq 0 ]]; then
    echo -e "${GREEN}TOUS LES TESTS PASSENT (0 échec)${NC}"
    exit 0
else
    echo -e "${RED}${FAILURES} TEST(S) ÉCHOUÉ(S)${NC}"
    exit 1
fi
