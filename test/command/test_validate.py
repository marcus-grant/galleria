# test/command/test_validate.py
"""
Input verification before a build.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path

from click.testing import CliRunner
import pytest

from galleria.command.validate import resolve_inputs, validate


def _write_manifest(
    manifest_path: Path,
    root: Path,
    names: list[Path],
    version: str = "0.1.0",
) -> Path:
    """Write a manifest describing the named pics under root.

    Local to this module deliberately: the reader and models leave for
    a normpic-owned package post-MVP, which will ship its own test
    factories. A factory here would be a second definition of a
    contract this project does not own.
    """
    manifest = {
        "version": version,
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


class TestResolveInputs:
    """Config resolution and manifest reading as one step."""

    def test_returns_config_and_both_manifests(self, tmp_path: Path):
        """Validated inputs come back so a caller need not re-read."""
        names = [Path("2026/a.jpg")]
        path_o = _write_manifest(
            tmp_path / "original.json", tmp_path / "original", names
        )
        path_d = _write_manifest(tmp_path / "display.json", tmp_path / "display", names)
        cfg, manifest_o, manifest_d = resolve_inputs(path_o, path_d)
        assert cfg.original_manifest == path_o
        assert cfg.display_manifest == path_d
        assert manifest_o is not None
        assert manifest_d is not None

    def test_absent_variant_returns_none_for_it(self, tmp_path: Path):
        """Either variant alone resolves, with None in the other
        slot."""
        path_o = _write_manifest(
            tmp_path / "original.json", tmp_path / "original", [Path("2026/a.jpg")]
        )
        _, manifest_o, manifest_d = resolve_inputs(path_o, None)
        assert manifest_o is not None
        assert manifest_d is None

    def test_no_manifest_exits_non_zero(self):
        """Nothing to resolve is a failure the caller never sees
        past."""
        with pytest.raises(SystemExit) as exc:
            resolve_inputs(None, None)
        assert exc.value.code != 0

    def test_unreadable_manifest_exits_non_zero(self, tmp_path: Path):
        """A manifest that does not parse exits rather than
        returning."""
        path_man = tmp_path / "original.json"
        path_man.write_text("{not json")
        with pytest.raises(SystemExit) as exc:
            resolve_inputs(path_man, None)
        assert exc.value.code != 0


class TestValidateCommand:
    """The command's output contract."""

    def test_success_is_quiet_and_zero(self, tmp_path: Path):
        """One summary line naming the collection and the pic count."""
        names = [Path("2026/a.jpg"), Path("2026/b.png")]
        root = tmp_path / "original"
        path_man = _write_manifest(tmp_path / "original.json", root, names)
        result = CliRunner().invoke(validate, ["--original-manifest", str(path_man)])
        assert result.exit_code == 0
        assert "wedding" in result.output
        assert "2 pic" in result.output

    def test_no_manifest_reports_and_exits_non_zero(self):
        """Neither variant supplied leaves nothing to validate."""
        result = CliRunner().invoke(validate, [])
        assert result.exit_code != 0
        assert "Traceback" not in result.output
        assert "manifest" in result.output

    def test_unreadable_manifest_reports_and_exits_non_zero(self, tmp_path: Path):
        """A manifest that does not parse is named, not raised as a
        traceback."""
        path_man = tmp_path / "original.json"
        path_man.write_text("{not json")
        result = CliRunner().invoke(validate, ["--original-manifest", str(path_man)])
        assert result.exit_code != 0
        assert "Traceback" not in result.output

    def test_unsupported_version_reports_and_exits_non_zero(self, tmp_path: Path):
        """A manifest outside the supported major.minor is named."""
        path_man = _write_manifest(
            tmp_path / "original.json",
            tmp_path / "original",
            [Path("2026/a.jpg")],
            version="9.9.3",
        )
        result = CliRunner().invoke(validate, ["--original-manifest", str(path_man)])
        assert result.exit_code != 0
        assert "Traceback" not in result.output
        assert "9.9.3" in result.output
