#!/usr/bin/env python3
"""Acceptance oracle for the Marketing Page Quality Gate build loop.

Runs the pytest CONTRACT suite and emits the JSON shape the build loop expects:

    {"total": N, "passed": K, "results": [{"id", "passed", "detail"}, ...]}

Each test == one acceptance criterion. "Done" is the suite going green — never
Grok's own opinion. Collection/import errors are surfaced as failing criteria so
the loop always gets a gradeable signal (exit 0 always; --summary exits 1 on fail).

Usage:
    pytest_oracle.py <repo_dir>            # prints JSON
    pytest_oracle.py <repo_dir> --summary  # human lines, exit 1 if any fail
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


def run(repo_dir: Path) -> dict:
    report_path = Path(tempfile.mkstemp(suffix=".json", prefix="oracle-")[1])
    cmd = [
        "uv", "run", "pytest", "-q", "-p", "no:cacheprovider",
        "--json-report", f"--json-report-file={report_path}",
    ]
    proc = subprocess.run(cmd, cwd=repo_dir, capture_output=True, text=True)

    if not report_path.exists():
        return {
            "total": 1, "passed": 0,
            "results": [{
                "id": "pytest::session",
                "passed": False,
                "detail": "pytest produced no report (collection crashed). stderr tail: "
                          + (proc.stderr or proc.stdout or "")[-600:],
            }],
        }

    data = json.loads(report_path.read_text())
    report_path.unlink(missing_ok=True)

    results = []
    for t in data.get("tests", []):
        outcome = t.get("outcome")
        passed = outcome == "passed"
        detail = ""
        if not passed:
            for phase in ("call", "setup", "teardown"):
                info = t.get(phase) or {}
                if info.get("longrepr"):
                    detail = str(info["longrepr"]).strip().splitlines()[-1][:300]
                    break
            detail = detail or outcome or "failed"
        results.append({"id": t.get("nodeid", "?"), "passed": passed, "detail": detail})

    # surface collection errors (e.g. missing quality_gate module) as criteria too
    for c in data.get("collectors", []):
        if c.get("outcome") == "failed":
            results.append({
                "id": "collect::" + c.get("nodeid", "?"),
                "passed": False,
                "detail": str(c.get("longrepr", "collection error"))[:300],
            })

    if not results:
        results.append({
            "id": "pytest::session", "passed": False,
            "detail": "no tests collected: " + (proc.stdout or proc.stderr or "")[-400:],
        })

    passed = sum(1 for r in results if r["passed"])
    return {"total": len(results), "passed": passed, "results": results}


def main() -> int:
    if len(sys.argv) < 2:
        print("usage: pytest_oracle.py <repo_dir> [--summary]", file=sys.stderr)
        return 2
    repo_dir = Path(sys.argv[1]).resolve()
    summary = "--summary" in sys.argv[2:]
    out = run(repo_dir)
    if summary:
        for r in out["results"]:
            mark = "PASS" if r["passed"] else "FAIL"
            print(f"[{mark}] {r['id']}" + ("" if r["passed"] else f"  — {r['detail']}"))
        print(f"\n{out['passed']}/{out['total']} criteria pass")
        return 0 if out["passed"] == out["total"] else 1
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
