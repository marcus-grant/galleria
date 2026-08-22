# src/services/rendition.py
"""
Merge variant manifests into per photo rendition records.

Author: Marcus Grant
Created: 2026-08-21
License: AGPL-3.0-or-later
"""

from src.models.normpic import NormpicManifest
from src.models.rendition import PicRenditions


def merge_variants(
    original: NormpicManifest, display: NormpicManifest
) -> list[PicRenditions]:
    """Merge two variant manifests into one record per relative path."""
    dict_o = {pic.relative_path: pic for pic in original.pics}
    dict_d = {pic.relative_path: pic for pic in display.pics}
    paths = dict_o.keys() | dict_d.keys()
    renditions = []
    for path in paths:
        pic_o, pic_d = dict_o.get(path), dict_d.get(path)
        rendition = PicRenditions(relative_path=path, original=pic_o, display=pic_d)
        renditions.append(rendition)
    return sorted(renditions, key=(lambda p: (p.taken_at, p.relative_path)))
