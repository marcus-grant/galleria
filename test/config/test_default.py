# test/config/test_default.py
"""
Program-default configuration values.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.config import default
from galleria.models.rendition import Derivation


class TestDefaultKeys:
    """The default layer holds output values, never input paths."""

    def test_exposes_no_manifest_path_keys(self):
        """A default manifest path would let galleria read the wrong
        collection silently, so neither may appear here."""
        for key in ("ORIGINAL_MANIFEST", "DISPLAY_MANIFEST"):
            assert not hasattr(default, key)

    def test_output_dir_defaults_to_build(self):
        """Output is build product, so a wrong guess costs a deleted
        directory rather than wrong data."""
        assert default.OUTPUT_DIR == Path("_build")

    def test_load_ahead_defaults_to_two_viewports(self):
        """The client starts fetching when the grid end is two
        viewport heights below the visible area."""
        assert default.LOAD_AHEAD_VIEWPORTS == 2

    def test_artifact_name_length_defaults_to_eight(self):
        """Eight characters of a b3c32 code name a derived artifact."""
        assert default.ARTIFACT_NAME_LENGTH == 8

    def test_specs_cover_every_derived_rendition(self):
        """Display, preview, and thumb have specs; original does not."""
        assert set(default.RENDITION_SPECS) == set(Derivation) - {Derivation.ORIGINAL}
