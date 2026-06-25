"""Contract: cta_clarity(html) — primary CTA presence / count / above-the-fold."""
from __future__ import annotations

from quality_gate.cta import cta_clarity


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
