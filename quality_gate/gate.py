"""Spend gate — refuse to greenlight spend on a leaky landing page."""

from __future__ import annotations

from collections.abc import Callable

from quality_gate.connectors import get_campaign_metrics, read_spend_csv
from quality_gate.scoring import score_page

Fetcher = Callable[[str], int]

_PASS_GRADES = frozenset({"A", "B", "C"})


def gate_spend(
    html: str,
    base_url: str | None = None,
    platform: str | None = None,
    platform_csv: str | None = None,
    fetcher: Fetcher | None = None,
) -> dict:
    """Score the page and block spend when the grade is below C."""
    result = score_page(html, base_url=base_url, fetcher=fetcher, verbose=False)

    if platform_csv is not None:
        spend_data = read_spend_csv(platform_csv)
        monthly_spend = spend_data["total_spend"]
        currency = spend_data["currency"]
        spend_source = "csv"
    else:
        metrics = get_campaign_metrics(platform or "meta")
        monthly_spend = round(metrics["totals"]["spend"], 2)
        currency = metrics["currency"]
        spend_source = "mock"

    risk_pct = result["spend_at_risk"]["risk_pct"]
    factors = result["spend_at_risk"]["factors"]
    spend_at_risk = round(monthly_spend * risk_pct / 100, 2)

    grade = result["grade"]
    verdict = "PASS" if grade in _PASS_GRADES else "BLOCK"

    if verdict == "PASS":
        reason = f"Page grade {grade} ({result['score']}) meets minimum C threshold."
    else:
        reason = f"Page grade {grade} ({result['score']}) below C — block spend."

    return {
        "verdict": verdict,
        "grade": grade,
        "score": result["score"],
        "monthly_spend": monthly_spend,
        "currency": currency,
        "risk_pct": risk_pct,
        "spend_at_risk": spend_at_risk,
        "factors": factors,
        "spend_source": spend_source,
        "reason": reason,
    }