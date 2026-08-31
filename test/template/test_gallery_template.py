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
