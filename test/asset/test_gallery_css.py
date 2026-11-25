# test/asset/test_gallery_css.py
"""
The gallery stylesheet keeps a rule for each class the markup relies on.
Author: Marcus Grant
Created: 2026-11-20
License: AGPL-3.0-or-later
"""

import re
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
            ".pager",
            ".pager__prev",
            ".pager__up",
            ".pager__next",
            ".button",
            ".button--primary",
            ".button-group",
            ".frame",
            ".frame__img",
        ],
    )
    def test_targets_the_block_classes(self, selector: str):
        """Each class the markup carries is a whole selector in the CSS.

        A bare substring would let .button pass on .button-group alone,
        so the match must not run on into a longer class name.
        """
        pattern = re.escape(selector) + r"(?![\w-])"
        assert re.search(pattern, CSS.read_text())

    def test_page_background_fills_the_root_from_a_token(self):
        """The root, not a content-height body, paints the page color."""
        css = CSS.read_text()
        assert re.search(r"--page-bg\s*:", css)
        assert re.search(r"html\s*\{[^}]*background:\s*var\(--page-bg\)", css)
