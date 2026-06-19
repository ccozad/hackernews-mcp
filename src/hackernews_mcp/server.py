"""MCP server: registers the ``search_hackernews`` tool over a stdio transport.

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
from .models import LIMIT_MAX, LIMIT_MIN, SORTS, TAGS, TIME_RANGES, Hit

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


def build_server() -> Server:
    """Construct the MCP server with all tools registered."""
    server: Server = Server("hackernews-mcp")

    @server.list_tools()
    async def list_tools() -> list[types.Tool]:
        return [SEARCH_TOOL]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
        if name != "search_hackernews":
            raise HackerNewsError(f"unknown tool: {name}")
        # Typed errors propagate; the SDK maps them to an isError tool result
        # whose text is this exception's message (see errors.py).
        hits: list[Hit] = await search_hackernews(**arguments)
        return {"hits": [hit.model_dump() for hit in hits]}

    return server


async def run() -> None:
    """Run the stdio MCP server until the client disconnects."""
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main() -> None:
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
