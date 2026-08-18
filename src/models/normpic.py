# src/models/normpic.py
"""
Records for pics read from a NormPic manifest.

Author: Marcus Grant
Created: 2026-08-17
License: AGPL-3.0-or-later
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class Pic:
    """A single pic read from a manifest."""

    hash: str
    relative_path: Path
    size_bytes: int
    mtime: datetime


@dataclass
class NormpicManifest:
    """A manifest's pics and the collection they belong to."""

    version: str
    collection_name: str
    collection_root: Path
    generated_at: datetime
    pics: list[Pic]
