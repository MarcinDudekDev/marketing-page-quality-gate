# CONTRACT — Marketing Page Quality Gate (MCP server) · v2

You (Grok) are building a **deterministic quality gate for AI-generated marketing
landing pages**, exposed as an **MCP server**. An automated pytest suite under `tests/`
grades you. Build code **only under `quality_gate/`** until every test passes. The pitch:
*"AI velocity never ships a leaky funnel."*

> **v2 note:** a 3-agent review (see `FIXES.md`) found correctness/honesty bugs and added
> strategic features. The contract below is the corrected, expanded target. Match the EXACT
> dict keys, scoring weights, penalties, and grade thresholds — the tests assert exact numbers.

## Hard rules
- **Python 3.14 + uv only.** Deps pre-installed (`mcp`, `beautifulsoup4`, `httpx`, `pytest`,
  `pytest-json-report`). Use `uv run`. **Do NOT run `uv add` or edit `pyproject.toml`.**
- **NEVER edit anything in:** `tests/`, `contract/`, `fixtures/`, `CONTRACT.md`, `BRIEF.md`,
  `FIXES.md`, `pyproject.toml`, `.python-version`, `build_loop.sh`. The contract is restored
  every round.
- **Pure scoring functions are offline.** Parse HTML with BeautifulSoup. Network (httpx) is
  allowed ONLY in the MCP server's url-fetch path and the *default* link fetcher.
- Clean, typed, small modules. No global state.

## Package layout (under `quality_gate/`)
```
quality_gate/__init__.py      # re-export the pure functions
quality_gate/pixels.py        # detect_pixels
quality_gate/mobile.py        # audit_mobile
quality_gate/cta.py           # cta_clarity  (+ _element_offset helper)
quality_gate/speed.py         # audit_speed          (NEW in v2)
quality_gate/links.py         # extract_links, check_links
quality_gate/connectors.py    # get_campaign_metrics, read_spend_csv, SUPPORTED_PLATFORMS
quality_gate/scoring.py       # score_page
quality_gate/gate.py          # gate_spend           (NEW in v2)
quality_gate/server.py        # FastMCP server: mcp + main(); 8 tools
```

---

## 1. `pixels.detect_pixels(html: str) -> dict`
Keys: `meta_pixel`, `ga4`, `gtm`, `tiktok` (bools), `found` (present keys in canonical
order `["meta_pixel","ga4","gtm","tiktok"]`), `count` (int).
- `meta_pixel`: `fbq(` OR `connect.facebook.net` OR `fbevents.js`
- `ga4`: `googletagmanager.com/gtag/js` OR (`gtag(` present AND a real measurement id present)
- `gtm`: `googletagmanager.com/gtm.js` OR a real GTM container id present
- `tiktok`: `analytics.tiktok.com` OR `ttq.load` OR `ttq(`

**v2 fix (item 2):** the GA4/GTM id checks must match the real id SHAPE, not the bare prefix.
A GA4 id is `G-` + **4+ uppercase alphanumerics** on a word boundary (regex `\bG-[A-Z0-9]{4,}\b`,
case-SENSITIVE). A GTM id is `GTM-` + **5+ uppercase alphanumerics** (`\bGTM-[A-Z0-9]{5,}\b`,
case-SENSITIVE). Bare `G-`/`GTM-` in prose ("G-Shock", "GTM-compatible") must NOT register.

## 2. `mobile.audit_mobile(html: str) -> dict`
Keys: `viewport` (bool), `viewport_content` (str|None), `responsive_viewport` (bool, content
has `width=device-width`), `horizontal_scroll_risk` (bool), `issues` (list[str]), `score` (int).
- `horizontal_scroll_risk`: True if any fixed width ≥ 600px is declared — `width:<N>px` in an
  inline style OR a `width="<N>"` attribute where N ≥ 600. **v2:** ignore any element that is an
  `<svg>` or lives inside one (SVG widths are not page layout). **v4 fix:** do NOT match
  `max-width:<N>px` — `max-width` is a responsive pattern (caps width, shrinks on mobile), the
  opposite of a scroll risk. Match the `width:` property only when it is NOT preceded by `max-`
  (e.g. regex `(?<!max-)width\s*:\s*(\d+)\s*px`). `min-width` and bare `width` still count.
