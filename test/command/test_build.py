# test/command/test_build.py
"""
The build command's CLI surface.
Author: Marcus Grant
License: AGPL-3.0-or-later
"""

from dataclasses import replace
from importlib import resources
import json
from pathlib import Path
from unittest.mock import patch

import b3c32
from bs4 import BeautifulSoup as BSoup
from click.testing import CliRunner
from PIL import Image

from galleria.cli import cli
from galleria.config import Config
from galleria.config.default import RENDITION_SPECS
from galleria.command.build import build_gallery
from galleria.models.rendition import Derivation
from galleria.models.spec import Format
from galleria.services.derive import derive_collection
from galleria.services.manifest_reader import read_manifest
from galleria.services.template_renderer import TemplateRenderer


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
    return len(BSoup(path.read_text(), "html.parser").select("img:not(template *)"))


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

    def test_writes_a_page_per_record(self, tmp_path: Path):
        """Every record gets gallery/COLLECTION/pic/STEM.html."""
        man, out, records = _records(tmp_path, 3)
        build_gallery(_cfg(man, out, 2), "wedding", records)
        pic_dir = out / "gallery" / "wedding" / "pic"
        expected = [f"{r.key.name}.html" for r in records]
        assert sorted(p.name for p in pic_dir.glob("*.html")) == expected


class TestBuildGalleryScrollContext:
    """build_gallery supplies page 1 everything the scroll hooks read."""

    def test_page_one_renders_its_cell_template(self, tmp_path: Path):
        """A real build renders page 1 with the sentinel cell template."""
        man, out, recs = _records(tmp_path, 1)
        build_gallery(_cfg(man, out, 2), "wedding", recs)
        page1 = out / "gallery" / "wedding" / "page1.html"
        soup = BSoup(page1.read_text(), "html.parser")
        assert soup.select_one("template .pic-cell") is not None

    def test_template_thumb_follows_the_thumb_spec(self, tmp_path: Path):
        """The template cell's thumb extension comes from the thumb spec."""
        man, out, recs = _records(tmp_path, 1)
        cfg = _cfg(man, out, 2)
        thumb = replace(cfg.specs[Derivation.THUMB], format=Format.PJPEG)
        cfg = replace(cfg, specs={**cfg.specs, Derivation.THUMB: thumb})
        build_gallery(cfg, "wedding", recs)
        page1 = out / "gallery" / "wedding" / "page1.html"
        soup = BSoup(page1.read_text(), "html.parser")
        img = soup.select_one("template .pic-cell img")
        assert img is not None
        assert str(img["src"]).endswith("/thumb/__STEM__.jpg")

    def test_page_one_carries_configured_scroll_settings(self, tmp_path: Path):
        """Load-ahead and page size on page 1 are the Config values."""
        man, out, recs = _records(tmp_path, 1)
        cfg = replace(_cfg(man, out, 2), load_ahead_viewports=3)
        build_gallery(cfg, "wedding", recs)
        page1 = out / "gallery" / "wedding" / "page1.html"
        soup = BSoup(page1.read_text(), "html.parser")
        hooks = soup.select_one("[data-grid-index]")
        assert hooks is not None
        assert hooks["data-load-ahead"] == "3"
        assert hooks["data-page-size"] == "2"


class TestBuildGalleryGridIndex:
    """The grid index artifact written beside the pages."""

    collection = "wedding"  # the name _write_collection gives its manifest

    def _site(self, out: Path) -> Path:
        """The collection's gallery directory under out."""
        return out / "gallery" / self.collection

    def _artifacts(self, out: Path) -> list[Path]:
        """Grid index artifacts beside the pages."""
        return sorted(self._site(out).glob("grid-index-*.json"))

    def _rendered_stems(self, out: Path) -> list[str]:
        """Pic page stems linked from each page's cells, in page order."""
        stems = []
        for page in sorted(self._site(out).glob("page*.html")):
            soup = BSoup(page.read_text(), "html.parser")
            stems += [
                Path(str(a["href"])).stem
                for a in soup.select(".pic-cell:not(template *) a")
            ]
        return stems

    def test_order_matches_rendered_pages(self, tmp_path: Path):
        """The artifact lists photos in the order the pages show them."""
        man, out, records = _records(tmp_path, 12)
        build_gallery(_cfg(man, out, 5), self.collection, records)
        (artifact,) = self._artifacts(out)
        assert json.loads(artifact.read_text()) == self._rendered_stems(out)

    def test_name_length_comes_from_config(self, tmp_path: Path):
        """A configured length, not a fixed one, sizes the name's code."""
        man, out, records = _records(tmp_path, 3)
        cfg = replace(_cfg(man, out, 2), artifact_name_length=5)
        name = build_gallery(cfg, self.collection, records)
        assert len(Path(name).stem.removeprefix("grid-index-")) == 5

    def test_returns_the_artifact_name(self, tmp_path: Path):
        """The caller learns the written file's name from the return."""
        man, out, records = _records(tmp_path, 3)
        name = build_gallery(_cfg(man, out, 2), self.collection, records)
        assert [p.name for p in self._artifacts(out)] == [name]

    def test_grid_pages_get_the_name_in_context(self, tmp_path: Path):
        """Every grid page renders with the artifact name available."""
        man, out, records = _records(tmp_path, 3)
        real = TemplateRenderer.render
        with patch.object(TemplateRenderer, "render", autospec=True) as spy:
            spy.side_effect = real
            name = build_gallery(_cfg(man, out, 2), self.collection, records)
        grid = [c.args[2] for c in spy.call_args_list if c.args[1] == "gallery.j2.html"]
        assert [ctx["grid_index"] for ctx in grid] == [name, name]


