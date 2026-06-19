"""Typed error hierarchy for the Hacker News MCP tools.

Every failure mode an LLM (or a test) might care about is a distinct type so
callers can branch on it, and ``str(error)`` always yields a message clear
enough to surface directly in an MCP tool error response.
"""

from __future__ import annotations


class HackerNewsError(Exception):
    """Base class for all errors raised by this package."""


class InputValidationError(HackerNewsError):
    """A tool argument was invalid (out of range, unknown enum value, etc.).

    Raised *before* any network call is made.
    """


class UpstreamError(HackerNewsError):
    """The Algolia API returned a non-success (4xx/5xx) HTTP status."""

    def __init__(self, status_code: int, message: str | None = None) -> None:
        self.status_code = status_code
        detail = f": {message}" if message else ""
        super().__init__(f"Algolia API returned HTTP {status_code}{detail}")


class UpstreamTimeoutError(HackerNewsError):
    """The request to the Algolia API timed out."""

    def __init__(self, timeout: float) -> None:
        self.timeout = timeout
        super().__init__(f"Request to Algolia API timed out after {timeout:g}s")
