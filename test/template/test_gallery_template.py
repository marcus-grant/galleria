# test/template/test_gallery_template.py
"""
Structural tests for the grid page and its components.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

import posixpath
from pathlib import Path

import pytest
from bs4 import BeautifulSoup, Tag
from conftest import make_asset_context, make_pic

from galleria.config import default
from galleria.models.rendition import PicRenditions
from galleria.services.link import rendition_href
from galleria.services.template_renderer import TemplateRenderer

# A rendered grid cell. Page 1 also carries one inert cell inside a
# <template> for the scroll script to clone; html.parser does not
# treat template content as inert, so it would otherwise match.
GRID_CELL = ".pic-cell:not(template *)"

# The per-photo page's two action links, told apart by the download
# attribute rather than a hook class: only the download link carries it.
ORIGINAL_LINK = ".button-group a:not([download])"
DOWNLOAD_LINK = ".button-group a[download]"


def _record(stem: str) -> PicRenditions:
    """A filled record whose paths carry their kinds."""
    return PicRenditions(
        Path(stem),
        original=make_pic(relative_path=Path(f"original/{stem}.jpg")),
        display=make_pic(relative_path=Path(f"display/{stem}.webp")),
        preview=make_pic(relative_path=Path(f"preview/{stem}.jpg")),
        thumb=make_pic(relative_path=Path(f"thumb/{stem}.webp")),
    )


def _page(pics, **overrides) -> BeautifulSoup:
    """Render gallery.j2.html with the context build_gallery supplies.

    A base context mirrors build_gallery for a single-page
    collection, with total from pics and scroll settings from program
    defaults; each keyword override replaces one context key.
    """
    ctx = {
        **make_asset_context(),
        "collection": "wedding",
        "pics": pics,
        "page": 1,
        "pages": 1,
        "total": len(pics),
        "root": "../..",
        "grid_index": "grid-index-TEST0000.json",
        "load_ahead_viewports": default.LOAD_AHEAD_VIEWPORTS,
        "page_size": default.PAGE_SIZE,
        "sentinel_pic": _record("__STEM__"),
    }
    ctx.update(overrides)
    html = TemplateRenderer().render("gallery.j2.html", ctx)
    return BeautifulSoup(html, "html.parser")


def _one(soup: BeautifulSoup, selector: str) -> Tag:
    """The single element matching selector, asserted present."""
    tag = soup.select_one(selector)
    assert tag is not None, selector
    return tag


def _pic_page(rec, prev=None, next=None) -> BeautifulSoup:
    """Render pic.j2.html with the context build_gallery supplies."""
    ctx = {
        **make_asset_context(asset_base="../"),
        "collection": "wedding",
        "pic": rec,
        "prev": prev,
        "next": next,
        "total": 1,
        "root": "../../..",
    }
    html = TemplateRenderer().render("pic.j2.html", ctx)
    return BeautifulSoup(html, "html.parser")


class TestGalleryPage:
    """What other parts of the system depend on in the grid page."""

    def test_page_is_marked_noindex(self):
        """The head carries the robots noindex, nofollow meta."""
        soup = _page([])
        meta = soup.find("meta", {"name": "robots"})
        assert meta is not None and meta["content"] == "noindex, nofollow"

    def test_one_grid_container(self):
        """Exactly one grid container renders, carrying the grid block."""
        assert len(_page([_record("a")]).select(".pic-grid")) == 1

    def test_grid_does_not_use_picos_grid_class(self):
        """Pico defines .grid, so the grid takes its own block name."""
        assert _page([_record("a")]).select(".grid") == []

    def test_cell_links_the_per_photo_page(self):
        """Each cell's anchor targets pic/STEM.html, never an image."""
        soup = _page([_record("a"), _record("b")])
        hrefs = [a["href"] for a in soup.select(f"{GRID_CELL} a")]
        assert hrefs == ["pic/a.html", "pic/b.html"]

    def test_thumb_src_is_the_thumb_rendition(self):
        """Each img src is root plus the thumb href, never display or original."""
        rec = _record("a")
        assert rec.thumb is not None
        src = str(_one(_page([rec]), f"{GRID_CELL} img")["src"])
        assert src == f"../../{rendition_href('wedding', rec.thumb)}"
        assert "/thumb/" in src

    def test_cells_follow_record_order(self):
        """Cells render in list order, which is merge order."""
        soup = _page([_record("b"), _record("a")])
        hrefs = [a["href"] for a in soup.select(f"{GRID_CELL} a")]
        assert hrefs == ["pic/b.html", "pic/a.html"]

    def test_no_root_absolute_links(self):
        """No anchor or image points at a root-absolute or remote path."""
        soup = _page([_record("a")], page=2, pages=3)
        urls = [str(a["href"]) for a in soup.select("a")]
        urls += [str(i["src"]) for i in soup.select("img")]
        assert urls and not any(u.startswith(("/", "http")) for u in urls)

    def test_page_navigation_links_neighbors(self):
        """A middle page links prev and next; the ends omit the missing one."""
        soup = _page([_record("a")], page=2, pages=3)
        assert _one(soup, "a[rel=prev]")["href"] == "page1.html"
        assert _one(soup, "a[rel=next]")["href"] == "page3.html"
        assert _page([], page=1, pages=3).select_one("a[rel=prev]") is None
        assert _page([], page=3, pages=3).select_one("a[rel=next]") is None

    def test_cell_reserves_its_box(self):
        """Every cell's link carries the class the stylesheet gives the
        fixed aspect, so arriving images do not reflow the grid."""
        soup = _page([_record("a")])
        assert "pic-cell__link" in _one(soup, ".pic-cell a")["class"]


