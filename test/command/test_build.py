# test/command/test_build.py
"""
The build command's CLI surface.
Author: Marcus Grant
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
from PIL import Image
import pytest

from galleria.cli import cli
from galleria.config.default import RENDITION_SPECS
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

    @pytest.mark.skip(reason="Output layout settles in the static gallery item")
    def test_creates_output_directory_structure(self):
        """Test that build command creates output directory structure."""
        from galleria.cli import cli

        runner = CliRunner()
        with runner.isolated_filesystem():
            # Create source structure
            source_dir = Path.cwd() / "prod" / "pics"
            source_dir.mkdir(parents=True)
            (source_dir / "full").mkdir()
            (source_dir / "web").mkdir()
            (source_dir / "thumb").mkdir()

            # Run build command
            result = runner.invoke(cli, ["build"])

            # Check output directory was created
            output_dir = Path.cwd() / "prod" / "site"
            assert output_dir.exists()
            assert output_dir.is_dir()

            # Check subdirectories were created
            assert (output_dir / "css").exists()
            assert (output_dir / "js").exists()

            # Check output mentions creation
            assert (
                "creating" in result.output.lower()
                or "created" in result.output.lower()
            )
