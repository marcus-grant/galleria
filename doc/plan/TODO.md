# Galleria tasks

Planned, active, and imminent work.
Completed tasks are deleted from this file; the
[changelog](../CHANGELOG.md) is the record of what was done.

Galleria reads two photo manifests produced by NormPic, pairs the
variants, and generates a static gallery to a local output directory.
It does not deploy that output and does not process source photos.

The goal this sequence works toward is a presentable wedding gallery
for a real 645-photo collection.

## Upstream contract

Galleria consumes NormPic's manifest format, currently v0.1.1.
Field semantics are documented at
<https://github.com/marcus-grant/normpic/blob/v0.1.1/doc/architecture/manifest-contract.md>.

Do not copy that contract into this repository, in code or in
documentation.
A copy is a second definition of one thing and it drifts silently.
Point at the tagged document instead.

Galleria does not validate manifests.
marcustack runs NormPic and validates its output before handing
manifests over, so a manifest reaching Galleria has already been
checked.
Galleria reads the JSON, uses the fields it needs, and fails clearly
naming any required field that is missing.

## Working through this sequence

This repository predates the split into NormPic, marcustack, and
b3c32, and still carries residue from it: modules whose work moved
upstream, and tests covering behavior the project has shed.

Every task below will encounter some.
Remove it as part of the task when it is adjacent to the work.
When it is not adjacent, add it here as a standalone task rather
than leaving it unmentioned.
This note goes away when the residue does.

The entries below record what has been found so far.
Each is a discovery about the current state of this repository, not a
lasting fact about the project, so each has an expiry.
When a task resolves one, delete it in the same `Pln:` commit that
deletes the task, the way completed task lines are deleted.
An entry that outlives what it describes is worse than no entry: it
sends a reader looking for a problem that is no longer there.

### What has been found

**Derived output is durable despite living in `_build`.**
Derived renditions are written under the output directory, which for
the wedding collection is marcustack's `_build` alongside its
manifests.
The name suggests scratch space; it is not.
A full derive run over 645 photos takes six and a half minutes and
there is no incremental skip, so cleaning that directory means
re-encoding everything.
This is a stopgap rather than a design.
The real fix is a cache keyed on source hash plus rendition spec, and
it lands with the derive pipeline second pass.

**Three helpers named for writing manifests have different shapes.**
`test_validate.py` and `test_manifest_reader.py` each define a
`_write_manifest`, and `test_derive.py` defines a `_write_collection`
that also writes the images its manifest names.
All hand-build a contract this project does not own; they leave when
NormPic ships a consumer package with test factories.

**A test that asserts nothing can still pass.**
Watch for an unused local in a test.
It is often a call whose result was never asserted on.
Ten test modules were also found to contain no `pytest.raises` at all.
So error paths in the code they cover are unexercised.

**A local build has no `original/` or `display/` renditions.**
Only preview and thumb are written under `output_dir`; the other two
are marcustack's to place at deploy.
For a browser run, symlink the manifest directories in at
`pics/COLLECTION/original` and `pics/COLLECTION/display`, or every
per-photo page 404s on its image and both links.
The same fact is recorded for the output layout document under
`doc/mvp-docs-pass`.

**Not chased.**
The `realworld` pytest marker was defined and never applied to the
real-photo tests, which guard on a settings path instead.
It moved to `salvage/` with them.
`debug/template_debug.py` and its test remain, exercising a debugging
helper rather than the project.

## MVP sequence

The tasks below are ordered by what unblocks what.
Each is a separate change with its own plan and sign-off.

### ft/pic-page-loading

Per-photo page loading, moved out of `ft/static-gallery-refinements`.
The display rendition is roughly 2MB and reads as a wait on mobile.

- The page renders `pic.display` today.
  The preview rendition is derived but no template uses it.
- Preview is progressive JPEG by default spec, so preview-first needs
  no JavaScript.
- Plan: `<img src>` is the preview, with `srcset` naming preview and
  display.
