"""Shared test fixtures."""

from datetime import datetime, timezone
from pathlib import Path

from galleria.models.normpic import Pic


def make_pic(**overrides) -> Pic:
    """Creates a default test Pic, overridden per keyword given."""
    defaults = {
        "hash": "b3c32:NW9MKEFNZ6GTD8209QN3DQ69",
        "relative_path": Path("2026/a.jpg"),
        "size_bytes": 1024,
        "mtime": datetime(2026, 8, 17, 8, 0, tzinfo=timezone.utc),
    }
    return Pic(**{**defaults, **overrides})
