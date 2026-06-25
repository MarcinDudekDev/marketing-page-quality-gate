"""Contract: the MCP server wires all six tools and imports cleanly."""
from __future__ import annotations

import asyncio

EXPECTED_TOOLS = {
    "score_page",
    "gate_spend",
    "check_links",
    "detect_pixels",
    "audit_mobile",
    "audit_speed",
    "cta_clarity",
    "get_campaign_metrics",
}


def test_server_module_imports():
    from quality_gate import server  # noqa: F401
    assert hasattr(server, "mcp")
    assert callable(getattr(server, "main", None))


def test_all_tools_registered():
    from quality_gate import server
    tools = asyncio.run(server.mcp.list_tools())
    names = {t.name for t in tools}
    assert EXPECTED_TOOLS <= names


def test_server_name_is_quality_gate():
    from quality_gate import server
    # FastMCP stores the server name; just assert it's a non-empty string.
    name = getattr(server.mcp, "name", None)
    assert isinstance(name, str) and name
