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
from galleria.services.derive import CollectionDeriveError, derive_collection


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
    manifest = manifest_o or manifest_d
    name = manifest.collection_name if manifest else ""
    fail_count = 0
    try:
        derive_collection(manifest_o, manifest_d, cfg.specs, cfg.output_dir)
    except CollectionDeriveError as e:
        for f in e.failures:
            click.echo(f"Skipping: {f}", err=True)
            fail_count += 1
    click.echo(f"Derived renditions for {name}, {fail_count} skipped")
