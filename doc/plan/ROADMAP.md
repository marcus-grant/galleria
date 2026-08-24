# Galleria Roadmap

Loose, unsequenced goals for Galleria beyond v0.1, toward a stable v1.0.
Nothing here is committed or ordered; it records direction, not a schedule.

Galleria sits in a wider ecosystem.
The durable element across every item below is the NormPic manifest contract;
the renderer that consumes it is replaceable, and several goals below replace or
re-home large parts of it.

## Goals

### Lightbox quality of life

Smoother transitions, swipe gestures on touch devices, image preloading for
next and previous navigation, and zoom for high-resolution photos.

### EXIF and metadata display

Show capture date, camera, and other available metadata in the preview overlay,
with privacy care around location.
The data is already in the manifest; the work is template-side.

### Per-collection compression configurability

Let each collection declare how its web-optimized variants are produced:
a photographer-curated mirror used directly, auto-generation from originals with
configurable size, quality, and format, or a mix of the two.
This is the natural successor to the v0.1 assumption that web-optimized images
already exist.
Open question: where the configuration lives (manifest extension, sidecar, or
Galleria-side config).

Beyond configurability, renditions generalize into an ordered fidelity
chain rather than named slots.
Derivation flows downward only: a rendition is generated from the
nearest higher-fidelity one available, and a missing higher-fidelity
rendition can only alias to what exists, by metadata rather than by
copying bytes.
MVP does not attempt this.
It assumes both manifested variants are present, which the production
collection satisfies, and does only the abstraction that keeps the
generalization cheap later.

The values the production gallery was built with are recorded in the
changelog: web variants at 2048x2048, thumbnails at 400x400, and
quality 85 for both JPEG and WebP.
They answer the size, quality, and format question with real numbers
rather than assumptions.

### Module organization

Revisit the package layout once the CLI is no longer the only adaptor.
Questions it has to answer, rather than answers already chosen:

- Whether `command/` survives once the CLI is one adaptor among
  several.
  NormPic uses `manager/` for the same role, and ecosystem
  consistency probably decides it.
- Whether grouping directories earn their place at this size, or
  whether flat modules under `galleria/` read better.
- `models/` and `util/` are plural against the singular convention.
  `util/` is empty and likely just goes.

### 11ty plugin packaging

Package Galleria as an 11ty plugin: read a NormPic manifest into the 11ty data
cascade and ship gallery templates.
This unifies gallery rendering with the main site renderer.
Prerequisite is a clean separation of the manifest reader and page model from
the HTML output, which the v0.1 render seam already gestures at.

### Tag-driven views

Once the manifest tag array is populated, build tag pages, tag filtering on
collection pages, and tag navigation.
Galleria tolerates the tag field at v0.1 but does not act on it.

### Rust rewrite

A core crate for manifest parsing, the page model, and thumbnail logic, with an
HTML-output crate, a WASM build for Node-based renderers, a CLI binary, and a
PyO3 binding as needed.
It reuses the same manifest contract, with the Python Galleria as the reference
implementation.

## Unplanned

Uncategorized items with no home yet.
Each either graduates into a section above, moves to
[TODO](TODO.md) when it becomes real work, or is deleted for
falling outside the project's scope.

- Pre-split preview design (AlpineJS component structure, photo modal
  navigation) exists in git history before the doc reorganization.
  Recover it if the modal work wants a starting point; otherwise it
  stays dead.
- Measure the web set's actual file size on the real collection.
  It decides whether the thumbnail-to-web swap feels immediate or
  feels like waiting, and it is the input to any future decision about
  an additional rendition.

### Configuration precedence

Galleria resolves configuration from program defaults and CLI
arguments only.
A general solution belongs to a separate library, with Galleria as its
first consumer.

`salvage/settings.py` is a working precedent for it: four ordered
layers, poorly organized and not generalized at all.
What transfers is the shape rather than the code.

- Four layers: program defaults, config directory resolution, a local
  settings file, then per-key environment overrides.
- ALL_CAPS as the public-key convention.
- Uniform prefixing of environment variable names with the project
  name, applied across roughly twenty keys without exception.
  Derived keys are excluded from environment visibility, which is the
  rule a prefix convention needs alongside it.
- A test-mode escape hatch skipping the local file layer.
- Keys need declared types.
  The precedent coerces paths by matching `_PATH` and `_DIR` name
  suffixes, which is type information smuggled into a naming
  convention because there is no schema.
  That is the part not to repeat.
