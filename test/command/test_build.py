"""Tests for build command."""

from click.testing import CliRunner
from pathlib import Path


def test_build_command_exists_and_outputs_status():
    """Test that build command exists and outputs status messages."""
    from galleria.cli import cli

    runner = CliRunner()
    result = runner.invoke(cli, ["build"])

    # Command should run without crashing
    assert result.exit_code == 0

    # Output should contain status keywords
    output_keywords = ["build", "site", "generating"]
    for keyword in output_keywords:
        assert keyword.lower() in result.output.lower()


def test_build_creates_output_directory_structure():
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
        assert "creating" in result.output.lower() or "created" in result.output.lower()
