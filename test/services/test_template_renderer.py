# test/services/test_template_renderer.py
"""
Tests for the packaged template renderer.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

from pathlib import Path

from galleria.services.template_renderer import TEMPLATE_DIR, TemplateRenderer


class TestTemplateRenderer:
    """Loading and writing independent of the working directory."""

    def test_loads_templates_from_the_package(self, tmp_path: Path, monkeypatch):
        """Rendering works with cwd anywhere, because the loader is package-relative."""
        monkeypatch.chdir(tmp_path)
        assert (TEMPLATE_DIR / "gallery.j2.html").is_file()
        html = TemplateRenderer().render("base.j2.html", {})
        assert "<html" in html

    def test_save_html_creates_parent_directories(self, tmp_path: Path):
        """save_html writes the content, creating missing parents."""
        target = tmp_path / "gallery" / "wedding" / "page1.html"
        TemplateRenderer().save_html("<html></html>", target)
        assert target.read_text() == "<html></html>"
