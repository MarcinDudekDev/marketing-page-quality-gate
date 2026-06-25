# Marketing Page Quality Gate — MCP Server

> **AI velocity never ships a leaky funnel.**

An **MCP server** that gives a media-buying team one natural-language interface to two things:

1. **A deterministic quality gate for AI-generated landing pages** — every page scored
   *before launch* on the signals that actually move conversion: load/mobile layout,
   CTA clarity, tracking-pixel presence, and broken links. CodeSieve-for-marketing-pages.
2. **Ad-platform campaign metrics** (Meta / Google / Taboola / TikTok) — spend / ROAS /
   creative performance, behind one clean tool. *(Half-A is honestly **mocked** — see below.)*

When a team ships AI-generated pages at velocity, the failure mode isn't ugly copy — it's a
**leaky funnel**: a missing Meta Pixel so you can't retarget, a CTA buried below the fold, a
1200px shell that horizontal-scrolls on every phone, a dead link in the hero. Those don't show
up in a glance. This server scores them deterministically — the **same page always gets the same
grade** — so a page can be *gated* in CI/agent workflows before a dollar of spend hits it.

---

## The tools

| Tool | What it returns |
|------|-----------------|
| `score_page(url \| html)` | Deterministic **A–F grade** + per-signal scores (pixels, mobile, cta, links) |
| `detect_pixels(url \| html)` | Meta Pixel / GA4 / GTM / TikTok presence |
| `audit_mobile(url \| html)` | Viewport meta, responsiveness, horizontal-scroll risk |
| `cta_clarity(url \| html)` | Primary CTA presence, count, above-the-fold placement |
| `check_links(url \| html)` | Broken / internal / outbound links with HTTP status codes |
| `get_campaign_metrics(platform)` | **MOCKED** spend / ROAS / creative perf (`"mock": true`) |

Every page tool accepts **either** a live `url` (fetched server-side) **or** raw `html`
(score AI output before it's even deployed).

### The grade

`score_page` weights the four conversion signals and maps to a letter:

```
overall = 0.20·pixels + 0.25·mobile + 0.25·cta + 0.30·links
A ≥ 90   B ≥ 80   C ≥ 70   D ≥ 60   else F
```

Broken links carry the heaviest weight — a dead link in a paid funnel is the most expensive
defect on the page. A flawless page scores **A/100**; a no-viewport, no-pixel, no-CTA page with
three dead links scores **F/8**.

---

## How it was built — the Grok contract-loop

This entry was built with a **deterministic contract loop** that keeps the AI honest:

1. **Claude authored the contract** — a `pytest` oracle (`contract/pytest_oracle.py`) that tests
   every scorer against **fixture HTML pages with known defects** (`fixtures/`: a page with a
   broken link, one missing the viewport, one with no CTA, one with each pixel, …). The oracle
   emits machine-readable JSON: `{passed, total, results}`.
2. **Grok built the implementation** against that contract in a loop (`build_loop.sh`): run oracle
   → feed only the *failing* criteria to Grok → it edits code under `quality_gate/` → re-run oracle
   → commit per net-new passing criterion. **Grok never grades itself** — the oracle does.
3. **Three brakes guarantee halt:** all criteria pass / MAX_ROUNDS / PATIENCE stale rounds.
4. The contract (`tests/`, `contract/`, `fixtures/`, `CONTRACT.md`) is **protected** — restored
   each round so the builder can't "pass" by weakening the test.

Before Grok ever ran, the contract was validated with a throwaway reference implementation to
prove it was satisfiable (and it caught a real spec bug). Result: **33/33 criteria green.**

---

## Run it

Requires **Python 3.14** and [`uv`](https://docs.astral.sh/uv/).

```bash
uv sync                       # install deps (mcp, beautifulsoup4, httpx)
uv run pytest -q              # 33/33 — the deterministic oracle
uv run python -m quality_gate.server   # start the MCP server (stdio)
```

### Register with an MCP client (e.g. Claude Desktop / Claude Code)

```json
{
  "mcpServers": {
    "marketing-page-quality-gate": {
      "command": "uv",
      "args": ["--directory", "/path/to/itstoday-entry", "run", "python", "-m", "quality_gate.server"]
    }
  }
}
```

Then ask, in natural language: *"Score this landing page before we launch it"* →
the agent calls `score_page` and gets a gradeable, deterministic verdict.

---

## What's real vs. mocked (honest scope)

- **Half-B — the Quality Gate — is the real, working core.** Fully deterministic, no external
  API keys, offline scoring. This is the demo.
- **Half-A — ad-platform connectors — is mocked behind a clean interface.** Live
  Meta/Google/Taboola/TikTok APIs need credentials. `get_campaign_metrics` returns realistic,
  deterministic mock data with an explicit `"mock": true` flag and a `note` pointing to exactly
  where real API keys plug in (`connectors.py`). **It does not pretend to be live.**

---

## Layout

```
contract/pytest_oracle.py   # the deterministic oracle (Claude-authored)
tests/                      # 26 acceptance tests = the contract
fixtures/                   # HTML pages with known defects
CONTRACT.md                 # exact spec Grok built against
build_loop.sh               # the Grok contract-loop
quality_gate/               # the implementation (Grok-built)
  pixels.py mobile.py cta.py links.py scoring.py connectors.py server.py
```

---

*Built for the It's Today Media build challenge · Marcin Dudek · marcin.dudek.dev@gmail.com*