- `srcset` widths are nominal, taken from each spec's
  `max_dimension` through `Config`, because manifests carry no
  dimensions.
  Real dimensions arrive with `ref/derive-pipeline`.
- On a 3x-DPR phone the slot can exceed the preview's 1024px, so the
  browser may pick display anyway.
  `sizes` and preview size decide this; verify in a throttled
  browser.
- Build hrefs through the existing `href` helper, so the
  `ref/derive-pipeline` move of `rendition_href` stays mechanical.

### ft/gallery-styling

The first stylesheet this project has had.

There is no CSS file anywhere in the repository.
Styling today is Tailwind utility classes against a CDN script tag,
which ships a compiler to the browser and is explicitly not a
production configuration.

- Remove the Tailwind CDN tag and the utility classes.
  Roughly nine test assertions name Tailwind classes and will need
  updating.
- PicoCSS as the base.
- A simple custom stylesheet over it.
  No real theming yet.
- Colors, spacing, and fonts as CSS custom properties at the root,
  so a later shared theme is an override of variables rather than a
  rewrite of rules.
- Conventional BEM block names rather than clever ones, so a second
  consumer would plausibly arrive at the same words.

- `base.j2.html` carries an inline `<style>` block: a token layer on
  `:root` and BEM rules for `pic-cell__link` and `pic-cell__img`.
  Move it into the first stylesheet and keep it as the token layer's
  seed.
- `hidePagination` in `components/grid-scroll.j2.html` sets inline
  `display: none` because Tailwind's `flex` outranks the `hidden`
  attribute.
  Switch it to `hidden` once Tailwind is gone.
- Asset content addressing lands with the first stylesheet.
  Name static assets by a b3c32 code prefix, pass a name map in
  template context, and keep any stale-asset cleanup scoped by
  pattern.
  marcustack's `_upload_dir` uploads only top-level files, so an
  asset subdirectory needs a marcustack change.
  That boundary is the maintainer's call.

Some renaming later is expected and fine.
Spend no more effort here than that.

### ref/derive-pipeline

A second pass at derivation, after the first landed enough to publish
a gallery.

It works: 1290 renditions from 645 photos in six and a half minutes.
What it lacks is legibility while running, any notion of what it has
already done, and an input path as wide as the model behind it.

- The input path names two manifests where the model holds four
  renditions.
  `option.py`, `Config`, `resolve_inputs`, and `merge_variants` are
  all two-shaped, so a manifested preview or thumb cannot be
  expressed.
  The production case is one or two manifests in the original and
  display classes, which is why this was deferred.
- `derive_absences` does too much: resolves the source, decides alias
  from generate, encodes, builds a `Pic` per written file, assembles
  the record.
  At least the first and last of those are their own units.
- `derive_rendition` takes a source, a destination directory, a stem,
  and a spec, where three combine into one resolved destination.
  `Overrides` lists keys without expressing which belong together.
- Progress and failure reporting.
  A successful run prints nothing until it finishes, which reads as a
  hang; a run where everything fails prints 645 lines and a summary
  that reads like partial success.
- `--force`, and skipping a rendition whose destination exists.
  Cheap and wrong when a source or spec changed, which `--force`
  covers until hashes are persisted.
- A count check closing a build.
  Manifest pics, merged records, renditions per class, and rendered
  thumbnails should agree.
  Aliased renditions have no file, so that class legitimately differs
  and the check needs to know which were aliased.
- Consider another look at the defaults for derivations based on decision point
- `services/link.py` and its test are interim.
  `rendition_href` composes `pics/COLLECTION/RELATIVE_PATH` from a
  `Pic` whose path already carries its kind; that belongs on a model
  that knows its own kind and path, and both files go when it does.
  Every filled `Pic` path is now relative to the collection's pics
  directory and starts with its kind; an aliased shallower field
  holds the deeper `Pic` itself, so it resolves to a real file.
