# Example transcripts

Saved transcripts of Claude using this MCP server, so you can see what the tools
do before wiring anything up.

> **These four files are templates.** Each one has the suggested prompt and the
> tool call Claude is expected to make pre-filled; the reasoning, tool response,
> and final answer are placeholders to paste a **real** Claude Desktop session
> into. See "How to capture" below.

| # | Transcript | Tools exercised |
|---|-----------|-----------------|
| 1 | [Tech trend research](01-tech-trend-research.md) | `search_hackernews` (time-ranged) |
| 2 | [Ask HN deep dive](02-ask-hn-deep-dive.md) | `search_hackernews` (`tag=ask_hn`) |
| 3 | [Comparative analysis](03-comparative-analysis.md) | `search_hackernews` ×2 |
| 4 | [Tool composition](04-tool-composition.md) | `search_hackernews` → `get_hackernews_thread` |

## How to capture

1. Wire up the server following [../docs/claude-desktop.md](../docs/claude-desktop.md).
2. Open the transcript file you want to fill and copy its **suggested prompt** into
   a new Claude Desktop chat.
3. Let Claude run the tool call(s). In Claude Desktop, click the tool-use
   indicator to expand the exact request payload and the (often large) response.
4. Paste into the template's sections:
   - **Claude's reasoning** — the lead-up text before/around the tool call.
   - **Tool call** — confirm or correct the pre-filled JSON arguments.
   - **Tool response (trimmed)** — paste the response, trimmed to a few
     representative hits/comments so the file stays readable.
   - **Claude's final answer** — the summary Claude produced.
5. Remove the "template" callout at the top once a file holds a real session.

Because LLM output is non-deterministic, your captured session won't match these
templates word-for-word — that's expected. The point is that the tool calls and
the shape of the result line up.
