"""MCP server exposing the Marketing Page Quality Gate tools."""

from __future__ import annotations

from urllib.parse import urlparse

import httpx
from mcp.server.fastmcp import FastMCP

from quality_gate.connectors import get_campaign_metrics as _get_campaign_metrics
from quality_gate.cta import cta_clarity as _cta_clarity
from quality_gate.links import check_links as _check_links
from quality_gate.mobile import audit_mobile as _audit_mobile
from quality_gate.pixels import detect_pixels as _detect_pixels
from quality_gate.scoring import score_page as _score_page

mcp = FastMCP("marketing-page-quality-gate")


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
def score_page(url: str | None = None, html: str | None = None) -> dict:
    """Score a landing page and return an A-F grade with per-signal breakdown."""
    content, base_url = _resolve_content(url, html)
    return _score_page(content, base_url=base_url)


@mcp.tool()
def check_links(url: str | None = None, html: str | None = None) -> dict:
    """Check internal and outbound links for broken HTTP status codes."""
    content, base_url = _resolve_content(url, html)
    return _check_links(content, base_url=base_url)


@mcp.tool()
def detect_pixels(url: str | None = None, html: str | None = None) -> dict:
    """Detect Meta Pixel, GA4, GTM, and TikTok tracking pixels."""
    content, _ = _resolve_content(url, html)
    return _detect_pixels(content)


@mcp.tool()
def audit_mobile(url: str | None = None, html: str | None = None) -> dict:
    """Audit viewport meta and horizontal-scroll risk on mobile."""
    content, _ = _resolve_content(url, html)
    return _audit_mobile(content)


@mcp.tool()
def cta_clarity(url: str | None = None, html: str | None = None) -> dict:
    """Analyze CTA presence, count, and above-the-fold placement."""
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