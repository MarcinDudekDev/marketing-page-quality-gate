"""Composite landing-page quality gate scoring."""

from __future__ import annotations

from collections.abc import Callable

from quality_gate.cta import cta_clarity
from quality_gate.links import check_links
from quality_gate.mobile import audit_mobile
from quality_gate.pixels import detect_pixels

Fetcher = Callable[[str], int]

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


def score_page(
    html: str,
    base_url: str | None = None,
    fetcher: Fetcher | None = None,
) -> dict:
    """Compute weighted A-F grade from pixel, mobile, CTA, and link signals."""
    pixels_detail = detect_pixels(html)
    mobile_detail = audit_mobile(html)
    cta_detail = cta_clarity(html)
    links_detail = check_links(html, base_url=base_url, fetcher=fetcher)

    pixels_score = min(100, pixels_detail["count"] * 50)
    mobile_score = mobile_detail["score"]
    cta_score = cta_detail["score"]

    if links_detail["total"] == 0:
        links_score = 100
    else:
        links_score = max(0, 100 - 25 * len(links_detail["broken"]))

    overall = round(
        0.20 * pixels_score
        + 0.25 * mobile_score
        + 0.25 * cta_score
        + 0.30 * links_score
    )

    return {
        "grade": _grade(overall),
        "score": overall,
        "signals": {
            "pixels": pixels_score,
            "mobile": mobile_score,
            "cta": cta_score,
            "links": links_score,
        },
        "details": {
            "pixels": pixels_detail,
            "mobile": mobile_detail,
            "cta": cta_detail,
            "links": links_detail,
        },
    }