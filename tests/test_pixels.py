"""Contract: detect_pixels(html) — Meta Pixel / GA4 / GTM / TikTok presence."""
from __future__ import annotations

from quality_gate.pixels import detect_pixels


def test_all_four_pixels_detected(load):
    r = detect_pixels(load("pixels_all.html"))
    assert r["meta_pixel"] is True
    assert r["ga4"] is True
    assert r["gtm"] is True
    assert r["tiktok"] is True


def test_all_four_count_and_found(load):
    r = detect_pixels(load("pixels_all.html"))
    assert r["count"] == 4
    assert set(r["found"]) == {"meta_pixel", "ga4", "gtm", "tiktok"}


def test_no_pixels_all_false(load):
    r = detect_pixels(load("pixels_none.html"))
    assert r["meta_pixel"] is False
    assert r["ga4"] is False
    assert r["gtm"] is False
    assert r["tiktok"] is False


def test_no_pixels_count_zero(load):
    r = detect_pixels(load("pixels_none.html"))
    assert r["count"] == 0
    assert r["found"] == []
