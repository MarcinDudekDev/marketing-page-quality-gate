# Fix & Improve Plan — from 3-agent review (2026-06-25)

Marcin approved ALL THREE TIERS. Workflow discipline: for every code bug, **first add a
failing contract test** (extend contract/ + tests/ + fixtures/), THEN let the Grok loop fix it,
so the oracle proves the fix. Don't hand-fix without a guarding test. Re-run build_loop.sh after
extending the contract. Keep Half-A honest. Report to main BEFORE submitting.

## TIER 1 — correctness + honesty (must-do, do FIRST)

1. **CTA keyword matching is substring, not word-boundary** (`quality_gate/cta.py`, _ACTION_KEYWORDS).
   `"try"`->"indus-try", `"book"`->"face-book", `"order"`->"b-order", `"start"`->"re-start",
   `"shop"`->"work-shop". Fix: word-boundary regex for single-word keywords
   (wrap each keyword in \b ... \b); keep `in` for multiword ("sign up","add to cart").
   ADD FIXTURE: a page whose nav links are "Industry", "Follow us on Facebook" + ONE real CTA -> cta_count must be 1.

2. **Pixel regex false positives** (`quality_gate/pixels.py`). The GA4 measurement-id pattern is just the
   two characters G-dash, and the GTM pattern is just GTM-dash, so they match any body text (product names
   like the G-series watch brand, code snippets, "GTM-compatible"). Anchor both to the real id SHAPE:
   the GA4 prefix followed by 4+ uppercase-alphanumeric chars on a word boundary, the GTM prefix followed
   by 5+; drop IGNORECASE since real ids are uppercase.
   ADD FIXTURE: a page with that product-name text and NO real pixel -> count 0.

3. **CTA above-the-fold `-1` bug** (`quality_gate/cta.py` _element_offset). The text-search fallback
   `return body_html.find(text)` can return -1, and `-1 <= fold_line` is always True -> false "above fold".
   Fix: guard, return `len(body_html)` sentinel on not-found. ADD TEST for the not-found path.

4. **Protocol-relative URL crash** (`quality_gate/links.py`). A `//cdn.example.com/x.js` href with
   base_url=None is misclassified "internal", probed, and throws `httpx.InvalidURL` — which is NOT a
   subclass of `httpx.HTTPError`, so it's uncaught -> crashes score_page. Fix: classify `//` hrefs as
   outbound; widen fetcher except to `(httpx.HTTPError, httpx.InvalidURL)`. ADD TEST with a `//` href.

5. **"load speed" honesty gap** (BRIEF/README claim it; tool measures none). DECISION: ADD a cheap,
   deterministic static perf signal to `audit_mobile` (or a new `audit_speed`) — HTML byte weight,
   render-blocking `<script>` count (sync scripts in <head>), and `<img>` missing width/height. Fold a
   small perf sub-score into the page grade (re-balance weights, keep sum=1.0). This makes the pitch's
   own words TRUE without a headless browser. ADD FIXTURES + tests for heavy/blocking vs lean pages.

6. **`get_campaign_metrics` raises raw ValueError** on unknown platform (`connectors.py`/`server.py`).
   Return a structured `{"error":..., "supported":[...]}` dict instead. ADD TEST.

7. **README test-count inconsistency** — says "26" in Layout block, "33" elsewhere. Make consistent
   with actual collected count.

(Also worth fixing, lower sev, from review: dedupe + cap links before probing & reuse one httpx.Client
in check_links to avoid 200-sequential-request hangs; skip <svg>/children in mobile width heuristic to
cut horizontal-scroll false positives; reconsider pixels_score so GA4-only = 100 not 50.)

## TIER 2 — strategic uplift (what makes it WIN; audience = a MEDIA BUYER, not an engineer)

8. **Grade 8–10 REAL landing pages -> one visual HTML scorecard** (use the /report skill). Recognizable
   live URLs, A–F badges, leaky-funnel failures highlighted. Save images as WebP next to the report
   (NO base64). This is the single biggest "wow" — turns toy fixtures into "I want this Monday."

9. **$ / "spend at risk" framing.** Add a field/section translating each failure into a money
   consequence (e.g. "no Meta Pixel -> retargeting audience never built -> ~$Y wasted"). Reframe the whole
   tool from QA-utility to profit-protection. Update README headline to lead with money, not determinism.

10. **Turn the mocked connector into a CSV-export reader** — accept a real Ads Manager CSV export
    (universal Meta/Google/Taboola format), keep live-API as documented TODO. ADD a `gate_spend(page_url
    or html, platform_csv)` tool that refuses to greenlight spend on a sub-C page. Keep `mock:true` only
    for the no-CSV demo path. This converts a liability into the literal job ("gate spend on bad pages").

11. **90-second narrated (Loom-style) walkthrough** over the asciinema: open on the problem ("we ship 50
    AI pages/week — who checks them?"), show a real F page, end on the gate blocking spend. Keep the
    asciinema as backup. If headless-only, script + record what you can and flag for Marcin to voice.

## TIER 3 — MCP polish

12. **Thicken tool docstrings** (`quality_gate/server.py`) — every page tool must state "pass a live `url`
    (fetched server-side) OR a raw `html` string" + one line on return shape. The LLM picks tools by these.
13. **Console entry point** in pyproject: `[project.scripts] quality-gate = "quality_gate.server:main"`.
14. **README**: add a sample score_page JSON output, a pointer to `demo/show.py` (the no-MCP demo,
    currently unmentioned), and a `claude mcp add ...` one-liner + Claude Desktop config path.
15. (nice-to-have) `score_page(verbose=False)` to drop the big nested `details` by default (token bloat).

## Done = all new+existing contract tests green, README/demo updated, MCP server verified running,
## real-page scorecard produced. Then REPORT to main with artifacts. Do NOT submit until Marcin signs off.
