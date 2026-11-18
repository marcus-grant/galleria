# Static Site Generation Architecture

## Template Structure

```
src/template/
-> base.j2.html             (Base layout with head, scripts)
-> gallery.j2.html          (Main gallery page extending base)
-> index.j2.html            (Landing page)
-> components/
   -> photo-grid.j2.html    (Grid container with ALL photos)
   -> photo-cell.j2.html    (Direct-link photo thumbnail)
   -> navbar.j2.html        (Navigation component)
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
```
src/template/
├── base.j2.html              # Base layout
├── index.j2.html             # Landing page
├── gallery.j2.html           # Photo gallery
└── components/
    ├── navbar.j2.html         # Navigation
    ├── photo-grid.j2.html     # Photo grid container
    └── photo-cell.j2.html     # Individual photo cells
```

### Output Structure
```
<output-dir>/                  # Generated static site
├── index.html                 # Landing page
├── gallery.html               # Photo gallery
├── css/                       # Tailwind CSS
└── js/                        # Future: AlpineJS enhancements
```

## Static-First Approach

Gallery renders all photos server-side with direct image links. JavaScript features (modals, selection) are post-deployment enhancements.