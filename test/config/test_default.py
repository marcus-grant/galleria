# test/config/test_default.py
"""
Program-default configuration values.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.config import default


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
