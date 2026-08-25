# src/galleria/command/validate.py
"""
Verify a build's inputs before anything is generated.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

import click

from galleria.config import Config
from galleria.models.rendition import PicRenditions
from galleria.services.manifest_reader import NormpicManifest, read_manifest
from galleria.services.rendition import merge_variants


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


def missing_pics_for(
    original: NormpicManifest | None, display: NormpicManifest | None
) -> list[Path]:
    """Return every pic path that does not resolve on disk.

    Each variant is checked against its own collection root. Reports
    rather than raises, so one run names the full gap.
    """
    renditions = merge_variants(original, display)
    return missing_pic_paths(
        renditions,
        original.collection_root if original else None,
        display.collection_root if display else None,
    )


@click.command()
@click.option("--original-manifest", type=click.Path(exists=True, path_type=Path))
@click.option("--display-manifest", type=click.Path(exists=True, path_type=Path))
def validate(original_manifest: Path | None, display_manifest: Path | None) -> None:
    """Verify a build's inputs without generating anything."""
    overrides = {  # Acquire overrides from CLI and load Config with overrides
        "original_manifest": original_manifest,
        "display_manifest": display_manifest,
    }
    cfg = Config.from_overrides(**overrides)
    # Load/deserialize manifests if possible
    manifest_o = read_manifest(cfg.original_manifest) if cfg.original_manifest else None
    manifest_d = read_manifest(cfg.display_manifest) if cfg.display_manifest else None
    # Gather facts about pic collections from manifests
    pics_missing = missing_pics_for(manifest_o, manifest_d)
    pics_total = len(merge_variants(manifest_o, manifest_d))
    name_o = manifest_o.collection_name if manifest_o else None
    # Check for problems and report, then exit
    if len(pics_missing) > 0:  # Pics from manifest are missing
        msg = "These pictures from the manifests are missing on disk:"
        pics_text = "\n".join(f"  {p}" for p in pics_missing)
        click.echo(f"{msg}\n{pics_text}", err=True)
        raise SystemExit(1)
    # Print Out Facts
    msg = f"Valid config, tracking {pics_total} pics of normpic collection {name_o}."
    click.echo(msg)
    return
