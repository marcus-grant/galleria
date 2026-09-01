# src/galleria/services/derive.py
"""
Derivation of renditions from a source image.
Author: Marcus Grant
Created: 2026-08-27
License: AGPL-3.0-or-later
"""

from dataclasses import replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from b3c32 import hash_b32
from PIL import Image as Img

from galleria.models.normpic import NormpicManifest, Pic
from galleria.models.rendition import Derivation, PicRenditions
from galleria.models.spec import RenditionSpec
from galleria.services.rendition import merge_variants


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
    """Fill a record's absences, deriving deeper ones and aliasing shallower ones.

    Every Pic in the returned record has a relative_path relative to
    dest_dir and starting with its kind directory. Manifested Pics are
    re-keyed under their kind; derived Pics are written there; an
    aliased shallower absence holds the deeper Pic itself and so
    carries that Pic's kind.
    """
    present = {
        d: replace(p, relative_path=Path(d.name.lower()) / p.relative_path)
        for d, p in renditions.present
    }
    origin_deriv = renditions.present[0][0]
    origin_pic = present[origin_deriv]
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
    fields = {d.name.lower(): p for d, p in present.items()}
    fields.update({d.name.lower(): p for d, p in derived_pics.items()})
    return PicRenditions(renditions.key, **fields)


def adopt_rendition(
    src_path: Path, dest_dir: Path, stem: Path, spec: RenditionSpec
) -> Path:
    """Return the path derive_rendition would write, without encoding.

    Path prediction only: the extension comes from the spec and the
    directory from the caller, the same inputs derive_rendition uses,
    so the two can never disagree. The file must already exist from a
    prior derive run; a missing file raises DeriveError so the edge
    can stop and tell the user to re-run derive. src_path is unused,
    accepted to match the generate signature.
    """
    path = dest_dir / stem.with_suffix(f".{spec.format.extension}")
    if not path.is_file():
        msg = "not derived; re-run derive"
        raise DeriveError(src_path, path, spec, cause=FileNotFoundError(msg))
    return path


class CollectionDeriveError(Exception):
    """Raised after a collection fill when any record failed.

    Carries the failure messages and the records that did fill, so an
    edge can choose to continue with the partial result or stop.
    """

    def __init__(self, failures: list[str], records: list[PicRenditions]) -> None:
        """Record what failed and what still filled."""
        self.failures = failures
        self.records = records
        super().__init__(f"{len(failures)} records failed to fill")


def derive_collection(
    manifest_o: NormpicManifest | None,
    manifest_d: NormpicManifest | None,
    specs: dict[Derivation, RenditionSpec],
    output_dir: Path,
    generate: Callable[[Path, Path, Path, RenditionSpec], Path] = derive_rendition,
) -> list[PicRenditions]:
    """Fill every record of a merged collection, returning the filled records.

    Merges the variant manifests, resolves each record's source from
    its shallowest present rendition, and fills its absences through
    generate. A record whose source has no manifest root, or whose
    generation raises DeriveError, is recorded as a failure; the loop
    finishes the collection, then raises CollectionDeriveError carrying
    the failures and the records that filled.

    Returns the filled records in merge order when nothing failed.
    """
    roots = {
        Derivation.ORIGINAL: manifest_o.collection_root if manifest_o else None,
        Derivation.DISPLAY: manifest_d.collection_root if manifest_d else None,
    }
    manifest = manifest_o or manifest_d
    name = manifest.collection_name if manifest else ""
    dest_dir = output_dir / "pics" / name
    records: list[PicRenditions] = []
    failures: list[str] = []
    for r in merge_variants(manifest_o, manifest_d):
        src_deriv, src_pic = r.present[0]
        root = roots[src_deriv]
        assert root is not None, "Unknown Error: This codepath shouldn't be possible"
        src_path = root / src_pic.relative_path
        try:
            records.append(derive_absences(r, specs, src_path, dest_dir, generate))
        except DeriveError as e:
            failures.append(str(e))
    if failures:
        raise CollectionDeriveError(failures, records)
    return records
