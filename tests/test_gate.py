"""Contract: gate_spend — refuse to greenlight ad spend on a sub-C page."""
from __future__ import annotations

from quality_gate.gate import gate_spend


def test_blocks_sub_c_page_with_real_csv_spend(load, base_url, fetcher):
    r = gate_spend(
        load("leaky_funnel.html"),
        base_url=base_url,
        platform_csv=load("meta_ads_export.csv"),
        fetcher=fetcher,
    )
    assert r["verdict"] == "BLOCK"
    assert r["grade"] == "F"
    assert r["monthly_spend"] == 12750.75
    assert r["spend_source"] == "csv"
    # F page puts a large share of real spend at risk
    assert r["spend_at_risk"] > 5000
    assert r["factors"]


def test_passes_grade_a_page(load, base_url, fetcher):
    r = gate_spend(
        load("perfect.html"),
        base_url=base_url,
        platform_csv=load("meta_ads_export.csv"),
        fetcher=fetcher,
    )
    assert r["verdict"] == "PASS"
    assert r["grade"] == "A"
    assert r["spend_at_risk"] == 0


def test_falls_back_to_mock_spend_without_csv(load, base_url, fetcher):
    r = gate_spend(load("leaky_funnel.html"), base_url=base_url, platform="meta", fetcher=fetcher)
    assert r["spend_source"] == "mock"
    assert r["verdict"] == "BLOCK"
    assert r["monthly_spend"] > 0
