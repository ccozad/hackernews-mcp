# Tool composition

**Scenario:** search surfaces an interesting story, then dive into its comments.
**Tools exercised:** `search_hackernews` → `get_hackernews_thread`.

> ⚠️ **Template.** The prompt and expected tool calls are filled in; replace the
> _italic placeholders_ with a real Claude Desktop session. See
> [README.md](README.md#how-to-capture). This is the flagship demo — it shows the
> two tools composing.

## Suggested prompt

> Find a highly-discussed recent HN story about Rust and summarize what the top
> commenters are arguing about.

## Step 1 — search

### Tool call

```json
{
  "name": "search_hackernews",
  "arguments": {
    "query": "rust",
    "tag": "story",
    "time_range": "past_week",
    "sort": "relevance",
    "limit": 10
  }
}
```

### Tool response (trimmed)

```json
{ "hits": [ { "id": "<picked-id>", "title": "...", "points": 0, "num_comments": 0, "created_at": "..." } ] }
```

_Note the `id` Claude picks to dive into — it feeds the next call._

## Step 2 — dive into the thread

### Tool call

```json
{
  "name": "get_hackernews_thread",
  "arguments": {
    "item_id": "<picked-id>",
    "max_comments": 30,
    "max_depth": 4
  }
}
```

### Tool response (trimmed)

```json
{
  "root": { "id": "<picked-id>", "title": "...", "points": 0, "author": "...", "created_at": "..." },
  "comments": [
    { "id": "...", "parent_id": "<picked-id>", "author": "...", "text": "...", "depth": 0, "created_at": "..." }
  ],
  "truncated": true
}
```

_Trim `comments` to ~4 representative entries; keep the `truncated` flag so the
bounding behavior is visible._

## Claude's final answer

_Paste Claude's summary of the discussion, ideally noting it only read a bounded
slice when `truncated` is true._
