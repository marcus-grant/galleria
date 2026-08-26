"""
Build command for Galleria.

Generates static website from processed photos.
"""

import click
from pathlib import Path

from galleria.command.option import manifest_options
from galleria.command.validate import resolve_inputs
from galleria.services.site_generator import (
    check_source_directory,
    check_source_subdirectories,
    create_output_directory_structure,
)
from galleria.services.template_renderer import TemplateRenderer


def build_gallery():
    """Pure function that orchestrates gallery building services.

    Returns:
        Dict with build results: {
            'success': bool,
            'photos_processed': int,
            'gallery_generated': bool
        }
    """
    # Create output directory structure
    create_output_directory_structure(Path.cwd())

    # Generate pic metadata
    pic_data = {"pics": []}
    # Use gallery metadata file if it exists, otherwise scan files directly
    # metadata_file = Path("prod/pics/gallery-metadata.json")
    pics_count = len(pic_data["pics"])
    gallery_generated = False

    if pic_data["pics"]:
        # Render templates
        renderer = TemplateRenderer()

        # Generate gallery page
        gallery_template = Path("src/galleria/template/gallery.j2.html")
        if gallery_template.exists():
            gallery_html = renderer.render("gallery.j2.html", pic_data)
            renderer.save_html(gallery_html, "prod/site/gallery.html")
            gallery_generated = True

        # Generate index page
        index_template = Path("src/galleria/template/index.j2.html")
        if index_template.exists():
            index_html = renderer.render("index.j2.html", pic_data)
            renderer.save_html(index_html, "prod/site/index.html")

    return {
        "success": True,
        "pics_processed": pics_count,
        "gallery_generated": gallery_generated,
    }


@click.command()
@manifest_options
@click.option("--output-dir", type=click.Path(path_type=Path))
def build(
    original_manifest: Path | None,
    display_manifest: Path | None,
    output_dir: Path | None,
) -> None:
    """Build static photo gallery site from processed photos."""
    cfg, manifest_o, manifest_d = resolve_inputs(
        original_manifest, display_manifest, output_dir
    )
    click.echo("Generating static site...")
    build_gallery()
    click.echo("Generating static site...")

    # Check source directory
    base_dir = Path.cwd()
    click.echo("Checking source directory: prod/pics")

    if not check_source_directory(base_dir):
        click.echo("Source directory not found: prod/pics")
    else:
        # Check subdirectories
        subdirs = check_source_subdirectories(base_dir)
        missing = [name for name, exists in subdirs.items() if not exists]

        if missing:
            click.echo(f"Missing subdirectories: {', '.join(missing)}")
        else:
            click.echo("All source directories found")

    # Call the pure build function
    click.echo("Creating output directory structure: prod/site")
    result = build_gallery()

    # Report results
    if result["success"]:
        click.echo(f"Found {result['pics_processed']} pics")
        if result["gallery_generated"]:
            click.echo("Gallery page created: prod/site/gallery.html")
            click.echo("Index page created: prod/site/index.html")
        else:
            click.echo("No photos found to generate gallery")
        click.echo("Build complete!")
    else:
        click.echo("Build failed!")
        SystemExit(1)
