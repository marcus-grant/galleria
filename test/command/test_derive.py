# test/command/test_derive.py
"""
Tests for the derive command.
Author: Marcus Grant
Created: 2026-08-28
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path

from click.testing import CliRunner
from PIL import Image

from galleria.command.derive import derive


def _write_collection(
    manifest_path: Path,
    root: Path,
    names: list[Path],
    size: tuple[int, int] = (800, 600),
) -> Path:
    """Write a manifest and the real images it names under root.

    Local to this module deliberately, as in the validate tests: the
    reader and models leave for a normpic-owned package post-MVP,
    which will ship its own test factories.
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


class TestDeriveCommand:
    """Generating missing renditions from a collection."""

    def test_writes_every_missing_rendition(self, tmp_path: Path):
        """Each manifested photo gains the renditions it lacks."""
        names = [Path("2026/a.jpg"), Path("2026/b.jpg")]
        man = _write_collection(tmp_path / "o.json", tmp_path / "src", names)
        out = tmp_path / "out"
        result = CliRunner().invoke(
            derive,
            ["--original-manifest", str(man), "--output-dir", str(out)],
        )
        assert result.exit_code == 0
        for rendition, ext in (
            ("display", "webp"),
            ("preview", "jpg"),
            ("thumb", "webp"),
        ):
            for n in names:
                written = (
                    out / "pics" / "wedding" / rendition / n.with_suffix(f".{ext}")
                )
                assert written.exists()

    def test_a_failed_photo_warns_and_continues(self, tmp_path: Path):
        """One unreadable source does not stop the rest of the run."""
        names = [Path("2026/a.jpg"), Path("2026/b.jpg")]
        root = tmp_path / "src"
        man = _write_collection(tmp_path / "o.json", root, names)
        (root / names[0]).write_bytes(b"not an image")
        out = tmp_path / "out"
        result = CliRunner().invoke(
            derive,
            ["--original-manifest", str(man), "--output-dir", str(out)],
        )
        assert result.exit_code == 0
        assert "Skipping 2026/a" in result.output
        assert (out / "pics" / "wedding" / "thumb" / "2026/b.webp").exists()

    def test_no_manifest_reports_and_exits_non_zero(self):
        """The command fails the same way validate does."""
        result = CliRunner().invoke(derive, [])
        assert result.exit_code != 0
