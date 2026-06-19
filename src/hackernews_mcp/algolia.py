"""Algolia HN Search API client and the ``search_hackernews`` core logic.

The HTTP-free request builders (``build_search_request``, the tag/time maps)
are pure functions so they can be unit-tested without a network, and
``search_hackernews`` is a plain async function so tests can call it directly
with a mocked transport.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .errors import InputValidationError, UpstreamError, UpstreamTimeoutError
from .models import (
    LIMIT_MAX,
    LIMIT_MIN,
    SORTS,
    TAGS,
    TIME_RANGES,
    Hit,
    Sort,
    Tag,
    TimeRange,
)

BASE_URL = "https://hn.algolia.com/api/v1"
USER_AGENT = "hackernews-mcp (+https://github.com/ccozad/hackernews-mcp)"
DEFAULT_TIMEOUT = 10.0

# tag -> Algolia ``tags`` filter value. "all" maps to None (omit the filter).
_TAG_FILTER: dict[Tag, str | None] = {
    "story": "story",
    "comment": "comment",
    "ask_hn": "ask_hn",
    "show_hn": "show_hn",
    "all": None,
}

# time range -> lookback window in seconds. "all_time" maps to None (no filter).
_TIME_WINDOW: dict[TimeRange, int | None] = {
    "past_24h": 24 * 60 * 60,
    "past_week": 7 * 24 * 60 * 60,
    "past_month": 30 * 24 * 60 * 60,
    "all_time": None,
}


def _validate(query: str, tag: Tag, time_range: TimeRange, sort: Sort, limit: int) -> None:
    """Raise :class:`InputValidationError` for any bad argument, before any I/O."""
    if not isinstance(query, str) or not query.strip():
        raise InputValidationError("query must be a non-empty string")
    if tag not in TAGS:
        raise InputValidationError(f"unknown tag {tag!r}; expected one of {', '.join(TAGS)}")
    if time_range not in TIME_RANGES:
        raise InputValidationError(
            f"unknown time_range {time_range!r}; expected one of {', '.join(TIME_RANGES)}"
        )
    if sort not in SORTS:
        raise InputValidationError(f"unknown sort {sort!r}; expected one of {', '.join(SORTS)}")
    if not isinstance(limit, int) or isinstance(limit, bool):
        raise InputValidationError("limit must be an integer")
    if not LIMIT_MIN <= limit <= LIMIT_MAX:
        raise InputValidationError(
            f"limit must be between {LIMIT_MIN} and {LIMIT_MAX}, got {limit}"
        )


def build_search_request(
    query: str,
    tag: Tag,
    time_range: TimeRange,
    sort: Sort,
    limit: int,
    *,
    now: float | None = None,
) -> tuple[str, dict[str, Any]]:
    """Map validated arguments to an Algolia ``(path, params)`` pair.

    ``now`` (a Unix timestamp) anchors the time-range filter; it is injectable
    so time-window tests are deterministic. ``sort`` selects the endpoint:
    relevance -> ``/search``, date -> ``/search_by_date``.
    """
    path = "/search" if sort == "relevance" else "/search_by_date"
    params: dict[str, Any] = {"query": query, "hitsPerPage": limit}

    tag_filter = _TAG_FILTER[tag]
    if tag_filter is not None:
        params["tags"] = tag_filter

    window = _TIME_WINDOW[time_range]
    if window is not None:
        anchor = int(now if now is not None else time.time())
        params["numericFilters"] = f"created_at_i>{anchor - window}"

    return path, params


def _extract_excerpt(raw: dict[str, Any]) -> str | None:
    """Pull the first highlighted snippet Algolia attached to a hit, if any."""
    highlights = raw.get("_highlightResult")
    if not isinstance(highlights, dict):
        return None
    for key in ("title", "story_text", "comment_text", "url", "author"):
        field = highlights.get(key)
        if isinstance(field, dict) and field.get("matchLevel", "none") != "none":
            value = field.get("value")
            if isinstance(value, str) and value:
                return value
    return None


def parse_hit(raw: dict[str, Any]) -> Hit:
    """Convert one raw Algolia hit object into a :class:`Hit`."""
    return Hit(
        id=str(raw.get("objectID", "")),
        title=raw.get("title"),
        url=raw.get("url"),
        points=raw.get("points"),
        author=raw.get("author"),
        num_comments=raw.get("num_comments"),
        created_at=raw.get("created_at"),
        excerpt=_extract_excerpt(raw),
    )


async def search_hackernews(
    query: str,
    tag: Tag = "story",
    time_range: TimeRange = "all_time",
    sort: Sort = "relevance",
    limit: int = 10,
    *,
    client: httpx.AsyncClient | None = None,
    now: float | None = None,
) -> list[Hit]:
    """Search Hacker News via Algolia and return a list of :class:`Hit`.

    Validates arguments first (raising :class:`InputValidationError` before any
    network call), then issues a single GET. Empty results return ``[]``; HTTP
    errors raise :class:`UpstreamError`; timeouts raise
    :class:`UpstreamTimeoutError`. Pass ``client`` to reuse a configured
    ``httpx.AsyncClient`` (tests inject a mocked transport this way).
    """
    _validate(query, tag, time_range, sort, limit)
    path, params = build_search_request(query, tag, time_range, sort, limit, now=now)

    owns_client = client is None
    if client is None:
        client = httpx.AsyncClient(
            timeout=DEFAULT_TIMEOUT,
            headers={"User-Agent": USER_AGENT},
        )
    try:
        response = await client.get(f"{BASE_URL}{path}", params=params)
    except httpx.TimeoutException as exc:
        raise UpstreamTimeoutError(DEFAULT_TIMEOUT) from exc
    finally:
        if owns_client:
            await client.aclose()

    if response.status_code >= 400:
        raise UpstreamError(response.status_code, response.text[:200] or None)

    try:
        payload = response.json()
    except ValueError as exc:
        raise UpstreamError(response.status_code, "response body was not valid JSON") from exc

    # Be defensive about the payload shape: a missing or wrongly-typed "hits"
    # field, or a stray non-object hit, is treated as "no usable results"
    # rather than crashing the tool call.
    raw_hits = payload.get("hits") if isinstance(payload, dict) else None
    if not isinstance(raw_hits, list):
        return []
    return [parse_hit(h) for h in raw_hits if isinstance(h, dict)]
