"""Shared pytest fixtures: loaders for the saved Algolia response fixtures."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_fixture(name: str) -> Any:
    """Load and parse ``tests/fixtures/<name>.json``."""
    return json.loads((FIXTURES_DIR / f"{name}.json").read_text())


@pytest.fixture
def algolia_response() -> Any:
    """A normal multi-hit Algolia search response (story, ask_hn, comment)."""
    return load_fixture("search_multi")


@pytest.fixture
def algolia_empty() -> Any:
    """An empty Algolia search response."""
    return load_fixture("search_empty")


@pytest.fixture
def algolia_malformed() -> Any:
    """A malformed payload whose ``hits`` field is the wrong type."""
    return load_fixture("search_malformed")


@pytest.fixture
def load() -> Any:
    """Expose the fixture loader to tests that need other shapes by name."""
    return load_fixture