- ft/static-gallery left the seam ready: `derive_collection` takes
  a `generate` callable, and `adopt_rendition` fills records from
  disk without encoding, failing on a missing file.
  Adopt-or-encode per record is most of the incremental skip.
- When incremental derivation lands:
  - Flip build's `--derive` default to opt-out.
  - Revisit `--validate` with it.
  - marcustack passes `--derive` and `--validate` explicitly.
  - Flipping either default is still a behavior change.
    - It affects any caller that omits the flag.
- Move `derive.py` hashing from `hash_b32` on read bytes to
  `code_from_path`.
  The b3c32 floor is already 0.0.3.
- Record rendition dimensions.
  They make `srcset` widths real and allow `width` and `height`
  attributes.
- Content-addressed rendition names, if wanted, come from this
  pipeline's source-hash-plus-spec key.

`PicRenditions` holds relative paths against a root and knows nothing
of where files live.
That stays until marcustack's routing and deploy tail exist, since a
final shape now would be guessing at half the requirements.

### ft/dev-loop

Make iteration on templates and styles fast.

Build does no image processing, so it is fast regardless of
collection size.

- `serve` and the dev server were removed.
  - The loop needs its own serving and reload mechanism.
- Assemble a small fixture collection for the loop.
  Iterating against 645 photos is not the working rhythm; the real
  collection is for acceptance runs.
- `base_url` and the dev-versus-prod distinction land here.
  It has no sensible program default: prod is a domain galleria must
  not know, and dev is an address that does not exist until this loop
  does.
- `debug/template_debug.py` needs a refit.
  Its sample data keys do not match the current template surface, its
  structural analysis counts Alpine and Tailwind artifacts that are
  being removed, and it manipulates `sys.path` at import rather than
  relying on the package.
- The `grid-scroll` inline script has no automated tests.
  Add JS test tooling and backfill tests for it.
- Interim loop until then: `uv run python -m galleria build` with
  both manifests and `--output-dir` pointed at a built collection,
  served by `python -m http.server`.
  `fetch` needs HTTP, so `file://` cannot exercise the scroll.

### ft/preview-modal

Clicking a thumbnail opens a preview.

- Modal or full-page.
- Show the scaled-up thumbnail immediately, swap in the web version
  once loaded.
- A toggle switches to full resolution.
- A download button acts on whichever rendition is currently
  displayed.
- Keyboard navigation and a working no-JS anchor underneath.
- A modal keeps scroll position, which infinite scroll loses on Back
  when the browser evicts the page from its back-forward cache.
  Until the modal exists, restoring loaded count and scroll offset
  per tab is the interim fix; it is redundant once the modal lands.
- Decide here whether Alpine.js earns a place.
  The scroll script is plain JavaScript; Alpine fits state-driven UI
  like a modal, not imperative DOM work.
- A modal's markup can follow the grid's pattern: a `<template>`
  rendered by the same include as the page, cloned by script.

The web set averages 3.5MB per image across 645 photos.
That is "web" as a photographer means it, sized to survive a social
network's ingest, not as a browser means it.
The swap will feel like waiting, which is what the decision after
this task addresses.

### Decision point: what the preview needs

Not a task.
After the preview works, look at it on mobile against the real
collection and answer two independent questions.

Does the placeholder look acceptable while the larger image loads?
If not, a progressive JPEG rendition is what fixes it.

Does the larger image arrive fast enough to feel like a swap rather
than a wait?
If not, a smaller display rendition between thumbnail and web is what
fixes it.

Either, both, or neither may be needed for MVP.
Progressive encoding changes what is seen during a transfer; a smaller
rendition changes what is transferred.
They address different complaints and neither substitutes for the
other.

What this decides is only what ships for MVP, not what exists.
Both progressive JPEG and WEBP are formats a rendition spec names, and
both belong in the set of options eventually.
The rendition model is what makes that true: whichever is not chosen
here lands later as configuration and a named generator, not as new
plumbing.
If adding the other one afterward would mean touching the generator's
callers or branching on where output is displayed, the abstraction is
wrong and that is the thing to fix.

