# src/galleria/services/rendition.py
"""
Merge variant manifests into per photo rendition records.

Author: Marcus Grant
Created: 2026-08-21
License: AGPL-3.0-or-later
"""

from galleria.models.normpic import NormpicManifest
from galleria.models.rendition import PicRenditions


def merge_variants(
    original: NormpicManifest | None, display: NormpicManifest | None
) -> list[PicRenditions]:
    """Merge two variant manifests into one record per relative path."""
    dict_o, dict_d = {}, {}
    if original is not None:
        dict_o = {pic.relative_path: pic for pic in original.pics}
    if display is not None:
        dict_d = {pic.relative_path: pic for pic in display.pics}
    paths = dict_o.keys() | dict_d.keys()
    renditions = []
    for path in paths:
        pic_o, pic_d = dict_o.get(path), dict_d.get(path)
        rendition = PicRenditions(relative_path=path, original=pic_o, display=pic_d)
        renditions.append(rendition)
    return sorted(renditions, key=(lambda p: (p.taken_at, p.relative_path)))
