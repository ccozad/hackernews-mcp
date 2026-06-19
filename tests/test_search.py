"""Lightweight M1 sanity checks.

The full mocked-Algolia suite (error paths, fixtures, coverage gate) lands in
M2; these just exercise the pure builders, input validation, and tool
registration so the contract isn't entirely unverified until then.
"""

import httpx
import mcp.types as types
import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from hackernews_mcp import server as server_module
from hackernews_mcp.algolia import build_search_request, parse_hit, search_hackernews
from hackernews_mcp.errors import InputValidationError, UpstreamError
from hackernews_mcp.models import Hit
from hackernews_mcp.server import SEARCH_TOOL, build_server

# Anchor for deterministic time-window assertions.
NOW = 1_700_000_000


def test_relevance_uses_search_endpoint() -> None:
    path, params = build_search_request("rust", "story", "all_time", "relevance", 10)
    assert path == "/search"
    assert params["query"] == "rust"
    assert params["hitsPerPage"] == 10
    assert params["tags"] == "story"
    assert "numericFilters" not in params


def test_date_sort_uses_search_by_date_endpoint() -> None:
    path, _ = build_search_request("rust", "story", "all_time", "date", 10)
    assert path == "/search_by_date"


def test_all_tag_omits_tags_filter() -> None:
    _, params = build_search_request("rust", "all", "all_time", "relevance", 5)
    assert "tags" not in params


@pytest.mark.parametrize(
    ("time_range", "window"),
    [("past_24h", 86_400), ("past_week", 604_800), ("past_month", 2_592_000)],
)
def test_time_range_builds_numeric_filter(time_range: str, window: int) -> None:
    _, params = build_search_request("x", "story", time_range, "relevance", 10, now=NOW)  # type: ignore[arg-type]
    assert params["numericFilters"] == f"created_at_i>{NOW - window}"


@pytest.mark.parametrize("limit", [0, 51, -1])
async def test_limit_out_of_range_rejected_before_io(limit: int) -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", limit=limit)


async def test_unknown_tag_rejected_before_io() -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", tag="bogus")  # type: ignore[arg-type]


async def test_empty_query_rejected() -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("   ")


def test_parse_hit_pulls_excerpt_from_highlight() -> None:
    hit = parse_hit(
        {
            "objectID": "42",
            "title": "Async Rust",
            "url": "https://example.com",
            "points": 100,
            "author": "alice",
            "num_comments": 7,
            "created_at": "2024-01-01T00:00:00Z",
            "_highlightResult": {"title": {"value": "Async <em>Rust</em>", "matchLevel": "full"}},
        }
    )
    assert hit == Hit(
        id="42",
        title="Async Rust",
        url="https://example.com",
        points=100,
        author="alice",
        num_comments=7,
        created_at="2024-01-01T00:00:00Z",
        excerpt="Async <em>Rust</em>",
    )


async def test_search_parses_hits_with_mocked_transport() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/v1/search"
        return httpx.Response(200, json={"hits": [{"objectID": "1", "title": "t"}]})

    transport = httpx.MockTransport(handler)
    async with httpx.AsyncClient(transport=transport) as client:
        hits = await search_hackernews("rust", limit=1, client=client)
    assert [h.id for h in hits] == ["1"]


async def test_upstream_error_carries_status() -> None:
    transport = httpx.MockTransport(lambda req: httpx.Response(503, text="down"))
    async with httpx.AsyncClient(transport=transport) as client:
        with pytest.raises(UpstreamError) as excinfo:
            await search_hackernews("rust", client=client)
    assert excinfo.value.status_code == 503


def test_server_registers_search_tool() -> None:
    server = build_server()
    assert server.name == "hackernews-mcp"
    assert SEARCH_TOOL.name == "search_hackernews"
    assert SEARCH_TOOL.inputSchema["required"] == ["query"]


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


async def test_call_tool_maps_invalid_input_to_error() -> None:
    async with create_connected_server_and_client_session(build_server()) as client:
        result = await client.call_tool("search_hackernews", {"query": "rust", "limit": 999})
    assert result.isError is True
    block = result.content[0]
    assert isinstance(block, types.TextContent)
    assert "50" in block.text
