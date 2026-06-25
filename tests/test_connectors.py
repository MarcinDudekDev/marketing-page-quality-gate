"""Contract: get_campaign_metrics(platform) — MOCKED ad-platform connector.

Half-A (Meta/Google/Taboola/TikTok ad data) is intentionally mocked behind a
clean interface. It must be HONEST about being mock data, deterministic, and
cover all four platforms.
"""
from __future__ import annotations

import pytest

from quality_gate.connectors import SUPPORTED_PLATFORMS, get_campaign_metrics


def test_supported_platforms():
    assert set(SUPPORTED_PLATFORMS) == {"meta", "google", "taboola", "tiktok"}


@pytest.mark.parametrize("platform", ["meta", "google", "taboola", "tiktok"])
def test_metrics_shape_and_mock_flag(platform):
    r = get_campaign_metrics(platform)
    assert r["platform"] == platform
    assert r["mock"] is True            # honest: never pretend it's live
    assert isinstance(r["campaigns"], list) and r["campaigns"]
    first = r["campaigns"][0]
    for key in ("name", "spend", "impressions", "clicks", "conversions", "roas"):
        assert key in first


def test_metrics_deterministic(platform="meta"):
    assert get_campaign_metrics(platform) == get_campaign_metrics(platform)


def test_unknown_platform_raises():
    with pytest.raises(ValueError):
        get_campaign_metrics("linkedin")