- `score`: `+60` responsive / else `+20` viewport-only / else `+0`; plus `+40` if NOT scroll risk.

## 3. `cta.cta_clarity(html: str) -> dict`
A CTA is an `<a>`/`<button>` where ANY holds: `class` contains `btn`/`cta`; `role="button"`;
or its text matches an action keyword.
**v2 fix (item 1):** single-word keywords match on **word boundaries** (regex `\b…\b`,
case-insensitive) so `try`✗`industry`, `book`✗`facebook`, `order`✗`reorder`, `start`✗`restart`,
`shop`✗`workshop`. Single-word set: `buy, start, try, download, claim, book, order, join, shop,
register, subscribe, signup`. Multi-word phrases use plain substring: `sign up, get started,
add to cart, get the`.

Keys: `cta_count`, `primary_cta` (first CTA text | None), `has_cta`, `above_the_fold`, `score`.
- `above_the_fold`: first CTA's offset within `<body>` ≤ `0.5 * len(body_html)`. False if no CTA.
- **v2 fix (item 3):** the offset helper **`_element_offset(element, body_html) -> int`** must
  return `len(body_html)` (a below-fold sentinel) when the element can't be located — NEVER `-1`
  (since `-1 <= fold_line` would falsely read as above-the-fold). Keep this helper name.
- `score`: `+50` has_cta; `+30` above_the_fold; `+20` if `1 <= cta_count <= 3`.

## 4. `speed.audit_speed(html: str) -> dict`  (NEW — item 5)
Cheap static load-speed signal (no browser). Keys: `html_bytes` (int, `len(html.encode("utf-8"))`),
`render_blocking_scripts` (int), `imgs_missing_dimensions` (int), `issues` (list[str]), `score` (int).
- `render_blocking_scripts`: external `<script src>` **inside `<head>`** WITHOUT `async`/`defer`.
- `imgs_missing_dimensions`: `<img>` lacking width AND/OR height attribute (count if either missing).
- `score = max(0, 100 - size_penalty - blocking_penalty - img_penalty)` where:
  - `size_penalty`: `40` if html_bytes > 250·1024; `20` if > 100·1024; else `0`
  - `blocking_penalty`: `min(45, 15 * render_blocking_scripts)`
  - `img_penalty`: `min(30, 10 * imgs_missing_dimensions)`

## 5. `links` module
### `extract_links(html, base_url=None) -> list[dict]`
Each `{"href": raw, "url": absolute, "kind": kind}`. Kinds: `anchor` (`#…`), `mailto`, `tel`,
`internal`, `outbound`, `other`.
- **v2 fix (item 4):** a **protocol-relative** href (`//cdn.example.com/x`) is `outbound`, with
  `url` given an explicit `https:` scheme (`"https:" + href`) so it is probeable.
- Non-http(s) schemes (`javascript:`, `data:`, …) → kind `other` (never probed).
- Relative → `internal` (resolved via `urljoin`). Absolute same-host → `internal`, else `outbound`.

### `check_links(html, base_url=None, fetcher=None) -> dict`
Probe only `internal`+`outbound`. `fetcher(url) -> int` (0 = unreachable). Default fetcher uses
httpx; **v2 fix (item 4):** its except clause must catch `(httpx.HTTPError, httpx.InvalidURL)` —
`InvalidURL` is NOT an `HTTPError` subclass and would otherwise crash `score_page`. Keep the helper
name **`_default_fetcher`**. Broken = status ≥ 400 or == 0. Dedupe URLs before probing; cap probes
(≤100). Keys: `total`, `internal`, `outbound`, `ok`, `broken` (`[{url,status}]`), `has_broken`.

