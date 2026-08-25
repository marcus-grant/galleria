# test/command/test_validate.py
"""
Input verification before a build.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from galleria.command.validate import missing_pics_for, missing_pic_paths, validate
from galleria.models.rendition import PicRenditions
from galleria.services.manifest_reader import NormpicManifest
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


def _write_manifest(manifest_path: Path, root: Path, names: list[Path]) -> Path:
    """Write a manifest describing the named pics under root.

    Local to this module deliberately: the reader and models leave for
    a normpic-owned package post-MVP, which will ship its own test
    factories. A factory here would be a second definition of a
    contract this project does not own.
    """
    manifest = {
        "version": "0.1.0",
        "collection_name": "wedding",
        "generated_at": "2026-08-17T09:00:00Z",
        "collection_root": str(root),
        "pic": [
            {
                "hash": "b3c32:NW9MKEFNZ6GTD8209QN3DQ69",
                "relative_path": str(n),
                "size_bytes": 1024,
                "mtime": "2026-08-17T08:00:00Z",
            }
            for n in names
        ],
    }
    manifest_path.write_text(json.dumps(manifest))
    return manifest_path


def _make_manifest(root: Path, names: list[Path]) -> NormpicManifest:
    """Build a manifest record for the named pics under root."""
    return NormpicManifest(
        version="0.1.0",
        collection_name="wedding",
        collection_root=root,
        generated_at=datetime(2026, 8, 17, 9, 0, tzinfo=timezone.utc),
        pics=[make_pic(relative_path=n) for n in names],
    )


class TestMissingPicsFor:
    """Report manifest-described pics with no file behind them."""

    def test_checks_paths_under_each_manifest_root(self, tmp_path: Path):
        """Roots come from the manifests, so each variant is checked
        under its own collection."""
        names = [Path("2026/a.jpg")]
        original_root = tmp_path / "original"
        display_root = tmp_path / "display"
        _write_pic_files(original_root, names)  # NOTE: Only writing to original root
        results = missing_pics_for(
            _make_manifest(original_root, names),
            _make_manifest(display_root, names),
        )
        assert results == [display_root / names[0]]

    def test_returns_every_unresolved_path(self, tmp_path: Path):
        """The full gap, not the first failure."""
        names = [Path("2026/a.jpg"), Path("2026/b.jpg")]
        root = tmp_path / "original"
        results = missing_pics_for(_make_manifest(root, names), None)
        assert results == [root / n for n in names]

    def test_single_manifest_is_sufficient(self, tmp_path: Path):
        """Either variant alone validates, since either alone
        builds."""
        names = [Path("2026/a.jpg")]
        root = tmp_path / "original"
        results = missing_pics_for(_make_manifest(root, names), None)
        assert results == [root / names[0]]


@pytest.mark.skip
class TestValidateCommand:
    """The command's output contract."""

    def test_success_is_quiet_and_zero(self, tmp_path: Path):
        """One summary line naming collection, count, and paths
        verified."""
        names, root = [Path("2026/a.jpg")], tmp_path / "original"
        _write_pic_files(root, names)
        path_man = _write_manifest(tmp_path / "original.json", root, names)
        result = CliRunner().invoke(validate, ["--original-manifest", str(path_man)])
        assert result.exit_code == 0
        assert "wedding" in result.output
        assert "1" in result.output

    @pytest.mark.skip
    def test_failure_exits_non_zero(self, tmp_path: Path):
        """A missing path is a failed validation."""

    @pytest.mark.skip
    def test_failure_output_is_bounded(self, tmp_path: Path):
        """Many missing paths summarize by kind with examples, rather
        than one line each."""
