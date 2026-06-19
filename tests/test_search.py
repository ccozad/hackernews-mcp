"""Pure-unit tests: request builders, input validation, and hit parsing.

No network here — HTTP behavior lives in test_http.py, the MCP layer in
test_server.py, and the gated live check in test_live.py.
"""

import pytest

from hackernews_mcp.algolia import build_search_request, parse_hit, search_hackernews
from hackernews_mcp.errors import InputValidationError
from hackernews_mcp.models import TAGS, Hit

# Anchor for deterministic time-window assertions.
NOW = 1_700_000_000


# --- endpoint + param building ------------------------------------------------


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


@pytest.mark.parametrize(
    ("tag", "expected"),
    [
        ("story", "story"),
        ("comment", "comment"),
        ("ask_hn", "ask_hn"),
        ("show_hn", "show_hn"),
    ],
)
def test_each_tag_maps_to_filter(tag: str, expected: str) -> None:
    _, params = build_search_request("rust", tag, "all_time", "relevance", 10)  # type: ignore[arg-type]
    assert params["tags"] == expected


def test_all_tag_omits_tags_filter() -> None:
    _, params = build_search_request("rust", "all", "all_time", "relevance", 5)
    assert "tags" not in params


def test_limit_propagates_as_hits_per_page() -> None:
    _, params = build_search_request("rust", "story", "all_time", "relevance", 37)
    assert params["hitsPerPage"] == 37


@pytest.mark.parametrize(
    ("time_range", "window"),
    [
        ("past_24h", 86_400),
        ("past_week", 604_800),
        ("past_month", 2_592_000),
    ],
)
def test_time_range_builds_numeric_filter(time_range: str, window: int) -> None:
    _, params = build_search_request("x", "story", time_range, "relevance", 10, now=NOW)  # type: ignore[arg-type]
    assert params["numericFilters"] == f"created_at_i>{NOW - window}"


def test_all_time_omits_numeric_filter() -> None:
    _, params = build_search_request("x", "story", "all_time", "relevance", 10, now=NOW)
    assert "numericFilters" not in params


# --- input validation (pre-flight, no I/O) ------------------------------------


@pytest.mark.parametrize("limit", [0, 51, -1, 100])
async def test_limit_out_of_range_rejected_before_io(limit: int) -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", limit=limit)


async def test_unknown_tag_rejected_before_io() -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", tag="bogus")  # type: ignore[arg-type]


async def test_unknown_time_range_rejected() -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", time_range="yesterday")  # type: ignore[arg-type]


async def test_unknown_sort_rejected() -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", sort="popularity")  # type: ignore[arg-type]


@pytest.mark.parametrize("query", ["", "   ", "\n\t"])
async def test_blank_query_rejected(query: str) -> None:
    with pytest.raises(InputValidationError):
        await search_hackernews(query)


async def test_bool_limit_rejected() -> None:
    # bool is a subclass of int; make sure True/False can't sneak through.
    with pytest.raises(InputValidationError):
        await search_hackernews("rust", limit=True)  # type: ignore[arg-type]


# --- hit parsing --------------------------------------------------------------


def test_parse_hit_full_story() -> None:
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


def test_parse_hit_comment_has_no_title_or_url() -> None:
    hit = parse_hit(
        {
            "objectID": "99",
            "author": "bob",
            "created_at": "2024-02-02T00:00:00Z",
            "comment_text": "good point",
            "_highlightResult": {
                "comment_text": {"value": "good <em>point</em>", "matchLevel": "full"}
            },
        }
    )
    assert hit.id == "99"
    assert hit.title is None
    assert hit.url is None
    assert hit.points is None
    assert hit.excerpt == "good <em>point</em>"


def test_parse_hit_without_highlight_has_no_excerpt() -> None:
    hit = parse_hit({"objectID": "7", "title": "plain", "created_at": "2024-01-01T00:00:00Z"})
    assert hit.excerpt is None


def test_parse_hit_ignores_none_matchlevel_highlight() -> None:
    hit = parse_hit(
        {
            "objectID": "8",
            "title": "t",
            "_highlightResult": {"title": {"value": "t", "matchLevel": "none"}},
        }
    )
    assert hit.excerpt is None


def test_tags_vocabulary_is_complete() -> None:
    assert set(TAGS) == {"story", "comment", "ask_hn", "show_hn", "all"}
