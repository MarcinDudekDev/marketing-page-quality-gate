#!/usr/bin/env bash
# build_loop.sh — autonomous "Marketing Page Quality Gate" MCP-server builder driven by Grok Build.
#
# Adapted from ~/Projects/shipswipe/server/build_backend_loop.sh (PROVEN 2026-06-22).
# Repointed for this entry; Postgres/Redis preflight removed (no datastore here).
#
#   Oracle  = contract/pytest_oracle.py  (runs the pytest CONTRACT suite)
#   Builder = grok  (headless, ~free)    -> edits code under quality_gate/ until green
#
# Loop: run pytest oracle -> if all green STOP -> feed FAILING tests to Grok -> code -> repeat.
# "Finished" == the contract suite is green. Grok NEVER grades itself.
#
# Three brakes guarantee halt: (1) all criteria pass, (2) MAX_ROUNDS, (3) PATIENCE stale rounds.
# Safety: atomic git commit per progress round; regressions reverted; the CONTRACT
# (tests/, contract/, fixtures/, CONTRACT.md, BRIEF.md, pyproject.toml, etc.) restored if Grok touches it.
set -euo pipefail

REPO="$(cd "$(dirname "$0")" && pwd)"
ORACLE="$REPO/contract/pytest_oracle.py"
MAX_ROUNDS="${1:-12}"; PATIENCE="${2:-3}"

# Contract paths (relative to REPO) that Grok must not alter — restored each round.
PROTECTED=( "tests" "contract" "fixtures" "CONTRACT.md" "BRIEF.md" "pyproject.toml" ".python-version" "build_loop.sh" "README.md" )

cd "$REPO"
git config user.email "marcin.dudek.dev@gmail.com" >/dev/null 2>&1 || true
git config user.name  "Marcin Dudek" >/dev/null 2>&1 || true

# ---- preflight ---------------------------------------------------------------
command -v uv   >/dev/null || { echo "FATAL: uv not found"; exit 1; }
command -v grok >/dev/null || { echo "FATAL: grok not found"; exit 1; }
echo "preflight OK — uv, grok"

restore_contract() {
  for p in "${PROTECTED[@]}"; do
    git ls-files --error-unmatch "$p" >/dev/null 2>&1 && git checkout -- "$p" 2>/dev/null || true
  done
}

QA_JSON=""
qa_run()     { QA_JSON="$(python3 "$ORACLE" "$REPO" 2>/dev/null)"; }
qa_passing() { printf '%s' "$QA_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['passed'])"; }
qa_total()   { printf '%s' "$QA_JSON" | python3 -c "import sys,json;print(json.load(sys.stdin)['total'])"; }
qa_fails()   { printf '%s' "$QA_JSON" | python3 -c "import sys,json;[print(f\"- {r['id']}: {r['detail']}\") for r in json.load(sys.stdin)['results'] if not r['passed']]"; }

# TOT is recomputed every round: at start the package doesn't exist so the suite
# fails to collect (few criteria); once quality_gate/ appears, files collect into the
# full ~26 tests and TOT grows. "Done" = passed == total (with total > 0), checked live.
qa_run; TOT=$(qa_total); best=$(qa_passing); stale=0
echo "── start: $best/$TOT criteria pass"
[ "$best" -eq "$TOT" ] && [ "$TOT" -gt 6 ] && { echo "already complete"; exit 0; }

for ((r=1; r<=MAX_ROUNDS; r++)); do
  fails="$(qa_fails)"
  echo "── round $r/$MAX_ROUNDS  ($best/$TOT pass, stale $stale/$PATIENCE)"

  ( grok -p "You are building a Python 3.14 + MCP server (the 'Marketing Page Quality Gate') in this directory. Read CONTRACT.md (the precise spec for every function, return shape, and scoring rubric) and BRIEF.md (the pitch/context). Build code ONLY under quality_gate/ (pixels.py, mobile.py, cta.py, links.py, scoring.py, connectors.py, server.py, __init__.py). An automated pytest contract grades you; these criteria currently FAIL and are your job this round:
$fails
Implement/fix code under quality_gate/ so those tests pass. Match the exact dict keys, scoring weights, and grade thresholds in CONTRACT.md — the tests assert exact numbers. Parse HTML with beautifulsoup4. Pure scoring functions must be OFFLINE (no network); only the MCP server's url-fetch path and the default link fetcher may use httpx. Deps are pre-installed; use 'uv run' — do NOT run 'uv add' or edit pyproject.toml. DO NOT edit or read-as-authoritative anything under tests/, contract/, fixtures/, CONTRACT.md, BRIEF.md, pyproject.toml, or build_loop.sh — they are the fixed contract. Keep code clean, typed, no runtime network calls in pure functions." \
    --no-plan --always-approve --no-subagents --disable-web-search \
    --max-turns 60 --reasoning-effort high \
    >/dev/null 2>&1 ) || echo "  (grok exited non-zero — evaluating anyway)"

  restore_contract

  qa_run; TOT=$(qa_total); now=$(qa_passing)
  if [ "$now" -gt "$best" ]; then
    git add -A && git commit -q -m "build(round $r): $best->$now/$TOT criteria [grok]"
    echo "  ✓ progress $best->$now/$TOT"; best=$now; stale=0
  elif [ "$now" -lt "$best" ]; then
    echo "  ✗ regression $best->$now → revert round"; git checkout -- . ; git clean -fdq -e .venv; stale=$((stale+1))
  else
    if [ -n "$(git status --porcelain)" ]; then git add -A && git commit -q -m "build(round $r): no-criteria-change churn [grok]"; fi
    echo "  · no new criterion green ($now/$TOT)"; stale=$((stale+1))
  fi

  [ "$best" -eq "$TOT" ] && { echo "── DONE: all $TOT criteria pass 🎉"; break; }
  [ "$stale" -ge "$PATIENCE" ] && { echo "── STOP: stale ($PATIENCE rounds no progress). Stuck at $best/$TOT."; break; }
done

echo "── final $best/$TOT. Remaining:"; qa_fails | sed 's/^/   /'
echo "── commits:"; git --no-pager log --oneline -"$((MAX_ROUNDS+2))" | sed 's/^/   /'
