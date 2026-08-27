# src/galleria/services/derive.py
"""
Derivation of renditions from a source image.
Author: Marcus Grant
Created: 2026-08-27
License: AGPL-3.0-or-later
"""

from pathlib import Path

from PIL import Image as Img

from galleria.models.spec import RenditionSpec


class DeriveError(Exception):
    """A rendition that could not be encoded."""

    def __init__(
        self, src_path: Path, dst_path: Path, spec: RenditionSpec, cause: Exception
    ) -> None:
        """Record what failed to encode and why."""
        self.src_path = src_path
        self.dst_path = dst_path
        self.spec = spec
        self.cause = cause
        msg = f"cannot derive {dst_path} from {src_path} "
        super().__init__(msg + f"as {spec.format.value}: {cause}")


def derive_rendition(
    src_path: Path, dest_dir: Path, stem: str, spec: RenditionSpec
) -> Path:
    """Encode src_path into dest_dir as stem plus the spec's extension.

    The output filename comes from the spec's format, so the written
    extension can never disagree with the encoded bytes. Any OSError
    from reading, resizing, or writing is re-raised as DeriveError
    carrying both paths, the spec, and the original cause.

    Returns the path written.
    """
    path, dim = dest_dir / f"{stem}.{spec.format.extension}", spec.max_dimension
    try:
        with Img.open(src_path) as img:
            img.thumbnail((dim, dim), Img.Resampling.LANCZOS)
            img.save(path, spec.format.pil_name, **spec.pil_args)
    except OSError as e:  # Parent class to whole domain of derive error causes
        raise DeriveError(src_path, path, spec, cause=e)
    return path
