"""Cheap static load-speed signals from HTML (no browser)."""

from __future__ import annotations

from bs4 import BeautifulSoup


def audit_speed(html: str) -> dict:
    """Return HTML size, render-blocking scripts, missing img dimensions, and score."""
    soup = BeautifulSoup(html, "html.parser")
    html_bytes = len(html.encode("utf-8"))

    render_blocking_scripts = 0
    head = soup.find("head")
    if head is not None:
        for script in head.find_all("script", src=True):
            if not script.has_attr("async") and not script.has_attr("defer"):
                render_blocking_scripts += 1

    imgs_missing_dimensions = 0
    for img in soup.find_all("img"):
        if not img.has_attr("width") or not img.has_attr("height"):
            imgs_missing_dimensions += 1

    issues: list[str] = []
    if html_bytes > 250 * 1024:
        issues.append("HTML payload exceeds 250 KB")
    elif html_bytes > 100 * 1024:
        issues.append("HTML payload exceeds 100 KB")
    if render_blocking_scripts:
        issues.append(f"{render_blocking_scripts} render-blocking script(s) in <head>")
    if imgs_missing_dimensions:
        issues.append(f"{imgs_missing_dimensions} image(s) missing width/height")

    if html_bytes > 250 * 1024:
        size_penalty = 40
    elif html_bytes > 100 * 1024:
        size_penalty = 20
    else:
        size_penalty = 0

    blocking_penalty = min(45, 15 * render_blocking_scripts)
    img_penalty = min(30, 10 * imgs_missing_dimensions)
    score = max(0, 100 - size_penalty - blocking_penalty - img_penalty)

    return {
        "html_bytes": html_bytes,
        "render_blocking_scripts": render_blocking_scripts,
        "imgs_missing_dimensions": imgs_missing_dimensions,
        "issues": issues,
        "score": score,
    }