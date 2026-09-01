"""
Build command for Galleria.

Generates static website from processed photos.
"""

from pathlib import Path
import shutil

import click

from galleria.config import Config
from galleria.command.option import derive_options
from galleria.command.validate import resolve_inputs
from galleria.models.rendition import PicRenditions
from galleria.services.derive import (
    CollectionDeriveError,
    adopt_rendition,
    derive_rendition,
    derive_collection,
)
from galleria.services.rendition import merge_variants
from galleria.services.template_renderer import TemplateRenderer


def build_gallery(cfg: Config, collection: str, records: list[PicRenditions]) -> None:
    """Render the collection's pages under output_dir/gallery/COLLECTION.

    Records are sliced into pages of cfg.page_size in the order given,
    which is merge order. An empty collection still writes page1.html.
    index.html is a byte copy of page1.html. Every page renders from
    two levels below the site root, so templates prefix hrefs with
    root. A missing or broken template raises; there is no silent
    partial build.
    """
    renderer = TemplateRenderer()
    site_dir = cfg.output_dir / "gallery" / collection
    size = cfg.page_size
    pages = [records[i : i + size] for i in range(0, len(records), size)] or [[]]
    for n, page in enumerate(pages, start=1):
        ctx = {
            "collection": collection,
            "pics": page,
            "page": n,
            "pages": len(pages),
            "total": len(records),
            "root": "../..",
        }
        renderer.save_html(
            renderer.render("gallery.j2.html", ctx), site_dir / f"page{n}.html"
        )
    shutil.copyfile(site_dir / "page1.html", site_dir / "index.html")
    for i, rec in enumerate(records):
        ctx = {
            "collection": collection,
            "pic": rec,
            "prev": records[i - 1] if i > 0 else None,
            "next": records[i + 1] if i + 1 < len(records) else None,
            "total": len(records),
            "root": "../../..",
        }
        html = renderer.render("pic.j2.html", ctx)
        renderer.save_html(html, site_dir / "pic" / f"{rec.key.name}.html")


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
    manifest = manifest_o or manifest_d
    assert manifest is not None, "resolve_inputs guarantees a manifest"
    name = manifest.collection_name
    if validate:
        renditions = merge_variants(manifest_o, manifest_d)
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
    build_gallery(cfg, name, records)
