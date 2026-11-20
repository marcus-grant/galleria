"""Shared test fixtures."""

from datetime import datetime, timezone
from pathlib import Path

from galleria.models.normpic import Pic


def make_asset_context(**overrides) -> dict:
    """The stylesheet keys build_gallery adds to every page context.

    Defaults describe a grid page: names for both emitted stylesheets,
    no stylesheet URL, and no directory prefix. Overridden per keyword.
    """
    defaults = {
        "asset": {"pico": "pico-TEST0000.css", "gallery": "gallery-TEST0000.css"},
        "stylesheet_url": None,
        "asset_base": "",
    }
    return {**defaults, **overrides}


def make_pic(**overrides) -> Pic:
    """Creates a default test Pic, overridden per keyword given."""
    defaults = {
        "hash": "b3c32:NW9MKEFNZ6GTD8209QN3DQ69",
        "relative_path": Path("2026/a.jpg"),
        "size_bytes": 1024,
        "mtime": datetime(2026, 8, 17, 8, 0, tzinfo=timezone.utc),
    }
    return Pic(**{**defaults, **overrides})
