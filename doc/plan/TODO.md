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

**A test in `test_file_processing_dual.py` fails only in a full run.**
`test_skip_processing_when_up_to_date` compares mtimes and passes when
run alone.
It leaves with the module.

**Three helpers named for writing manifests have different shapes.**
`test_validate.py` and `test_manifest_reader.py` each define a
`_write_manifest`, and `test_derive.py` defines a `_write_collection`
that also writes the images its manifest names.
All hand-build a contract this project does not own; they leave when
NormPic ships a consumer package with test factories.

**A test that asserts nothing can still pass.**
A batch-ordering test in `test_filename_service.py` looped over a list
of expected values with `pass` as the body.
The loop was removed and its intent recorded as a comment.
The same shape is worth watching for elsewhere: an unused local in a
test is often a call whose result was never asserted on.
Eleven test modules were also found to contain no `pytest.raises` at
all, so error paths in the code they cover are unexercised.

**Module dependents shrink as deletions land.**
Each deletion removes an importer, and a module with none left can
leave without argument.
`s3_storage.py` now has no dependents; `template_renderer.py` dropped
it with `PICS_BASE_URL`.
Worth asking after each deletion which module just lost a dependent,
and which has reached zero.

**`file_processing.py` cannot simply be deleted.**
It holds thumbnail generation, which Galleria keeps, alongside dual
collection processing, which moved upstream.
Its imports of `exif`, `filename_service`, `photo_validation`, and
`s3_storage` are function-local rather than at module top, so grepping
the import block understates what depends on what.

**Empty scaffolding directories exist and are referenced by nothing.**
`sample-photos/` and `sample-pics/` are tracked and empty.
`cache/`, `content/`, and `temp_test/` are untracked working
directories.

**Two settings are set and never read.**
`SITE_BASE_URL` and `THEME_DIR`.
`PICS_BASE_URL` is gone from the renderer and templates; the setting
itself leaves with `settings.py`.

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

### ft/static-gallery

A correct gallery with no JavaScript at all.

This is the fallback, and it must be right on its own before
anything enhances it.

PR 1 landed the data path: `derive_collection`, `adopt_rendition`,
and the build flags, both defaulting off.
Settled for the presentation PR, against the code:

- `output_dir` is the site root: HTML at `gallery/COLLECTION/`,
  beside the existing `pics/COLLECTION/KIND/` renditions, all links
  relative within that tree.
- Per-photo pages at `gallery/COLLECTION/pic/STEM.html`.
- `index.html` is a byte-identical copy of `page1.html`.
- Next and previous follow merge order, chronological then key;
  no other ordering exists.
- A variant absent from a manifest warns and keeps building.
  A derived file missing on disk stops the build, telling the user
  to re-run derive.
- Delete `site_generator.py`'s now-uncalled source checks with the
  rest of the `prod/pics` residue.
- Thumbnail links the web version.
- Full resolution reachable by an explicit separate link, never from
  the thumbnail itself.
  Originals are often over 20MB.
- Configurable pagination.
  None exists today; the template loops over the whole collection
  unbounded, which for 645 photos is one enormous page.
- Fixed-dimension containers so images arriving do not reflow the
  grid.
- `photos` and `pics` are two names for one thing.
  The loop iterates `pics`; two expressions call `photos|length`.
  Jinja renders an undefined name as empty, so the count reads wrong
  rather than failing.
- The `{% if photos %}` guard at `navbar.j2.html:11` is always false,
  so the navbar count does not render at all rather than rendering
  wrong.
- Both template renders are guarded by `.exists()`.
  Make them fail loud: a silent partial build is plausible output with
  a wrong answer, expensive to diagnose.
- Remove `PICS_BASE_URL` with `_generate_pics_base_url()` and the two
  template references.
  Galleria emits paths; templates never compose URLs.
- `build_gallery`'s data acquisition is stubbed to an empty pics list.
  The render path is intact but fed nothing, and wiring merged
  renditions into it is this item's work.
- Emit relative paths in rendered output.
  Output must be self-contained; a CDN hostname baked into generated
  HTML is stale the moment anything moves.
- Per-photo pages, the no-JavaScript equivalent of the modal.
  Each shows the display rendition, an explicit link to the original,
  a download link, and next and previous navigation.
  The grid links to a page rather than an image, so a click can never
  pull a 26MB original.
  This also makes the eventual modal an enhancement over something
  that already works.

Display order is Galleria's decision, not NormPic's.
Chronological is the default for a wedding.

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
- `base_url` and the dev-versus-prod distinction land here.
  It has no sensible program default: prod is a domain galleria must
  not know, and dev is an address that does not exist until this loop
  does.
- The `serve` command is a stub reporting its unwired state on stderr.
- `debug/template_debug.py` needs a refit.
  Its sample data keys do not match the current template surface, its
  structural analysis counts Alpine and Tailwind artifacts that are
  being removed, and it manipulates `sys.path` at import rather than
  relying on the package.

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

### ft/static-gallery-refinements

Observed on the real collection during the static gallery acceptance
run.
None blocks publishing; each is decided by looking at it.

- Grid loading.
  On LTE the grid shows empty cells with alt text for a noticeable
  time.
  Either thumbs move to progressive JPEG so cells fill smoothly, or
  they stay WEBP behind a neutral placeholder block.
  Decide against a throttled browser run.
