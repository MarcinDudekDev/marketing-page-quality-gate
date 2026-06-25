# CONTRACT — Marketing Page Quality Gate (MCP server)

You (Grok) are building a **deterministic quality gate for AI-generated marketing
landing pages**, exposed as an **MCP server**. An automated pytest suite under
`tests/` grades you. Build code **only under `quality_gate/`** until every test
passes. The pitch: *"AI velocity never ships a leaky funnel."*

## Hard rules
- **Python 3.14 + uv only.** All deps are pre-installed (`mcp`, `beautifulsoup4`,
  `httpx`, `pytest`, `pytest-json-report`). Use `uv run`. **Do NOT run `uv add`
  or edit `pyproject.toml`** — deps are fixed.
- **NEVER edit, read-as-authoritative, or try to satisfy by editing anything in:**
  `tests/`, `contract/`, `fixtures/`, `CONTRACT.md`, `BRIEF.md`, `pyproject.toml`,
  `.python-version`, `build_loop.sh`. These are the fixed contract and are restored
  every round.
- **All scoring functions are pure and offline.** No network calls inside the pure
  functions. Parse HTML with BeautifulSoup (`bs4`). Network (httpx) is allowed ONLY
  inside the MCP server's url-fetch path and the *default* link fetcher — never in
  the pure functions the tests call.
- Keep code clean, typed (type hints), small modules. No global state.

## Package layout to build (under `quality_gate/`)
```
quality_gate/__init__.py      # re-export the pure functions
quality_gate/pixels.py        # detect_pixels
quality_gate/mobile.py        # audit_mobile
quality_gate/cta.py           # cta_clarity
quality_gate/links.py         # extract_links, check_links
quality_gate/scoring.py       # score_page
quality_gate/connectors.py    # get_campaign_metrics, SUPPORTED_PLATFORMS  (MOCKED)
quality_gate/server.py        # FastMCP server: mcp instance + main(); 6 tools
```

---

## 1. `pixels.detect_pixels(html: str) -> dict`
Detect marketing/analytics pixels by case-insensitive string/regex match.

Return dict with keys:
- `meta_pixel: bool` — True if any of: `fbq(`, `connect.facebook.net`, `fbevents.js`
- `ga4: bool` — True if `googletagmanager.com/gtag/js` OR (`gtag(` present AND `G-` present)
- `gtm: bool` — True if `googletagmanager.com/gtm.js` OR `GTM-`
- `tiktok: bool` — True if `analytics.tiktok.com` OR `ttq.load` OR `ttq(`
- `found: list[str]` — the present keys among `["meta_pixel","ga4","gtm","tiktok"]`,
  in that canonical order
- `count: int` — `len(found)`

## 2. `mobile.audit_mobile(html: str) -> dict`
Return dict with keys:
- `viewport: bool` — a `<meta name="viewport">` tag exists
- `viewport_content: str | None` — its `content` attribute (or None)
- `responsive_viewport: bool` — viewport content contains `width=device-width`
- `horizontal_scroll_risk: bool` — True if the HTML declares any fixed width ≥ 600px:
  match `width: <N>px` in inline styles OR a `width="<N>"` attribute where N ≥ 600.
  (A `width=device-width` viewport has no digits and must NOT trigger this.)
- `issues: list[str]` — short human strings for any problems found
- `score: int` (0–100):
  - `+60` if `responsive_viewport`, else `+20` if `viewport` (non-responsive), else `+0`
  - `+40` if NOT `horizontal_scroll_risk`, else `+0`

So: responsive + no-scroll-risk = **100**; missing viewport + scroll risk = **0**.

## 3. `cta.cta_clarity(html: str) -> dict`
A CTA is an `<a>` or `<button>` that is action-oriented. Treat an element as a CTA if
ANY holds:
- its `class` contains `btn` or `cta` (case-insensitive substring), OR
- it has `role="button"`, OR
- its stripped, lower-cased text contains any action keyword:
  `buy`, `sign up`, `signup`, `get started`, `subscribe`, `start`, `try`,
  `download`, `claim`, `book`, `order`, `join`, `shop`, `add to cart`,
  `request`, `register`, `get the`.

Return dict with keys:
- `cta_count: int` — number of CTA elements
- `primary_cta: str | None` — stripped text of the FIRST CTA in document order (or None)
- `has_cta: bool` — `cta_count > 0`
- `above_the_fold: bool` — the first CTA's character offset **within the `<body>`**
  is `<= 0.5 * len(body_html)` (first half of the body; measuring inside `<body>` so a
  heavy `<head>` of tracking scripts does not push a top-of-page CTA below the fold).
  False if no CTA. (If there is no `<body>` tag, measure against the whole document.)
