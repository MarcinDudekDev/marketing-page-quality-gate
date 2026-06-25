"""Contract: cta_clarity(html) — primary CTA presence / count / above-the-fold."""
from __future__ import annotations

from bs4 import BeautifulSoup

from quality_gate.cta import _element_offset, cta_clarity


def test_good_single_cta(load):
    r = cta_clarity(load("cta_good.html"))
    assert r["has_cta"] is True
    assert r["cta_count"] == 1
    assert r["primary_cta"] == "Get Started"
    assert r["above_the_fold"] is True
    assert r["score"] == 100


def test_footer_only_cta_below_fold(load):
    r = cta_clarity(load("cta_footer_only.html"))
    assert r["has_cta"] is True
    assert r["cta_count"] == 1
    assert r["above_the_fold"] is False
    assert r["score"] == 70


def test_no_cta(load):
    r = cta_clarity(load("cta_none.html"))
    assert r["has_cta"] is False
    assert r["cta_count"] == 0
    assert r["primary_cta"] is None
    assert r["score"] == 0


def test_too_many_ctas_penalised(load):
    r = cta_clarity(load("cta_too_many.html"))
    assert r["cta_count"] == 5
    assert r["above_the_fold"] is True
    # has_cta(+50) + above_fold(+30) but NO "reasonable count" bonus (>3 CTAs)
    assert r["score"] == 80


def test_word_boundary_keywords_dont_false_match(load):
    # nav links "Industry", "Workshop", "Facebook", "Reorder" must NOT count as CTAs;
    # only the real "Get Started" button does.
    r = cta_clarity(load("cta_word_boundary.html"))
    assert r["cta_count"] == 1
    assert r["primary_cta"] == "Get Started"


def test_element_offset_not_found_is_below_fold():
    # An element that can't be located in the body must return a below-fold sentinel
    # (len(body)), never -1 — else `-1 <= fold_line` falsely reads as "above fold".
    el = BeautifulSoup('<a class="btn">Ghost CTA</a>', "html.parser").a
    body = "<p>completely different body content with no such element</p>"
    assert _element_offset(el, body) == len(body)
