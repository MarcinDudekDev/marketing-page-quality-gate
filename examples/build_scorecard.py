"""Build the live quality scorecard: report/scorecard.html.

Two honestly-labeled sections:
  * REAL — recognizable server-rendered DTC/campaign landing pages, graded AS-IS
    (the gate's actual audience input; pixels/CTAs are inline so static analysis is valid).
  * ILLUSTRATIVE — 2 hand-built demo pages to anchor a clean A and a textbook F.

Link-probing is skipped for the snapshot (hundreds of cross-site HEAD requests would be
slow + non-deterministic); link integrity is a separate tool (check_links). Run from repo
root:  PYTHONPATH=. uv run python examples/build_scorecard.py
"""
from __future__ import annotations

import html as _html
import json
from pathlib import Path

import httpx

from quality_gate.scoring import score_page

# Recognizable, server-rendered DTC/campaign pages — the tool's real audience input.
REAL = [
    ("Dr. Squatch", "https://drsquatch.com"),
    ("HelloFresh", "https://www.hellofresh.com"),
    ("Bombas", "https://bombas.com"),
    ("AG1", "https://drinkag1.com"),
    ("Magic Spoon", "https://magicspoon.com"),
    ("Ruggable", "https://ruggable.com"),
    ("Manscaped", "https://manscaped.com"),
]
ILLUSTRATIVE = [
    ("Reference build (illustrative)", "examples/illustrative_A_reference.html"),
    ("Textbook leaky funnel (illustrative)", "examples/illustrative_F_leaky.html"),
]
# Illustrative monthly ad spend used only to translate risk_pct into a concrete dollar figure.
ASSUMED_MONTHLY_SPEND = 50_000
UA = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"}
BADGE = {"A": "#16a34a", "B": "#4d9e2a", "C": "#ca8a04", "D": "#ea580c", "F": "#dc2626"}


def _demo_fetcher(url: str) -> int:
    return 404 if "broken" in url else 200


def grade_real(name: str, url: str) -> dict:
    try:
        with httpx.Client(follow_redirects=True, timeout=15.0, headers=UA) as c:
            html = c.get(url).text
        base = "/".join(url.split("/")[:3])
        r = score_page(html, base_url=base, verbose=True, fetcher=lambda _u: 200)
        return {**r, "name": name, "url": url, "ok": True}
    except Exception as exc:  # noqa: BLE001
        return {"name": name, "url": url, "ok": False, "error": str(exc)[:100]}


def grade_local(name: str, path: str) -> dict:
    html = Path(path).read_text(encoding="utf-8")
    r = score_page(html, base_url="https://demo.example.com", verbose=True, fetcher=_demo_fetcher)
    return {**r, "name": name, "url": path, "ok": True}


def card(r: dict) -> str:
    if not r["ok"]:
        return (f'<div class="card err"><div class="name">{_html.escape(r["name"])}</div>'
                f'<div class="e">could not fetch — {_html.escape(r["error"])}</div></div>')
    g, sig, risk = r["grade"], r["signals"], r["spend_at_risk"]
    bars = "".join(
        f'<div class="bar"><span>{k}</span><div class="track">'
        f'<i style="width:{v}%;background:{BADGE[g]}"></i></div><b>{v}</b></div>'
        for k, v in sig.items())
    dollars = round(ASSUMED_MONTHLY_SPEND * risk["risk_pct"] / 100)
    factors = "".join(f"<li>{_html.escape(f)}</li>" for f in risk["factors"]) or "<li>Clean funnel</li>"
    return f"""<div class="card">
      <div class="head"><span class="badge" style="background:{BADGE[g]}">{g}</span>
        <span class="name">{_html.escape(r['name'])}</span><span class="score">{r['score']}/100</span></div>
      <div class="bars">{bars}</div>
      <div class="risk"><b>{risk['risk_pct']}% of ad spend at risk</b>
        <span class="dol">≈ ${dollars:,}/mo at ${ASSUMED_MONTHLY_SPEND//1000}k spend</span>
        <ul>{factors}</ul></div></div>"""


def section(title: str, note: str, rows: list[dict]) -> str:
    return (f'<h2>{title}</h2><p class="note">{note}</p>'
            f'<div class="grid">{"".join(card(r) for r in rows)}</div>')


