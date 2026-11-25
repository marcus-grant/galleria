# src/galleria/services/stylesheet.py
"""
Emit the stylesheets every page links, content-addressed.

Author: Marcus Grant
Created: 2026-11-20
License: AGPL-3.0-or-later
"""

from importlib import resources
from pathlib import Path

from galleria.services import artifact

# Name-map key, mapped to the package file it is copied from.
SOURCES = {
    "pico": ("vendor", "pico", "pico.min.css"),
    "gallery": ("asset", "gallery.css"),
}


def emit_stylesheets(site_dir: Path, length: int) -> dict[str, str]:
    """Copy each stylesheet into site_dir and return its file names.

    The names are keyed pico and gallery and are what every page's
    links are built from. Each file is named by a code prefix of its
    bytes, and prior copies of the same stylesheet are removed.
    """
    names = {}
    for key, parts in SOURCES.items():
        source = resources.files("galleria").joinpath(*parts)
        with resources.as_file(source) as path:
            names[key] = artifact.copy_artifact(site_dir, key, "css", path, length)
    return names
