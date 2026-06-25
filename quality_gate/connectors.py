"""Mocked ad-platform campaign metrics connector (Half-A stub)."""

from __future__ import annotations

import csv
import io
import re

SUPPORTED_PLATFORMS = ["meta", "google", "taboola", "tiktok"]

_SPEND_COLUMNS = frozenset(
    {
        "amount spent",
        "amount spent (usd)",
        "spend",
        "cost",
        "total spent",
    }
)

_PLATFORM_CAMPAIGNS: dict[str, list[dict]] = {
    "meta": [
        {
            "name": "Meta Prospecting Q2",
            "spend": 12500.0,
            "impressions": 850000,
            "clicks": 12400,
            "conversions": 310,
            "roas": 2.8,
        },
        {
            "name": "Meta Retargeting",
            "spend": 4200.0,
            "impressions": 210000,
            "clicks": 5800,
            "conversions": 145,
            "roas": 3.4,
        },
    ],
    "google": [
        {
            "name": "Google Search Brand",
            "spend": 9800.0,
            "impressions": 420000,
            "clicks": 18200,
            "conversions": 520,
            "roas": 4.1,
        },
    ],
    "taboola": [
        {
            "name": "Taboola Native Discovery",
            "spend": 6500.0,
            "impressions": 1200000,
            "clicks": 9600,
            "conversions": 88,
            "roas": 1.6,
        },
    ],
    "tiktok": [
        {
            "name": "TikTok Spark Ads",
            "spend": 7300.0,
            "impressions": 950000,
            "clicks": 14100,
            "conversions": 205,
            "roas": 2.2,
        },
    ],
}


def _aggregate_totals(campaigns: list[dict]) -> dict:
    return {
        "spend": sum(c["spend"] for c in campaigns),
        "impressions": sum(c["impressions"] for c in campaigns),
        "clicks": sum(c["clicks"] for c in campaigns),
        "conversions": sum(c["conversions"] for c in campaigns),
    }


def get_campaign_metrics(platform: str) -> dict:
    """Return deterministic mock campaign metrics for a supported platform."""
    if platform not in SUPPORTED_PLATFORMS:
        return {
            "error": f"Unsupported platform: {platform}",
            "supported": list(SUPPORTED_PLATFORMS),
        }

    campaigns = _PLATFORM_CAMPAIGNS[platform]
    return {
        "platform": platform,
        "mock": True,
        "note": f"MOCK DATA — plug real {platform} API keys in connectors.py",
        "currency": "USD",
        "campaigns": campaigns,
        "totals": _aggregate_totals(campaigns),
    }


def _parse_spend_value(raw: str) -> float:
    cleaned = re.sub(r"[$£€,\s]", "", raw.strip())
    if not cleaned:
        return 0.0
    return float(cleaned)


def read_spend_csv(csv_text: str) -> dict:
    """Parse spend totals from an Ads Manager CSV export."""
    reader = csv.DictReader(io.StringIO(csv_text))
    if reader.fieldnames is None:
        raise ValueError("CSV has no header row")

    spend_col: str | None = None
    for name in reader.fieldnames:
        if name.strip().lower() in _SPEND_COLUMNS:
            spend_col = name
            break

    if spend_col is None:
        raise ValueError("No spend column found in CSV")

    total = 0.0
    rows = 0
    for row in reader:
        value = row.get(spend_col, "")
        if value and value.strip():
            total += _parse_spend_value(value)
            rows += 1

    return {
        "total_spend": round(total, 2),
        "rows": rows,
        "currency": "USD",
        "mock": False,
        "source": "csv",
    }