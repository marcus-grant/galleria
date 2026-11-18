# src/galleria/services/grid_index.py
"""
The grid index artifact: a JSON list of photo keys beside the pages.

Author: Marcus Grant
Created: 2026-11-11
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path
import re

from b3c32 import code_from_chunks

from galleria.models.rendition import PicRenditions

# b3c32 certifies only this width today, so the full code is computed
# and the name takes a prefix of it.
CODE_BITS = 120

# Exactly the names write_grid_index produces: nothing else in the
# output directory may match, since matches are deleted.
ARTIFACT_NAME = re.compile(r"grid-index-[0-9A-Z]+\.json")


def write_grid_index(site_dir: Path, records: list[PicRenditions], length: int) -> str:
    """Write the keys of records to site_dir and return the file name.

    The artifact is a compact JSON array of each record's full key as
    a POSIX path, in the order given. The name is grid-index- plus
    the first length characters of the b3c32 code of the artifact's
    bytes, so equal content always gets an equal name. The directory
    persists across builds, so any prior artifact is removed first.
    """
    keys = [rec.key.as_posix() for rec in records]
    data = json.dumps(keys, separators=(",", ":")).encode()
    code = code_from_chunks([data], CODE_BITS)[:length]
    name = f"grid-index-{code}.json"
    for prior in site_dir.iterdir():
        if ARTIFACT_NAME.fullmatch(prior.name):
            prior.unlink()
    (site_dir / name).write_bytes(data)
    return name
