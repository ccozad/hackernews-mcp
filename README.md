# Hacker News MCP

An [MCP](https://modelcontextprotocol.io) server that lets an LLM search and
read [Hacker News](https://news.ycombinator.com), backed by HN's free
[Algolia](https://hn.algolia.com/api) search API. Point Claude (or any MCP
client) at it and ask things like "search HN for Rust async" or "summarize the
top comments on this thread."

> **Status:** both tools are live — `search_hackernews` (M1) and
> `get_hackernews_thread` (M3). Full docs and integration guide land in M4.

## Development

This project uses [`uv`](https://docs.astral.sh/uv/) for package management.

```bash
# Install dependencies (including dev tools) into a local .venv
uv sync --extra dev

# Run the test suite
uv run pytest

# Lint, format-check, and type-check
uv run ruff check .
uv run ruff format --check .
uv run pyright
```

All four checks (`ruff check`, `ruff format --check`, `pyright`, `pytest`) run
in CI on every pull request and push to `main`, and must pass to merge.

Requires Python 3.11+.

## License

[MIT](LICENSE)
