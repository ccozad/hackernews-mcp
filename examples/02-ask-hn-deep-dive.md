# Ask HN deep dive

**Scenario:** find recent Ask HN posts on a theme and summarize the advice.
**Tools exercised:** `search_hackernews` with `tag="ask_hn"`.

> ⚠️ **Template.** The prompt and expected tool call are filled in; replace the
> _italic placeholders_ with a real Claude Desktop session. See
> [README.md](README.md#how-to-capture).

## Suggested prompt

> Find recent Ask HN posts about hiring senior engineers and summarize the top advice.

## Claude's reasoning

_Paste Claude's lead-up — e.g. that it will search the `ask_hn` tag, sorted by
recency._

## Tool call

```json
{
  "name": "search_hackernews",
  "arguments": {
    "query": "hiring senior engineers",
    "tag": "ask_hn",
    "time_range": "all_time",
    "sort": "date",
    "limit": 10
  }
}
```

## Tool response (trimmed)

```json
{
  "hits": [
    {
      "id": "...",
      "title": "Ask HN: ...",
      "url": null,
      "points": 0,
      "author": "...",
      "num_comments": 0,
      "created_at": "...",
      "excerpt": "..."
    }
  ]
}
```

_Trim to ~3 representative Ask HN hits (note `url` is typically null)._

## Claude's final answer

_Paste Claude's summary of the top advice across the posts._
