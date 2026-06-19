"""MCP-layer tests: tool registration and the call_tool success/error contract."""

from typing import Any

import mcp.types as types
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from hackernews_mcp import server as server_module
from hackernews_mcp.errors import UpstreamError
from hackernews_mcp.models import Hit, Thread, ThreadComment, ThreadRoot
from hackernews_mcp.server import SEARCH_TOOL, THREAD_TOOL, build_server


def test_server_registers_search_tool() -> None:
    server = build_server()
    assert server.name == "hackernews-mcp"
    assert SEARCH_TOOL.name == "search_hackernews"
    assert SEARCH_TOOL.inputSchema["required"] == ["query"]
    # The docstring/description is rich enough for an LLM to call cold.
    assert SEARCH_TOOL.description is not None
    assert "search phrase" in SEARCH_TOOL.description.lower()


def test_server_registers_thread_tool() -> None:
    assert THREAD_TOOL.name == "get_hackernews_thread"
    assert THREAD_TOOL.inputSchema["required"] == ["item_id"]
    assert THREAD_TOOL.description is not None
    assert "item id" in THREAD_TOOL.description.lower()


async def test_list_tools_registers_both_tools() -> None:
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.list_tools()
    assert {t.name for t in result.tools} == {"search_hackernews", "get_hackernews_thread"}


async def test_call_thread_tool_returns_structured_thread(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def fake_thread(**kwargs: object) -> Thread:
        return Thread(
            root=ThreadRoot(id="1", title="t"),
            comments=[ThreadComment(id="2", parent_id="1", depth=0)],
            truncated=True,
        )

    monkeypatch.setattr(server_module, "get_hackernews_thread", fake_thread)
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.call_tool("get_hackernews_thread", {"item_id": "1"})

    assert result.isError is False
    assert result.structuredContent is not None
    assert result.structuredContent["truncated"] is True
    assert result.structuredContent["root"]["id"] == "1"
    assert result.structuredContent["comments"][0]["id"] == "2"


async def test_call_tool_returns_structured_hits(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(**kwargs: object) -> list[Hit]:
        return [Hit(id="1", title="t", created_at="2024-01-01T00:00:00Z")]

    monkeypatch.setattr(server_module, "search_hackernews", fake_search)
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.call_tool("search_hackernews", {"query": "rust", "limit": 1})

    assert result.isError is False
    assert result.structuredContent == {
        "hits": [Hit(id="1", title="t", created_at="2024-01-01T00:00:00Z").model_dump()]
    }


async def test_call_tool_empty_results(monkeypatch: pytest.MonkeyPatch) -> None:
    async def fake_search(**kwargs: object) -> list[Hit]:
        return []

    monkeypatch.setattr(server_module, "search_hackernews", fake_search)
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.call_tool("search_hackernews", {"query": "rust"})

    assert result.isError is False
    assert result.structuredContent == {"hits": []}


async def test_call_tool_maps_schema_violation_to_error() -> None:
    # limit out of the schema's bounds is caught at the MCP boundary.
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.call_tool("search_hackernews", {"query": "rust", "limit": 999})

    assert result.isError is True
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    assert "50" in block.text


async def test_call_tool_maps_upstream_error_to_error(monkeypatch: pytest.MonkeyPatch) -> None:
    async def boom(**kwargs: object) -> list[Hit]:
        raise UpstreamError(503, "down")

    monkeypatch.setattr(server_module, "search_hackernews", boom)
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.call_tool("search_hackernews", {"query": "rust"})

    assert result.isError is True
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    assert "503" in block.text


async def test_call_tool_unknown_tool_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    # Directly exercise the dispatch guard for an unregistered tool name.
    server = build_server()
    handler = server.request_handlers[types.CallToolRequest]
    request = types.CallToolRequest(
        method="tools/call",
        params=types.CallToolRequestParams(name="nope", arguments={}),
    )
    result = await handler(request)
    call_result: Any = result.root
    assert call_result.isError is True
