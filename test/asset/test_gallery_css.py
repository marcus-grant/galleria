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
        "selector", [".pic-grid", ".pic-cell__link", ".pic-cell__img"]
    )
    def test_targets_the_grid_and_cell_classes(self, selector: str):
        """Each class the grid markup carries appears in the stylesheet."""
        assert selector in CSS.read_text()
