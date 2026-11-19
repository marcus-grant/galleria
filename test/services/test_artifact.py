# test/services/test_artifact.py
"""
Content-addressed artifact naming, writing, and pruning.
Author: Marcus Grant
Created: 2026-11-19
License: AGPL-3.0-or-later
"""

from pathlib import Path
import re

import b3c32
import pytest

from galleria.services import artifact


class TestWriteArtifact:
    """Bytes in, a content-named file out."""

    def test_name_is_stem_code_prefix_and_extension(self, tmp_path: Path):
        """The name's code is the b3c32 code of the bytes, cut to length."""
        name = artifact.write_artifact(tmp_path, "site", "css", b"body{}", 8)
        code = b3c32.code_from_chunks([b"body{}"], 120)
        assert name == f"site-{code[:8]}.css"

    def test_name_carries_configured_code_length(self, tmp_path: Path):
        """The code in the name is as many characters as configured."""
        name = artifact.write_artifact(tmp_path, "site", "css", b"x", 5)
        assert re.fullmatch(r"site-[0-9A-Z]{5}\.css", name)

    def test_equal_bytes_give_equal_name(self, tmp_path: Path):
        """A rebuild of unchanged content lands on the same file."""
        first = artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        second = artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        assert first == second

    def test_changed_bytes_give_different_name(self, tmp_path: Path):
        """Any change to the bytes changes the name."""
        first = artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        second = artifact.write_artifact(tmp_path, "site", "css", b"b", 8)
        assert first != second

    def test_file_holds_the_bytes_given(self, tmp_path: Path):
        """The file written under the name is the input, byte for byte."""
        name = artifact.write_artifact(tmp_path, "site", "css", b"\x00\xffabc", 8)
        assert (tmp_path / name).read_bytes() == b"\x00\xffabc"

    def test_empty_bytes_still_write(self, tmp_path: Path):
        """An empty artifact is a file, not a skipped write."""
        name = artifact.write_artifact(tmp_path, "site", "css", b"", 8)
        assert (tmp_path / name).read_bytes() == b""


class TestPruneScope:
    """Matches are deleted, so only the same stem and extension go."""

    def test_stale_artifact_is_removed(self, tmp_path: Path):
        """A previous build's artifact must not deploy beside the new."""
        old = artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        new = artifact.write_artifact(tmp_path, "site", "css", b"b", 8)
        assert not (tmp_path / old).exists()
        assert (tmp_path / new).is_file()

    def test_identical_rewrite_keeps_its_artifact(self, tmp_path: Path):
        """Cleanup must not delete the artifact a rewrite just wrote."""
        artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        name = artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        assert [p.name for p in tmp_path.glob("site-*.css")] == [name]

    def test_other_stem_survives(self, tmp_path: Path):
        """Writing one stem leaves another stem's artifact alone."""
        other = artifact.write_artifact(tmp_path, "theme", "css", b"a", 8)
        artifact.write_artifact(tmp_path, "site", "css", b"b", 8)
        assert (tmp_path / other).is_file()

    def test_same_stem_other_extension_survives(self, tmp_path: Path):
        """The extension is part of the match."""
        other = artifact.write_artifact(tmp_path, "site", "js", b"a", 8)
        artifact.write_artifact(tmp_path, "site", "css", b"b", 8)
        assert (tmp_path / other).is_file()

    def test_grid_index_survives_other_stem(self, tmp_path: Path):
        """A stylesheet write must not delete the grid index."""
        index = tmp_path / "grid-index-AB12CD34.json"
        index.write_text("[]")
        artifact.write_artifact(tmp_path, "site", "json", b"b", 8)
        assert index.read_text() == "[]"

    def test_stem_prefix_of_another_stem_spares_it(self, tmp_path: Path):
        """Writing stem grid does not prune grid-index artifacts."""
        index = tmp_path / "grid-index-AB12CD34.json"
        index.write_text("[]")
        artifact.write_artifact(tmp_path, "grid", "json", b"b", 8)
        assert index.read_text() == "[]"

    def test_longer_stem_spares_its_shorter_prefix(self, tmp_path: Path):
        """Writing stem grid-index does not prune grid artifacts."""
        short = tmp_path / "grid-XYZ12345.json"
        short.write_text("keep")
        artifact.write_artifact(tmp_path, "grid-index", "json", b"b", 8)
        assert short.read_text() == "keep"

    @pytest.mark.parametrize("other", ["page1.html", "notes.json", "site.css"])
    def test_unrelated_file_survives(self, tmp_path: Path, other: str):
        """The output directory is not scratch: only artifacts go."""
        (tmp_path / other).write_text("keep")
        artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        assert (tmp_path / other).read_text() == "keep"

    def test_matching_name_in_subdirectory_survives(self, tmp_path: Path):
        """Pruning is one level: pic/ and nested files are never candidates."""
        nested = tmp_path / "pic" / "site-AB12CD34.css"
        nested.parent.mkdir()
        nested.write_text("keep")
        artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        assert nested.read_text() == "keep"

    def test_matching_name_directory_survives(self, tmp_path: Path):
        """Only regular files are removed; a directory is left alone."""
        folder = tmp_path / "site-AB12CD34.css"
        folder.mkdir()
        artifact.write_artifact(tmp_path, "site", "css", b"a", 8)
        assert folder.is_dir()