- `score: int` (0–100):
  - `+50` if `has_cta`
  - `+30` if `above_the_fold`
  - `+20` if `1 <= cta_count <= 3` (reasonable focus); 0 bonus if `cta_count > 3`

Examples from fixtures: one top CTA = **100**; footer-only single CTA = **70**
(50 + 0 + 20); five top CTAs = **80** (50 + 30 + 0); no CTA = **0**.

## 4. `links` module
### `extract_links(html: str, base_url: str | None = None) -> list[dict]`
For every `<a href>`, return `{"href": raw, "url": absolute, "kind": kind}` where `kind`:
- `anchor` if href starts with `#`
- `mailto` if starts with `mailto:`
- `tel` if starts with `tel:`
- otherwise it is an http link: resolve to absolute against `base_url`
  (use `urllib.parse.urljoin`). `internal` if its host equals `base_url`'s host
  (or it was relative), else `outbound`. If `base_url` is None, relative links are
  `internal` and absolute ones `outbound`.

`url` is the absolute resolved URL for http links; for anchor/mailto/tel it is the raw href.

### `check_links(html, base_url=None, fetcher=None) -> dict`
Only http(s) links (`internal` + `outbound`) are fetched. `fetcher(url) -> int` returns
an HTTP status (0 = unreachable). If `fetcher` is None, default to a real httpx HEAD/GET
probe (network — used only in production, never in tests). A link is **broken** if its
status `>= 400` or `== 0`.

Return dict:
- `total: int` — number of http links checked
- `internal: int`, `outbound: int`
- `ok: int` — non-broken count
- `broken: list[dict]` — `[{"url": ..., "status": ...}, ...]`
- `has_broken: bool`

## 5. `scoring.score_page(html, base_url=None, fetcher=None) -> dict`
Composite gate. Compute the four sub-scores (0–100):
- `pixels = min(100, detect_pixels(html)["count"] * 50)`
- `mobile = audit_mobile(html)["score"]`
- `cta    = cta_clarity(html)["score"]`
- `links  = max(0, 100 - 25 * len(check_links(...)["broken"]))`; if 0 links checked → 100

Weighted overall = `round(0.20*pixels + 0.25*mobile + 0.25*cta + 0.30*links)`.

Grade: `A` ≥ 90, `B` ≥ 80, `C` ≥ 70, `D` ≥ 60, else `F`.

Return dict:
- `grade: str`
- `score: int` — the weighted overall
- `signals: dict` — `{"pixels": int, "mobile": int, "cta": int, "links": int}`
- `details: dict` — the full sub-dicts: `{"pixels": ..., "mobile": ..., "cta": ..., "links": ...}`

## 6. `connectors` module (HALF-A — MOCKED, but honest)
- `SUPPORTED_PLATFORMS = ["meta", "google", "taboola", "tiktok"]`
- `get_campaign_metrics(platform: str) -> dict`:
  - raise `ValueError` for any platform not in `SUPPORTED_PLATFORMS`
  - otherwise return a **deterministic** dict (no randomness — same input → same output):
    - `platform: str`
    - `mock: True` (never claim it's live)
    - `note: str` — e.g. `"MOCK DATA — plug real <platform> API keys in connectors.py"`
    - `currency: "USD"`
    - `campaigns: list[dict]` — at least one campaign, each with keys
      `name, spend, impressions, clicks, conversions, roas`
    - `totals: dict` — aggregate spend/impressions/clicks/conversions

## 7. `server` module — the MCP server
Build a `FastMCP` app exposing 6 tools. Required module attributes:
- `mcp` — the `FastMCP(...)` instance (give it a real name, e.g. `"marketing-page-quality-gate"`)
- `main()` — callable that runs the server (`mcp.run()`); also wire `if __name__ == "__main__": main()`

Register exactly these tool names (use `@mcp.tool()`):
- `score_page(url: str | None = None, html: str | None = None)` — if `url` given, fetch
  HTML with httpx and use its host as base_url; else score the `html` string. Return
  `scoring.score_page(...)`.
- `check_links(url: str | None = None, html: str | None = None)` → `links.check_links(...)`
- `detect_pixels(url: str | None = None, html: str | None = None)` → `pixels.detect_pixels(...)`
- `audit_mobile(url: str | None = None, html: str | None = None)` → `mobile.audit_mobile(...)`
- `cta_clarity(url: str | None = None, html: str | None = None)` → `cta.cta_clarity(...)`
- `get_campaign_metrics(platform: str)` → `connectors.get_campaign_metrics(platform)`

The tool wrappers may fetch URLs over the network; the underlying pure functions never do.
Make sure `from quality_gate import server` imports with NO side effects (do not start the
server at import time) and that `await mcp.list_tools()` returns the six tools.

---

## Definition of done
`uv run pytest -q` is fully green. That is the only finish line.
