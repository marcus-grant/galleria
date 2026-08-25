# test/command/test_build.py
"""
The build command's CLI surface.
Author: Marcus Grant
License: AGPL-3.0-or-later
"""

from pathlib import Path
from unittest.mock import patch

from click.testing import CliRunner
import pytest

from galleria.cli import cli


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
