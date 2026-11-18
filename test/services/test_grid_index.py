# test/services/test_grid_index.py
"""
The grid index artifact: a JSON list of photo keys beside the pages.
Author: Marcus Grant
Created: 2026-11-11
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path
import re

from b3c32 import code_from_path
import pytest

from conftest import make_pic
from galleria.models.rendition import PicRenditions
from galleria.services.grid_index import write_grid_index


def _rec(key: str) -> PicRenditions:
    """A record whose only meaningful field is its key."""
    return PicRenditions(Path(key), original=make_pic())


class TestWriteGridIndex:
    """Records in, the artifact's JSON content out."""

    def test_empty_collection_is_empty_array(self, tmp_path: Path):
        """No records is an empty list, not a missing or null file."""
        name = write_grid_index(tmp_path, [], 8)
        assert (tmp_path / name).read_text() == "[]"

    def test_order_follows_records(self, tmp_path: Path):
        """Keys follow the order given, which is page render order."""
        records = [_rec("b"), _rec("a"), _rec("c")]
        name = write_grid_index(tmp_path, records, 8)
        assert json.loads((tmp_path / name).read_text()) == ["b", "a", "c"]

    def test_nested_key_keeps_directories(self, tmp_path: Path):
        """Thumb paths use the full key, so a basename would break them."""
        name = write_grid_index(tmp_path, [_rec("2026/06/a")], 8)
        assert json.loads((tmp_path / name).read_text()) == ["2026/06/a"]

    def test_separators_are_compact(self, tmp_path: Path):
        """No whitespace between items or after separators."""
        name = write_grid_index(tmp_path, [_rec("a"), _rec("b")], 8)
        assert (tmp_path / name).read_text() == '["a","b"]'


class TestWriteGridIndexStale:
    """Prior artifacts in the directory after a rebuild."""

    def test_stale_artifact_is_removed(self, tmp_path: Path):
        """A previous build's artifact must not deploy beside the new."""
        old = write_grid_index(tmp_path, [_rec("a")], 8)
        new = write_grid_index(tmp_path, [_rec("b")], 8)
        assert not (tmp_path / old).exists()
        assert (tmp_path / new).is_file()

    def test_identical_rebuild_keeps_its_artifact(self, tmp_path: Path):
        """Cleanup must not delete the artifact a rebuild just wrote."""
        write_grid_index(tmp_path, [_rec("a")], 8)
        name = write_grid_index(tmp_path, [_rec("a")], 8)
        assert [p.name for p in tmp_path.glob("grid-index-*.json")] == [name]

    @pytest.mark.parametrize("other", ["page1.html", "notes.json", "grid-index.txt"])
    def test_unrelated_file_survives(self, tmp_path: Path, other: str):
        """The output directory is not scratch: only artifacts go."""
        (tmp_path / other).write_text("keep")
        write_grid_index(tmp_path, [_rec("a")], 8)
        assert (tmp_path / other).read_text() == "keep"


class TestWriteGridIndexName:
    """Records in, the artifact's file name out."""

    def test_identical_input_gives_identical_name(self, tmp_path: Path):
        """A rebuild of unchanged content lands on the same file."""
        first = write_grid_index(tmp_path, [_rec("a")], 8)
        second = write_grid_index(tmp_path, [_rec("a")], 8)
        assert first == second

    def test_changed_input_gives_different_name(self, tmp_path: Path):
        """Any change to the key list changes the name."""
        first = write_grid_index(tmp_path, [_rec("a"), _rec("b")], 8)
        second = write_grid_index(tmp_path, [_rec("b"), _rec("a")], 8)
        assert first != second

    def test_name_is_prefix_of_written_files_code(self, tmp_path: Path):
        """The name's code is the b3c32 code of the bytes on disk."""
        name = write_grid_index(tmp_path, [_rec("a"), _rec("2026/b")], 8)
        code = code_from_path(tmp_path / name, 120)
        assert name == f"grid-index-{code[:8]}.json"

    def test_name_carries_configured_code_length(self, tmp_path: Path):
        """The code in the name is as many characters as configured."""
        name = write_grid_index(tmp_path, [_rec("a")], 5)
        assert re.fullmatch(r"grid-index-[0-9A-Z]{5}\.json", name)
