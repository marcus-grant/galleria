# test/command/test_validate.py
"""
Input verification before a build.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.command.validate import missing_pic_paths
from galleria.models.rendition import PicRenditions
from conftest import make_pic


def _records(
    names: list[Path], original: bool = True, display: bool = False
) -> list[PicRenditions]:
    """Build one record per relative path, with the named variants."""
    return [
        PicRenditions(
            relative_path=n,
            original=make_pic(relative_path=n) if original else None,
            display=make_pic(relative_path=n) if display else None,
        )
        for n in names
    ]


def _write_pic_files(root: Path, names: list[Path]) -> None:
    """Create every named file under root, parents included."""
    for name in names:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(str(path))  # contents dont actually matter


class TestMissingPicPaths:
    """Every configured rendition resolves on disk."""

    def test_all_present_reports_nothing(self, tmp_path: Path):
        """A complete collection returns an empty list."""
        names = [Path("2026/a.jpg"), Path("2026/b.png"), Path("2026/c.webp")]
        _write_pic_files(tmp_path, names)
        assert missing_pic_paths(_records(names), tmp_path, None) == []

    def test_absent_rendition_is_reported(self, tmp_path: Path):
        """A path with no file behind it appears in the result."""
        bad = [Path("not/exist.jpg")]
        expect = [tmp_path / p for p in bad]
        assert missing_pic_paths(_records(bad), tmp_path, None) == expect

    def test_every_absent_path_is_reported(self, tmp_path: Path):
        """One run names the full gap rather than the first failure."""
        bad = [Path("not/exist/a.jpg"), Path("not/exist/b.png")]
        expect = [tmp_path / p for p in bad]
        results = missing_pic_paths(_records(bad), tmp_path, None)
        assert results == expect

    def test_unconfigured_variant_is_not_checked(self, tmp_path: Path):
        """A root of None means that variant was never configured, so
        its absence is not a defect."""
        names = [Path("2026/a.jpg")]
        records = _records(names, original=False, display=True)
        results = missing_pic_paths(records, None, tmp_path)
        assert results == [tmp_path / names[0]]

    def test_both_variants_are_checked_against_their_own_roots(self, tmp_path: Path):
        """A record carrying both variants can report a miss from
        either root, since the two collections live apart."""
        names = [Path("2026/a.jpg")]
        original_root = tmp_path / "original"
        display_root = tmp_path / "display"
        _write_pic_files(original_root, names)
        results = missing_pic_paths(
            _records(names, display=True), original_root, display_root
        )
        assert results == [display_root / names[0]]
