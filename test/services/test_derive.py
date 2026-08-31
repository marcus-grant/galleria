# test/services/test_derive.py
"""
Tests for single-rendition derivation.
Author: Marcus Grant
Created: 2026-08-27
License: AGPL-3.0-or-later
"""

import json
from pathlib import Path
import re

from b3c32 import verify_conformance
import pytest
from PIL import Image

from conftest import make_pic
from galleria.config.default import RENDITION_SPECS
from galleria.models.spec import Format, RenditionSpec
from galleria.models.rendition import Derivation, PicRenditions
from galleria.services.derive import (
    CollectionDeriveError,
    DeriveError,
    adopt_rendition,
    derive_absences,
    derive_collection,
    derive_rendition,
)
from galleria.services.manifest_reader import read_manifest


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


def _write_collection(
    manifest_path: Path,
    root: Path,
    names: list[Path],
    size: tuple[int, int] = (800, 600),
) -> Path:
    """Write a manifest and the real images it names under root.

    Duplicated from test/command/test_derive.py deliberately: the
    clean conftest version demands the derive-pipeline or orphan
    removal scope. Centralize or replace when NormPic ships a
    consumer package with test factories.
    DELETEME once appropriate PR centralizes this helper which is duped
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


class TestDeriveCollection:
    """derive_collection fills merged records and aggregates failures."""

    def test_fills_every_record_in_merge_order(self, tmp_path):
        """A clean collection returns one filled record per photo, in order."""
        names = [Path("a.jpg"), Path("b.jpg")]
        manifest = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        records = derive_collection(
            manifest_o=read_manifest(manifest),
            manifest_d=None,
            specs=RENDITION_SPECS,
            output_dir=tmp_path / "_build",
        )
        assert [r.key for r in records] == [Path("a"), Path("b")]
        assert all(r.absent == [] for r in records)

    def test_derive_error_fails_that_record_and_continues(self, tmp_path):
        """A DeriveError on one record does not stop the others filling."""
        names = [Path("a.jpg"), Path("b.jpg")]
        manifest = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        (tmp_path / "src" / "a.jpg").write_text("not an image")
        with pytest.raises(CollectionDeriveError) as e:
            derive_collection(
                manifest_o=read_manifest(manifest),
                manifest_d=None,
                specs=RENDITION_SPECS,
                output_dir=tmp_path / "_build",
            )
        assert [r.key for r in e.value.records] == [Path("b")]
        assert all(r.absent == [] for r in e.value.records)

    def test_failures_raise_after_the_loop_with_partials(self, tmp_path):
        """CollectionDeriveError carries failures and the records that filled."""
        names = [Path("a.jpg"), Path("b.jpg")]
        manifest = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        (tmp_path / "src" / "a.jpg").write_text("not an image")
        with pytest.raises(CollectionDeriveError) as e:
            derive_collection(
                manifest_o=read_manifest(manifest),
                manifest_d=None,
                specs=RENDITION_SPECS,
                output_dir=tmp_path / "_build",
            )
        assert len(e.value.failures) == 1
        assert "a.jpg" in e.value.failures[0]
        assert len(e.value.records) == 1

    def test_empty_manifests_fill_nothing_and_raise_nothing(self):
        """Two absent manifests produce an empty record list."""
        records = derive_collection(
            manifest_o=None,
            manifest_d=None,
            specs=RENDITION_SPECS,
            output_dir=Path("unused"),
        )
        assert records == []


class TestAdoptRendition:
    """adopt_rendition predicts paths and never encodes."""

    def test_returns_the_path_derive_would_write(self, tmp_path, _mk_src):
        """Adoption after a real derive returns the identical path."""
        src, dst = _mk_src(tmp_path), tmp_path / "out"
        spec = RENDITION_SPECS[Derivation.THUMB]
        written = derive_rendition(src, dst, Path("derived"), spec)
        adopted = adopt_rendition(src, dst, Path("derived"), spec)
        assert adopted == written

    def test_missing_file_raises_derive_error(self, tmp_path):
        """A rendition absent on disk raises, naming the expected path."""
        spec = RENDITION_SPECS[Derivation.THUMB]
        src, dst = tmp_path / "src.jpg", tmp_path / "dst"
        with pytest.raises(DeriveError, match="derived.webp"):
            adopt_rendition(src, dst, Path("derived"), spec)

    def test_adopting_reads_real_file_metadata(self, tmp_path, _mk_src):
        """derive_collection with adopt fills Pics from the on-disk files."""
        names = [Path("a.jpg")]
        manifest = _write_collection(tmp_path / "m.json", tmp_path / "src", names)
        manifest_o = read_manifest(manifest)
        args = (manifest_o, None, RENDITION_SPECS, tmp_path / "_build")
        derived = derive_collection(*args)
        adopted = derive_collection(*args, generate=adopt_rendition)
        assert adopted == derived


class TestB3C32:
    """Pin library to its own conformance standard"""

    def test_b3c32_still_honors_its_contract(self):
        """The pinned b3c32 conforms; a bump breaking the surface fails here."""
        verify_conformance()
