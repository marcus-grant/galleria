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

## MVP sequence

The tasks below are ordered by what unblocks what.
Each is a separate change with its own plan and sign-off.

### ft/manifest-read-v0-1

Read the two manifests and produce the list of pics the renderer
consumes.

Keep this module standalone, with no page-generation logic in it.
NormPic may later expose a shared reading surface that consumers sit
on top of; a reader entangled with rendering could not adopt it.

- Read both manifests as plain JSON.
- Pair full and web variants on `relative_path`.
  `original_filename` is unpopulated by every producer path and
  cannot be a key.
- Refuse a manifest whose `version` major.minor is unrecognized.
  This is the contract's one consumer MUST that is not validation.
- Sort explicitly.
  The `pic` array's order is not semantically meaningful and is
  known to be unstable on NormPic's cache path.
- Sort chronologically by `timestamp`, which is optional and
  nullable.
  Name the fallback for pics without one; `mtime` is required and is
  the obvious candidate.
- Fail clearly on a missing required field, naming the field and the
  manifest it was missing from.
- Report back if anything makes the array's original order matter.
  That would escalate a fix upstream to NormPic.

Assert the expected pair count at build time and fail loudly on a
mismatch, rather than pairing silently wrong.
Source filenames are identical across both variants, and same-second
collisions are disambiguated by an ordinal assigned in processing
order.
That ordinal holds only while both collections have identical
membership, so a count mismatch is the signal that it no longer does.
Pixel hashing is the durable fix and is post-MVP.

Boundary cases to pin: an empty manifest, a pic present in one
variant set but not the other, a pic with no timestamp, and a
manifest at an unrecognized version.

Develop against hand-written JSON fixtures in `tmp_path` covering
those four cases.
None of them occurs in a real 645-photo manifest, which pairs 645/645.
One acceptance run against a real manifest before sign-off.
That path is supplied at invocation and is never a constant here.

### ft/cli-config

Give Galleria the interface marcustack calls it through.

marcustack invokes the CLI, never a task-runner recipe.
Three paths are required with no defaults: the full-collection
manifest, the web-collection manifest, and the output directory.
Separate manifest paths rather than a root with an assumed layout;
the two manifests may not share a parent.

Missing configuration or a missing manifest fails immediately,
naming what was not found.

- Add the three required paths to `build`, which currently takes no
  options and hardcodes all three.
- Emit relative paths in rendered output.
  Output must be self-contained and portable; a CDN hostname baked
  into generated HTML is stale the moment anything moves.
  The relative-path branch in `photo_metadata.py` already exists but
  is unreachable from the render pipeline.
- Remove `PICS_BASE_URL`, `SITE_BASE_URL`, and
  `_generate_pics_base_url()`.
  The renderer ignores the settings and builds its own URL from S3
  settings, which is two sources of truth for one value.
- Decide each existing command's fate: `process-photos`,
  `upload-photos`, `deploy`, `find-samples`, `collection-stats`.
  Their work moved to NormPic and marcustack.
- Remove the modules those commands depend on, and their tests, as
  they are orphaned: EXIF extraction, filename generation, S3
  storage, photo validation, and the processing pipeline.
  Thumbnail generation lives in `file_processing.py` and stays;
  split it out rather than deleting the file.
- Remove the S3 settings left unread.

This is the largest task in the sequence and the one most likely to
want per-commit sign-off.

Its module decisions also determine the suite's remaining cost.
`test_e2e_pipeline.py` and the GPS timezone tests in
`test_filename_service.py` are nearly all of the current runtime, and
both cover producer work that leaves with these modules.

Removing this code also removes the pyright suppressions covering it.
`template_renderer.py` and `file_processing.py` each carry a file-level
suppression with the reason stated above the directive.
Neither should survive the code it covers.

### ft/static-gallery

A correct gallery with no JavaScript at all.

This is the fallback, and it must be right on its own before
anything enhances it.

- Thumbnail links the web version.
- Full resolution reachable by an explicit separate link, never from
  the thumbnail itself.
  Originals are often over 20MB.
- Configurable pagination.
  None exists today; the template loops over the whole collection
  unbounded, which for 645 photos is one enormous page.
- Fixed-dimension containers so images arriving do not reflow the
  grid.

Display order is Galleria's decision, not NormPic's.
Chronological is the default for a wedding.

### ft/dev-loop

Make iteration on templates and styles fast.

Most of this exists: `serve --reload` watches `src/template` and
`static`, and rebuilds through a subprocess.
Build does no image processing, so it is fast regardless of
collection size.

- Wire the static asset copy into `build`.
  `static_assets.py` has `copy_css_files()` and `copy_js_files()`
  but nothing calls them.
- Create the `static` directory the watcher already watches and the
  build already creates empty output directories for.
