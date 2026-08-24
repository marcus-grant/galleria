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

**A test that asserts nothing can still pass.**
A batch-ordering test in `test_filename_service.py` looped over a list
of expected values with `pass` as the body.
The loop was removed and its intent recorded as a comment.
The same shape is worth watching for elsewhere: an unused local in a
test is often a call whose result was never asserted on.
Eleven test modules were also found to contain no `pytest.raises` at
all, so error paths in the code they cover are unexercised.

**`file_processing.py` cannot simply be deleted.**
It holds thumbnail generation, which Galleria keeps, alongside dual
collection processing, which moved upstream.
Its imports of `exif`, `filename_service`, `photo_validation`, and
`s3_storage` are function-local rather than at module top, so grepping
the import block understates what depends on what.

**The renderer reaches storage settings.**
`template_renderer.py` and `photo_metadata.py` both import
`is_dual_bucket_configured` from `s3_storage.py`, which is why storage
code cannot leave while the render path still calls it.

**Empty scaffolding directories exist and are referenced by nothing.**
`sample-photos/` and `sample-pics/` are tracked and empty.
`cache/`, `content/`, and `temp_test/` are untracked working
directories.

**Three settings are set and never read.**
`PICS_BASE_URL`, `SITE_BASE_URL`, and `THEME_DIR`.
The renderer composes its own URL rather than reading the first two.

**A relative-path code path exists but is unreachable.**
`photo_metadata.py` contains it; nothing in the render pipeline calls
it.

**Two spellings of the local settings example coexist.**
`settings.local.example.py` and `settings.local.py.example`.
One is stale; which has not been determined.

**Not chased.**
The `realworld` pytest marker was defined and never applied to the
real-photo tests, which guard on a settings path instead.
It moved to `salvage/` with them.
`debug/template_debug.py` and its test remain, exercising a debugging
helper rather than the project.

## MVP sequence

The tasks below are ordered by what unblocks what.
Each is a separate change with its own plan and sign-off.

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
- Decide what the CLI does with a photo present in only one variant
  set.
  `merge_variants` reports these as records with a missing variant and
  never fails on its own.
  Options are a warning, a threshold, generating the missing rendition,
  or refusing to build.
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
  - What that removal is walking into, found by reading rather than
grepping:

    - Delete root-level `settings.py`.
      Three test modules go wholesale, since they test the deleted
      mechanism: `test_settings.py`, `test_settings_isolation_fix.py`,
      and `test_gallery_settings_complete.py`.
      Remaining dependents get `pytest.mark.skip` with a reason naming
      the item that restores them.
    - Verify `python -m galleria build` runs from a directory that is not
      the repository root.
      Running from the root can succeed because the current directory is
      on the path, which is how a package that cannot actually run passes
      its own check.
    - `process_photos.py` is the only caller of the dual-collection
      processing path, but five test modules reach it: its own,
      `test_e2e_pipeline.py`, `test_batch_metadata_efficiency.py`,
      `test_file_processing_dual.py`, and `test_photo_metadata.py`.
      The last two are named for services rather than for the command, so
      the coupling is not visible from their filenames.
    - `file_processing.py` imports its dependencies inside functions rather
      than at module top.
      A grep of import blocks will show fewer dependents than exist.
    - `link_photo_with_filename` raises rather than returning an error
      value, so its callers correctly ignore its return.
      Worth knowing before treating those as defects.
    - The thumbnail generation to split out is generated from the web
      variant, not the full one.
    - Remove the S3 settings left unread.
    - Remove the dependencies those modules were the only users of:
      `exifread`, `timezonefinder`, and `boto3`.
      Grep before removing; `pillow` stays with thumbnail generation.
      Run `uv sync` and commit `uv.lock` alongside the
      `pyproject.toml` edit.

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
- Generate thumbnails from the display variant.
  This is the first derived rendition, and it raises a model question
  to settle before writing it: a generated rendition carries the same
  fields as a manifested one, so decide whether `Pic` serves both
  rather than adding a parallel record.
  If it does, the container tracks which renditions were manifested
  and which were generated, since the type no longer says.
- Decide how the no-JavaScript page offers original, display and
  thumbnail without a viewer to switch between them.
  Deferred until the static page exists to look at.

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
constants, generated from the display variant.
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
- Settle whether a generated rendition is a `Pic`.
  It carries the same fields, so a parallel record is duplication, but
  reusing `Pic` loses the manifested-versus-generated distinction and
  the container has to track it instead.
- The fidelity chain in ROADMAP is what makes named slots insufficient
  eventually.
  Not MVP work; noted here so the spec shape does not foreclose it.
- Production rendition values, recovered from the deleted settings
  file and the only record of what the deployed gallery was built
  with.
  `WEB_SIZE = (2048, 2048)` is the `display` rendition under the
  settled variant names.
  `THUMB_SIZE = (400, 400)` is the hardcoded 400 that `doc/QA.md`
  cites as its example of a literal standing in for unwritten
  configuration.
  `JPEG_QUALITY = 85` and `WEBP_QUALITY = 85`.
- `doc/command/process-photos.md` documents a command this item may
  rename or delete.
  Its fate follows the module's.

Thumbnail format is unsettled.
WEBP is a good size-to-quality compromise, but it has no progressive
mode: it decodes top-to-bottom rather than coarse-to-fine, so a larger
progressive JPEG may read better on a grid despite the extra bytes.
Settle it cheaply before MVP: generate a grid in each format and look
at both over a throttled connection.
The point is a decision, not a benchmark.
The winner becomes the default and the loser stays reachable.
Before MVP, do only the abstraction that makes swapping formats a
configuration change rather than a rewrite: format as a field on the
spec, and the generator dispatching on it.
Everything else in this section is post-MVP.

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

### chr/orphaned-test-fixtures

`test/conftest.py` holds two fixtures building JPEG files with optional
EXIF, `create_test_images` and `create_fake_photo_with_exif`.
Both are producer-side work that moved to NormPic.

They stay while any test module still requests them, so this runs after
`ft/cli-config` removes the modules that do.

- Grep `test/` for each fixture name and confirm no requester remains.
  An orphaned fixture raises no failure, so the grep is the only
  signal.
- Move the orphaned fixtures to `salvage/` with the modules that used
  them.
- Drop the `piexif` import guard and the file-level pyright suppression
  at the top of `test/conftest.py` if nothing needing them remains.
- Remove `piexif` from the dev dependency group once no test imports
  it, running `uv sync` and committing `uv.lock` in the same commit.

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
- CONTRIBUTE forbids batching questions.
  Independent questions batch fine and doing so saves exchanges; the
  rule means only that a question must not be buried in prose.
  Reword it.
- `pyright` and `beautifulsoup4` are unpinned.
  Both changed their finding sets materially across recent versions,
  so a fresh environment can re-red a green gate.
