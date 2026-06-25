#!/usr/bin/env bash
# Narrated demo of the Marketing Page Quality Gate MCP server.
# Recorded with: asciinema rec --command "demo/demo.sh" demo/demo.cast
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"

C='\033[36m'; B='\033[1m'; D='\033[2m'; G='\033[32m'; R='\033[31m'; OFF='\033[0m'
say()  { printf "${C}# %b${OFF}\n" "$1"; sleep 2.4; }
run()  { printf "${B}\$ %s${OFF}\n" "$1"; sleep 0.9; eval "$2"; echo; sleep 2.2; }

clear
printf "${B}  Marketing Page Quality Gate — MCP server${OFF}\n"
printf "${D}  Stop paying to send traffic to leaky pages.${OFF}\n\n"
sleep 2

say "We ship AI landing pages at velocity. Who checks them before we spend? Grade one, deterministically."
run "score: leaky_funnel.html"  "uv run --quiet python demo/show.py score leaky_funnel.html"
say "${R}F.${OFF} No viewport, no pixel, no CTA, dead links — and 84% of ad spend at risk."

run "score: perfect.html"  "uv run --quiet python demo/show.py score perfect.html"
say "${G}A.${OFF} Responsive, tracked, one clear CTA, fast, no broken links. Zero spend at risk."

say "The point isn't a grade — it's GATING spend. Feed a real Ads Manager CSV export:"
run "gate_spend: leaky_funnel.html + meta CSV"  "uv run --quiet python demo/show.py gate leaky_funnel.html"
say "BLOCKED — \$10k+ of real budget would have burned on a broken funnel. That's the job."

say "Each signal is its own tool. Why is the funnel leaking? Pixels = your biggest dollar leak:"
run "detect_pixels: leaky_funnel.html"  "uv run --quiet python demo/show.py pixels leaky_funnel.html"
say "No pixel = no measurement, no retargeting — the whole budget runs blind."

say "Half-A: ad metrics. HONESTLY mocked (mock:true); the CSV reader above is the REAL path."
run "get_campaign_metrics: meta"  "uv run --quiet python demo/show.py metrics meta | head -12"

say "It's a real MCP server — eight tools, callable by any agent in natural language:"
run "list tools"  "uv run --quiet python -c \"import asyncio; from quality_gate import server; print('  ' + '  '.join(sorted(t.name for t in asyncio.run(server.mcp.list_tools()))))\""

say "And all of it is gated by a deterministic oracle — 54/54 green."
run "uv run pytest -q"  "uv run --quiet pytest -q 2>/dev/null | tail -1"
printf "${B}  Built via the Grok contract-loop. Claude wrote the oracle; Grok built to pass it.${OFF}\n\n"
sleep 2
