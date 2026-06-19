# Comparative analysis

**Scenario:** compare two related stories by points and comment volume/sentiment.
**Tools exercised:** `search_hackernews` (one or more calls to locate each story).

> ⚠️ **Template.** The prompt and expected tool calls are filled in; replace the
> _italic placeholders_ with a real Claude Desktop session. See
> [README.md](README.md#how-to-capture).

## Suggested prompt

> Compare the HN reception of two recent stories about a tech topic of your choice
> (e.g. two competing frameworks) — which got more points and more discussion?

## Claude's reasoning

_Paste Claude's plan — e.g. that it will search for each story, then compare
`points` and `num_comments`._

## Tool call(s)

```json
{
  "name": "search_hackernews",
  "arguments": { "query": "<first story topic>", "sort": "relevance", "limit": 5 }
}
```

```json
{
  "name": "search_hackernews",
  "arguments": { "query": "<second story topic>", "sort": "relevance", "limit": 5 }
}
```

## Tool response (trimmed)

```json
{ "hits": [ { "id": "...", "title": "...", "points": 0, "num_comments": 0, "created_at": "..." } ] }
```

_Trim to the one hit per call that Claude actually compared._

## Claude's final answer

_Paste Claude's side-by-side comparison (points, comment counts, and any
sentiment read it offers — noting that sentiment is inferred, not provided by the
tool)._