class TestNavbar:
    """The navbar renders on both page kinds and links home from each."""

    def test_counts_the_collection(self):
        """The navbar count is the collection total, not the page size."""
        soup = _page([_record("a")], total=645)
        count = _one(soup, ".navbar__count")
        assert count.get_text(strip=True) == "645 photos"

    @pytest.mark.parametrize(
        "soup, page_path",
        [
            (_page([_record("a")]), "gallery/wedding/page1.html"),
            (_pic_page(_record("a")), "gallery/wedding/pic/a.html"),
        ],
        ids=["grid page", "per-photo page"],
    )
    def test_title_link_lands_on_the_collection_index(
        self, soup: BeautifulSoup, page_path: str
    ):
        """The href, resolved from the page's own location, is the index."""
        href = str(_one(soup, ".navbar__title")["href"])
        here = posixpath.dirname(page_path)
        landed = posixpath.normpath(posixpath.join(here, href))
        assert landed == "gallery/wedding/index.html"


class TestScrollHooks:
    """Page 1 carries what the scroll script reads; later pages do not."""

    def test_page_one_carries_scroll_settings(self):
        """Page 1 exposes the grid index name, load-ahead, and page size.

        Values are the ones supplied in the render context, so the
        script never hard-codes them.
        """
        soup = _page(
            [_record("a")],
            grid_index="grid-index-ABCD1234.json",
            load_ahead_viewports=3,
            page_size=7,
        )
        assert (hooks := _one(soup, "[data-grid-index]"))["data-load-ahead"] == "3"
        assert hooks["data-grid-index"] == "grid-index-ABCD1234.json"
        assert hooks["data-page-size"] == "7"

    def test_later_pages_carry_no_scroll_settings(self):
        """Page 2 of a multi-page collection exposes none of them."""
        soup = _page(
            [_record("a")],
            page=2,
            pages=3,
            grid_index="grid-index-ABCD1234.json",
            load_ahead_viewports=3,
            page_size=7,
        )
        for attr in ("data-grid-index", "data-load-ahead", "data-page-size"):
            assert soup.select_one(f"[{attr}]") is None, attr

    def test_settings_sit_with_the_grid(self):
        """The script finds the settings from the grid container.
        One lookup reaches both the grid to append to and how to fill it."""
        soup = _page([_record("a"), _record("b")])
        hooks = _one(soup, "[data-grid-index]")
        cells = soup.select(GRID_CELL)
        assert cells
        for cell in cells:
            assert cell.parent is hooks


