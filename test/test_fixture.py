# test/test_fixture.py
"""
Tests that the committed fixture collection stays readable.
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.services import manifest_reader

FIXTURE = Path(__file__).resolve().parent.parent / "fixture" / "collection"


class TestFixtureCollection:
    """The fixture is a valid manifest whose every entry has a file."""

    def test_manifest_reads_with_six_pics(self):
        """The manifest parses and lists the six fixture pics."""
        manifest = manifest_reader.read_manifest(FIXTURE / "manifest.json")
        assert manifest.collection_name == "fixture"
        assert len(manifest.pics) == 6

    def test_every_entry_has_a_source_file(self):
        """Each pic resolves under the collection root to a real file."""
        manifest = manifest_reader.read_manifest(FIXTURE / "manifest.json")
        for pic in manifest.pics:
            assert (manifest.collection_root / pic.relative_path).is_file()
