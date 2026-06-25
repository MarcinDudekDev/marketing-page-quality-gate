"""Detect marketing/analytics tracking pixels in HTML."""

from __future__ import annotations

import re

_META_PATTERNS = (
    re.compile(r"fbq\s*\(", re.IGNORECASE),
    re.compile(r"connect\.facebook\.net", re.IGNORECASE),
    re.compile(r"fbevents\.js", re.IGNORECASE),
)
_GA4_GTAG_JS = re.compile(r"googletagmanager\.com/gtag/js", re.IGNORECASE)
_GA4_GTAG_CALL = re.compile(r"gtag\s*\(", re.IGNORECASE)
_GA4_MEASUREMENT_ID = re.compile(r"\bG-[A-Z0-9]{4,}\b")
_GTM_JS = re.compile(r"googletagmanager\.com/gtm\.js", re.IGNORECASE)
_GTM_ID = re.compile(r"\bGTM-[A-Z0-9]{5,}\b")
_TIKTOK_DOMAIN = re.compile(r"analytics\.tiktok\.com", re.IGNORECASE)
_TIKTOK_TTQ_LOAD = re.compile(r"ttq\.load", re.IGNORECASE)
_TIKTOK_TTQ_CALL = re.compile(r"ttq\s*\(", re.IGNORECASE)

_CANONICAL_ORDER = ("meta_pixel", "ga4", "gtm", "tiktok")


def detect_pixels(html: str) -> dict:
    """Detect Meta Pixel, GA4, GTM, and TikTok pixels in raw HTML."""
    meta_pixel = any(p.search(html) for p in _META_PATTERNS)
    ga4 = bool(
        _GA4_GTAG_JS.search(html)
        or (_GA4_GTAG_CALL.search(html) and _GA4_MEASUREMENT_ID.search(html))
    )
    gtm = bool(_GTM_JS.search(html) or _GTM_ID.search(html))
    tiktok = bool(
        _TIKTOK_DOMAIN.search(html)
        or _TIKTOK_TTQ_LOAD.search(html)
        or _TIKTOK_TTQ_CALL.search(html)
    )

    flags = {
        "meta_pixel": meta_pixel,
        "ga4": ga4,
        "gtm": gtm,
        "tiktok": tiktok,
    }
    found = [key for key in _CANONICAL_ORDER if flags[key]]

    return {
        **flags,
        "found": found,
        "count": len(found),
    }