## 6. `connectors` module
- `SUPPORTED_PLATFORMS = ["meta", "google", "taboola", "tiktok"]`
- `get_campaign_metrics(platform) -> dict`: for a supported platform return deterministic mock
  data: `platform`, `mock: True`, `note` (mentions plugging real keys), `currency: "USD"`,
  `campaigns` (≥1, each `name/spend/impressions/clicks/conversions/roas`), `totals`.
  **v2 fix (item 6):** for an UNKNOWN platform, **return a structured `{"error": ..., "supported":
  [...]}` dict — do NOT raise.**
- `read_spend_csv(csv_text: str) -> dict`  (NEW — item 10): parse REAL spend from an Ads Manager
  CSV export. Find a spend column among (case-insensitive) `amount spent`, `amount spent (usd)`,
  `spend`, `cost`, `total spent`; sum it (strip `$ £ € ,`). Return `total_spend` (float, rounded 2),
  `rows` (int), `currency: "USD"`, `mock: False`, `source: "csv"`. Raise `ValueError` if no spend
  column exists.

## 7. `scoring.score_page(html, base_url=None, fetcher=None, verbose=True) -> dict`
Five sub-scores (0–100): `mobile`, `cta`, `speed`, `links = max(0, 100 - 25*broken_count)`
(100 if 0 links checked), and **`pixels = 100 if count >= 1 else 0`**.
**v3 pixels rule:** any single real pixel = full measurability → 100 (a properly-tracked
GA4-only page must NOT be capped at 50). 0 pixels = 0.
**Quality weights (item 5)** — sum 1.0: `links .25, mobile .20, cta .20, speed .20, pixels .15`.
`overall = round(Σ weight·signal)`. Grade: A≥90, B≥80, C≥70, D≥60, else F.

Returns: `grade`, `score`, `signals` (`{pixels,mobile,cta,speed,links}`), `spend_at_risk`
(see below), and — **only when `verbose=True`** (item 15) — `details` (the 5 sub-dicts incl. `speed`).

**`spend_at_risk` (item 9, v3 buyer-centric model):** `{"risk_pct": int, "factors": [str, ...]}`.
For each signal `shortfall = 1 - signal/100`; `risk_pct = round(Σ shortfall · risk_weight)`.
The $-at-risk lens differs from the quality lens: a MISSING PIXEL is the biggest dollar leak (no
measurement → the whole budget runs blind, unoptimizable), so pixels rank TOP here. Risk weights:
**`pixels 30, links 25, cta 20, mobile 15, speed 10`** (sum 100). `factors` lists a human message
for each signal scoring < 100. A perfect page → `risk_pct 0`, `factors []`.

## 8. `gate.gate_spend(html, base_url=None, platform=None, platform_csv=None, fetcher=None) -> dict`  (NEW — item 10)
The literal job: refuse to greenlight spend on a leaky page. Score the page (verbose=False).
Spend source: if `platform_csv` given → `read_spend_csv`; else mock via `get_campaign_metrics`.
Returns: `verdict` (`"PASS"` if grade in {A,B,C} else `"BLOCK"`), `grade`, `score`,
`monthly_spend` (float), `currency`, `risk_pct`, `spend_at_risk` (= `monthly_spend*risk_pct/100`,
rounded 2), `factors`, `spend_source` (`"csv"`|`"mock"`), `reason` (str).

## 9. `server` module — the MCP server
`FastMCP("marketing-page-quality-gate")` as module attr `mcp`; a `main()` running `mcp.run()`;
`if __name__ == "__main__": main()`. Register **8** tools: `score_page`, `gate_spend`,
`check_links`, `detect_pixels`, `audit_mobile`, `audit_speed`, `cta_clarity`,
`get_campaign_metrics`. Page tools take `url` (fetched server-side via httpx) OR `html`.
`score_page` exposes `verbose: bool = False`. **v2 (item 12):** every page tool's docstring must
say "pass a live `url` (fetched server-side) OR a raw `html` string" + one line on the return shape.
Importing `server` must have NO side effects; `await mcp.list_tools()` returns the 8 tools.

---

## Definition of done
`uv run pytest -q` fully green. That is the only finish line.
