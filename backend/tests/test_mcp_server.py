"""Smoke test — MCP server registers the expected tools."""
from __future__ import annotations

import pytest


@pytest.mark.asyncio
async def test_mcp_server_exposes_required_tools() -> None:
    from mcp_server.server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert {"query_data", "get_column_statistics", "generate_chart"} <= names


@pytest.mark.asyncio
async def test_mcp_server_includes_list_datasets_tool() -> None:
    from mcp_server.server import mcp

    tools = await mcp.list_tools()
    names = {t.name for t in tools}
    assert "list_datasets_tool" in names


@pytest.mark.asyncio
async def test_mcp_query_data_tool_has_correct_schema() -> None:
    from mcp_server.server import mcp

    tools = await mcp.list_tools()
    tool = next(t for t in tools if t.name == "query_data")
    required = tool.inputSchema.get("required", [])
    assert "dataset_id" in required
    assert "x" in required
