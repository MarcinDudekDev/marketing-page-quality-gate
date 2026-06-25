"""Contract: connectors — mocked metrics + REAL CSV spend reader.

Half-A is honest: get_campaign_metrics is MOCK (mock:true); read_spend_csv parses
real spend from an Ads Manager export (mock:false).
"""
from __future__ import annotations

import pytest

from quality_gate.connectors import (
    SUPPORTED_PLATFORMS,
    get_campaign_metrics,
    read_spend_csv,
)


def test_supported_platforms():
    assert set(SUPPORTED_PLATFORMS) == {"meta", "google", "taboola", "tiktok"}


@pytest.mark.parametrize("platform", ["meta", "google", "taboola", "tiktok"])
def test_metrics_shape_and_mock_flag(platform):
    r = get_campaign_metrics(platform)
    assert r["platform"] == platform
    assert r["mock"] is True
    assert isinstance(r["campaigns"], list) and r["campaigns"]
    first = r["campaigns"][0]
    for key in ("name", "spend", "impressions", "clicks", "conversions", "roas"):
        assert key in first


def test_metrics_deterministic(platform="meta"):
    assert get_campaign_metrics(platform) == get_campaign_metrics(platform)


def test_unknown_platform_returns_structured_error():
    r = get_campaign_metrics("linkedin")
    assert "error" in r
    assert set(r["supported"]) == {"meta", "google", "taboola", "tiktok"}


def test_read_spend_csv_sums_real_spend(load):
    r = read_spend_csv(load("meta_ads_export.csv"))
    assert r["mock"] is False
    assert r["source"] == "csv"
    assert r["rows"] == 3
    assert r["total_spend"] == 12750.75   # 8200.50 + 3450.00 + 1100.25


def test_read_spend_csv_rejects_columnless():
    with pytest.raises(ValueError):
        read_spend_csv("Foo,Bar\n1,2\n")
