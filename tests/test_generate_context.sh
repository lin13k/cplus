#!/usr/bin/env zsh
# Integration tests for: cplus generate-context
# Verifies subcommand wiring, prompt file existence, --dry-run flag, and key sections.

set -euo pipefail

PASS=0
FAIL=0

pass() {
  PASS=$((PASS + 1))
  echo "  ✓ $1"
}

fail() {
  FAIL=$((FAIL + 1))
  echo "  ✗ $1"
}

assert_contains() {
  local file="$1" pattern="$2" label="$3"
  if grep -q "$pattern" "$file" 2>/dev/null; then
    pass "$label"
  else
    fail "$label (pattern '$pattern' not found in $file)"
  fi
}

# --- Test: generate-context is a valid subcommand ---
echo "Test: generate-context is a valid subcommand"

if cplus ls 2>&1 | grep -q "generate-context"; then
  pass "cplus ls lists generate-context"
else
  fail "cplus ls does not list generate-context"
fi

if cplus generate-context --help 2>&1 | grep -q "module-path"; then
  pass "cplus generate-context --help works"
else
  fail "cplus generate-context --help does not work"
fi

# --- Test: all 4 prompt files exist ---
echo ""
echo "Test: all prompt files exist"

PROMPTS_DIR="$(dirname "$(dirname "$0")")/prompts"

# Find installed prompts dir — prefer the source tree prompts
if [[ ! -d "$PROMPTS_DIR" ]]; then
  PROMPTS_DIR="${CPLUS_HOME:-$HOME/.config/cplus}/prompts"
fi

ACTION_FILE="$PROMPTS_DIR/actions/generate-context.md"
ANALYZER_FILE="$PROMPTS_DIR/roles/generate-context/analyzer.md"
GENERATOR_FILE="$PROMPTS_DIR/roles/generate-context/generator.md"
VALIDATOR_FILE="$PROMPTS_DIR/roles/generate-context/validator.md"

for f in "$ACTION_FILE" "$ANALYZER_FILE" "$GENERATOR_FILE" "$VALIDATOR_FILE"; do
  if [[ -f "$f" ]]; then
    pass "exists: ${f##*/}"
  else
    fail "missing: $f"
  fi
done

# --- Test: --dry-run flag is recognized ---
echo ""
echo "Test: --dry-run flag is recognized"

DRY_RUN_OUTPUT="$(cplus generate-context --help 2>&1)"
if echo "$DRY_RUN_OUTPUT" | grep -q "\-\-dry-run"; then
  pass "--dry-run documented in help"
else
  fail "--dry-run not in help output"
fi

# Calling with --dry-run but no module-path should error with usage, not "unknown flag"
DRY_RUN_ERR="$(cplus generate-context --dry-run 2>&1 || true)"
if echo "$DRY_RUN_ERR" | grep -qi "usage\|module-path\|<module-path>"; then
  pass "--dry-run flag accepted (missing path gives usage error)"
else
  fail "--dry-run flag not recognized: $DRY_RUN_ERR"
fi

# --- Test: prompt files contain key sections ---
echo ""
echo "Test: action prompt contains key sections"
assert_contains "$ACTION_FILE" "ANALYZER" "action references ANALYZER phase"
assert_contains "$ACTION_FILE" "GENERATOR" "action references GENERATOR phase"
assert_contains "$ACTION_FILE" "VALIDATOR" "action references VALIDATOR phase"

echo ""
echo "Test: ANALYZER prompt contains expected steps"
assert_contains "$ANALYZER_FILE" "Step.*Map the Module Structure" "analyzer: Map the Module Structure"
assert_contains "$ANALYZER_FILE" "Step.*Extract the Data Model" "analyzer: Extract the Data Model"
assert_contains "$ANALYZER_FILE" "Step.*Trace the Business Flows" "analyzer: Trace the Business Flows"
assert_contains "$ANALYZER_FILE" "Step.*Identify Integration Points" "analyzer: Identify Integration Points"
assert_contains "$ANALYZER_FILE" "Step.*Determine Scope" "analyzer: Determine Scope"

echo ""
echo "Test: GENERATOR prompt contains expected templates"
assert_contains "$GENERATOR_FILE" "AGENT.md" "generator: AGENT.md template"
assert_contains "$GENERATOR_FILE" "data-model" "generator: data-model template"
assert_contains "$GENERATOR_FILE" "flows" "generator: flows template"

echo ""
echo "Test: VALIDATOR prompt contains expected checks"
assert_contains "$VALIDATOR_FILE" "Check.*Accuracy" "validator: Accuracy check"
assert_contains "$VALIDATOR_FILE" "Check.*Completeness" "validator: Completeness check"
assert_contains "$VALIDATOR_FILE" "Check.*Consistency" "validator: Consistency check"
assert_contains "$VALIDATOR_FILE" "Check.*Freshness" "validator: Freshness check"
assert_contains "$VALIDATOR_FILE" "Verdict" "validator: Verdict section"

# --- Summary ---
echo ""
echo "================================"
echo "Results: $PASS passed, $FAIL failed"
echo "================================"

if [[ $FAIL -gt 0 ]]; then
  exit 1
fi
