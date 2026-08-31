# test/template/test_gallery_template.py
"""
Structural tests for the grid page and its components.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

from pathlib import Path

from bs4 import BeautifulSoup, Tag
from conftest import make_pic

from galleria.models.rendition import PicRenditions
from galleria.services.link import rendition_href
from galleria.services.template_renderer import TemplateRenderer


def _record(stem: str) -> PicRenditions:
    """A filled record whose paths carry their kinds."""
    return PicRenditions(
        Path(stem),
        original=make_pic(relative_path=Path(f"original/{stem}.jpg")),
        display=make_pic(relative_path=Path(f"display/{stem}.webp")),
        preview=make_pic(relative_path=Path(f"preview/{stem}.jpg")),
        thumb=make_pic(relative_path=Path(f"thumb/{stem}.webp")),
    )


def _page(pics, page=1, pages=1, total=None) -> BeautifulSoup:
    """Render gallery.j2.html with the context build_gallery supplies."""
    ctx = {
        "collection": "wedding",
        "pics": pics,
        "page": page,
        "pages": pages,
        "total": len(pics) if total is None else total,
        "root": "../..",
    }
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
        """Exactly one grid container renders, carrying the grid class."""
        assert len(_page([_record("a")]).select(".grid")) == 1

    def test_cell_links_the_per_photo_page(self):
        """Each cell's anchor targets pic/STEM.html, never an image."""
        soup = _page([_record("a"), _record("b")])
        hrefs = [a["href"] for a in soup.select(".pic-cell a")]
        assert hrefs == ["pic/a.html", "pic/b.html"]

    def test_thumb_src_is_the_thumb_rendition(self):
        """Each img src is root plus the thumb href, never display or original."""
        rec = _record("a")
        assert rec.thumb is not None
        src = str(_one(_page([rec]), ".pic-cell img")["src"])
        assert src == f"../../{rendition_href('wedding', rec.thumb)}"
        assert "/thumb/" in src

    def test_cells_follow_record_order(self):
        """Cells render in list order, which is merge order."""
        soup = _page([_record("b"), _record("a")])
        hrefs = [a["href"] for a in soup.select(".pic-cell a")]
        assert hrefs == ["pic/b.html", "pic/a.html"]

    def test_navbar_counts_the_collection(self):
        """The navbar count is the collection total, not the page size."""
        soup = _page([_record("a")], total=645)
        assert _one(soup, ".pic-count").get_text(strip=True) == "645 photos"

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
        """Every cell fixes its aspect so arriving images do not reflow the grid."""
        soup = _page([_record("a")])
        assert "aspect-square" in _one(soup, ".pic-cell a")["class"]


class TestPicPage:
    """The per-photo page: display rendition, original, download, neighbors."""

    def test_shows_the_display_rendition(self):
        """The main img src is root plus the display href."""
        rec = _record("a")
        assert rec.display is not None
        src = str(_one(_pic_page(rec), ".pic-display img")["src"])
        assert src == f"../../../{rendition_href('wedding', rec.display)}"

    def test_links_the_original_separately(self):
        """The original is reached by its own anchor, not the display img."""
        rec = _record("a")
        assert rec.original is not None
        href = str(_one(_pic_page(rec), "a.pic-original")["href"])
        assert href == f"../../../{rendition_href('wedding', rec.original)}"

    def test_download_link_is_marked_download(self):
        """The download anchor targets the original and carries download."""
        rec = _record("a")
        assert rec.original is not None
        tag = _one(_pic_page(rec), "a.pic-download")
        assert str(tag["href"]) == f"../../../{rendition_href('wedding', rec.original)}"
        assert tag.has_attr("download")

    def test_aliased_original_degrades_to_display(self):
        """With no manifested original both links resolve to the display path."""
        display = make_pic(relative_path=Path("display/a.webp"))
        rec = PicRenditions(Path("a"), original=display, display=display)
        soup = _pic_page(rec)
        original = str(_one(soup, "a.pic-original")["href"])
        assert original == str(_one(soup, "a.pic-download")["href"])
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

    def test_no_root_absolute_links(self):
        """No anchor or image points at a root-absolute or remote path."""
        soup = _pic_page(_record("b"), prev=_record("a"), next=_record("c"))
        urls = [str(a["href"]) for a in soup.select("a")]
        urls += [str(i["src"]) for i in soup.select("img")]
        assert urls and not any(u.startswith(("/", "http")) for u in urls)
