# Galleria v0.1 MVP Plan

Owner: Marcus Grant.
Status: active.
This is a provisional, PR-sequenced plan to take the existing Galleria to a
v0.1 MVP.
It is a companion to the Galleria near-term design document, which holds the
scope and non-goals; this document records the current state of the code, the
order of pull requests to MVP, and the upstream contract dependency that gates
part of that work.
It also records cleanup candidates for a future audit.

Galleria is one component of a wider ecosystem.
It consumes a manifest produced by NormPic and outputs a static gallery that a
separate composer deploys.
The whole is more than the sum of its parts, and this Galleria iteration is a
transitional stepping stone toward a more durable photo-presentation layer.

## Current state

These are the findings from reading the code, recorded so the implementer
knows the starting point.

Galleria predates the NormPic split.
It currently sources photos by scanning filesystem directories, extracts EXIF,
generates chronological filenames, computes a dual hash (a SHA-256 of the
original and a SHA-256 of an EXIF-modified copy), creates symlinks, generates
WEBP thumbnails, writes a gallery-metadata.json, and uploads to remote storage.

There is no NormPic manifest consumption today.
The internal gallery-metadata.json, modelled by the GalleryMetadata dataclass,
is a pre-split manifest analog.
Its fields differ from the NormPic v0.1.0 direction: a schema_version rather
than a version, a dual hash rather than a single content-addressed hash, a
precomputed file block of full, web, and thumb paths rather than a single
relative path, and a processing settings block.

The reusable core is the renderer.
Jinja2 templates iterate a flat list named pics.
The processing, hashing, and upload code is residue, now owned upstream:
NormPic processes content, and the composer deploys it.

The templates are skeletal.
base.j2.html wires no stylesheet and no scripts.
gallery.j2.html and pic-cell.j2.html style with Tailwind utility classes.
pic-cell wraps each thumbnail in a plain anchor that opens the web image in a
new tab; there is no preview overlay and no client-side behavior.

Thumbnail generation resizes to a 400 pixel maximum dimension and saves WEBP at
quality 85.
This produces files well below the design document's stated target of about
240KB, so the target and the implementation disagree and must be reconciled.

Static asset bundling copies CSS and JS files from a source directory into the
output.
This is the mechanism the stylesheet and any scripts flow through.

## The render seam

The templates consume a single flat list named pics.
Each entry carries an id, a timestamp, a camera string, and a filename, and the
templates build photo URLs from a base URL plus a web or thumb path.
Any data source that produces this pics list can drive the renderer.
The manifest reader is therefore a new producer of pics, not a rewrite of the
render path.

## Manifest contract dependency

Read this before planning the manifest migration.

The NormPic v0.1.0 manifest contract is being formalized in the NormPic
repository and is not final.
It will change.

What is currently known about the manifest format, including the legacy
gallery-metadata.json shape described above, is superseded and must not be
relied on.

The implementer of the migration binds against NormPic's published v0.1.0
contract once it is ready, and confirms every field against it.

The directional expectations from the design document are expectations to
verify against the contract, not a specification to implement.
They are: a single content-addressed hash (BLAKE2b-120, Crockford Base32) with
a contract-defined prefix, a version field, a per-pic relative path, an
optional original filename, a reserved tag array, and the removal of the error,
warning, and processing-status fields.

The hash prefix appears in more than one form across sources.
It is the NormPic contract's to fix, and this plan does not pin it.

## PR plan

A provisional sequence.
PRs 1 through 5 are unblocked and can proceed now.
PR 6 is gated on the NormPic contract.
Tests come first wherever behavior is deterministic: thumbnail sizing, the page
model and pagination, index generation, and the manifest reader.
Stylesheet and interaction work is reviewed visually.

1. Thumbnail pass.
   Verify and fix thumbnail generation.
   Reconcile the output target: the current 400 pixel, quality 85 WEBP falls
   well below the stated 240KB goal, so decide the real target (larger
   dimensions, a size-driven encode, or smaller thumbnails accepted) and record
   it.
   Surface failures to the log rather than silently returning a false result.
   Confirm the thumbnail URL extension: cells request a thumb path built from
   the photo filename while thumbnails are written with a .webp extension, which
   looks mismatched.
   Tests first.

2. CSS foundation.
   Wire an in-repo stylesheet into base.j2.html.
   Base it on PicoCSS and add BEM classes for the gallery-specific blocks, such
   as gallery and thumb.
   Convert the Tailwind utility classes in gallery.j2.html and pic-cell.j2.html
   to those BEM classes.
   The stylesheet is an in-repo placeholder until marcus-retro, the provisional
   name for the shared CSS design system, is ready.
   The BEM class surface produced here is the list handed to the marcus-retro
   owner during contract coordination, authored in BEM so that later
   reconciliation is mostly renaming rather than restructuring.

3. Click-to-preview.
   Replace the plain new-tab anchor in pic-cell with an Alpine.js
   near-full-page preview overlay.
   The overlay shows the web-optimized image, a link to the original, caption
   metadata where the manifest provides it, a close control, and keyboard
   navigation with the arrow keys and escape.
   Keep a working anchor as the no-JS fallback.
   Wire Alpine through the scripts block and the static asset copy.
   Front-end, reviewed visually.

