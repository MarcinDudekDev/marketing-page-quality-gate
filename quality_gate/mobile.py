"""Audit mobile-friendliness signals in landing-page HTML."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_WIDTH_STYLE_RE = re.compile(r"width\s*:\s*(\d+)\s*px", re.IGNORECASE)
_WIDTH_ATTR_RE = re.compile(r"^(\d+)$")


def _has_horizontal_scroll_risk(soup: BeautifulSoup) -> bool:
    for tag in soup.find_all(style=True):
        style = tag.get("style", "")
        for match in _WIDTH_STYLE_RE.finditer(style):
            if int(match.group(1)) >= 600:
                return True

    for tag in soup.find_all(width=True):
        width_value = str(tag.get("width", "")).strip()
        match = _WIDTH_ATTR_RE.match(width_value)
        if match and int(match.group(1)) >= 600:
            return True

    return False


def audit_mobile(html: str) -> dict:
    """Return viewport and horizontal-scroll-risk signals plus a 0-100 score."""
    soup = BeautifulSoup(html, "html.parser")
    viewport_tag = soup.find("meta", attrs={"name": re.compile(r"^viewport$", re.I)})

    viewport = viewport_tag is not None
    viewport_content = viewport_tag.get("content") if viewport_tag else None
    responsive_viewport = bool(
        viewport_content and "width=device-width" in viewport_content.lower()
    )
    horizontal_scroll_risk = _has_horizontal_scroll_risk(soup)

    issues: list[str] = []
    if not viewport:
        issues.append("Missing viewport meta tag")
    elif not responsive_viewport:
        issues.append("Viewport is not responsive (missing width=device-width)")
    if horizontal_scroll_risk:
        issues.append("Fixed width >= 600px may cause horizontal scroll on mobile")

    if responsive_viewport:
        score = 60
    elif viewport:
        score = 20
    else:
        score = 0

    if not horizontal_scroll_risk:
        score += 40

    return {
        "viewport": viewport,
        "viewport_content": viewport_content,
        "responsive_viewport": responsive_viewport,
        "horizontal_scroll_risk": horizontal_scroll_risk,
        "issues": issues,
        "score": score,
    }