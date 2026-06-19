# Hacker News MCP

An [MCP](https://modelcontextprotocol.io) server that lets Claude (or any MCP
client) search and read [Hacker News](https://news.ycombinator.com), backed by
HN's free [Algolia](https://hn.algolia.com/api) search API. Ask in plain
language; Claude calls the tools.

```text
You:    What's the discussion on Rust async runtimes been like this past month?
Claude: → search_hackernews(query="rust async runtime", time_range="past_month")
        Here are the threads HN has been talking about… [summary of real stories]

You:    Dive into the comments on the top one.
Claude: → get_hackernews_thread(item_id="…", max_comments=30)
        The top commenters are split on… [summary of the thread]
```

> See [`examples/`](examples/) for full transcripts, and
> [`docs/claude-desktop.md`](docs/claude-desktop.md) to wire it into Claude
> Desktop in about five minutes.

## What's in this repo

Two MCP tools:

- **`search_hackernews`** — search stories and comments by query, with filters
  for tag (`story` / `comment` / `ask_hn` / `show_hn` / `all`), time range, sort
  (relevance or date), and result limit.
- **`get_hackernews_thread`** — fetch a story's comment tree by id, flattened
  depth-first and bounded by `max_comments` / `max_depth` to keep the response
  within an honest token budget (with a `truncated` flag when it was trimmed).

**Tech stack:** Python 3.11+, the official [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk),
[`httpx`](https://www.python-httpx.org/), and — for development —
[`pytest`](https://docs.pytest.org/), [`ruff`](https://docs.astral.sh/ruff/),
and [`pyright`](https://microsoft.github.io/pyright/).

## Install

Uses [`uv`](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/ccozad/hackernews-mcp.git
cd hackernews-mcp
uv sync
```

Run the stdio server directly with `uv run hackernews-mcp` (it speaks the MCP
protocol on stdout, so you normally let a client launch it rather than running it
by hand).

## Use it with Claude Desktop

Add this to your `claude_desktop_config.json` (full guide, config-file locations,
and troubleshooting in [`docs/claude-desktop.md`](docs/claude-desktop.md)):

```json
{
  "mcpServers": {
    "hackernews": {
      "command": "uv",
      "args": ["--directory", "/absolute/path/to/hackernews-mcp", "run", "hackernews-mcp"]
    }
  }
}
```

Restart Claude Desktop, then ask it to *"search HN for Rust async"* and confirm a
tool call happens.

## How it works

Both tools are thin wrappers over HN's Algolia API. `search_hackernews` maps its
arguments to Algolia's `/search` (or `/search_by_date`) endpoint — tag filters,
a `numericFilters` time window, and `hitsPerPage`. `get_hackernews_thread` pulls
the full nested thread from `/items/{id}` and trims it client-side. Input is
validated before any network call; upstream errors, timeouts, and empty results
all have defined behavior. See the tool docstrings in
[`src/hackernews_mcp/`](src/hackernews_mcp/) for the full contract.

## Development

```bash
uv sync --extra dev      # install dev tools
uv run pytest            # run the test suite (network-mocked)
uv run ruff check .      # lint
uv run ruff format --check .
uv run pyright           # type-check
```

All four checks run in CI on every pull request across Python 3.11 and 3.12. The
suite mocks Algolia and never hits the network; a gated live smoke test runs only
when `HACKERNEWS_MCP_LIVE_TEST=1` is set.

## License

[MIT](LICENSE)
