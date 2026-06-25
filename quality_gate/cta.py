"""Score call-to-action clarity on marketing landing pages."""

from __future__ import annotations

import re

from bs4 import BeautifulSoup

_SINGLE_WORD_KEYWORDS = (
    "buy",
    "start",
    "try",
    "download",
    "claim",
    "book",
    "order",
    "join",
    "shop",
    "register",
    "subscribe",
    "signup",
)

_MULTI_WORD_KEYWORDS = (
    "sign up",
    "get started",
    "add to cart",
    "get the",
)

_SINGLE_WORD_PATTERNS = tuple(
    re.compile(rf"\b{re.escape(word)}\b", re.IGNORECASE)
    for word in _SINGLE_WORD_KEYWORDS
)


def _text_matches_keywords(text: str) -> bool:
    lower = text.lower()
    if any(phrase in lower for phrase in _MULTI_WORD_KEYWORDS):
        return True
    return any(pattern.search(text) for pattern in _SINGLE_WORD_PATTERNS)


def _is_cta(element) -> bool:
    classes = " ".join(element.get("class", [])).lower()
    if "btn" in classes or "cta" in classes:
        return True

    if element.get("role", "").lower() == "button":
        return True

    text = element.get_text(strip=True)
    return _text_matches_keywords(text)


def _body_html(soup: BeautifulSoup, html: str) -> str:
    body = soup.find("body")
    if body is None:
        return html
    return body.decode_contents()


def _element_offset(element, body_html: str) -> int:
    element_html = str(element)
    offset = body_html.find(element_html)
    if offset >= 0:
        return offset

    text = element.get_text(strip=True)
    if text:
        offset = body_html.find(text)
        if offset >= 0:
            return offset
    return len(body_html)


def cta_clarity(html: str) -> dict:
    """Detect CTAs, primary CTA text, above-the-fold placement, and score."""
    soup = BeautifulSoup(html, "html.parser")
    body_content = _body_html(soup, html)

    ctas = [el for el in soup.find_all(["a", "button"]) if _is_cta(el)]
    cta_count = len(ctas)

    if cta_count == 0:
        return {
            "cta_count": 0,
            "primary_cta": None,
            "has_cta": False,
            "above_the_fold": False,
            "score": 0,
        }

    first_cta = ctas[0]
    primary_cta = first_cta.get_text(strip=True)
    offset = _element_offset(first_cta, body_content)
    fold_line = 0.5 * len(body_content)
    above_the_fold = offset <= fold_line

    score = 50
    if above_the_fold:
        score += 30
    if 1 <= cta_count <= 3:
        score += 20

    return {
        "cta_count": cta_count,
        "primary_cta": primary_cta,
        "has_cta": True,
        "above_the_fold": above_the_fold,
        "score": score,
    }