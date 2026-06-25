"""MCP server exposing the Marketing Page Quality Gate tools."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

from quality_gate.connectors import get_campaign_metrics as _get_campaign_metrics
from quality_gate.cta import cta_clarity as _cta_clarity
from quality_gate.gate import gate_spend as _gate_spend
from quality_gate.links import check_links as _check_links
from quality_gate.mobile import audit_mobile as _audit_mobile
from quality_gate.pixels import detect_pixels as _detect_pixels
from quality_gate.scoring import score_page as _score_page
from quality_gate.speed import audit_speed as _audit_speed

mcp = FastMCP("marketing-page-quality-gate")

_PAGE_TOOL_DOC = (
    "Pass a live `url` (fetched server-side) OR a raw `html` string. "
    "Returns a dict with signal scores and diagnostic details."
)


def _fetch_page(url: str) -> tuple[str, str]:
    with httpx.Client(follow_redirects=True, timeout=30.0) as client:
        response = client.get(url)
        response.raise_for_status()
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    return response.text, base_url


def _resolve_content(
    url: str | None,
    html: str | None,
) -> tuple[str, str | None]:
    if url:
        return _fetch_page(url)
    if html is None:
        raise ValueError("Either url or html must be provided")
    return html, None


@mcp.tool()
def score_page(
    url: str | None = None,
    html: str | None = None,
    verbose: bool = False,
) -> dict:
    """Score a landing page and return an A-F grade with per-signal breakdown.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns grade, overall score, signals, spend_at_risk, and optional details.
    """
    content, base_url = _resolve_content(url, html)
    return _score_page(content, base_url=base_url, verbose=verbose)


@mcp.tool()
def gate_spend(
    url: str | None = None,
    html: str | None = None,
    platform: str | None = None,
    platform_csv: str | None = None,
) -> dict:
    """Block ad spend on leaky landing pages.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns verdict, grade, monthly_spend, spend_at_risk, and risk factors.
    """
    content, base_url = _resolve_content(url, html)
    return _gate_spend(
        content,
        base_url=base_url,
        platform=platform,
        platform_csv=platform_csv,
    )


@mcp.tool()
def check_links(url: str | None = None, html: str | None = None) -> dict:
    """Check internal and outbound links for broken HTTP status codes.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns total, internal, outbound, ok, broken links, and has_broken flag.
    """
    content, base_url = _resolve_content(url, html)
    return _check_links(content, base_url=base_url)


@mcp.tool()
def detect_pixels(url: str | None = None, html: str | None = None) -> dict:
    """Detect Meta Pixel, GA4, GTM, and TikTok tracking pixels.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns per-pixel booleans, found list, and count.
    """
    content, _ = _resolve_content(url, html)
    return _detect_pixels(content)


@mcp.tool()
def audit_mobile(url: str | None = None, html: str | None = None) -> dict:
    """Audit viewport meta and horizontal-scroll risk on mobile.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns viewport flags, issues list, and mobile score.
    """
    content, _ = _resolve_content(url, html)
    return _audit_mobile(content)


@mcp.tool()
def audit_speed(url: str | None = None, html: str | None = None) -> dict:
    """Audit static load-speed signals from HTML.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns html_bytes, render-blocking scripts, missing img dimensions, and score.
    """
    content, _ = _resolve_content(url, html)
    return _audit_speed(content)


@mcp.tool()
def cta_clarity(url: str | None = None, html: str | None = None) -> dict:
    """Analyze CTA presence, count, and above-the-fold placement.

    Pass a live `url` (fetched server-side) OR a raw `html` string.
    Returns cta_count, primary_cta, above_the_fold flag, and score.
    """
    content, _ = _resolve_content(url, html)
    return _cta_clarity(content)


@mcp.tool()
def get_campaign_metrics(platform: str) -> dict:
    """Return mock ad-platform campaign metrics (plug real API keys to go live)."""
    return _get_campaign_metrics(platform)


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()