# Using Hacker News MCP with Claude Desktop

Wire this server into [Claude Desktop](https://claude.ai/download) so you can ask
Claude to search and read Hacker News directly. Should take about five minutes.

## 1. Prerequisites

- **Claude Desktop** installed.
- **Python 3.11+** and **[`uv`](https://docs.astral.sh/uv/)** installed.
- This repo cloned locally, with dependencies synced:

  ```bash
  git clone https://github.com/ccozad/hackernews-mcp.git
  cd hackernews-mcp
  uv sync
  ```

  Note the absolute path to the repo — you'll need it below. Run `pwd` to print it.

## 2. Add the server to your config

Claude Desktop reads its MCP servers from `claude_desktop_config.json`. Find it here:

| OS      | Path |
|---------|------|
| macOS   | `~/Library/Application Support/Claude/claude_desktop_config.json` |
| Windows | `%APPDATA%\Claude\claude_desktop_config.json` |
| Linux   | `~/.config/Claude/claude_desktop_config.json` |

> Tip: in Claude Desktop you can open it via **Settings → Developer → Edit Config**.
> If the file doesn't exist yet, create it with the content below.

Add a `hackernews` entry under `mcpServers` (merge with any servers you already
have), replacing the path with your repo's absolute path:

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

`uv --directory <path> run hackernews-mcp` runs the server's console script inside
the project's environment, so you don't have to install anything globally.

## 3. Restart Claude Desktop

Fully **quit** Claude Desktop (not just close the window) and reopen it. On
launch it spawns the server. You should see a tools/hammer icon in the chat box;
clicking it lists `search_hackernews` and `get_hackernews_thread`.

## 4. Test it works

Start a new chat and ask:

> **search HN for Rust async**

Claude should call `search_hackernews` (you'll see a tool-use indicator) and
answer with real stories. Try a follow-up to exercise the second tool:

> **dive into the comments on the top result**

That should trigger `get_hackernews_thread`.

## Troubleshooting

- **"command not found" / server won't start.** Claude Desktop launches with a
  minimal `PATH`, so it may not find `uv`. Replace `"command": "uv"` with the
  absolute path from `which uv` (macOS/Linux) or `where uv` (Windows), e.g.
  `"command": "/Users/you/.local/bin/uv"`.
- **No tools appear.** Confirm the JSON is valid (no trailing commas) and that the
  `--directory` path is correct and absolute. Re-quit and reopen Claude Desktop.
- **Wrong Python.** The server needs Python 3.11+. `uv sync` provisions a matching
  interpreter; if you pinned an older one, remove `.venv` and re-run `uv sync`.
- **Checking logs.** The server logs to **stderr** (stdout is reserved for the MCP
  protocol). Claude Desktop captures MCP server logs under:
  - macOS: `~/Library/Logs/Claude/`
  - Windows: `%APPDATA%\Claude\logs\`

  Look for `starting hackernews-mcp stdio server` to confirm it launched.
