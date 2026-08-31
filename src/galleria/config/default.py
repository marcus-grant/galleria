# src/galleria/config/default.py
"""
Program-default configuration values.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.models.rendition import Derivation
from galleria.models.spec import Format, RenditionSpec


RENDITION_SPECS: dict[Derivation, RenditionSpec] = {
    Derivation.DISPLAY: RenditionSpec(Format.WEBP, 2048, 85),
    Derivation.PREVIEW: RenditionSpec(Format.PJPEG, 1024, 70),
    Derivation.THUMB: RenditionSpec(Format.WEBP, 400, 85),
}

OUTPUT_DIR = Path("_build")

# Grid fills 6, 4, or 2 columns by breakpoint; 96 fills whole rows at
# every width and paginates a 645-photo collection into 7 pages.
PAGE_SIZE = 96
