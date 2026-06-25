"""Composite landing-page quality gate scoring."""

from __future__ import annotations

from collections.abc import Callable

from quality_gate.cta import cta_clarity
from quality_gate.links import check_links
from quality_gate.mobile import audit_mobile
from quality_gate.pixels import detect_pixels
from quality_gate.speed import audit_speed

Fetcher = Callable[[str], int]

_WEIGHTS = {
    "links": 0.25,
    "mobile": 0.20,
    "cta": 0.20,
    "speed": 0.20,
    "pixels": 0.15,
}

_RISK_WEIGHTS = {
    "links": 30,
    "mobile": 25,
    "cta": 20,
    "pixels": 15,
    "speed": 10,
}

_FACTOR_MESSAGES = {
    "links": "Broken or unreachable links reduce conversion",
    "mobile": "Mobile layout issues hurt on-device conversion",
    "cta": "Weak or missing CTAs leave revenue on the table",
    "pixels": "Missing tracking pixels blind optimization",
    "speed": "Slow page load increases bounce before the CTA",
}

_GRADE_THRESHOLDS = (
    (90, "A"),
    (80, "B"),
    (70, "C"),
    (60, "D"),
)


def _grade(score: int) -> str:
    for threshold, letter in _GRADE_THRESHOLDS:
        if score >= threshold:
            return letter
    return "F"


def _compute_spend_at_risk(signals: dict[str, int]) -> dict:
    risk_pct = 0.0
    factors: list[str] = []

    for key, weight in _RISK_WEIGHTS.items():
        signal = signals[key]
        shortfall = 1 - signal / 100
        risk_pct += shortfall * weight
        if signal < 100:
            factors.append(_FACTOR_MESSAGES[key])

    return {
        "risk_pct": round(risk_pct),
        "factors": factors,
    }


def score_page(
    html: str,
    base_url: str | None = None,
    fetcher: Fetcher | None = None,
    verbose: bool = True,
) -> dict:
    """Compute weighted A-F grade from pixel, mobile, CTA, speed, and link signals."""
    pixels_detail = detect_pixels(html)
    mobile_detail = audit_mobile(html)
    cta_detail = cta_clarity(html)
    speed_detail = audit_speed(html)
    links_detail = check_links(html, base_url=base_url, fetcher=fetcher)

    pixels_score = min(100, pixels_detail["count"] * 50)
    mobile_score = mobile_detail["score"]
    cta_score = cta_detail["score"]
    speed_score = speed_detail["score"]

    if links_detail["total"] == 0:
        links_score = 100
    else:
        links_score = max(0, 100 - 25 * len(links_detail["broken"]))

    signals = {
        "pixels": pixels_score,
        "mobile": mobile_score,
        "cta": cta_score,
        "speed": speed_score,
        "links": links_score,
    }

    overall = round(sum(_WEIGHTS[key] * signals[key] for key in _WEIGHTS))

    result: dict = {
        "grade": _grade(overall),
        "score": overall,
        "signals": signals,
        "spend_at_risk": _compute_spend_at_risk(signals),
    }

    if verbose:
        result["details"] = {
            "pixels": pixels_detail,
            "mobile": mobile_detail,
            "cta": cta_detail,
            "speed": speed_detail,
            "links": links_detail,
        }

    return result