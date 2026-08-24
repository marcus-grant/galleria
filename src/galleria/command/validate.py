# src/galleria/command/validate.py
"""
Verify a build's inputs before anything is generated.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.models.rendition import PicRenditions


def _missing_under(
    pics: list[PicRenditions], root: Path | None, variant: str
) -> list[Path]:
    """Return paths for one variant that do not resolve under root.

    A root of None means the variant was never configured, so nothing
    is checked and nothing is reported.
    """
    result = []
    if root is not None:
        variant_pics = [r for r in pics if getattr(r, variant)]
        for p_renditions in variant_pics:
            path = root / p_renditions.relative_path
            if not path.exists():
                result.append(path)
    return result


def missing_pic_paths(
    pics: list[PicRenditions],
    original_root: Path | None,
    display_root: Path | None,
) -> list[Path]:
    """Return every rendition path that does not resolve on disk.

    Reports rather than raises, so one run names the full gap rather
    than the first failure. A root of None means that variant was not
    configured and its renditions are not checked.
    """
    missing_originals = _missing_under(pics, original_root, "original")
    missing_displays = _missing_under(pics, display_root, "display")
    return [*missing_originals, *missing_displays]
