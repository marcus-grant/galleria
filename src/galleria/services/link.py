# src/galleria/services/link.py
"""
Composition of site-root-relative hrefs for renditions.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

from galleria.models.normpic import Pic
from galleria.models.rendition import Derivation


def rendition_href(collection: str, deriv: Derivation, pic: Pic) -> str:
    """Return pics/COLLECTION/KIND/RELATIVE_PATH for one rendition.
    Interim: once ref/derive-pipeline reworks the rendition models,
    this composition belongs on the model that knows its own kind
    and path, and this module goes away.
    Site-root-relative with forward slashes and no leading slash; the
    template prefixes whatever root it renders from. KIND is the
    derivation name lowercased, matching the derive output directory,
    and RELATIVE_PATH is the Pic's kind-relative path as-is. Every
    kind takes the same shape whether or not it is physically present
    under the output directory; routing is the deployer's concern.
    """
    return f"pics/{collection}/{deriv.name.lower()}/{pic.relative_path.as_posix()}"
