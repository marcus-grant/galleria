# test/asset/test_gallery_css.py
"""
The gallery stylesheet keeps a rule for each class the markup relies on.
Author: Marcus Grant
Created: 2026-11-20
License: AGPL-3.0-or-later
"""

from importlib import resources

import pytest

CSS = resources.files("galleria") / "asset" / "gallery.css"


class TestGalleryStylesheet:
    """A class renamed in a template must not silently lose its rule."""

    @pytest.mark.parametrize(
        "selector",
        [
            ".pic-grid",
            ".pic-cell__link",
            ".pic-cell__img",
            ".navbar",
            ".navbar__inner",
            ".navbar__title",
            ".navbar__count",
        ],
    )
    def test_targets_the_block_classes(self, selector: str):
        """Each class the grid and navbar markup carry appears in the CSS."""
        assert selector in CSS.read_text()
