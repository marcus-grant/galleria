# Galleria changelog

Most recent first.
Pre-split history is archived under [changelog/](changelog/).

## 2026-08-25

### ft/cli-config

Give Galleria the interface its caller invokes it through.

- Added a frozen `Config` carrying the manifest paths and the output
  directory, constructed at the CLI boundary and passed down rather
  than reached for as global state.
- Added a program-default layer in `galleria/config/default.py`.
  Overrides layer over it, with an unset CLI option treated as absent.
- Settled that inputs have no defaults and outputs do.
  A wrong input guess reads the wrong collection silently; a wrong
  output guess writes a directory you delete.
  `OUTPUT_DIR` defaults to `_build`.
- Raised `MissingConfigError` when neither manifest is configured.
  Either variant alone builds, so either alone validates.
- Widened `merge_variants` to accept an absent variant manifest.
- Added `resolve_inputs`, shared by both commands: it resolves
  config, reads the manifests config names, and reports through the
  CLI rather than raising into its caller.
- Added the `validate` command.
  Quiet on success with one line naming the collection and pic count;
  non-zero and named on failure.
- Gave `build` the shared manifest options and `--output-dir`, and
  had it resolve its inputs before building.
- Settled that each stage validates its own outputs and trusts its
  inputs.
  Checking that manifested files exist is NormPic verifying its own
  output, done a second time by a consumer that did not write them.
- Deleted `photo_metadata.py` and its tests.
  The manifest supersedes the metadata service it wrapped.
- Centralized the `Pic` test factory, which two modules held copies
  of.

## 2026-08-24

### ref/module-layout

Move the source tree under a package and replace the entry point.

- Moved `src/` to `src/galleria/` so the package name matches the
  project name.
  Imports, patch targets, and hardcoded path literals follow.
- Replaced `manage.py` with `galleria/cli.py` and
  `galleria/__main__.py`.
  Invocation becomes `python -m galleria`, and the Justfile recipes
  and development server subprocess follow.
- Added a setuptools build backend and package discovery, with an
  editable install so the package resolves outside the test suite.
  No console script and no distribution metadata: the package is
  importable, not yet distributable.
- Rewrote `doc/command/README.md` for the current command surface.
- Moved `doc/deployment/`, `doc/guides/bunnycdn-setup.md`, and
  `doc/command/collection-stats.md` to `salvage/`.
  Deployment and CDN work is owned by the composer project.
- Recorded the production rendition values before the settings module
  holding them is removed: web variants at 2048x2048, thumbnails at
  400x400, quality 85 for both JPEG and WebP.

The suite is unchanged at 254 passed and 3 skipped, matching the
baseline taken before the move.

### ft/manifest-reader-v01

Read NormPic manifests and merge variants into renditions.

- Added `read_manifest`, building typed records from one manifest.
  Timestamps parse at read time and an absent `collection_root`
  defaults to the current directory.
- Refused a manifest outside the supported major.minor, accepting any
  patch level within it.
- Refused a timestamp carrying a numeric offset rather than `Z`, per
  the contract's canonical form.
- Added `merge_variants`, pairing on `relative_path` and ordering by
  capture time across both manifests.
- Renamed the manifested variants from full and web to original and
  display.
  Original is accurate for an untouched source, and marcustack's
  routing prefixes should follow.
- Settled that both variant manifests share one `collection_name`,
  distinguished by their roots rather than by name.
- Verified against the production collection: 645 pics, pairing
  645/645, none falling back to `mtime`, ordering monotonic.

Manifest errors are typed: `ManifestError` carries the manifest path,
with `MissingField`, `UnsupportedVersion`, and `MalformedField` under
it.

## 2026-08-17

Migrated to a new remote and brought the gate to green.

- Repository moved from `static-gallery` to `galleria`.
- Ruff clean from 112 findings, pyright from 152, both now zero.
  Most cleared by moving producer-side modules out of the tree; the
  rest were unused imports, dead locals, and genuine typing errors.
  Findings in code the config rework removes are suppressed with the
  reason stated above the directive.
- Suite down from 85 seconds to under 7, and from 342 tests to 207.
  A single module accounted for 44 of those seconds.
- Added `salvage/`, holding modules pulled out of the tree pending a
  decision, with an inventory in its README.
  It is excluded from linting, type checking, and test collection.
  The former `deleteme-normpic-modules` buffer is tracked under it for
  the first time.
- Documentation for salvaged modules moved with them and was removed
  from the indexes.
- Added a `Justfile`, whose `check` recipe runs the gate in order.
- Consolidated pytest configuration into `pyproject.toml` and added
  pyright configuration so it resolves the project environment.

## 2026-08-15

### Documentation reorganization

- Rewrote `doc/CONTRIBUTE.md` to the current ecosystem standard.
- Split verification into `doc/QA.md`.
- Moved planning documents under `doc/plan/`: TODO and ROADMAP.
- Deleted the duplicate v0.1 plan, which had drifted from TODO.
- Consolidated changelog archives under `doc/changelog/`, split by
  version rather than by date.
- Archived all pre-split history as `doc/changelog/v0.0.md`.
- Rewrote `doc/README.md` as an index with a Related projects section.