- Make a missing `watchdog` loud.
  Reload currently catches the ImportError and prints a warning,
  then silently does not reload, so an edit appears to do nothing
  and the wrong thing gets debugged.
- Assemble a small fixture collection for the loop.
  Iterating against 645 photos is not the working rhythm; the real
  collection is for acceptance runs.

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

Some renaming later is expected and fine.
Spend no more effort here than that.

### ft/rendition-model

Make derived image sets configurable rather than hardcoded.

Thumbnails are currently 400px WEBP at quality 85, from module-level
constants, generated from the web set.
Derived sets are build output, not content, and are never
manifested.

- A rendition spec as data: format, maximum dimension, and a
  quality-or-byte-budget constraint.
  The constraint must admit both, even if only quality is
  implemented now, because a byte budget means iterating encode
  attempts and an interface taking only quality cannot grow into it.
- The generator takes a spec instead of reading module constants.
  Behavior unchanged; the existing values become the default spec.
- Configuration supplies the specs.
  One rendition at MVP, more without code changes.
- Named generator implementations behind one call, so a second
  format lands without touching callers.

Keep WEBP for grid thumbnails.
It is a good size-to-quality compromise and its incremental decoding
suits tiles.

### ft/preview-modal

Clicking a thumbnail opens a preview.

- Modal or full-page.
- Show the scaled-up thumbnail immediately, swap in the web version
  once loaded.
- A toggle switches to full resolution.
- A download button acts on whichever rendition is currently
  displayed.
- Keyboard navigation and a working no-JS anchor underneath.

The web set averages 3.5MB per image across 645 photos.
That is "web" as a photographer means it, sized to survive a social
network's ingest, not as a browser means it.
The swap will feel like waiting, which is what the decision after
this task addresses.

### ft/lazy-scroll

Lazy-loaded infinite scroll, overriding the static pagination.

- Not literally infinite.
- Configurable.
- Load ahead of the viewport by a tunable distance.
- Fixed-dimension containers so arriving images do not reflow.

Blank tiles filling in behind a fast scroll is the failure mode to
avoid.

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

### doc/mvp-docs-pass

Reconcile the documentation subdirectories that describe the
pre-split project.

Left until here because each describes a moving target.

- `doc/architecture/`: rewrite against what Galleria actually is.
- `doc/command/`: rewrite against the CLI as it ends up.
- `doc/deployment/`: salvage anything useful to marcustack, then
  delete.
- `doc/guides/`: rewrite or delete per guide.
- Restore a Quick Start to the root README once the CLI is settled.

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

### tst/fakefs-fixture

Three test modules suppress the same finding: pyfakefs types
`Patcher.fs` as optional, so every call through it reports.
Replace the suppressions with a fixture that asserts it once.

### ref/path-typed-interfaces

`fs.py` declares path parameters as optional strings and then rebinds
them to `Path`.
Rewrite it, and audit for other interfaces taking an optional string
where they mean a path.
An absent value collapsing into a wrong-typed one is the shape to look
for.

### chr/format-sweep

No formatter has run across this repository.
Diffs are dominated by incidental reformatting whenever a file is
touched, which hides what actually changed.
Run one sweep, then keep it in the gate.

### fix/template-photos-variable

`index.j2.html` and `navbar.j2.html` access `photos|length`, but the
render context provides `pics`.
Jinja renders an undefined variable as empty, so this fails silently.
A leftover from the photo-to-pic rename.

### tst/fixture-dedup

Roughly seven near-identical "create a JPEG with EXIF" factories are
scattered across seven test files; only two live in a `conftest.py`.
Consolidate them.

Worth doing after the module removals in `ft/cli-config`, since some
of these fixtures serve tests that are being deleted anyway.

### chr/remove-empty-theme

`themes/wedding/` holds two empty directories and nothing else.
`THEME_DIR` in `settings.py` points at it and is never read.
Remove both.

## Deferred

Recorded so they are not rediscovered.

- `settings.py` loads local settings with `exec()`.
  It works, but an executed config file can do anything.
  Worth revisiting once the settings surface is smaller.
- The live CDN has no web set, so the deployed gallery serves
  full-resolution files.
  Galleria's templates reference the web prefix correctly and the
  old pipeline did produce it; the upload was full-only.
  This belongs to marcustack and is reported after MVP.
- `manage.py` as the CLI entry point.
  The name follows a Django convention this project does not
  otherwise follow.
  What replaces it is a contract with marcustack, so it settles in
  `ft/cli-config` rather than separately.
- CONTRIBUTE forbids batching questions.
  Independent questions batch fine and doing so saves exchanges; the
  rule means only that a question must not be buried in prose.
  Reword it.
- `pyright` and `beautifulsoup4` are unpinned.
  Both changed their finding sets materially across recent versions,
  so a fresh environment can re-red a green gate.
