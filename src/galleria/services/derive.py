# src/galleria/services/derive.py
"""
Derivation of renditions from a source image.
Author: Marcus Grant
Created: 2026-08-27
License: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from b3c32 import hash_b32
from PIL import Image as Img

from galleria.models.normpic import Pic
from galleria.models.rendition import Derivation, PicRenditions
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
    src_path: Path, dest_dir: Path, stem: Path, spec: RenditionSpec
) -> Path:
    """Encode src_path into dest_dir as stem plus the spec's extension.

    The output filename comes from the spec's format, so the written
    extension can never disagree with the encoded bytes. Any OSError
    from reading, resizing, or writing is re-raised as DeriveError
    carrying both paths, the spec, and the original cause.

    Returns the path written.
    """
    path = dest_dir / stem.with_suffix(f".{spec.format.extension}")
    path.parent.mkdir(parents=True, exist_ok=True)
    dim = spec.max_dimension
    try:
        with Img.open(src_path) as img:
            img.thumbnail((dim, dim), Img.Resampling.LANCZOS)
            img.save(path, spec.format.pil_name, **spec.pil_args)
    except OSError as e:  # Parent class to whole domain of derive error causes
        raise DeriveError(src_path, path, spec, cause=e)
    return path


def derive_absences(
    renditions: PicRenditions,
    specs: dict[Derivation, RenditionSpec],
    src_path: Path,
    dest_dir: Path,
    generate: Callable[[Path, Path, Path, RenditionSpec], Path] = derive_rendition,
) -> PicRenditions:
    """Fill a record's absences, deriving deeper ones and aliasing shallower ones."""
    origin_deriv, origin_pic = renditions.present[0]
    derived_pics: dict[Derivation, Pic] = {}
    for deriv in renditions.absent:
        if deriv < origin_deriv:
            derived_pics[deriv] = origin_pic
            continue
        deriv_dest_dir = dest_dir / deriv.name.lower()
        path = generate(src_path, deriv_dest_dir, renditions.key, specs[deriv])
        stat = path.stat()
        derived_pics[deriv] = Pic(
            hash=f"b3c32:{hash_b32(path.read_bytes(), 120)}",
            relative_path=path.relative_to(dest_dir),
            size_bytes=stat.st_size,
            mtime=datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc),
        )
    fields = {d.name.lower(): p for d, p in renditions.present}
    fields.update({d.name.lower(): p for d, p in derived_pics.items()})
    return PicRenditions(renditions.key, **fields)
