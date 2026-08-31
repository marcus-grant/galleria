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
