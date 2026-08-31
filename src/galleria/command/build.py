"""
Build command for Galleria.

Generates static website from processed photos.
"""

import click
from pathlib import Path

from galleria.command.option import derive_options
from galleria.command.validate import resolve_inputs
from galleria.services.derive import (
    CollectionDeriveError,
    adopt_rendition,
    derive_rendition,
    derive_collection,
)
from galleria.services.rendition import merge_variants
from galleria.services.site_generator import create_output_directory_structure
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
@derive_options
@click.option("--derive/--no-derive", default=False)
@click.option("--validate/--no-validate", default=False)
def build(
    original_manifest: Path | None,
    display_manifest: Path | None,
    output_dir: Path | None,
    derive: bool,
    validate: bool,
) -> None:
    """Build the static gallery site from derived renditions.

    Both flags default off while a full derive run has no
    incremental skip; the derive default flips to opt-out when
    ref/derive-pipeline lands. With --derive, missing renditions
    are encoded; without it they are adopted from a prior derive
    run, and a missing file stops the build. With --validate, the
    merge report prints before building.
    """
    cfg, manifest_o, manifest_d = resolve_inputs(
        original_manifest, display_manifest, output_dir
    )
    if validate:
        renditions = merge_variants(manifest_o, manifest_d)
        manifest = manifest_o or manifest_d
        name = manifest.collection_name if manifest else None
        click.echo(f"Valid config, tracking {len(renditions)} pics of {name}.")
    generate = derive_rendition if derive else adopt_rendition
    try:
        records = derive_collection(
            manifest_o, manifest_d, cfg.specs, cfg.output_dir, generate
        )
    except CollectionDeriveError as e:
        for failure in e.failures:
            click.echo(failure, err=True)
        if not derive:
            click.echo("Missing renditions; re-run derive.", err=True)
            raise SystemExit(1)
        records = e.records
    click.echo(f"Tracking {len(records)} pics.")
    click.echo("Generating static site...")
    build_gallery()