WEBP has incremental decoding, which paints top-to-bottom as bytes
arrive.
It does not have progressive decoding, the blurry-whole-image effect
that makes a good placeholder.
That is a JPEG feature, and it is why the two formats are not
interchangeable here.

Decide this by looking at it, not by reasoning about it.
Then ask marcus how to proceed.
Since both options need to exist, documenting both options' results and
providing at least high-level planning documentation for both are required.

### ft/static-gallery-refinements

Observed on the real collection during the static gallery acceptance
run.
None blocks publishing; each is decided by looking at it.

- Grid thumbs at mobile widths.
  The grey placeholder and hidden alt text landed.
  At mobile widths a cell is about 180 CSS px, roughly 540 device px
  on a 3x screen, so the 400px WebP thumb is upscaled and its
  artifacts show.
  A larger thumb or `srcset` on grid cells, decided against the real
  collection.
- Jump to top and bottom.
  Top is trivial.
  Bottom is ill-defined under infinite scroll: the real end means
  appending every remaining batch first.
- Alt text wording.
  Cells read `COLLECTION STEM`, which repeats the collection and
  reads out a filename to screen readers.
- Per-photo page numbering.
  Pages are named by stem.
  The maintainer prefers grid position, `pic/1.html` onward.
  Trade-off: position renumbers every URL when a photo is added or
  removed, where the stem is stable; decide by whether the published
  set is frozen.
- Supplied navbar.
  The parent site owns landing page and navigation; galleria emits
  gallery trees only, so the built-in navbar, "COLLECTION Gallery"
  and a count, stands pre-MVP.
  The constraint that decides the mechanism: pages sit at two depths,
  `gallery/COLLECTION/` and `gallery/COLLECTION/pic/`, and every link
  is relative, so a verbatim fragment included by path cannot carry
  links correct at both depths.
  A template override directory solves depth but puts two projects
  in authority over one template set.
  Current lean is the parent post-processing the output, which reuses
  the injection mechanism marcustack builds for the deprecation
  banner and knows each file's path.
  Who owns the navbar markup is open and is the director's call.
- STEM collision.
  Per-photo pages are named by `key.name`, so nested manifest paths
  flatten.
  Two photos sharing a basename in different directories write one
  page, silently, the second overwriting the first.
  The wedding collection has none.
  Trigger: any collection whose manifest has subdirectories.
  Fix is naming by the full key or by position; decide with the
  numbering bullet above.
  The grid scroll script substitutes the whole key into the cell
  template, so nested keys would also put directories into
  per-photo hrefs.

### doc/mvp-docs-pass

Reconcile the documentation subdirectories that describe the
pre-split project.

Left until here because each describes a moving target.

- `doc/architecture/`: rewrite against what Galleria actually is.
- `doc/command/`: rewrite against the CLI as it ends up.
- `doc/deployment/`: salvage anything useful to marcustack, then
  delete.
- Restore a Quick Start to the root README once the CLI is settled.
- Write the configuration document.
- `static-site-generation.md` still names a nonexistent service.
  - The service is `PhotoMetadataService`.
- The testing README tree omits four directories.
  - They are `models/`, `config/`, `template/`, and `debug/`.
- Dead links in two READMEs.
  - `doc/testing/README.md` links `patterns.md`.
  - `doc/util/README.md` links `UUIDv7.md`.

- Write the output layout document from these settled facts.
  `output_dir` is the site root.
  Pages at `gallery/COLLECTION/pageN.html`, `PAGE_SIZE` records each,
  in merge order; `index.html` is a byte copy of `page1.html`.
  Per-photo pages at `gallery/COLLECTION/pic/STEM.html` with display
  rendition, view-original and download links, prev and next by
  position.
  Renditions at `pics/COLLECTION/KIND/`; every emitted link is
  relative to the page.
  An absent original aliases to display and its links degrade to the
  shallowest present rendition; an absent display is derived from
  the original, or stops an adopt-only build as stale.
  A local tree lacks `original/` and `display/`; the acceptance run
  symlinks the manifest directories in.

