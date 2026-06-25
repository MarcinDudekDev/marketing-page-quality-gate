"""Contract: extract_links / check_links — classification + broken detection."""
from __future__ import annotations

from quality_gate.links import check_links, extract_links


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
