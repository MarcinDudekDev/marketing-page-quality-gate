"""Contract: score_page(html) — composite A–F grade + per-signal scores.

Weights: pixels .20, mobile .25, cta .25, links .30.
Sub-scores (0-100):
  pixels = min(100, pixel_count * 50)
  mobile = audit_mobile score
  cta    = cta_clarity score
  links  = max(0, 100 - 25 * broken_count)   (100 when no links checked)
Grade: A>=90, B>=80, C>=70, D>=60, else F.
"""
from __future__ import annotations

from quality_gate.scoring import score_page


def test_perfect_page_grade_a(load, base_url, fetcher):
    r = score_page(load("perfect.html"), base_url=base_url, fetcher=fetcher)
    assert r["grade"] == "A"
    assert r["score"] == 100
    assert r["signals"] == {"pixels": 100, "mobile": 100, "cta": 100, "links": 100}


def test_broken_links_drags_to_b(load, base_url, fetcher):
    r = score_page(load("broken_links.html"), base_url=base_url, fetcher=fetcher)
    assert r["signals"]["links"] == 50   # two broken links
    assert r["score"] == 85
    assert r["grade"] == "B"


def test_no_viewport_grade_d(load, base_url, fetcher):
    r = score_page(load("no_viewport.html"), base_url=base_url, fetcher=fetcher)
    assert r["signals"]["mobile"] == 0
    assert r["signals"]["pixels"] == 50   # meta pixel only
    assert r["grade"] == "D"


def test_no_cta_grade_c(load, base_url, fetcher):
    r = score_page(load("no_cta.html"), base_url=base_url, fetcher=fetcher)
    assert r["signals"]["cta"] == 0
    assert r["grade"] == "C"


def test_no_pixels_grade_b(load, base_url, fetcher):
    r = score_page(load("no_pixels.html"), base_url=base_url, fetcher=fetcher)
    assert r["signals"]["pixels"] == 0
    assert r["grade"] == "B"


def test_leaky_funnel_grade_f(load, base_url, fetcher):
    r = score_page(load("leaky_funnel.html"), base_url=base_url, fetcher=fetcher)
    assert r["signals"] == {"pixels": 0, "mobile": 0, "cta": 0, "links": 25}
    assert r["score"] < 60
    assert r["grade"] == "F"
