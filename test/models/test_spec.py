"""
Tests for the rendition spec model.
Author: Marcus Grant
Created: 2026-08-26
License: AGPL-3.0-or-later
"""

import pytest
import re

from galleria.models.spec import Format, RenditionSpec, RenditionSpecError


class TestRenditionSpec:
    """Construction and the invariants a spec enforces on itself."""

    @pytest.mark.parametrize("quality", [1, 95])
    def test_accepts_quality_at_the_boundaries(self, quality):
        """The lowest and highest valid quality values construct."""
        spec = RenditionSpec(Format.JPEG, 1024, quality)
        assert spec == RenditionSpec(Format.JPEG, 1024, quality)

    @pytest.mark.parametrize("quality", [0, 96])
    def test_rejects_quality_out_of_range(self, quality):
        """A quality below or above the valid range raises."""
        match = re.escape(f"quality {quality} outside 1-95")
        with pytest.raises(RenditionSpecError, match=match):
            RenditionSpec(Format.JPEG, 1024, quality)

    @pytest.mark.parametrize("dimension", [0, -1])
    def test_rejects_non_positive_dimension(self, dimension):
        """A max dimension of zero or less raises."""
        match = re.escape(f"max_dimension {dimension} less than 1")
        with pytest.raises(RenditionSpecError, match=match):
            RenditionSpec(Format.WEBP, dimension, 42)


class TestFormat:
    """Config-facing values."""

    @pytest.mark.parametrize(
        "given,expected",
        [
            ("jpeg", Format.JPEG),
            ("JPG", Format.JPEG),
            (" .jpeg ", Format.JPEG),
            ("pjpeg", Format.PJPEG),
            ("prog-jpeg", Format.PJPEG),
            ("Progressive_JPEG", Format.PJPEG),
            ("webp", Format.WEBP),
            (".WEBP", Format.WEBP),
        ],
    )
    def test_coerces_aliases_to_members(self, given, expected):
        """Aliases resolve case-insensitively, ignoring dots and separators."""
        assert Format(given) == expected

    @pytest.mark.parametrize("given", ["jpegg", "tiff", "", "...", None, 3])
    def test_coerce_raises_spec_error(self, given):
        """An unresolvable value raises RenditionSpecError, whatever its type."""
        match = re.escape(f"format {given!r} unknown")
        with pytest.raises(RenditionSpecError, match=match):
            Format(given)