4. Pagination and progressive scroll.
   Generate paginated pages at a fixed thumbnails-per-page count, with pager
   links at the foot of each page for the no-JS path.
   With JS, hide the pager links and lazy-load later pages on scroll until the
   collection is exhausted.
   The page model and pagination math are tested first; the scroll behavior is
   front-end.
   A photos JSON output already exists and may serve the client-side fetch,
   while the design document parses the paginated pages; choose one approach in
   this PR.

5. Gallery index.
   Generate a self-contained index page that lists collections and serves as
   the entry point for the gallery domain.
   Light tests on the index model.

6. Manifest contract migration (gated).
   Implement a reader that parses NormPic's published v0.1.0 manifest into the
   pics model: validate the version field, carry the single content-addressed
   hash, resolve the per-pic relative path against the configured destination
   root, surface the optional original filename, and tolerate the reserved tag
   array without acting on it.
   Make this reader the gallery build's data source in place of the legacy
   gallery-metadata.json and filename-scan producers, leaving the legacy code in
   place but out of the build flow.
   Tests first, against fixtures drawn from the real contract.
   Do not start until the contract exists.
   This PR may split into a reader-and-mapping PR and a wire-in PR.

## Milestones

Going live is gated on PRs 1 through 5, not on NormPic.
The wedding set can render from the existing legacy producer while the contract
is formalized, and PR 6 then swaps the data source to the real manifest.
This keeps the MVP milestone independent of upstream contract work, consistent
with each component being independently deployable.
Confirm the legacy producer runs end to end before depending on this path.

## Cleanup candidates and doc realignment

This section records candidates for a future cleanup.
Trimming is out of scope for this work.
A dedicated audit precedes any removal, and a separate maintainer does that
pass.
Code trimming in particular waits until after the manifest migration, because
the residue pipeline is load-bearing for the interim legacy render path.

### Code residue (keep for now)

The directory scanning, EXIF extraction, dual hashing, EXIF-modified deployment
hash, remote upload, and deploy code is now owned upstream by NormPic or by the
composer.
It stays in the repository and out of the v0.1 gallery build.
Once the manifest reader replaces the legacy producer it becomes the largest
trim, so it is a post-migration candidate rather than a current one.
CDN movement belongs to the composer or to NormPic, not to Galleria; v0.1 ends
at local output.

### File candidates (low risk, decision still belongs to the audit)

- Two settings examples exist, settings.local.example.py and
  settings.local.py.example; one naming should remain.
- doc/services/uuid_service.md documents a uuid_service that is absent from src,
  likely superseded by filename_service; verify, then remove.

### Doc realignment

The documentation footprint is dominated by the residue pipeline, while the
renderer is thinly covered.
The candidates below are lower risk than code trimming but still belong to the
maintainer's audit.

- Misleading entry point: the README quick start presents process-photos,
  build, and deploy as the pipeline.
  This is the first thing a cold reader sees and misrepresents the
  renderer-and-manifest direction.
  It is the highest-priority doc fix.
- Stale, describe residue: command/deploy, command/process-photos,
  command/collection-stats, guides/bunnycdn-setup, guides/remote-storage-setup,
  services/s3_storage, services/deployment, services/exif_modification, the
  deployment subdirectory, and architecture/metadata-consistency.
- Reframe for the renderer focus: README, architecture/overview,
  architecture/static-site-generation, services/file_processing, and
  settings.md.
- TODO.md is a pre-split development specification of the steps to MVP; the
  present plan supersedes much of it, so it needs reconciliation or retirement.
- Leave as is: changes, old-changelogs, CHANGELOG, and testing.

Doc staleness above is inferred from titles and the code already read; the
maintainer confirms by reading before acting.

## Conventions

- Task runner: just.
- Packaging and environment: uv, pyproject.toml, pytest.
- Tests first wherever behavior is deterministic.
- Styling: BEM classes on a PicoCSS base.
- Versioning: semver, v0.x while pre-stable.

## Related projects

Each piece here sits in the wider ecosystem; the statuses below are current at
the time of writing.

- NormPic.
  Upstream.
  Owns the manifest contract that the migration PR consumes.
  Status: design complete; the v0.1.0 contract is being formalized in its own
  repository and is not final.
- Composer (marcustack).
  Orchestrates Galleria's build and handles CDN upload.
  Status: design complete; awaiting bootstrap.
- marcus-retro (provisional name).
  Shared CSS design system.
  Galleria consumes its bundle at build time once it exists, with in-repo CSS
  until then.
  Status: parked pre-bootstrap.
- personal-site.
  11ty renderer.
  Independent of Galleria today; a future 11ty-plugin direction would bring
  Galleria into its process.
  Status: design complete; awaiting bootstrap.
- Future Rust rewrite.
  Anticipated.
  Reuses the manifest contract, with Python Galleria as the reference
  implementation.
  Status: not designed.

## Out of scope for v0.1

The full list is in the Galleria near-term design document.
In short: tag-driven views, per-collection compression configurability,
self-managed CDN upload, EXIF display beyond the manifest, the Rust rewrite, and
11ty plugin packaging.
