"""Score call-to-action clarity on marketing landing pages."""

from __future__ import annotations

from bs4 import BeautifulSoup

_ACTION_KEYWORDS = (
    "buy",
    "sign up",
    "signup",
    "get started",
    "subscribe",
    "start",
    "try",
    "download",
    "claim",
    "book",
    "order",
    "join",
    "shop",
    "add to cart",
    "request",
    "register",
    "get the",
)


def _is_cta(element) -> bool:
    classes = " ".join(element.get("class", [])).lower()
    if "btn" in classes or "cta" in classes:
        return True

    if element.get("role", "").lower() == "button":
        return True

    text = element.get_text(strip=True).lower()
    return any(keyword in text for keyword in _ACTION_KEYWORDS)


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
        return body_html.find(text)
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