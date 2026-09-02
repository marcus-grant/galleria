# src/galleria/cli.py
"""
Command-line adaptor for Galleria.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

import click

from galleria.command.build import build
from galleria.command.derive import derive
from galleria.command.validate import validate


@click.group()
def cli():
    """Galleria photo gallery management commands."""
    pass


cli.add_command(validate, name="validate")
cli.add_command(derive, name="derive")
cli.add_command(build, name="build")
