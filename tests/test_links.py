"""Contract: extract_links / check_links — classification + broken detection."""
from __future__ import annotations

from quality_gate.links import _default_fetcher, check_links, extract_links
from quality_gate.scoring import score_page


def _kinds(items):
    return [i["kind"] for i in items]


def test_extract_classifies_all_kinds(load, base_url):
    items = extract_links(load("links_mixed.html"), base_url)
    kinds = _kinds(items)
    assert kinds.count("internal") == 2   # /about + same-host absolute
    assert kinds.count("outbound") == 1   # external.example.org
    assert kinds.count("anchor") == 1     # #top
    assert kinds.count("mailto") == 1
    assert kinds.count("tel") == 1


def test_extract_resolves_relative_to_absolute(load, base_url):
    items = extract_links(load("links_mixed.html"), base_url)
    urls = [i["url"] for i in items]
    assert "https://site.example.com/about" in urls


def test_check_links_no_broken(load, base_url, fetcher):
    r = check_links(load("links_mixed.html"), base_url, fetcher=fetcher)
    # 3 http(s) links checked; anchor/mailto/tel are not fetched
    assert r["total"] == 3
    assert r["internal"] == 2
    assert r["outbound"] == 1
    assert r["has_broken"] is False
    assert r["broken"] == []


def test_check_links_finds_broken(load, base_url, fetcher):
    r = check_links(load("links_broken.html"), base_url, fetcher=fetcher)
    assert r["has_broken"] is True
    assert len(r["broken"]) == 2
    assert all(b["status"] == 404 for b in r["broken"])


def test_protocol_relative_classified_outbound(load, fetcher):
    # //cdn.example.com/widget.js is an external resource, not an internal page.
    items = extract_links(load("links_protocol_relative.html"), base_url=None)
    proto = next(i for i in items if i["href"].startswith("//"))
    assert proto["kind"] == "outbound"
    assert proto["url"].startswith("https://")


def test_protocol_relative_does_not_crash_score_page(load, fetcher):
    # base_url=None + a // href previously misclassified internal, then httpx.InvalidURL
    # (not an HTTPError subclass) crashed score_page. Must score cleanly now.
    r = score_page(load("links_protocol_relative.html"), base_url=None, fetcher=fetcher)
    assert "grade" in r


def test_default_fetcher_swallows_invalid_url():
    # InvalidURL must be caught (returns 0 = unreachable), never propagate.
    assert _default_fetcher("//cdn.example.com/no-scheme.js") == 0
