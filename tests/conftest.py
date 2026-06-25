"""Shared fixtures for the Marketing Page Quality Gate contract suite.

These tests are the FIXED CONTRACT. Grok builds the `quality_gate` package
until every test here passes. The oracle (contract/pytest_oracle.py) runs this
suite and reports each test as one acceptance criterion.
"""
from __future__ import annotations

import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parent.parent
FIXTURES = ROOT / "fixtures"

# Canonical base URL used to classify internal vs outbound links in fixtures.
BASE_URL = "https://site.example.com"


@pytest.fixture
def load():
    """Return a loader: load("perfect.html") -> str (fixture HTML)."""
    def _load(name: str) -> str:
        return (FIXTURES / name).read_text(encoding="utf-8")
    return _load


@pytest.fixture
def base_url() -> str:
    return BASE_URL


@pytest.fixture
def fetcher():
    """Deterministic fake HTTP status probe injected into link checks.

    Any URL containing the substring "broken" is a 404; everything else is 200.
    This keeps the contract fully offline — no real network calls in tests.
    """
    def _fetch(url: str) -> int:
        return 404 if "broken" in url else 200
    return _fetch
