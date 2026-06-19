"""Public data shapes and the controlled vocabularies for tool arguments."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

Tag = Literal["story", "comment", "ask_hn", "show_hn", "all"]
TimeRange = Literal["past_24h", "past_week", "past_month", "all_time"]
Sort = Literal["relevance", "date"]

# Allowed values, kept next to the Literals so the server schema and the
# runtime validation in algolia.py share a single source of truth.
TAGS: tuple[Tag, ...] = ("story", "comment", "ask_hn", "show_hn", "all")
TIME_RANGES: tuple[TimeRange, ...] = ("past_24h", "past_week", "past_month", "all_time")
SORTS: tuple[Sort, ...] = ("relevance", "date")

LIMIT_MIN = 1
LIMIT_MAX = 50


class Hit(BaseModel):
    """A single Hacker News search result.

    For comment hits ``title`` and ``url`` are typically ``None`` and the
    matched text shows up in ``excerpt`` instead.
    """

    id: str = Field(description="The HN item id (Algolia objectID).")
    title: str | None = Field(default=None, description="Story title; None for comments.")
    url: str | None = Field(default=None, description="Story URL; None for text/ask posts.")
    points: int | None = Field(default=None, description="Score; None for comments.")
    author: str | None = Field(default=None, description="Submitter username.")
    num_comments: int | None = Field(default=None, description="Comment count; None for comments.")
    created_at: str | None = Field(default=None, description="ISO8601 creation timestamp.")
    excerpt: str | None = Field(
        default=None,
        description="Highlighted snippet from Algolia, if one was provided.",
    )


# Thread bounding limits (see get_hackernews_thread).
MAX_COMMENTS_LIMIT = 500
MAX_DEPTH_LIMIT = 20


class ThreadRoot(BaseModel):
    """The story (or comment) at the top of a fetched thread."""

    id: str = Field(description="The HN item id.")
    title: str | None = Field(default=None, description="Story title; None for comment roots.")
    url: str | None = Field(default=None, description="Story URL; None for text/ask/comment.")
    points: int | None = Field(default=None, description="Score, when present.")
    author: str | None = Field(default=None, description="Submitter username.")
    created_at: str | None = Field(default=None, description="ISO8601 creation timestamp.")
    text: str | None = Field(default=None, description="Body text for text/ask posts or comments.")


class ThreadComment(BaseModel):
    """A single comment, flattened out of the reply tree."""

    id: str = Field(description="The HN comment id.")
    parent_id: str | None = Field(default=None, description="Id of the parent item.")
    author: str | None = Field(default=None, description="Comment author username.")
    text: str | None = Field(default=None, description="Comment HTML/text.")
    depth: int = Field(description="Reply depth; 0 for top-level comments on the root.")
    created_at: str | None = Field(default=None, description="ISO8601 creation timestamp.")


class Thread(BaseModel):
    """A bounded view of a Hacker News thread."""

    root: ThreadRoot
    comments: list[ThreadComment] = Field(
        description="Comments flattened depth-first, capped at max_comments."
    )
    truncated: bool = Field(
        description="True if comments were dropped for exceeding max_comments or max_depth.",
    )
