# src/galleria/models/rendition.py
"""
Records for a photo's renditions.

Author: Marcus Grant
Created: 2026-08-21
License: AGPL-3.0-or-later
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from galleria.models.normpic import Pic


@dataclass
class PicRenditions:
    """One photo's renditions, sharing a relative path."""

    relative_path: Path
    original: Pic | None = None
    display: Pic | None = None

    def __post_init__(self) -> None:
        """Reject a record with no renditions at all."""
        if self.original is None and self.display is None:
            raise ValueError(f"PicRenditions for {self.relative_path} has no variants")

    @property
    def taken_at(self) -> datetime:
        """From the original Pic first, then display, prefer the timestamp over mtime"""
        assert (pic := self.original or self.display) is not None
        return pic.timestamp or pic.mtime
