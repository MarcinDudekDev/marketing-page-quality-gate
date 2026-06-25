# It's Today Media — Build Challenge Entry

**Prize:** $5,000 + full-time Marketing Development Engineer role.
**Deadline:** July 4, 2026 11:59 PM ET (submit via private link below).
**Submit link (private, do NOT share):** https://www.itstoday.media/submit/<private-link-redacted>
**Status link:** https://www.itstoday.media/status/<private-link-redacted>
**Applicant:** Marcin Dudek · marcin.dudek.dev@gmail.com · github.com/MarcinDudekDev/codesieve

## What we pitched (committed in the registration)
> An MCP server giving the media-buying team one natural-language interface to Meta,
> Google, Taboola, TikTok ad data (spend / ROAS / creative perf), PLUS a **deterministic
> quality gate for AI-generated landing pages** — every page scored before launch on the
> signals that move conversion (load speed, mobile layout, CTA clarity, tracking-pixel
> presence, broken links). CodeSieve-for-marketing-pages: "AI velocity never ships a leaky funnel."

## Scope decision (orchestrator call — honest & demoable in 9 days)
- **HALF B = the real, working core: "Marketing Page Quality Gate" MCP server.** Fully
  deterministic, no external API keys needed. THIS is the demo. Build it well.
- **HALF A = ad-platform connector: MOCKED behind a clean "plug your keys here" interface.**
  Live Meta/Google/Taboola/TikTok APIs need credentials we don't have. Expose the MCP tools
  with realistic mock data + clear TODO for real keys. Do NOT fake it as if live.

## Deliverable shape
An **MCP server** (Python 3.14, uv) exposing tools like:
- `score_page(url | html)` → deterministic A–F grade + per-signal scores (CodeSieve-style)
- `check_links(url)` → broken/outbound/internal link report with status codes
- `detect_pixels(url)` → Meta Pixel / GA4 / GTM / TikTok pixel presence
- `audit_mobile(url)` → viewport meta, tap-target size, horizontal-scroll check
- `cta_clarity(url)` → primary CTA presence/count/above-the-fold/contrast
- `get_campaign_metrics(platform)` → **MOCKED** spend/ROAS/creative perf (clear stub)
Plus: README with the pitch, a 60–90s demo (asciinema or screen recording), clean typed code.

## HOW TO BUILD IT — use the proven Grok contract-loop (off Claude tokens)
Reference implementation: `~/Projects/shipswipe/server/build_backend_loop.sh` (PROVEN 2026-06-22).
Pattern:
1. **Claude (this session) authors the CONTRACT** — a deterministic `pytest` oracle that tests
   each scorer/tool against fixture HTML with known issues (a page with a broken link, a page
   missing viewport meta, a page with no CTA, a page with/without each pixel, etc.). The oracle
   prints JSON `{passed, total, results:[{id, passed, detail}]}`. **Grok never grades itself.**
2. **Grok builds against it in a loop.** Each round: run oracle → feed ONLY failing criteria to
   `grok -p` → it edits code → re-run oracle. Commit per net-new passing criterion; revert
   regressions; restore protected contract files if Grok touches them.
3. **Three brakes:** all criteria pass / MAX_ROUNDS / PATIENCE stale rounds. Guarantees halt.
4. **Grok flags (MANDATORY):** `--no-plan --always-approve --no-subagents --disable-web-search
   --max-turns 60 --reasoning-effort high`. `--no-subagents` is REQUIRED — it prevents the
   recursive fork-bomb that got grok-imagine disabled. One grok call per round, never recursive.

## Protected (Grok must NEVER edit — restored each round)
`tests/`, `contract/`, `CONTRACT.md`, `BRIEF.md`, the plan doc, pytest config.

## Definition of done
- Oracle 100% green (all quality-gate signals tested & passing).
- MCP server runs; tools callable; README + short demo recorded.
- Honest about mocked ad half. Then: review, then submit via the private link before July 4.
