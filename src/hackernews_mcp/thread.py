"""The ``get_hackernews_thread`` tool: a bounded dive into a comment tree.

Algolia's ``/items/{id}`` endpoint returns the *entire* nested thread in one
shot; we flatten it depth-first and trim it client-side so the result stays
within an honest token budget.
"""

from __future__ import annotations

from typing import Any

import httpx

from .algolia import get_json
from .errors import InputValidationError
from .models import (
    MAX_COMMENTS_LIMIT,
    MAX_DEPTH_LIMIT,
    Thread,
    ThreadComment,
    ThreadRoot,
)


def _validate(item_id: str, max_comments: int, max_depth: int) -> str:
    """Validate arguments before any I/O and return the normalized item id."""
    if not isinstance(item_id, str) or not item_id.strip():
        raise InputValidationError("item_id must be a non-empty string")
    normalized = item_id.strip()
    if not normalized.isdigit():
        raise InputValidationError(f"item_id must be a numeric HN id, got {item_id!r}")
    if not isinstance(max_comments, int) or isinstance(max_comments, bool):
        raise InputValidationError("max_comments must be an integer")
    if not 1 <= max_comments <= MAX_COMMENTS_LIMIT:
        raise InputValidationError(
            f"max_comments must be between 1 and {MAX_COMMENTS_LIMIT}, got {max_comments}"
        )
    if not isinstance(max_depth, int) or isinstance(max_depth, bool):
        raise InputValidationError("max_depth must be an integer")
    if not 0 <= max_depth <= MAX_DEPTH_LIMIT:
        raise InputValidationError(
            f"max_depth must be between 0 and {MAX_DEPTH_LIMIT}, got {max_depth}"
        )
    return normalized


def _parse_root(raw: dict[str, Any]) -> ThreadRoot:
    return ThreadRoot(
        id=str(raw.get("id", "")),
        title=raw.get("title"),
        url=raw.get("url"),
        points=raw.get("points"),
        author=raw.get("author"),
        created_at=raw.get("created_at"),
        text=raw.get("text"),
    )


def flatten_comments(
    children: list[Any],
    max_depth: int,
) -> tuple[list[ThreadComment], bool]:
    """Flatten a nested ``children`` tree depth-first (pre-order).

    Top-level comments are depth 0. A comment deeper than ``max_depth`` is
    dropped along with its descendants. Returns the flat list (in Algolia's
    reply order) and whether anything was dropped for depth.
    """
    out: list[ThreadComment] = []
    depth_truncated = False

    def walk(nodes: list[Any], depth: int) -> None:
        nonlocal depth_truncated
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if depth > max_depth:
                depth_truncated = True
                continue
            out.append(
                ThreadComment(
                    id=str(node.get("id", "")),
                    parent_id=str(node["parent_id"]) if node.get("parent_id") is not None else None,
                    author=node.get("author"),
                    text=node.get("text"),
                    depth=depth,
                    created_at=node.get("created_at"),
                )
            )
            kids = node.get("children")
            if isinstance(kids, list) and kids:
                walk(kids, depth + 1)

    walk(children, 0)
    return out, depth_truncated


async def get_hackernews_thread(
    item_id: str,
    max_comments: int = 50,
    max_depth: int = 4,
    *,
    client: httpx.AsyncClient | None = None,
) -> Thread:
    """Fetch a Hacker News thread and return it as a bounded :class:`Thread`.

    Backed by Algolia's ``/items/{item_id}`` endpoint, which returns the full
    nested thread; the tree is flattened depth-first (preserving Algolia's reply
    ordering) and trimmed client-side.

    Bounding (so the result stays within an honest token budget):

    - Top-level comments are depth 0. Any comment deeper than ``max_depth``
      (default 4) is dropped along with its descendants.
    - At most ``max_comments`` (default 50) comments are returned, taking the
      first N in depth-first order.
    - ``truncated`` is ``True`` whenever comments were dropped for either
      reason, so a caller knows the thread is incomplete.

    Args:
        item_id: the HN story or comment id (a numeric string).
        max_comments: cap on returned comments, 1-500.
        max_depth: deepest reply level to include, 0-20.

    Raises ``InputValidationError`` for bad arguments (before any network call),
    ``UpstreamError`` for HTTP failures (e.g. an unknown ``item_id`` 404s), and
    ``UpstreamTimeoutError`` on timeout.
    """
    normalized = _validate(item_id, max_comments, max_depth)
    payload = await get_json(f"/items/{normalized}", client=client)
    if not isinstance(payload, dict):
        raise InputValidationError(f"item {item_id!r} returned an unexpected payload")

    root = _parse_root(payload)
    children = payload.get("children")
    eligible, depth_truncated = flatten_comments(
        children if isinstance(children, list) else [], max_depth
    )

    count_truncated = len(eligible) > max_comments
    comments = eligible[:max_comments]
    return Thread(
        root=root,
        comments=comments,
        truncated=depth_truncated or count_truncated,
    )
