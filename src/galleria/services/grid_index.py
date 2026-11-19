# src/galleria/services/grid_index.py
"""
The grid index artifact: a JSON list of photo keys beside the pages.

Author: Marcus Grant
Created: 2026-11-11
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path

from galleria.models.rendition import PicRenditions
from galleria.services import artifact


def write_grid_index(site_dir: Path, records: list[PicRenditions], length: int) -> str:
    """Write the keys of records to site_dir and return the file name.

    The artifact is a compact JSON array of each record's full key as
    a POSIX path, in the order given. Naming and pruning of prior
    artifacts is the shared artifact unit's: grid-index plus a code
    prefix of these bytes.
    """
    keys = [rec.key.as_posix() for rec in records]
    data = json.dumps(keys, separators=(",", ":")).encode()
    return artifact.write_artifact(site_dir, "grid-index", "json", data, length)
