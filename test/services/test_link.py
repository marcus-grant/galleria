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
from galleria.models.rendition import Derivation
from galleria.services.link import rendition_href


class TestRenditionHref:
    def test_derived_pic_composes_kind_path(self):
        """A kind-relative derived Pic yields pics/COLLECTION/KIND/PATH."""
        pic = make_pic(relative_path=Path(fname := "stem.webp"))
        href = rendition_href(col_name := "wedding", Derivation.THUMB, pic)
        assert href == f"pics/{col_name}/{Derivation.THUMB.name.lower()}/{fname}"

    def test_manifested_pic_composes_same_shape(self):
        """A manifested Pic with a nested relative_path yields the same shape.

        Only the KIND segment differs from the derived case, and the
        result carries no leading slash, scheme, or root prefix.
        """
        pic = make_pic(relative_path=Path(rel := "2025/08/09/IMG_0001.jpg"))
        href = rendition_href(col_name := "wedding", Derivation.ORIGINAL, pic)
        assert href == f"pics/{col_name}/{Derivation.ORIGINAL.name.lower()}/{rel}"
        assert not href.startswith(("/", "http", "."))
