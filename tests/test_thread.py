"""Tests for get_hackernews_thread: parsing, depth-first flattening, bounding."""

from typing import Any

import pytest
from pytest_httpx import HTTPXMock

from hackernews_mcp.errors import InputValidationError, UpstreamError
from hackernews_mcp.models import MAX_COMMENTS_LIMIT, MAX_DEPTH_LIMIT
from hackernews_mcp.thread import flatten_comments, get_hackernews_thread

ROOT_ID = 1


def _comment(
    cid: int, children: list[Any] | None = None, parent_id: int = ROOT_ID
) -> dict[str, Any]:
    return {
        "id": cid,
        "parent_id": parent_id,
        "author": f"user{cid}",
        "text": f"comment {cid}",
        "created_at": "2024-01-01T00:00:00Z",
        "children": children or [],
    }


def _item(children: list[Any]) -> dict[str, Any]:
    return {
        "id": ROOT_ID,
        "title": "Root story",
        "url": "https://example.com",
        "points": 100,
        "author": "op",
        "created_at": "2024-01-01T00:00:00Z",
        "text": None,
        "children": children,
    }


def _linear_chain(depth: int) -> dict[str, Any]:
    """A single comment chain reaching the given depth (0-based)."""
    node = _comment(depth, parent_id=depth - 1 if depth > 0 else ROOT_ID)
    for d in range(depth - 1, -1, -1):
        node = _comment(d, children=[node], parent_id=d - 1 if d > 0 else ROOT_ID)
    return _item([node])


# --- flattening / ordering ----------------------------------------------------


def test_flatten_is_depth_first_preorder() -> None:
    # c0 -> (c1 -> c2), c3 ; preorder = c0, c1, c2, c3
    tree = [
        _comment(0, children=[_comment(1, children=[_comment(2)])]),
        _comment(3),
    ]
    comments, depth_truncated = flatten_comments(tree, max_depth=10)
    assert [c.id for c in comments] == ["0", "1", "2", "3"]
    assert [c.depth for c in comments] == [0, 1, 2, 0]
    assert depth_truncated is False


def test_flatten_skips_non_dict_nodes() -> None:
    comments, _ = flatten_comments([_comment(0), "garbage", None], max_depth=4)
    assert [c.id for c in comments] == ["0"]


# --- root + small thread parsing ----------------------------------------------


async def test_parses_root_and_nested_comments(httpx_mock: HTTPXMock, load: Any) -> None:
    httpx_mock.add_response(json=load("thread_small"))
    thread = await get_hackernews_thread("26406989")

    assert thread.root.id == "26406989"
    assert thread.root.title == "Why asynchronous Rust doesn't work"
    assert thread.root.points == 603
    # depth-first: top1, its nested reply, then top2
    assert [c.id for c in thread.comments] == ["26407001", "26407050", "26407002"]
    assert [c.depth for c in thread.comments] == [0, 1, 0]
    assert thread.comments[1].parent_id == "26407001"
    assert thread.truncated is False


async def test_request_targets_items_endpoint(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=_item([]))
    await get_hackernews_thread("12345")
    assert httpx_mock.get_requests()[0].url.path == "/api/v1/items/12345"


# --- bounding: max_comments ---------------------------------------------------


async def test_caps_at_max_comments_with_truncated_flag(httpx_mock: HTTPXMock) -> None:
    payload = _item([_comment(i) for i in range(200)])
    httpx_mock.add_response(json=payload)

    thread = await get_hackernews_thread("1", max_comments=50)
    assert len(thread.comments) == 50
    # first 50 in depth-first order
    assert [c.id for c in thread.comments] == [str(i) for i in range(50)]
    assert thread.truncated is True


async def test_returns_all_when_under_cap(httpx_mock: HTTPXMock) -> None:
    # 10 top-level, each with 2 replies -> 30 comments, depths 0 and 1
    payload = _item(
        [_comment(i, children=[_comment(i * 100 + 1), _comment(i * 100 + 2)]) for i in range(10)]
    )
    httpx_mock.add_response(json=payload)

    thread = await get_hackernews_thread("1", max_comments=50)
    assert len(thread.comments) == 30
    assert thread.truncated is False
    assert max(c.depth for c in thread.comments) == 1


# --- bounding: max_depth ------------------------------------------------------


async def test_drops_comments_deeper_than_max_depth(httpx_mock: HTTPXMock) -> None:
    # chain reaching depth 5; default max_depth=4 keeps depths 0..4
    httpx_mock.add_response(json=_linear_chain(5))
    thread = await get_hackernews_thread("1", max_depth=4)

    depths = [c.depth for c in thread.comments]
    assert depths == [0, 1, 2, 3, 4]
    assert max(depths) == 4
    assert thread.truncated is True


async def test_max_depth_zero_keeps_only_top_level(httpx_mock: HTTPXMock) -> None:
    payload = _item([_comment(0, children=[_comment(1)])])
    httpx_mock.add_response(json=payload)
    thread = await get_hackernews_thread("1", max_depth=0)
    assert [c.id for c in thread.comments] == ["0"]
    assert thread.truncated is True


# --- error paths --------------------------------------------------------------


async def test_unknown_item_id_404_raises_upstream(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(status_code=404, text="not found")
    with pytest.raises(UpstreamError) as excinfo:
        await get_hackernews_thread("999999999")
    assert excinfo.value.status_code == 404


@pytest.mark.parametrize("item_id", ["", "   ", "abc", "12a", "-5"])
async def test_invalid_item_id_rejected_before_io(item_id: str) -> None:
    with pytest.raises(InputValidationError):
        await get_hackernews_thread(item_id)


@pytest.mark.parametrize("max_comments", [0, -1, MAX_COMMENTS_LIMIT + 1])
async def test_invalid_max_comments_rejected(max_comments: int) -> None:
    with pytest.raises(InputValidationError):
        await get_hackernews_thread("1", max_comments=max_comments)


@pytest.mark.parametrize("max_depth", [-1, MAX_DEPTH_LIMIT + 1])
async def test_invalid_max_depth_rejected(max_depth: int) -> None:
    with pytest.raises(InputValidationError):
        await get_hackernews_thread("1", max_depth=max_depth)


async def test_bool_args_rejected() -> None:
    with pytest.raises(InputValidationError):
        await get_hackernews_thread("1", max_comments=True)  # type: ignore[arg-type]
    with pytest.raises(InputValidationError):
        await get_hackernews_thread("1", max_depth=True)  # type: ignore[arg-type]


async def test_non_dict_payload_rejected(httpx_mock: HTTPXMock) -> None:
    httpx_mock.add_response(json=["unexpected"])
    with pytest.raises(InputValidationError):
        await get_hackernews_thread("1")