- Per-photo page loading.
  The display rendition is roughly 2MB and reads as a wait on mobile.
  Two no-JavaScript mechanisms to try: `srcset` naming preview and
  display so a phone fetches only the preview, and the preview as
  the image's CSS background so it paints first and display paints
  over it.
  ft/preview-modal may make this moot; try it there first.
- Per-photo page numbering.
  Pages are named by stem.
  The maintainer prefers grid position, `pic/1.html` onward.
  Trade-off: position renumbers every URL when a photo is added or
  removed, where the stem is stable; decide by whether the published
  set is frozen.
- Supplied navbar.
  The parent site owns landing page and navigation; galleria emits
  gallery trees only.
  How a caller supplies a navbar is an ecosystem question for the
  director.
  Pre-MVP the built-in one, "COLLECTION Gallery" and a count, stands.

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
- When incremental derivation lands, flip build's `--derive`
  default to opt-out and revisit `--validate` with it.

`PicRenditions` holds relative paths against a root and knows nothing
of where files live.
That stays until marcustack's routing and deploy tail exist, since a
final shape now would be guessing at half the requirements.

### chr/orphaned-module-removal

Remove the modules whose work moved to NormPic and marcustack: EXIF
extraction, filename generation, S3 storage, photo validation, the
processing pipeline, and root-level `settings.py`.

Thumbnail generation lives in `file_processing.py` and stays.
Split it out rather than deleting the file.

If enough lands to make future work less painful without finishing,
stop, document what remains, and move it to a later item.

What this walks into, found by reading rather than grepping:

- `file_processing.py` imports its dependencies inside functions
  rather than at module top, so a grep of import blocks understates
  what depends on what.
- `process_photos.py` is the only caller of the dual-collection path,
  but four test modules reach it: its own, `test_e2e_pipeline.py`,
  `test_batch_metadata_efficiency.py`, and
  `test_file_processing_dual.py`.
  Two are named for services rather than for the command, so the
  coupling is invisible from their filenames.
  `test_dual_hash_integration.py` also imports `file_processing`, and
  sits at the top level of `test/`.
- `create_thumbnail` has no consumer outside its own module, and
  `derive_rendition` supersedes it.
  Delete it here rather than migrating, with its three tests in
  `test_file_processing_comprehensive.py`.
- `generate_batch_metadata` and `merge_partial_metadata_files` write
  partial metadata files and merge them by index, carrying a
  pre-extraction `schema_version` and a `photos` key.
  That is a second manifest format NormPic now owns.
  Delete rather than salvage.
- `generate_gallery_metadata` reads four values through
  `getattr(settings, ...)` with inline defaults, and leaves here.
- `s3_storage.py` has no dependents in `src`.
  Move it to `salvage/` with the tests that name it, and list it in
  the salvage README; marcustack may want it.
  Confirm with a grep that nothing outside those tests imports it
  before moving.
- `prod/` residue remains in `process_photos.py`, `serve.py`,
  `dev_server.py`, and `test_static_assets.py`.
- `link_photo_with_filename` raises rather than returning an error
  value, so its callers correctly ignore its return.
- Remaining `settings.py` dependents are `fs.py`, `exif.py`, and
  `s3_storage.py`.
  `process_photos.py` imports it too, but the command is stubbed and
  the import is dead.
  The module also creates `cache/` and the configured source path at
  import.
- Delete the three test modules covering the settings mechanism:
  `test_settings.py`, `test_settings_isolation_fix.py`, and
  `test_gallery_settings_complete.py`.
  That is 23 tests.
- Remove `exifread`, `timezonefinder`, and `boto3`, which only these
  modules used.
  `pillow` stays with thumbnail generation.
  Run `uv sync` and commit `uv.lock` with the `pyproject.toml` edit.
- `s3_storage.py` has no dependents in `src` except a function-local
  import in `file_processing.py`'s dual-collection path.
  When that path leaves, move `s3_storage.py` to `salvage/` with the
  tests that name it and list it in the salvage README; marcustack
  may want it.
- `prod/` residue remains in `process_photos.py`, `serve.py`,
  `dev_server.py`, and `test_static_assets.py`.
- Verify `python -m galleria build` runs from outside the repository
  root.
  A root-level module cannot ship, and running from the root succeeds
  only because the current directory is on the path.

`doc/settings.md` describes the settings hierarchy, environment
variables, XDG compliance, and Pelican settings, all of which leave
with the module.
Rewriting it as the configuration document waits for the
documentation pass, since the surface is still moving.

This determines the suite's remaining cost.
`test_e2e_pipeline.py` and the GPS timezone tests in
`test_filename_service.py` are nearly all of the current runtime, and
both cover producer work that leaves with these modules.

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

### tst/fixture-dedup

Roughly seven near-identical "create a JPEG with EXIF" factories are
scattered across seven test files; only two live in a `conftest.py`.
Consolidate them.

Worth doing after the module removals in `ft/cli-config`, since some
of these fixtures serve tests that are being deleted anyway.

`_write_collection` has three deliberate copies, in
`test/command/test_derive.py`, `test/services/test_derive.py`, and
`test/command/test_build.py`.
They change together or not at all until this task lands.
`test_build.py` adds `_records`, `_cfg`, `_pages`, and `_cells`;
`test_gallery_template.py` adds `_record`, `_page`, and `_pic_page`.
All belong in conftest modules.

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
