# Static Site Generation Architecture

## Template Structure

```
src/galleria/template/
-> base.j2.html             (Base layout with head, stylesheets, navbar)
-> gallery.j2.html          (Grid page extending base, with the pager)
-> pic.j2.html              (Per-photo page extending base)
-> components/
   -> navbar.j2.html        (Collection title and photo count)
   -> pic-grid.j2.html      (Grid container)
   -> pic-cell.j2.html      (One thumbnail cell, linking its photo page)
   -> grid-scroll.j2.html   (Cell template and infinite-scroll script)
```

## Build Process

1. **Photo Metadata Generation**: `PhotoMetadataService.generate_json_metadata()`
2. **Template Rendering**: Jinja2 with photo data context
3. **Output**: Complete static site in the output directory

## Configuration

```python
# Build command configuration
TEMPLATE_DIR = 'src/template/'

# Template mapping
TEMPLATES = {
    'index.j2.html': 'index.html',
    'gallery.j2.html': 'gallery.html',
}

# Photo metadata source
PHOTO_METADATA_SOURCE = 'json'  # Generated from processed photos
```

## Directory Structure

### Input Structure

```txt
src/galleria/template/
  base.j2.html              # Base layout
  gallery.j2.html           # Grid page
  pic.j2.html               # Per-photo page
  components/
    navbar.j2.html          # Collection title and photo count
    pic-grid.j2.html        # Grid container
    pic-cell.j2.html        # One thumbnail cell
    grid-scroll.j2.html     # Cell template and infinite-scroll script
```

### Output Structure

```txt
<output-dir>/                       # Generated static site
  gallery/COLLECTION/
    page1.html ... pageN.html       # Grid pages
    index.html                      # Byte copy of page1.html
    pic/KEY.html                    # One page per photo, KEY its basename
    grid-index-CODE.json            # Ordered keys for infinite scroll
    pico-CODE.css                   # Vendored Pico
    gallery-CODE.css                # Galleria's own stylesheet
  pics/COLLECTION/
    preview/                        # Derived renditions
    thumb/
    display/                        # Linked by pages; see below
    original/                       # Linked by pages; see below
```

The grid index and the stylesheets are content-addressed.
CODE is a prefix of a hash of the file's bytes, so a changed file gets a
new name and the build removes the previous one.

Build derives only the renditions that no manifest supplies.
The pages link `display/` and `original/` as well as `thumb/`, but a
deploy tool places `original/` and any `display/` a display manifest
supplies.
Build never writes `original/`.
With an original-only manifest, such as the test fixture, build also
derives `display/`.

## Static-First Approach

Gallery renders all photos server-side with direct image links.
JavaScript features (modals, selection) are post-deployment enhancements.

