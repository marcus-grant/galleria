# src/galleria/cli.py
"""
Command-line adaptor for Galleria.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

import click

from galleria.command.build import build
from galleria.command.process_photos import process_photos
from galleria.command.serve import serve
from galleria.command.validate import validate


@click.group()
def cli():
    """Galleria photo gallery management commands."""
    pass


cli.add_command(process_photos, name="process-photos")
cli.add_command(validate, name="validate")
cli.add_command(build, name="build")
cli.add_command(serve, name="serve")

