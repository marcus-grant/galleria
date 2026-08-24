# Galleria changelog

Most recent first.
Pre-split history is archived under [changelog/](changelog/).

## 2026-08-24

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
