# src/galleria/command/validate.py
"""
Verify a build's inputs before anything is generated.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

import click

from galleria.command.option import manifest_options
from galleria.config import Config, MissingConfigError
from galleria.services.manifest_reader import (
    ManifestError,
    NormpicManifest,
    read_manifest,
)
from galleria.services.rendition import merge_variants


def _read_if_set(path: Path | None) -> NormpicManifest | None:
    """Read a manifest when one is configured."""
    return read_manifest(path) if path else None


@click.command()
@manifest_options
def validate(original_manifest: Path | None, display_manifest: Path | None) -> None:
    """Verify a build's inputs without generating anything."""
    cli_overrides = {
        "original_manifest": original_manifest,
        "display_manifest": display_manifest,
    }
    manifest_o, manifest_d = None, None
    try:
        cfg = Config.from_overrides(**cli_overrides)
        manifest_o = _read_if_set(cfg.original_manifest)
        manifest_d = _read_if_set(cfg.display_manifest)
    except (MissingConfigError, ManifestError) as e:
        click.echo(f"Validation failed: {e}", err=True)
        raise SystemExit(1)
    except Exception as e:
        click.echo(f"Unknown error during validate: {e}", err=True)
        raise SystemExit(128)
    renditions = merge_variants(manifest_o, manifest_d)
    manifest = manifest_o or manifest_d
    name = manifest.collection_name if manifest else None
    click.echo(f"Valid config, tracking {len(renditions)} pics of {name}.")