def main() -> int:
    real = [grade_real(n, u) for n, u in REAL]
    illus = [grade_local(n, p) for n, p in ILLUSTRATIVE]
    graded = [r for r in real if r["ok"]]
    avg = round(sum(r["score"] for r in graded) / len(graded)) if graded else 0
    leaky = sum(1 for r in graded if r["grade"] in {"D", "F"})

    out = Path("report"); out.mkdir(exist_ok=True)
    (out / "scorecard_data.json").write_text(
        json.dumps([{k: r.get(k) for k in ("name", "url", "grade", "score", "signals", "spend_at_risk", "ok")}
                    for r in real + illus], indent=2), encoding="utf-8")

    doc = f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width,initial-scale=1">
<title>Marketing Page Quality Gate — Live Scorecard</title><style>
body{{margin:0;background:#0b0e14;color:#e6e9ef;font-family:-apple-system,Segoe UI,Roboto,sans-serif;padding:32px;max-width:1180px;margin:auto}}
h1{{font-size:1.6rem;margin:0}} h2{{margin:1.8rem 0 .2rem;font-size:1.15rem}}
.lede{{color:#9aa4b2;margin:.4rem 0 0}} .note{{color:#6b7689;font-size:.85rem;margin:.2rem 0 1rem}}
.grid{{display:grid;gap:14px;grid-template-columns:repeat(auto-fill,minmax(360px,1fr))}}
.card{{background:#131824;border:1px solid #222a3a;border-radius:12px;padding:15px}} .card.err{{opacity:.55}}
.head{{display:flex;align-items:center;gap:10px}}
.badge{{font-weight:800;color:#fff;border-radius:8px;padding:3px 12px;font-size:1.1rem}}
.name{{flex:1;font-weight:600}} .score{{color:#9aa4b2;font-variant-numeric:tabular-nums}}
.bars{{margin:11px 0}} .bar{{display:flex;align-items:center;gap:8px;font-size:.78rem;margin:3px 0}}
.bar span{{width:50px;color:#9aa4b2}} .bar b{{width:26px;text-align:right}}
.track{{flex:1;background:#0b0e14;border-radius:5px;height:7px;overflow:hidden}} .track i{{display:block;height:100%}}
.risk{{border-top:1px solid #222a3a;padding-top:8px;font-size:.8rem}}
.risk b{{color:#f6c177}} .dol{{color:#9aa4b2;margin-left:6px}}
.risk ul{{margin:.35rem 0 0;padding-left:16px;color:#8893a6}} .e{{color:#9aa4b2;font-size:.85rem;margin-top:6px}}
</style></head><body>
<h1>Marketing Page Quality Gate — Live Scorecard</h1>
<p class="lede"><b>{len(graded)} real DTC landing pages graded as-is · avg {avg}/100 · {leaky} would be
BLOCKED before spend.</b> Not one scored an A — even big brands ship leaky funnels.
"AI velocity never ships a leaky funnel."</p>
{section("Real campaign pages (graded as-is)",
         "Recognizable server-rendered DTC/Shopify landing pages — the gate's actual input, with "
         "inline pixels &amp; CTAs static analysis reads accurately. Live grades, outcome not curated. "
         "Link-probing skipped for this snapshot (separate check_links tool).", real)}
{section("Illustrative reference pages",
         "Two hand-built demo pages to anchor a clean A (what good looks like) and a textbook F "
         "leaky funnel — clearly labelled so they're never confused with the real grades above.", illus)}
<p class="note">$ figures translate each page's risk_pct against an illustrative ${ASSUMED_MONTHLY_SPEND//1000}k/mo
budget. Static analysis of the pre-launch HTML you control — built for server-rendered campaign pages,
not JS-SPA homepages (whose pixels/CTAs are injected client-side).</p>
</body></html>"""
    (out / "scorecard.html").write_text(doc, encoding="utf-8")
    print(f"wrote report/scorecard.html — {len(graded)}/{len(real)} real graded, avg {avg}, {leaky} leaky")
    for r in real + illus:
        print(f"  {(r['grade']+' '+str(r['score'])) if r['ok'] else 'FAIL':8} {r['name']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
