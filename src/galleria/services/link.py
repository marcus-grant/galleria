# src/galleria/services/link.py
"""
Composition of site-root-relative hrefs for renditions.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

from galleria.models.normpic import Pic


def rendition_href(collection: str, pic: Pic) -> str:
    """Return pics/COLLECTION/RELATIVE_PATH for one rendition.

    Site-root-relative with forward slashes and no leading slash; the
    template prefixes whatever root it renders from. A filled record's
    Pic paths already start with their kind, and an aliased field
    holds the deeper Pic itself, so an absent original resolves to the
    kind that was manifested with no logic here.

    Interim: once ref/derive-pipeline reworks the rendition models,
    this belongs on the model and this module goes away.
    """
    return f"pics/{collection}/{pic.relative_path.as_posix()}"
