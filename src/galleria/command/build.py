"""
Build command for Galleria.

Generates static website from processed photos.
"""

from datetime import datetime, timezone
from pathlib import Path
import shutil

import click

from galleria.config import Config
from galleria.command.option import derive_options
from galleria.command.validate import resolve_inputs
from galleria.models.normpic import Pic
from galleria.models.spec import RenditionSpec
from galleria.models.rendition import Derivation, PicRenditions
from galleria.services.derive import (
    CollectionDeriveError,
    adopt_rendition,
    derive_rendition,
    derive_collection,
)
from galleria.services.grid_index import write_grid_index
from galleria.services.rendition import merge_variants
from galleria.services.stylesheet import emit_stylesheets
from galleria.services.template_renderer import TemplateRenderer

SENTINEL = "__STEM__"


def sentinel_record(specs: dict[Derivation, RenditionSpec]) -> PicRenditions:
    """A placeholder record whose stem-derived paths carry SENTINEL.

    Rendered once into page 1's cell template for the scroll script
    to clone and fill. Its thumb path is named the way derive names
    thumbs, kind directory plus key plus the configured thumb spec's
    extension, so the template cell resolves exactly like a real one.
    Other renditions are absent; the cell reads only key and thumb.
    """
    ext = specs[Derivation.THUMB].format.extension
    rel = Path("thumb") / f"{SENTINEL}.{ext}"
    mtime = datetime.fromtimestamp(0, tz=timezone.utc)
    thumb = Pic(hash="", relative_path=rel, size_bytes=0, mtime=mtime)
    return PicRenditions(Path(SENTINEL), thumb=thumb)


def build_gallery(cfg: Config, collection: str, records: list[PicRenditions]) -> str:
    """Render the collection's pages under output_dir/gallery/COLLECTION.

    Records are sliced into pages of cfg.page_size in the order given,
    which is merge order. An empty collection still writes page1.html.
    index.html is a byte copy of page1.html. Every page renders from
    two levels below the site root, so templates prefix hrefs with
    root. The stylesheets are emitted flat beside the pages, and every
    page links them by name through the asset map, prefixed with
    asset_base for the pic/ depth. A missing or broken template raises; there is no silent
    partial build. The grid index artifact is written beside the pages
    first; its file name is returned and given to each grid page as
    grid_index.
    """
    renderer = TemplateRenderer()
    site_dir = cfg.output_dir / "gallery" / collection
    site_dir.mkdir(parents=True, exist_ok=True)
    grid_index = write_grid_index(site_dir, records, cfg.artifact_name_length)
    asset = emit_stylesheets(site_dir, cfg.artifact_name_length)
    size = cfg.page_size
    sentinel = sentinel_record(cfg.specs)
    pages = [records[i : i + size] for i in range(0, len(records), size)] or [[]]
    for n, page in enumerate(pages, start=1):
        ctx = {  # Thumbnail grid context
            "collection": collection,
            "pics": page,
            "page": n,
            "pages": len(pages),
            "total": len(records),
            "root": "../..",
            "grid_index": grid_index,
            "sentinel_pic": sentinel,
            "load_ahead_viewports": cfg.load_ahead_viewports,
            "page_size": cfg.page_size,
            "asset": asset,
            "asset_base": "",
            "stylesheet_url": cfg.stylesheet_url,
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
            "asset": asset,
            "asset_base": "../",
            "stylesheet_url": cfg.stylesheet_url,
        }
        html = renderer.render("pic.j2.html", ctx)
        renderer.save_html(html, site_dir / "pic" / f"{rec.key.name}.html")
    return grid_index


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
