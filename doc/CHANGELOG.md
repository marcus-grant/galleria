# Galleria changelog

Most recent first.
Pre-split history is archived under [changelog/](changelog/).

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

