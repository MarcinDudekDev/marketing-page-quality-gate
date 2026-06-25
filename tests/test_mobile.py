"""Contract: audit_mobile(html) — viewport + horizontal-scroll risk + score."""
from __future__ import annotations

from quality_gate.mobile import audit_mobile


def test_good_viewport_present_and_responsive(load):
    r = audit_mobile(load("mobile_good.html"))
    assert r["viewport"] is True
    assert r["responsive_viewport"] is True
    assert r["horizontal_scroll_risk"] is False


def test_good_score_full(load):
    assert audit_mobile(load("mobile_good.html"))["score"] == 100


def test_bad_missing_viewport(load):
    r = audit_mobile(load("mobile_bad.html"))
    assert r["viewport"] is False
    assert r["responsive_viewport"] is False


def test_bad_horizontal_scroll_risk_from_fixed_width(load):
    r = audit_mobile(load("mobile_bad.html"))
    assert r["horizontal_scroll_risk"] is True


def test_bad_score_zero(load):
    assert audit_mobile(load("mobile_bad.html"))["score"] == 0


def test_max_width_is_not_scroll_risk(load):
    # `max-width:1200px` is responsive (caps width, shrinks on mobile). The literal
    # `width:1200px` substring inside it must NOT register as a fixed-width scroll risk.
    r = audit_mobile(load("mobile_maxwidth_ok.html"))
    assert r["horizontal_scroll_risk"] is False
    assert r["score"] == 100