## Standalone tasks

No ordering constraint; pick these up alongside the sequence.

### chr/report-salvage

`salvage/` holds modules pulled out of the tree and held for a
decision, inventoried in its README.
Report that inventory to the maintainer, who decides per module
whether it is migrated, documented, or deleted.
The directory empties as those decisions land, and this task closes
when it is gone.

### tst/soup-assertion-helpers

The template tests carry file-level pyright suppressions because
BeautifulSoup's annotations reject callable `class_` predicates and
return an optional attribute value from `get()`.
Replace them with typed assertion helpers that narrow once.
Every template test added from here hits the same thing.

`_one(soup, selector)` in `test/template/test_gallery_template.py`
is the seed: it narrows `select_one` once.
Attribute values still need `str()` at each use.

- Template tests are hard to re-enter: it is not clear what each
  render sets up or what each assertion selects.
  Make helpers state both.
- `GRID_CELL = ".pic-cell:not(template *)"` lives in the template
  tests and is spelled out inline in `test_build.py`.
  Share one definition through a conftest.

### ref/template-autoescape

The Jinja `Environment` has autoescape off, so values reach
attributes raw.
Harmless for today's stems; enabling it may change existing output,
so it gets its own look.

### chr/template-markers

Every template's START and END comment says `src/template/`, which is
stale since the module layout change.
Correct them and give each template a `{# #}` header block (summary,
Author, Created, License), as `components/grid-scroll.j2.html` has.

### ref/path-typed-interfaces

Audit for interfaces taking an optional string where they mean a path.
An absent value collapsing into a wrong-typed one is the shape to look
for.

### chr/format-sweep

No formatter has run across this repository.
Diffs are dominated by incidental reformatting whenever a file is
touched, which hides what actually changed.
Run one sweep, then keep it in the gate.

### tst/fixture-dedup

`_write_collection` has three deliberate copies, in
`test/command/test_derive.py`, `test/services/test_derive.py`, and
`test/command/test_build.py`.
They change together or not at all until this task lands.
`test_build.py` adds `_records`, `_cfg`, `_pages`, and `_cells`;
`test_gallery_template.py` adds `_record`, `_page`, and `_pic_page`.
All belong in conftest modules.

## Deferred

Recorded so they are not rediscovered.

- The live CDN has no web set, so the deployed gallery serves
  full-resolution files.
  Galleria's templates reference the web prefix correctly and the
  old pipeline did produce it; the upload was full-only.
  This belongs to marcustack and is reported after MVP.
- CONTRIBUTE forbids batching questions.
  Independent questions batch fine and doing so saves exchanges; the
  rule means only that a question must not be buried in prose.
- Dominant-color thumb placeholders.
  One color per photo computed at derive time, painted at partial
  opacity.
  About 1.8KB gzipped extra in the grid index as 12-bit hex in a
  separate array.
  Low priority; after `ref/derive-pipeline`.
- Indexing the grid index by short hash instead of stem.
  Measured larger: hashes do not compress and the client still needs
  stems to build URLs.
  Revisit only if rendition URLs become hash-based.
  Reword it.
- `pyright` and `beautifulsoup4` are unpinned.
  Both changed their finding sets materially across recent versions,
  so a fresh environment can re-red a green gate.
- A strict flag on `derive`, checking every picture the manifests name
  exists before deriving anything.
  An escape hatch for when upstream is not trusted, not a standing
  pipeline step, which is why it is a flag rather than a stage.
- A post-build output check parsing emitted HTML for unresolved asset
  paths.
  This is galleria checking what it produced rather than re-checking
  what it was given, and only the output knows what got referenced.
  It works against deployed output too, so the composer project may
  want it as a smoke check.
  Existence is a stat; confirming an image decodes is not, so that is
  its own opt-in or a sample.
