# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalIterable=false, reportCallIssue=false, reportOperatorIssue=false, reportGeneralTypeIssues=false, reportOptionalSubscript=false
from bs4 import BeautifulSoup
from galleria.services.template_renderer import TemplateRenderer


def test_gallery_template_has_basic_structure():
    """Test that gallery template contains expected HTML structure"""
    renderer = TemplateRenderer()
    photo_data = {"photos": []}

    html = renderer.render("gallery.j2.html", photo_data)
    soup = BeautifulSoup(html, "html.parser")

    # Check for required meta tags
    assert soup.find("meta", {"name": "robots", "content": "noindex, nofollow"})
    assert soup.find("meta", {"name": "viewport"})

    # TODO: Not ready for Alpine.js tests - post-deployment feature
    # assert soup.find(attrs={'x-data': True})

    # Check for photo grid container
    assert soup.find(class_="grid")


def test_gallery_template_renders_pic_cells_when_pics_provided():
    """Test that gallery template includes pic-cell components for each pic"""
    from unittest.mock import patch

    with (
        patch(
            "galleria.services.template_renderer.is_dual_bucket_configured",
            return_value=True,
        ),
        patch("galleria.services.template_renderer.settings") as mock_settings,
    ):
        mock_settings.S3_PICS_ENDPOINT = "https://pics.example.com"
        mock_settings.S3_PICS_BUCKET = "test-bucket"

        renderer = TemplateRenderer()
        pic_data = {
            "pics": [
                {"filename": "2024-06-15_14-30-45_wedding-ceremony.jpg"},
                {"filename": "2024-06-15_14-32-10_wedding-rings.jpg"},
            ]
        }

        html = renderer.render("gallery.j2.html", pic_data)
        soup = BeautifulSoup(html, "html.parser")

        # Check that pic-cell components are rendered (images with click handlers)
        clickable_images = soup.find_all("img", src=lambda x: x and "thumb" in x)
        assert len(clickable_images) == 2

        # Verify URLs are constructed correctly with base URL
        thumb_img = soup.find("img", src=lambda x: x and "wedding-ceremony" in x)
        assert (
            thumb_img["src"]
            == "https://test-bucket.pics.example.com/thumb/2024-06-15_14-30-45_wedding-ceremony.jpg"
        )

        # Verify web links are constructed correctly
        web_link = soup.find("a", href=lambda x: x and "wedding-ceremony" in x)
        assert (
            web_link["href"]
            == "https://test-bucket.pics.example.com/web/2024-06-15_14-30-45_wedding-ceremony.jpg"
        )

    # TODO: Not ready for Alpine.js tests - post-deployment feature
    # click_elements = soup.find_all(attrs={'@click': True})
    # assert len(click_elements) >= 2


def test_gallery_template_uses_photo_grid_component():
    """Test that gallery template uses photo-grid component for structure"""
    renderer = TemplateRenderer()
    photo_data = {
        "photos": [
            {"filename": "test.jpg", "thumb_url": "/test.webp", "web_url": "/test.jpg"}
        ]
    }

    html = renderer.render("gallery.j2.html", photo_data)
    soup = BeautifulSoup(html, "html.parser")

    # Gallery should have only ONE grid container (from photo-grid component)
    grid_containers = soup.find_all(
        "div", class_=lambda x: x and "grid" in x and "grid-cols" in x
    )
    assert len(grid_containers) == 1

    # TODO: Not ready for Alpine.js tests - post-deployment feature
    # alpine_container = soup.find(attrs={'x-data': True})
    # grid_in_alpine = alpine_container.find('div', class_=lambda x: x and 'grid' in x)
    # assert grid_in_alpine is not None
