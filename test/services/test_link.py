# test/services/test_link.py
"""
Tests for rendition href composition.
Interim with the module under test: both go when ref/derive-pipeline
moves href composition onto the rendition models.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

from pathlib import Path

from conftest import make_pic
from galleria.services.link import rendition_href


class TestRenditionHref:
    def test_composes_collection_prefix(self):
        """A kind-prefixed Pic yields pics/COLLECTION/KIND/PATH."""
        pic = make_pic(relative_path=Path(rel := "thumb/stem.webp"))
        href = rendition_href(col_name := "wedding", pic)
        assert href == f"pics/{col_name}/{rel}"
        assert not href.startswith(("/", "http", "."))
