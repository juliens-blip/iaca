#!/usr/bin/env bash

set -euo pipefail

run_step() {
    local step_label="$1"
    shift

    echo "[START] ${step_label}"
    if "$@"; then
        echo "[PASS]  ${step_label}"
    else
        local exit_code=$?
        echo "[FAIL]  ${step_label} (exit ${exit_code})" >&2
        exit "${exit_code}"
    fi
}

run_step "1/4 backend compileall" backend/.venv/bin/python -m compileall backend/app
run_step "2/4 security regression" bash scripts/test_security_regression.sh
run_step "3/4 frontend typecheck" bash -lc 'cd frontend && ./node_modules/.bin/tsc --noEmit'

if [[ "${FAST:-0}" == "1" ]]; then
    echo "[START] 4/4 frontend build"
    echo "[PASS]  4/4 frontend build (skipped: FAST=1)"
else
    run_step "4/4 frontend build" bash -lc 'cd frontend && npm run build'
fi

echo "[PASS]  Ralph full validation completed"