class TestCellTemplate:
    """Page 1 carries one inert cell for the script to clone."""

    def test_page_one_holds_a_cell_template(self):
        """Page 1 renders exactly one template holding one grid cell."""
        templates = _page([_record("a")]).select("template")
        assert len(templates) == 1
        assert len(templates[0].select(".pic-cell")) == 1

    def test_later_pages_hold_no_cell_template(self):
        """Page 2 renders no template, even with the placeholder given."""
        soup = _page([_record("a")], page=2, pages=3)
        assert soup.select_one("template") is None

    def test_template_cell_matches_a_real_cell(self):
        """The template cell has a real cell's tags, attributes, classes.
        Built by the same include, so it can differ from a real cell
        only where the stem appears."""
        soup = _page([_record("real-stem")])
        real = _one(soup, GRID_CELL)
        clone = _one(soup, "template .pic-cell")
        assert str(real).replace("real-stem", "__STEM__") == str(clone)


class TestPicPage:
    """The per-photo page: display rendition, original, download, neighbors."""

    def test_shows_the_display_rendition(self):
        """The main img src is root plus the display href."""
        rec = _record("a")
        assert rec.display is not None
        src = str(_one(_pic_page(rec), ".frame__img")["src"])
        assert src == f"../../../{rendition_href('wedding', rec.display)}"

    def test_links_the_original_separately(self):
        """The original is reached by its own anchor, not the display img."""
        rec = _record("a")
        assert rec.original is not None
        href = str(_one(_pic_page(rec), ORIGINAL_LINK)["href"])
        assert href == f"../../../{rendition_href('wedding', rec.original)}"

    def test_download_link_is_marked_download(self):
        """The download anchor targets the original and carries download."""
        rec = _record("a")
        assert rec.original is not None
        tag = _one(_pic_page(rec), DOWNLOAD_LINK)
        assert str(tag["href"]) == f"../../../{rendition_href('wedding', rec.original)}"
        assert tag.has_attr("download")

    def test_aliased_original_degrades_to_display(self):
        """With no manifested original both links resolve to the display path."""
        display = make_pic(relative_path=Path("display/a.webp"))
        rec = PicRenditions(Path("a"), original=display, display=display)
        soup = _pic_page(rec)
        original = str(_one(soup, ORIGINAL_LINK)["href"])
        assert original == str(_one(soup, DOWNLOAD_LINK)["href"])
        assert "/display/" in original and "/original/" not in original

    def test_neighbors_by_position(self):
        """Prev and next link the neighboring stems; ends omit the missing one."""
        soup = _pic_page(_record("b"), prev=_record("a"), next=_record("c"))
        assert str(_one(soup, "a[rel=prev]")["href"]) == "a.html"
        assert str(_one(soup, "a[rel=next]")["href"]) == "c.html"
        assert (
            _pic_page(_record("a"), next=_record("b")).select_one("a[rel=prev]") is None
        )
        assert (
            _pic_page(_record("b"), prev=_record("a")).select_one("a[rel=next]") is None
        )

    def test_every_control_is_a_button(self):
        """All five controls carry the button block, so none can drop out."""
        soup = _pic_page(_record("b"), prev=_record("a"), next=_record("c"))
        controls = soup.select(".pager a, .button-group a")
        assert len(controls) == 5
        assert all("button" in c.get_attribute_list("class") for c in controls)

    def test_no_root_absolute_links(self):
        """No anchor or image points at a root-absolute or remote path."""
        soup = _pic_page(_record("b"), prev=_record("a"), next=_record("c"))
        urls = [str(a["href"]) for a in soup.select("a")]
        urls += [str(i["src"]) for i in soup.select("img")]
        assert urls and not any(u.startswith(("/", "http")) for u in urls)
