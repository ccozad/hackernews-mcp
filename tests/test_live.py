"""Gated live smoke test against the real Algolia API.

Skipped by default so CI never depends on the network. Run it with:

    HACKERNEWS_MCP_LIVE_TEST=1 uv run pytest tests/test_live.py
"""

import os

import pytest

from hackernews_mcp.algolia import search_hackernews
from hackernews_mcp.models import Hit
from hackernews_mcp.thread import get_hackernews_thread

pytestmark = pytest.mark.skipif(
    os.environ.get("HACKERNEWS_MCP_LIVE_TEST") != "1",
    reason="set HACKERNEWS_MCP_LIVE_TEST=1 to run the live Algolia smoke test",
)


async def test_live_search_returns_conforming_hits() -> None:
    hits = await search_hackernews(query="python", limit=5)
    assert hits, "expected a non-empty result for a common query"
    for hit in hits:
        assert isinstance(hit, Hit)
        assert hit.id
        # round-trips through validation
        assert Hit.model_validate(hit.model_dump()) == hit


async def test_live_thread_is_bounded() -> None:
    # A large, stable thread ("Why asynchronous Rust doesn't work").
    thread = await get_hackernews_thread(item_id="26406989", max_comments=10)
    assert thread.root.id == "26406989"
    assert len(thread.comments) == 10
    assert thread.truncated is True
    assert all(c.depth <= 4 for c in thread.comments)
