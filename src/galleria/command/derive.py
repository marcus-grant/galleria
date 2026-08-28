# src/galleria/command/derive.py
"""
Generate the renditions a collection does not manifest.
Author: Marcus Grant
Created: 2026-08-28
License: AGPL-3.0-or-later
"""

from pathlib import Path

import click

from galleria.command.option import derive_options
from galleria.command.validate import resolve_inputs
from galleria.models.rendition import Derivation
from galleria.services.derive import DeriveError, derive_absences
from galleria.services.rendition import merge_variants


@click.command()
@derive_options
def derive(
    original_manifest: Path | None,
    display_manifest: Path | None,
    output_dir: Path | None,
) -> None:
    """Generate the renditions a collection is missing."""
    cfg, manifest_o, manifest_d = resolve_inputs(
        original_manifest, display_manifest, output_dir
    )
    roots = {
        Derivation.ORIGINAL: manifest_o.collection_root if manifest_o else None,
        Derivation.DISPLAY: manifest_d.collection_root if manifest_d else None,
    }
    manifest = manifest_o or manifest_d
    name = manifest.collection_name if manifest else ""
    dest_dir = cfg.output_dir / "pics" / name
    failed = 0
    for rends in merge_variants(manifest_o, manifest_d):
        src_deriv, src_pic = rends.present[0]
        root = roots.get(src_deriv)
        if root is None:
            msg = f"Skipping {rends.key}: no manifest root for {src_deriv.name}"
            click.echo(msg, err=True)
            failed += 1
            continue
        try:
            src_path = root / src_pic.relative_path
            derive_absences(rends, cfg.specs, src_path, dest_dir)
        except DeriveError as e:
            click.echo(f"Skipping {rends.key}: {e}", err=True)
            failed += 1
    click.echo(f"Derived renditions for {name}, {failed} skipped.")
