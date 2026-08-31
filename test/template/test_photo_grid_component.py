# pyright: reportArgumentType=false, reportOptionalMemberAccess=false, reportOptionalIterable=false, reportCallIssue=false, reportOperatorIssue=false
from bs4 import BeautifulSoup
from galleria.services.template_renderer import TemplateRenderer


def test_pic_grid_component_renders_container():
    """Test that pic-grid component renders a container div"""
    renderer = TemplateRenderer()

    context = {
        "pics": [],
        "grid_classes": "grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4 p-4",
    }

    html = renderer.render("components/pic-grid.j2.html", context)
    soup = BeautifulSoup(html, "html.parser")

    # Check for grid container
    grid_container = soup.find("div", class_=lambda x: x and "grid" in x)
    assert grid_container is not None

    # Check that it has responsive classes
    classes = grid_container.get("class", [])
    assert any("grid-cols" in cls for cls in classes)


def test_pic_grid_component_is_configurable():
    """Test that pic-grid accepts custom CSS classes"""
    renderer = TemplateRenderer()

    custom_classes = "grid grid-cols-3 gap-2 p-2"
    context = {"pics": [], "grid_classes": custom_classes}

    html = renderer.render("components/pic-grid.j2.html", context)
    soup = BeautifulSoup(html, "html.parser")

    grid_container = soup.find("div")
    assert grid_container is not None

    # Check that custom classes are applied
    container_classes = " ".join(grid_container.get("class", []))
    assert "grid-cols-3" in container_classes
    assert "gap-2" in container_classes
    assert "p-2" in container_classes
