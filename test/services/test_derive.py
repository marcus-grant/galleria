# test/services/test_derive.py
"""
Tests for single-rendition derivation.
Author: Marcus Grant
Created: 2026-08-27
License: AGPL-3.0-or-later
"""

from pathlib import Path
import re

import pytest
from PIL import Image

from galleria.models.spec import Format, RenditionSpec
from galleria.services.derive import DeriveError, derive_rendition


@pytest.fixture
def _mk_src():
    """Build a source image on disk, overriding size, color, and format."""

    def _make(
        directory: Path,
        size: tuple[int, int] = (800, 600),
        fmt: str = "JPEG",
    ) -> Path:
        path = directory / f"source.{'jpg' if fmt == 'JPEG' else fmt.lower()}"
        Image.new("RGB", size).save(path, fmt)
        return path

    return _make


class TestDeriveRendition:
    """Encoding a single rendition from a source image."""

    @pytest.mark.parametrize("fmt", [Format.JPEG, Format.PJPEG, Format.WEBP])
    def test_writes_spec_fmt_at_mapped_ext(self, fmt, tmp_path, _mk_src):
        """The written file carries the spec's extension and opens as its format."""
        spec = RenditionSpec(fmt, 400, 85)
        written = derive_rendition(_mk_src(tmp_path), tmp_path, "photo", spec)
        assert written.name == f"photo.{fmt.extension}"
        with Image.open(written) as img:
            assert img.format == fmt.pil_name

    @pytest.mark.parametrize("size", [(800, 600), (600, 800)])
    def test_longest_edge_matches_the_spec_dimension(self, size, tmp_path, _mk_src):
        """A 4:3 or 3:4 source scales exactly to a dimension divisible by 12.
        120 shares factors of both edge ratios, so scaled
        dimensions are integers & ratio compares exactly."""
        src, max_edge = _mk_src(tmp_path, size=size), 120
        spec = RenditionSpec(Format.JPEG, max_edge, 85)
        written = derive_rendition(src, tmp_path, "photo", spec)
        with Image.open(written) as img:
            assert max(img.size) == max_edge
            assert size[0] / size[1] == img.size[0] / img.size[1]

    def test_non_image_source_raises_derive_error(self, tmp_path):
        """A file that exists but holds no image data raises DeriveError."""
        (src := tmp_path / "foobar.jpg").write_bytes(b"foobar")
        dest = tmp_path / "derived.jpg"
        spec = RenditionSpec(Format.JPEG, 6, 85)
        match = re.escape(f"cannot derive {dest} from {src} as jpeg")
        with pytest.raises(DeriveError, match=match) as exc:
            derive_rendition(src, tmp_path, "derived", spec)
        assert exc.value.src_path == src
        assert exc.value.dst_path == dest
        assert exc.value.spec == spec
        assert isinstance(exc.value.cause, OSError)

    def test_missing_source_raises_derive_error(self, tmp_path):
        """A source path with no file raises DeriveError."""
        src = tmp_path / "absent.jpg"
        spec = RenditionSpec(Format.JPEG, 6, 85)
        with pytest.raises(DeriveError) as exc:
            derive_rendition(src, tmp_path, "derived", spec)
        assert exc.value.src_path == src
        assert isinstance(exc.value.cause, OSError)

    def test_unwritable_destination_raises_derive_error(self, tmp_path, _mk_src):
        """A destination directory that does not exist raises DeriveError."""
        src = _mk_src(tmp_path)
        dest_dir = tmp_path / "absent"
        spec = RenditionSpec(Format.JPEG, 6, 85)
        with pytest.raises(DeriveError) as exc:
            derive_rendition(src, dest_dir, "derived", spec)
        assert exc.value.dst_path == dest_dir / "derived.jpg"
        assert isinstance(exc.value.cause, OSError)

    def test_failed_encode_raises_derive_error(self, tmp_path, _mk_src, monkeypatch):
        """An encoder failure surfaces as DeriveError carrying the spec."""
        src = _mk_src(tmp_path)
        spec = RenditionSpec(Format.WEBP, 120, 85)

        def _boom(*args, **kwargs):
            _, _ = args, kwargs  # Shut up LSP
            raise OSError("encoder refused")

        monkeypatch.setattr(Image.Image, "save", _boom)
        with pytest.raises(DeriveError) as exc:
            derive_rendition(src, tmp_path, "derived", spec)
        assert exc.value.spec == spec
        assert isinstance(exc.value.cause, OSError)
