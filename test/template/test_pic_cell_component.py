# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalIterable=false, reportCallIssue=false
from bs4 import BeautifulSoup
from unittest.mock import patch
from src.services.template_renderer import TemplateRenderer


def test_pic_cell_component_renders_basic_structure():
    """Test that pic-cell component renders with basic thumbnail structure"""
    with (
        patch(
            "src.services.template_renderer.is_dual_bucket_configured",
            return_value=True,
        ),
        patch("src.services.template_renderer.settings") as mock_settings,
    ):
        mock_settings.S3_PICS_ENDPOINT = "https://pics.example.com"
        mock_settings.S3_PICS_BUCKET = "test-bucket"

        renderer = TemplateRenderer()

        # Mock pic data for a single pic (needs to be wrapped in pic object)
        pic_data = {"pic": {"filename": "2024-06-15_14-30-45_wedding-ceremony.jpg"}}

        html = renderer.render("components/pic-cell.j2.html", pic_data)
        soup = BeautifulSoup(html, "html.parser")

        # Check for clickable image element
        img = soup.find("img")
        assert img is not None
        assert (
            "https://test-bucket.pics.example.com/thumb/2024-06-15_14-30-45_wedding-ceremony.jpg"
            in img["src"]
        )

        # Check for web link
        link = soup.find("a")
        assert link is not None
        assert (
            "https://test-bucket.pics.example.com/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
            in link["href"]
        )

        # TODO: Add Alpine.js click handler test after JS implementation
        # clickable_element = soup.find(attrs={'@click': True})
        # assert clickable_element is not None


def test_pic_cell_component_has_proper_alt_text():
    """Test that pic-cell has accessible alt text"""
    with (
        patch(
            "src.services.template_renderer.is_dual_bucket_configured",
            return_value=True,
        ),
        patch("src.services.template_renderer.settings") as mock_settings,
    ):
        mock_settings.S3_PICS_ENDPOINT = "https://pics.example.com"
        mock_settings.S3_PICS_BUCKET = "test-bucket"
        renderer = TemplateRenderer()

        pic_data = {"pic": {"filename": "2024-06-15_14-30-45_wedding-ceremony.jpg"}}

        html = renderer.render("components/pic-cell.j2.html", pic_data)
        soup = BeautifulSoup(html, "html.parser")

        img = soup.find("img")
        assert img is not None
        assert "alt" in img.attrs
        assert len(img["alt"]) > 0
        assert "Wedding pic" in img["alt"]


def test_pic_cell_component_includes_responsive_classes():
    """Test that pic-cell includes Tailwind responsive classes"""
    with (
        patch(
            "src.services.template_renderer.is_dual_bucket_configured",
            return_value=True,
        ),
        patch("src.services.template_renderer.settings") as mock_settings,
    ):
        mock_settings.S3_PICS_ENDPOINT = "https://pics.example.com"
        mock_settings.S3_PICS_BUCKET = "test-bucket"
        renderer = TemplateRenderer()

        pic_data = {"pic": {"filename": "2024-06-15_14-30-45_wedding-ceremony.jpg"}}

        html = renderer.render("components/pic-cell.j2.html", pic_data)
        soup = BeautifulSoup(html, "html.parser")

        # Check for responsive container with Tailwind classes
        container = soup.find(
            class_=lambda x: x
            and any(cls in x for cls in ["aspect-square", "cursor-pointer"])
        )
        assert container is not None