def _packaged(*parts: str) -> Path:
    """Path of a file shipped inside the galleria package."""
    return Path(str(resources.files("galleria").joinpath(*parts)))


def _stylesheet_links(page: Path) -> list[str]:
    """Hrefs of the page's stylesheet links, in document order."""
    soup = BSoup(page.read_text(), "html.parser")
    return [str(link["href"]) for link in soup.select("link[rel=stylesheet]")]


class TestStylesheets:
    """Pico and the gallery stylesheet, emitted and linked on every page."""

    collection = "wedding"
    url = "https://cdn.example.test/g.css?v=1&x=2"

    def _build(self, tmp_path: Path, **overrides) -> Path:
        """Build two pics and return the collection's site directory."""
        man, out, records = _records(tmp_path, 2)
        cfg = replace(_cfg(man, out, 5), **overrides)
        build_gallery(cfg, self.collection, records)
        return out / "gallery" / self.collection

    def _pages(self, site: Path) -> list[Path]:
        """One page at each depth: a grid page and a per-photo page."""
        return [site / "page1.html", site / "pic" / "000.html"]

    def test_both_stylesheets_are_emitted_by_content(self, tmp_path: Path):
        """Each name is its stem plus the code prefix of its source file."""
        site = self._build(tmp_path)
        pico = b3c32.code_from_path(_packaged("vendor", "pico", "pico.min.css"), 120)
        gallery = b3c32.code_from_path(_packaged("asset", "gallery.css"), 120)
        expected = [f"gallery-{gallery[:8]}.css", f"pico-{pico[:8]}.css"]
        assert sorted(p.name for p in site.glob("*.css")) == expected

    def test_links_resolve_to_emitted_files_at_both_depths(self, tmp_path: Path):
        """Relative hrefs reach a real file from a grid page and from pic/."""
        site = self._build(tmp_path)
        for page in self._pages(site):
            links = _stylesheet_links(page)
            assert len(links) == 2
            assert all((page.parent / href).is_file() for href in links)

    def test_pico_is_linked_before_the_gallery_stylesheet(self, tmp_path: Path):
        """The gallery stylesheet comes second, so it can override Pico."""
        site = self._build(tmp_path)
        for page in self._pages(site):
            first, second = _stylesheet_links(page)
            assert Path(first).name.startswith("pico-")
            assert Path(second).name.startswith("gallery-")

    def test_set_url_is_linked_verbatim_at_both_depths(self, tmp_path: Path):
        """A configured URL replaces the local link, unescaped."""
        site = self._build(tmp_path, stylesheet_url=self.url)
        for page in self._pages(site):
            assert f'href="{self.url}"' in page.read_text()
            assert _stylesheet_links(page)[1] == self.url

    def test_set_url_keeps_the_local_pico_link(self, tmp_path: Path):
        """Pico is linked locally whether or not a URL is set."""
        site = self._build(tmp_path, stylesheet_url=self.url)
        for page in self._pages(site):
            first, second = _stylesheet_links(page)
            assert (page.parent / first).is_file()
            assert Path(first).name.startswith("pico-")
            assert not Path(second).name.startswith("gallery-")

    def test_set_url_still_emits_the_local_gallery_stylesheet(self, tmp_path: Path):
        """The local copy is written either way, so output has one shape."""
        site = self._build(tmp_path, stylesheet_url=self.url)
        assert len(list(site.glob("gallery-*.css"))) == 1

    def test_rebuild_leaves_one_of_each_stylesheet(self, tmp_path: Path):
        """A rebuild into the same directory does not accumulate copies."""
        self._build(tmp_path)
        site = self._build(tmp_path)
        assert len(list(site.glob("pico-*.css"))) == 1
        assert len(list(site.glob("gallery-*.css"))) == 1


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
