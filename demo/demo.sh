#!/usr/bin/env bash
# Narrated demo of the Marketing Page Quality Gate MCP server.
# Recorded with: asciinema rec --command "demo/demo.sh" demo/demo.cast
set -e
cd "$(dirname "$0")/.."
export PYTHONPATH="$PWD"

C='\033[36m'; B='\033[1m'; D='\033[2m'; G='\033[32m'; OFF='\033[0m'
say()  { printf "${C}# %b${OFF}\n" "$1"; sleep 2.4; }
run()  { printf "${B}\$ %s${OFF}\n" "$1"; sleep 0.9; eval "$2"; echo; sleep 2.2; }

clear
printf "${B}  Marketing Page Quality Gate — MCP server${OFF}\n"
printf "${D}  \"AI velocity never ships a leaky funnel.\"${OFF}\n\n"
sleep 2

say "Grade an AI-generated page BEFORE it launches. Same page -> same grade, always."
run "score: leaky_funnel.html"  "uv run --quiet python demo/show.py score leaky_funnel.html"
say "F. No viewport, no tracking pixels, no CTA, and three dead links. Don't spend on it."

run "score: perfect.html"  "uv run --quiet python demo/show.py score perfect.html"
say "${G}A.${OFF} Responsive, Meta+GA4 firing, one clear CTA above the fold, no broken links."

say "Each signal is its own tool. Why is the funnel leaking?"
run "detect_pixels: leaky_funnel.html"  "uv run --quiet python demo/show.py pixels leaky_funnel.html"
say "No retargeting, no analytics — you're flying blind."

run "cta_clarity: perfect.html"  "uv run --quiet python demo/show.py cta perfect.html"
say "One primary CTA, above the fold. Exactly what converts."

say "Half-A: ad-platform metrics. HONESTLY mocked — note the mock:true flag."
run "get_campaign_metrics: meta"  "uv run --quiet python demo/show.py metrics meta | head -16"

say "It's a real MCP server — six tools, callable by any agent in natural language:"
run "list tools"  "uv run --quiet python -c \"import asyncio; from quality_gate import server; print('  ' + '  '.join(sorted(t.name for t in asyncio.run(server.mcp.list_tools()))))\""

say "And the whole thing is gated by a deterministic oracle — 33/33 green."
run "uv run pytest -q"  "uv run --quiet pytest -q 2>/dev/null | tail -1"
printf "${B}  Built via the Grok contract-loop. Claude wrote the oracle; Grok built to pass it.${OFF}\n\n"
sleep 2
