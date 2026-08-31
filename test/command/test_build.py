# test/command/test_build.py
"""
The build command's CLI surface.
Author: Marcus Grant
License: AGPL-3.0-or-later
"""

from dataclasses import replace
import json
from pathlib import Path
from unittest.mock import patch

from bs4 import BeautifulSoup
from click.testing import CliRunner
from PIL import Image

from galleria.cli import cli
from galleria.config import Config
from galleria.config.default import RENDITION_SPECS
from galleria.command.build import build_gallery
from galleria.services.derive import derive_collection
from galleria.services.manifest_reader import read_manifest


def _write_collection(
    manifest_path: Path,
    root: Path,
    names: list[Path],
    size: tuple[int, int] = (800, 600),
) -> Path:
    """Write a manifest and the real images it names under root.

    Third copy of this helper. It, and many arrangement helpers like
    it, awaits the test-infrastructure consolidation task, which
    replaces these with cascading conftest fixtures. Do not let the
    copies drift; change all or none.
    """
    root.mkdir(parents=True, exist_ok=True)
    for n in names:
        path = root / n
        path.parent.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size).save(path, "JPEG")
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


def _records(tmp_path: Path, count: int):
    """Write count pics, derive them, and return manifest, output, records."""
    names = [Path(f"{i:03d}.jpg") for i in range(count)]
    man = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
    out = tmp_path / "out"
    records = derive_collection(read_manifest(man), None, RENDITION_SPECS, out)
    return man, out, records


def _cfg(man: Path, out: Path, page_size: int) -> Config:
    """A Config for one manifest with the page size under test."""
    cfg = Config.from_overrides(original_manifest=man, output_dir=out)
    return replace(cfg, page_size=page_size)


def _pages(out: Path) -> list[str]:
    """Sorted page file names under the collection's gallery dir."""
    return sorted(p.name for p in (out / "gallery" / "wedding").glob("page*.html"))


def _cells(path: Path) -> int:
    """Number of grid cells rendered on one page."""
    return len(BeautifulSoup(path.read_text(), "html.parser").select("img"))


class TestBuildGallery:
    """Paginated rendering of filled records under output_dir."""

    def test_zero_records_writes_page1_and_index(self, tmp_path: Path):
        """An empty collection still yields page1.html and index.html."""
        man, out, records = _records(tmp_path, 0)
        build_gallery(_cfg(man, out, 2), "wedding", records)
        assert _pages(out) == ["page1.html"]
        assert (out / "gallery" / "wedding" / "index.html").is_file()

    def test_index_is_a_byte_copy_of_page1(self, tmp_path: Path):
        """index.html and page1.html are byte-identical."""
        man, out, records = _records(tmp_path, 1)
        build_gallery(_cfg(man, out, 2), "wedding", records)
        site = out / "gallery" / "wedding"
        assert (site / "index.html").read_bytes() == (site / "page1.html").read_bytes()

    def test_below_page_size_is_one_page(self, tmp_path: Path):
        """Fewer records than a page yields only page1.html."""
        man, out, records = _records(tmp_path, 1)
        build_gallery(_cfg(man, out, 2), "wedding", records)
        assert _pages(out) == ["page1.html"]

    def test_at_page_size_is_one_page(self, tmp_path: Path):
        """Exactly a page of records yields one page and no empty page2."""
        man, out, records = _records(tmp_path, 2)
        build_gallery(_cfg(man, out, 2), "wedding", records)
        assert _pages(out) == ["page1.html"]

    def test_over_page_size_splits_by_position(self, tmp_path: Path):
        """One record past a page yields two pages split at the page size."""
        man, out, records = _records(tmp_path, 3)
        build_gallery(_cfg(man, out, 2), "wedding", records)
        assert _pages(out) == ["page1.html", "page2.html"]
        site = out / "gallery" / "wedding"
        assert _cells(site / "page1.html") == 2
        assert _cells(site / "page2.html") == 1


class TestBuildCommand:
    """The command's CLI surface and wiring."""

    def test_validates_before_building(self, tmp_path: Path):
        """Build resolves and validates its inputs before writing."""
        path_man = tmp_path / "original.json"
        path_man.write_text("{}")
        with patch("galleria.command.build.resolve_inputs") as mock_resolve:
            mock_resolve.return_value = (None, None, None)
            CliRunner().invoke(cli, ["build", "--original-manifest", str(path_man)])
        mock_resolve.assert_called_once()

    def test_default_build_never_encodes(self, tmp_path: Path):
        """A flagless build adopts existing renditions and encodes nothing."""
        names = [Path("a.jpg")]
        man = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        out = tmp_path / "out"
        derive_collection(read_manifest(man), None, RENDITION_SPECS, out)
        bomb = AssertionError("encoded during default build")
        with patch("galleria.command.build.derive_rendition", side_effect=bomb):
            result = CliRunner().invoke(
                cli,
                ["build", "--original-manifest", str(man), "--output-dir", str(out)],
            )
        assert result.exit_code == 0

    def test_adopt_missing_rendition_stops_naming_derive(self, tmp_path: Path):
        """A build without derived files exits non-zero saying re-run derive."""
        names = [Path("a.jpg")]
        man = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        result = CliRunner().invoke(
            cli,
            [
                "build",
                "--original-manifest",
                str(man),
                "--output-dir",
                str(tmp_path / "out"),
            ],
        )
        assert result.exit_code != 0
        assert "re-run derive" in result.output

    def test_derive_flag_encodes_the_missing_renditions(self, tmp_path: Path):
        """Build --derive fills absences on disk like the derive command."""
        names = [Path("a.jpg")]
        man = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        out = tmp_path / "out"
        result = CliRunner().invoke(
            cli,
            [
                "build",
                "--derive",
                "--original-manifest",
                str(man),
                "--output-dir",
                str(out),
            ],
        )
        assert result.exit_code == 0
        assert (out / "pics" / "wedding" / "thumb" / "a.webp").exists()

    def test_validate_flag_reports_the_merge(self, tmp_path: Path):
        """Build --validate prints the tracked-pics report before building."""
        names = [Path("a.jpg")]
        man = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        out = tmp_path / "out"
        derive_collection(read_manifest(man), None, RENDITION_SPECS, out)
        result = CliRunner().invoke(
            cli,
            [
                "build",
                "--validate",
                "--original-manifest",
                str(man),
                "--output-dir",
                str(out),
            ],
        )
        assert result.exit_code == 0
        assert "tracking 1 pics" in result.output
