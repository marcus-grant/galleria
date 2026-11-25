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

# Grid fills 6, 4, or 3 columns by breakpoint, all of which divide 12;
# 96 fills whole rows at every width and paginates a 645-photo
# collection into 7 pages.
PAGE_SIZE = 96

# The client starts fetching more cells when the grid end is this many
# viewport heights below the visible area.
LOAD_AHEAD_VIEWPORTS = 2

# Characters of a b3c32 code prefix that name a derived artifact.
ARTIFACT_NAME_LENGTH = 8

# Where pages link the gallery stylesheet. None means the copy galleria
# emits beside the pages; a string is linked verbatim instead.
STYLESHEET_URL: str | None = None
