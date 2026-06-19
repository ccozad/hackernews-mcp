"""MCP server: registers the Hacker News tools over a stdio transport.

Logs go to stderr only — stdout is reserved for the MCP JSON-RPC protocol.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import mcp.types as types
from mcp.server import Server
from mcp.server.stdio import stdio_server

from .algolia import search_hackernews
from .errors import HackerNewsError
from .models import (
    LIMIT_MAX,
    LIMIT_MIN,
    MAX_COMMENTS_LIMIT,
    MAX_DEPTH_LIMIT,
    SORTS,
    TAGS,
    TIME_RANGES,
    Hit,
)
from .thread import get_hackernews_thread

logger = logging.getLogger("hackernews_mcp")

SEARCH_TOOL_DESCRIPTION = """\
Search Hacker News stories and comments via HN's Algolia API.

Use this to find HN discussion on a topic, surface Ask HN / Show HN posts, or
pull the most recent items in a time window. Returns a JSON object with a
`hits` array.

Parameters:
- query (str, required): the search phrase, e.g. "rust async runtime".
- tag (str): which item kind to search. One of "story" (default), "comment",
  "ask_hn", "show_hn", or "all".
- time_range (str): restrict by recency. One of "past_24h", "past_week",
  "past_month", or "all_time" (default).
- sort (str): "relevance" (default) ranks by Algolia relevance; "date" returns
  newest first.
- limit (int): number of hits to return, 1-50 (default 10).

Each hit has: id, title, url, points, author, num_comments, created_at
(ISO8601), and excerpt (a highlighted snippet when Algolia provides one). For
comment hits, title/url/points are usually null and the matched text appears in
excerpt. An empty search returns {"hits": []} rather than an error.
"""

SEARCH_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {"type": "string", "description": "The search phrase.", "minLength": 1},
        "tag": {
            "type": "string",
            "enum": list(TAGS),
            "default": "story",
            "description": "Which item kind to search.",
        },
        "time_range": {
            "type": "string",
            "enum": list(TIME_RANGES),
            "default": "all_time",
            "description": "Restrict results by recency.",
        },
        "sort": {
            "type": "string",
            "enum": list(SORTS),
            "default": "relevance",
            "description": "Ranking: relevance or newest-first.",
        },
        "limit": {
            "type": "integer",
            "minimum": LIMIT_MIN,
            "maximum": LIMIT_MAX,
            "default": 10,
            "description": "Number of hits to return (1-50).",
        },
    },
    "required": ["query"],
    "additionalProperties": False,
}

SEARCH_TOOL = types.Tool(
    name="search_hackernews",
    description=SEARCH_TOOL_DESCRIPTION,
    inputSchema=SEARCH_INPUT_SCHEMA,
)

THREAD_TOOL_DESCRIPTION = """\
Fetch a Hacker News thread (story + its comment tree) by item id.

Use this after search_hackernews surfaces an interesting item to read the
discussion. Returns a JSON object with `root`, `comments`, and `truncated`.

Parameters:
- item_id (str, required): the numeric HN story or comment id, e.g. "26406989".
- max_comments (int): cap on returned comments, 1-500 (default 50).
- max_depth (int): deepest reply level to include, 0-20 (default 4); top-level
  comments are depth 0.

`root` has: id, title, url, points, author, created_at, text. `comments` is a
flat list (flattened depth-first, preserving reply order) of objects with: id,
parent_id, author, text, depth, created_at. `truncated` is true when comments
were dropped for exceeding max_comments or max_depth — treat the thread as
incomplete when it is true.
"""

THREAD_INPUT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "item_id": {
            "type": "string",
            "pattern": "^[0-9]+$",
            "description": "Numeric HN story or comment id.",
        },
        "max_comments": {
            "type": "integer",
            "minimum": 1,
            "maximum": MAX_COMMENTS_LIMIT,
            "default": 50,
            "description": "Cap on returned comments (1-500).",
        },
        "max_depth": {
            "type": "integer",
            "minimum": 0,
            "maximum": MAX_DEPTH_LIMIT,
            "default": 4,
            "description": "Deepest reply level to include (0-20).",
        },
    },
    "required": ["item_id"],
    "additionalProperties": False,
}

THREAD_TOOL = types.Tool(
    name="get_hackernews_thread",
    description=THREAD_TOOL_DESCRIPTION,
    inputSchema=THREAD_INPUT_SCHEMA,
)


def build_server() -> Server:
    """Construct the MCP server with all tools registered."""
    server: Server = Server("hackernews-mcp")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [SEARCH_TOOL, THREAD_TOOL]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        # Typed errors propagate; the SDK maps them to an isError tool result
        # whose text is the exception's message (see errors.py).
        if name == "search_hackernews":
            hits: list[Hit] = await search_hackernews(**arguments)
            return {"hits": [hit.model_dump() for hit in hits]}
        if name == "get_hackernews_thread":
            thread = await get_hackernews_thread(**arguments)
            return thread.model_dump()
        raise HackerNewsError(f"unknown tool: {name}")

    return server


async def run() -> None:  # pragma: no cover - exercised only by a live stdio client
    """Run the stdio MCP server until the client disconnects."""
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:  # pragma: no cover - process entry point
    """Console-script entry point for ``hackernews-mcp``."""
    import anyio

    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stderr,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger.info("starting hackernews-mcp stdio server")
    anyio.run(run)


if __name__ == "__main__":
    main()
