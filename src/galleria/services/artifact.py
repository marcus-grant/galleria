# src/galleria/services/artifact.py
"""
Content-addressed artifacts: files named by a code of their bytes.

Author: Marcus Grant
Created: 2026-11-19
License: AGPL-3.0-or-later
"""

from pathlib import Path
import re
import shutil

import b3c32

# b3c32 certifies only this width today, so the full code is computed
# and the name takes a prefix of it.
CODE_BITS = 120


def _artifact_name(stem: str, ext: str, code: str, length: int) -> str:
    """STEM-CODE.EXT with the code cut to its first length characters."""
    return f"{stem}-{code[:length]}.{ext}"


def _prune_artifacts(dest_dir: Path, stem: str, ext: str) -> None:
    """Remove prior artifacts of this stem and extension from dest_dir.

    Matches are deleted, so the match is exactly the names
    write_artifact produces: the stem, a dash, an uppercase code, and
    the extension. Another stem sharing a prefix, such as grid-index
    beside grid, does not match because its next word is lowercase.
    One directory level only, and regular files only.
    """
    pattern = re.compile(rf"{re.escape(stem)}-[0-9A-Z]+\.{re.escape(ext)}")
    for prior in dest_dir.iterdir():
        if prior.is_file() and pattern.fullmatch(prior.name):
            prior.unlink()


def write_artifact(
    dest_dir: Path, stem: str, ext: str, data: bytes, length: int
) -> str:
    """Write data to dest_dir as STEM-CODE.EXT and return the file name.

    CODE is the first length characters of the b3c32 code of data, so
    equal bytes always get an equal name. The directory persists across
    builds, so prior artifacts of the same stem and extension are
    removed first.
    """
    code = b3c32.code_from_chunks([data], CODE_BITS)
    name = _artifact_name(stem, ext, code, length)
    _prune_artifacts(dest_dir, stem, ext)
    (dest_dir / name).write_bytes(data)
    return name


def copy_artifact(dest_dir: Path, stem: str, ext: str, src: Path, length: int) -> str:
    """Copy the file src to dest_dir as STEM-CODE.EXT and return the name.

    The code is the b3c32 code of the file's bytes, streamed so a
    large file is never read whole. Naming and pruning are write_artifact's.
    src must not be inside dest_dir, or pruning could delete it before
    the copy.
    """
    code = b3c32.code_from_path(src, CODE_BITS)
    name = _artifact_name(stem, ext, code, length)
    _prune_artifacts(dest_dir, stem, ext)
    shutil.copyfile(src, dest_dir / name)
    return name
