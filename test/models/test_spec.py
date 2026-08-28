# test/models/test_spec.py
"""
Tests for the rendition spec model.
Author: Marcus Grant
Created: 2026-08-26
License: AGPL-3.0-or-later
"""

import pytest
import re

from galleria.models.spec import Format, RenditionSpec, RenditionSpecError


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

    @pytest.mark.parametrize(
        "fmt,expected",
        [(Format.JPEG, "jpg"), (Format.PJPEG, "jpg"), (Format.WEBP, "webp")],
    )
    def test_extension_maps_to_written_suffix(self, fmt, expected):
        """Both JPEG variants write .jpg; WEBP writes .webp."""
        assert fmt.extension == expected

    @pytest.mark.parametrize(
        "fmt,expected",
        [(Format.JPEG, "JPEG"), (Format.PJPEG, "JPEG"), (Format.WEBP, "WEBP")],
    )
    def test_pil_name_maps_to_encoder(self, fmt, expected):
        """Both JPEG variants use PIL's JPEG encoder; WEBP uses WEBP."""
        assert fmt.pil_name == expected

    @pytest.mark.parametrize(
        "prop,label,mapping",
        [
            ("extension", "extension", "EXTENSIONS"),
            ("pil_name", "PIL name", "PIL_NAMES"),
        ],
    )
    def test_unmapped_member_raises(self, prop, label, mapping, monkeypatch):
        """A member absent from a mapping raises rather than returning None."""
        fmt = Format.WEBP
        monkeypatch.delitem(getattr(Format, mapping), fmt.value)
        match = re.escape(f"no {label} mapped for {fmt}, please report this bug")
        with pytest.raises(Exception, match=match):
            getattr(fmt, prop)


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

    def test_pil_args_carry_quality(self):
        """Save arguments include the spec's quality."""
        assert RenditionSpec(Format.WEBP, 1024, 42).pil_args["quality"] == 42

    @pytest.mark.parametrize(
        "fmt,expect",
        [(Format.JPEG, None), (Format.PJPEG, True), (Format.WEBP, None)],
    )
    def test_pil_args_mark_progressive_only_for_pjpeg(self, fmt, expect):
        """Only PJPEG carries the progressive flag."""
        assert RenditionSpec(fmt, 24, 42).pil_args.get("progressive") is expect
