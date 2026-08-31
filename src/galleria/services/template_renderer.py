# src/galleria/services/template_renderer.py
"""
Jinja rendering of the packaged templates.
Author: Marcus Grant
Created: 2026-08-31
License: AGPL-3.0-or-later
"""

from pathlib import Path

from jinja2 import Environment, FileSystemLoader

from galleria.services.link import rendition_href

TEMPLATE_DIR = Path(__file__).resolve().parent.parent / "template"


class TemplateRenderer:
    """Render templates shipped inside the galleria package."""

    def __init__(self) -> None:
        """Load templates from the package, independent of cwd."""
        self.env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))
        self.env.globals["href"] = rendition_href

    def render(self, template_path: str, context: dict) -> str:
        """Render one template with the given context."""
        return self.env.get_template(template_path).render(context)

    def render_gallery(self, pic_data: dict) -> str:
        """Render the gallery template."""
        return self.render("gallery.j2.html", pic_data)

    def save_html(self, html_content: str, output_path: Path) -> None:
        """Write rendered HTML, creating parent directories."""
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(html_content)
