#!/usr/bin/env bash
# prerelease_check.sh — mirrors the full CI gate locally before a release.
# Run from the repository root: bash scripts/prerelease_check.sh
set -euo pipefail

PASS=0
FAIL=0
SKIP=0

ok()   { echo "[PASS] $*"; PASS=$((PASS+1)); }
fail() { echo "[FAIL] $*"; FAIL=$((FAIL+1)); }
skip() { echo "[SKIP] $*"; SKIP=$((SKIP+1)); }

has_module() { python -c "import $1" 2>/dev/null; }

echo "=== CStyleCheck pre-release gate ==="
echo

# 1. YAML sync check (src/rules.yml must match tests/rules.yml except known test fixtures)
echo "--- 1. YAML sync check ---"
DIFF=$(diff src/rules.yml tests/rules.yml \
       | grep '^[<>]' \
       | grep -v 'style: tabs\|style: spaces\|allow_loop_vars_short\|TEST FIXTURE\|intentionally' \
       || true)
if [ -n "$DIFF" ]; then
    fail "tests/rules.yml differs from src/rules.yml"
    echo "$DIFF"
else
    ok "rules.yml in sync"
fi
echo

# 2. Full test suite (with coverage if pytest-cov is available)
echo "--- 2. pytest ---"
if has_module pytest; then
    COV_FLAGS=""
    if has_module pytest_cov; then
        COV_FLAGS="--cov=src --cov-branch --cov-fail-under=85"
    fi
    if python -m pytest tests/ -q --tb=short $COV_FLAGS 2>&1; then
        ok "pytest passed"
    else
        fail "pytest failed"
    fi
else
    skip "pytest not installed (pip install pytest)"
fi
echo

# 3. ruff lint
echo "--- 3. ruff lint ---"
if has_module ruff; then
    if python -m ruff check src/ tests/ 2>&1; then
        ok "ruff clean"
    else
        fail "ruff reported violations"
    fi
else
    skip "ruff not installed (pip install ruff)"
fi
echo

# 4. mypy type check
echo "--- 4. mypy ---"
if has_module mypy; then
    if python -m mypy src/cstylecheck/ --ignore-missing-imports --no-error-summary 2>&1; then
        ok "mypy clean"
    else
        fail "mypy reported errors"
    fi
else
    skip "mypy not installed (pip install mypy)"
fi
echo

# 5. Self-check: tool checks its own source with zero error-level violations
echo "--- 5. CStyleCheck self-check ---"
ERROR_COUNT=$(python src/cstylecheck.py --config src/rules.yml src/cstylecheck/ \
              | grep -c ': ERROR ' || true)
if [ "$ERROR_COUNT" -eq 0 ]; then
    ok "self-check: 0 error-level violations"
else
    fail "self-check: $ERROR_COUNT error-level violations"
    python src/cstylecheck.py --config src/rules.yml src/cstylecheck/ | grep ': ERROR '
fi
echo

# Summary
echo "=== Results: $PASS passed, $FAIL failed, $SKIP skipped ==="
[ "$FAIL" -eq 0 ]
