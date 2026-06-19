"""HTTP-level behavior of ``search_hackernews``, with Algolia mocked.

Uses ``pytest-httpx`` to intercept the real ``httpx.AsyncClient`` the tool
builds internally, so the request URL, params, headers, and every error path
are exercised without touching the network.
"""

from typing import Any

import httpx
import pytest
from pytest_httpx import HTTPXMock

from hackernews_mcp.algolia import USER_AGENT, search_hackernews
from hackernews_mcp.errors import UpstreamError, UpstreamTimeoutError
from hackernews_mcp.models import Hit

NOW = 1_700_000_000


# --- happy path ---------------------------------------------------------------


async def test_returns_parsed_hits(httpx_mock: HTTPXMock, algolia_response: Any) -> None:
    httpx_mock.add_response(json=algolia_response)
    hits = await search_hackernews("async rust", limit=10)

    assert [h.id for h in hits] == ["26406989", "30000001", "30000123"]
    assert hits[0].points == 603
    assert hits[0].excerpt == "Why asynchronous <em>Rust</em> doesn't work"
    # the comment hit has no title/url/points
    assert hits[2].title is None and hits[2].url is None and hits[2].points is None


async def test_request_targets_search_endpoint_with_params(
    httpx_mock: HTTPXMock, algolia_response: Any
) -> None:
    httpx_mock.add_response(json=algolia_response)
    await search_hackernews("async rust", tag="story", limit=10)

    request = httpx_mock.get_requests()[0]
    assert request.url.path == "/api/v1/search"
    assert request.url.params["query"] == "async rust"
    assert request.url.params["hitsPerPage"] == "10"
    assert request.url.params["tags"] == "story"
    assert request.headers["user-agent"] == USER_AGENT


async def test_date_sort_targets_search_by_date(httpx_mock: HTTPXMock, algolia_empty: Any) -> None:
    httpx_mock.add_response(json=algolia_empty)
    await search_hackernews("x", sort="date")
    assert httpx_mock.get_requests()[0].url.path == "/api/v1/search_by_date"


async def test_time_range_numeric_filter_reaches_request(
    httpx_mock: HTTPXMock, algolia_empty: Any
) -> None:
    httpx_mock.add_response(json=algolia_empty)
    await search_hackernews("x", time_range="past_week", now=NOW)
    params = httpx_mock.get_requests()[0].url.params
    assert params["numericFilters"] == f"created_at_i>{NOW - 604_800}"


async def test_injected_client_is_used(httpx_mock: HTTPXMock, algolia_response: Any) -> None:
    httpx_mock.add_response(json=algolia_response)
    async with httpx.AsyncClient() as client:
        hits = await search_hackernews("async rust", client=client)
    assert len(hits) == 3


# --- error paths --------------------------------------------------------------


async def test_empty_results_return_empty_list(httpx_mock: HTTPXMock, algolia_empty: Any) -> None:
    httpx_mock.add_response(json=algolia_empty)
    assert await search_hackernews("nonexistent-term") == []


async def test_4xx_raises_upstream_error_with_status(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404, text="not found")
    with pytest.raises(UpstreamError) as excinfo:
        await search_hackernews("x")
    assert excinfo.value.status_code == 404
    assert "404" in str(excinfo.value)


async def test_5xx_raises_upstream_error_with_status(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=503, text="service unavailable")
    with pytest.raises(UpstreamError) as excinfo:
        await search_hackernews("x")
    assert excinfo.value.status_code == 503


async def test_error_fixture_preserves_status(httpx_mock: HTTPXMock, load: Any) -> None:
    httpx_mock.add_response(status_code=405, json=load("error_response"))
    with pytest.raises(UpstreamError) as excinfo:
        await search_hackernews("x")
    assert excinfo.value.status_code == 405


async def test_timeout_raises_timeout_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_exception(httpx.ReadTimeout("timed out"))
    with pytest.raises(UpstreamTimeoutError):
        await search_hackernews("x")


async def test_malformed_payload_returns_empty(
    httpx_mock: HTTPXMock, algolia_malformed: Any
) -> None:
    httpx_mock.add_response(json=algolia_malformed)
    assert await search_hackernews("x") == []


async def test_non_json_body_raises_upstream_error(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(
        status_code=200,
        content=b"<html>definitely not json</html>",
        headers={"content-type": "text/html"},
    )
    with pytest.raises(UpstreamError):
        await search_hackernews("x")


# --- schema conformance -------------------------------------------------------


async def test_every_hit_conforms_to_schema(httpx_mock: HTTPXMock, algolia_response: Any) -> None:
    httpx_mock.add_response(json=algolia_response)
    hits = await search_hackernews("async rust")
    for hit in hits:
        assert isinstance(hit, Hit)
        # round-trips through pydantic validation without loss
        assert Hit.model_validate(hit.model_dump()) == hit


async def test_optional_fields_default_to_none(
    httpx_mock: HTTPXMock, algolia_response: Any
) -> None:
    httpx_mock.add_response(json=algolia_response)
    hits = await search_hackernews("async rust")
    ask_hn = hits[1]  # url is null in the fixture
    assert ask_hn.url is None
    assert ask_hn.num_comments == 17
