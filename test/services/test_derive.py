# test/services/test_derive.py
"""
Tests for single-rendition derivation.
Author: Marcus Grant
Created: 2026-08-27
License: AGPL-3.0-or-later
"""

from pathlib import Path
import re

from b3c32 import verify_conformance
import pytest
from PIL import Image

from conftest import make_pic
from galleria.models.spec import Format, RenditionSpec
from galleria.models.rendition import Derivation, PicRenditions
from galleria.services.derive import DeriveError, derive_absences, derive_rendition


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

    STEM = Path("derived")

    @pytest.mark.parametrize("fmt", [Format.JPEG, Format.PJPEG, Format.WEBP])
    def test_writes_spec_fmt_at_mapped_ext(self, fmt, tmp_path, _mk_src):
        """The written file carries the spec's extension and opens as its format."""
        spec, stem = RenditionSpec(fmt, 400, 85), self.STEM
        written = derive_rendition(_mk_src(tmp_path), tmp_path, stem, spec)
        assert written.name == f"derived.{fmt.extension}"
        with Image.open(written) as img:
            assert img.format == fmt.pil_name

    @pytest.mark.parametrize("size", [(800, 600), (600, 800)])
    def test_longest_edge_matches_the_spec_dimension(self, size, tmp_path, _mk_src):
        """A 4:3 or 3:4 source scales exactly to a dimension divisible by 12.
        120 shares factors of both edge ratios, so scaled
        dimensions are integers & ratio compares exactly."""
        src, max_edge = _mk_src(tmp_path, size=size), 120
        spec = RenditionSpec(Format.JPEG, max_edge, 85)
        written = derive_rendition(src, tmp_path, self.STEM, spec)
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
            derive_rendition(src, tmp_path, self.STEM, spec)
        assert exc.value.src_path == src
        assert exc.value.dst_path == dest
        assert exc.value.spec == spec
        assert isinstance(exc.value.cause, OSError)

    def test_missing_source_raises_derive_error(self, tmp_path):
        """A source path with no file raises DeriveError."""
        src = tmp_path / "absent.jpg"
        spec = RenditionSpec(Format.JPEG, 6, 85)
        with pytest.raises(DeriveError) as exc:
            derive_rendition(src, tmp_path, self.STEM, spec)
        assert exc.value.src_path == src
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
            derive_rendition(src, tmp_path, self.STEM, spec)
        assert exc.value.spec == spec
        assert isinstance(exc.value.cause, OSError)


class _Recorder:
    """A stand-in generator that writes a stub file and records its calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[Path, Path, Path, RenditionSpec]] = []

    def __call__(
        self, src_path: Path, dest_dir: Path, stem: Path, spec: RenditionSpec
    ) -> Path:
        """Write a stub file, record the call, return the path written."""
        self.calls.append((src_path, dest_dir, stem, spec))
        path = dest_dir / f"{stem}.{spec.format.extension}"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"stub")
        return path


class TestDeriveAbsences:
    """Filling a sparse record from its shallowest present rendition."""

    def test_derives_every_deeper_absence(self, tmp_path, _mk_src):
        """Each absence deeper than the source is generated from it."""
        specs = {
            d: RenditionSpec(Format.WEBP, 120, 85)
            for d in (Derivation.DISPLAY, Derivation.PREVIEW, Derivation.THUMB)
        }
        src = _mk_src(tmp_path)
        rends = PicRenditions(Path("2026/a"), original=make_pic())
        filled = derive_absences(rends, specs, src, tmp_path, (gen := _Recorder()))
        assert [s for _, _, _, s in gen.calls] == list(specs.values())
        assert filled.absent == []

    def test_aliases_shallower_and_derives_deeper(self, tmp_path, _mk_src):
        """Shallower absences alias the source; deeper ones derive from it."""
        src = _mk_src(tmp_path)
        display = make_pic()
        rends = PicRenditions(Path("2026/a"), display=display)
        specs = {
            d: RenditionSpec(Format.WEBP, 120, 85)
            for d in (Derivation.ORIGINAL, Derivation.PREVIEW, Derivation.THUMB)
        }
        filled = derive_absences(rends, specs, src, tmp_path, (gen := _Recorder()))
        assert filled.original is display
        assert filled.display is display
        assert filled.preview is not display
        assert filled.thumb is not display
        expect = [tmp_path / "preview", tmp_path / "thumb"]
        assert [d for _, d, _, _ in gen.calls] == expect
        assert filled.absent == []
        assert all(s == src for s, _, _, _ in gen.calls)

    def test_aliases_every_shallower_absence(self, tmp_path, _mk_src):
        """A thumb-only record aliases all three shallower absences."""
        src = _mk_src(tmp_path)
        thumb = make_pic()
        rends = PicRenditions(Path("2026/a"), thumb=thumb)
        filled = derive_absences(rends, {}, src, tmp_path, (gen := _Recorder()))
        assert all(p is thumb for _, p in filled.present)
        assert gen.calls == []

    def test_a_full_record_generates_nothing(self, tmp_path, _mk_src):
        """A record with no absences returns unchanged without generating."""
        src = _mk_src(tmp_path)
        pics = {d.name.lower(): make_pic() for d in Derivation}
        rends = PicRenditions(Path("2026/a"), **pics)
        filled = derive_absences(rends, {}, src, tmp_path, (gen := _Recorder()))
        assert gen.calls == []
        assert filled == rends


class TestB3C32:
    """Pin library to its own conformance standard"""

    def test_b3c32_still_honors_its_contract(self):
        """The pinned b3c32 conforms; a bump breaking the surface fails here."""
        verify_conformance()
