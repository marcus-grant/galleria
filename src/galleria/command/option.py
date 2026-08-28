# src/galleria/command/option.py
"""
CLI options shared across commands.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

import click


def manifest_options(f):
    """Apply the manifest options shared by commands reading a
    collection."""
    t = click.Path(exists=True, path_type=Path)
    f = click.option("--display-manifest", type=t)(f)
    f = click.option("--original-manifest", type=t)(f)
    return f


def derive_options(f):
    """Apply the options shared by commands writing renditions."""
    t = click.Path(path_type=Path)
    f = click.option("--output-dir", type=t)(f)
    f = manifest_options(f)
    return f
