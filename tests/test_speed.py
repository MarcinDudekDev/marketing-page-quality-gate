"""Contract: audit_speed(html) — static load-speed signal (the 'load speed' claim)."""
from __future__ import annotations

from quality_gate.speed import audit_speed


def test_lean_page_full_score(load):
    r = audit_speed(load("speed_lean.html"))
    assert r["render_blocking_scripts"] == 0
    assert r["imgs_missing_dimensions"] == 0
    assert r["score"] == 100


def test_heavy_page_counts_render_blocking(load):
    r = audit_speed(load("speed_heavy.html"))
    assert r["render_blocking_scripts"] == 3   # three sync <script src> in <head>
    assert r["imgs_missing_dimensions"] == 3   # three <img> with no width/height


def test_heavy_page_penalised(load):
    r = audit_speed(load("speed_heavy.html"))
    assert r["score"] < 100
    assert r["issues"]


def test_async_scripts_not_render_blocking(load):
    # speed_lean.html's only script is async — must not count as blocking
    assert audit_speed(load("speed_lean.html"))["render_blocking_scripts"] == 0


def test_reports_html_byte_weight(load):
    assert audit_speed(load("speed_heavy.html"))["html_bytes"] > 0
