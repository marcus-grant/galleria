# test/vendor/test_pico.py
"""
The vendored Pico stylesheet matches the version and code recorded for it.
Author: Marcus Grant
Created: 2026-11-20
License: AGPL-3.0-or-later
"""

from importlib import resources
import json

import b3c32

PICO = resources.files("galleria") / "vendor" / "pico"


def _record() -> dict:
    """The recorded version and code, as the vendoring script wrote them."""
    return json.loads((PICO / "pico.json").read_text())


class TestPicoVendored:
    """The packaged bytes are exactly what was recorded."""

    def test_record_has_exactly_version_and_code(self):
        """A malformed record cannot pass silently."""
        assert sorted(_record()) == ["code", "version"]

    def test_file_matches_recorded_code(self):
        """An edited, swapped, or truncated file changes the code."""
        with resources.as_file(PICO / "pico.min.css") as path:
            code = b3c32.code_from_path(path, 120)
        assert code == _record()["code"]

    def test_banner_names_the_recorded_version(self):
        """The recorded version and the file's own banner cannot drift."""
        head = (PICO / "pico.min.css").read_bytes()[:200]
        assert f"v{_record()['version']}".encode() in head

    def test_license_ships_beside_the_file(self):
        """MIT requires the notice with every copy."""
        text = (PICO / "LICENSE.md").read_text()
        assert "MIT" in text
