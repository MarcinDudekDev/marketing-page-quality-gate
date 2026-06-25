"""Extract and validate hyperlinks in landing-page HTML."""

from __future__ import annotations

from collections.abc import Callable
from urllib.parse import urljoin, urlparse

import httpx
from bs4 import BeautifulSoup

Fetcher = Callable[[str], int]


def _base_host(base_url: str | None) -> str | None:
    if base_url is None:
        return None
    return urlparse(base_url).netloc.lower()


def _classify_href(href: str, base_url: str | None) -> tuple[str, str]:
    if href.startswith("#"):
        return href, "anchor"
    if href.startswith("mailto:"):
        return href, "mailto"
    if href.startswith("tel:"):
        return href, "tel"

    absolute = urljoin(base_url, href) if base_url else href
    host = urlparse(absolute).netloc.lower()
    base_host = _base_host(base_url)

    if base_url is None:
        kind = "outbound" if urlparse(absolute).scheme in {"http", "https"} and host else "internal"
        if not urlparse(href).scheme and not href.startswith("//"):
            kind = "internal"
        elif urlparse(href).scheme in {"http", "https"}:
            kind = "outbound"
        return absolute, kind

    if host and base_host and host == base_host:
        return absolute, "internal"
    if not urlparse(href).scheme and not href.startswith("//"):
        return absolute, "internal"
    return absolute, "outbound"


def extract_links(html: str, base_url: str | None = None) -> list[dict]:
    """Return every anchor href with resolved URL and classification kind."""
    soup = BeautifulSoup(html, "html.parser")
    links: list[dict] = []

    for tag in soup.find_all("a", href=True):
        href = tag["href"].strip()
        if not href:
            continue
        url, kind = _classify_href(href, base_url)
        links.append({"href": href, "url": url, "kind": kind})

    return links


def _default_fetcher(url: str) -> int:
    try:
        with httpx.Client(follow_redirects=True, timeout=10.0) as client:
            response = client.head(url)
            if response.status_code >= 400 or response.status_code < 100:
                response = client.get(url)
            return response.status_code
    except httpx.HTTPError:
        return 0


def check_links(
    html: str,
    base_url: str | None = None,
    fetcher: Fetcher | None = None,
) -> dict:
    """Fetch http(s) links and report broken ones (status >= 400 or unreachable)."""
    probe = fetcher or _default_fetcher
    extracted = extract_links(html, base_url)

    http_links = [link for link in extracted if link["kind"] in {"internal", "outbound"}]
    internal = sum(1 for link in http_links if link["kind"] == "internal")
    outbound = sum(1 for link in http_links if link["kind"] == "outbound")

    broken: list[dict] = []
    ok = 0
    for link in http_links:
        status = probe(link["url"])
        if status >= 400 or status == 0:
            broken.append({"url": link["url"], "status": status})
        else:
            ok += 1

    return {
        "total": len(http_links),
        "internal": internal,
        "outbound": outbound,
        "ok": ok,
        "broken": broken,
        "has_broken": bool(broken),
    }