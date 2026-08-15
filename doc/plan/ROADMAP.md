# Galleria Roadmap

Loose, unsequenced goals for Galleria beyond v0.1, toward a stable v1.0.
Nothing here is committed or ordered; it records direction, not a schedule.

Galleria sits in a wider ecosystem.
The durable element across every item below is the NormPic manifest contract;
the renderer that consumes it is replaceable, and several goals below replace or
re-home large parts of it.

## Goals

### Per-collection compression configurability

Let each collection declare how its web-optimized variants are produced:
a photographer-curated mirror used directly, auto-generation from originals with
configurable size, quality, and format, or a mix of the two.
This is the natural successor to the v0.1 assumption that web-optimized images
already exist.
Open question: where the configuration lives (manifest extension, sidecar, or
Galleria-side config).

### Tag-driven views

Once the manifest tag array is populated, build tag pages, tag filtering on
collection pages, and tag navigation.
Galleria tolerates the tag field at v0.1 but does not act on it.

### EXIF and metadata display

Show capture date, camera, and other available metadata in the preview overlay,
with privacy care around location.
The data is already in the manifest; the work is template-side.

### Lightbox quality of life

Smoother transitions, swipe gestures on touch devices, image preloading for
next and previous navigation, and zoom for high-resolution photos.

### Self-managed deploy (revisit)

The composer owns CDN upload at v0.1.
Revisit whether Galleria should own its own deploy only once composer complexity
justifies the move; the default is to leave deploy with the composer.

### 11ty plugin packaging

Package Galleria as an 11ty plugin: read a NormPic manifest into the 11ty data
cascade and ship gallery templates.
This unifies gallery rendering with the main site renderer.
Prerequisite is a clean separation of the manifest reader and page model from
the HTML output, which the v0.1 render seam already gestures at.

### Rust rewrite

A core crate for manifest parsing, the page model, and thumbnail logic, with an
HTML-output crate, a WASM build for Node-based renderers, a CLI binary, and a
PyO3 binding as needed.
It reuses the same manifest contract, with the Python Galleria as the reference
implementation.

## Toward v1.0

v1.0 is a feature-mature Galleria, most likely still the Python implementation.
The Rust rewrite is a beyond-v1.0 or parallel horizon, not a v1.0 gate.
Timing depends on real friction with the Python version rather than on a fixed
plan.

## Related projects

- NormPic.
  Owns the manifest contract every goal here depends on.
  Status: v0.1.0 contract being formalized.
- Composer (marcustack).
  Owns build orchestration and CDN deploy.
  Status: design complete; awaiting bootstrap.
- marcus-retro (provisional name).
  Shared CSS design system that Galleria consumes once it exists.
  Status: parked pre-bootstrap.
- personal-site.
  11ty renderer; the plugin goal would bring Galleria into its process.
  Status: design complete; awaiting bootstrap.
