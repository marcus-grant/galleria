# Quality assurance in Galleria

This document is the source of truth for how a change is verified
before it is submitted.
`doc/CONTRIBUTE.md` holds the conventions a change must satisfy: how it
is planned, tested, committed, and documented.
This document holds how those claims are checked.
It does not restate them; read that document first.

Quality assurance is a gated, progressive hunt.
Its premise is that the green suite already proves mechanical
correctness, so review never re-derives that the code works.
Review spends its effort only on what tests cannot catch: a misread
spec, a missing but required thing, a false claim, and a latent trap.

Review grades commits against the approved plan, not against the
specification directly.
The plan is what was agreed; the specification is what the plan claimed
to satisfy, and reopening that during review turns a check into a
redesign.
Review starts from the author's summary, before any repository read.

## The author's summary

After each commit the author reports four things: the commit subject,
one sentence of what changed, pass or fail, and a `git diff --stat`.

No diff, no plan restatement, and no test output unless asked.

The stat is required, because scope drift is invisible in prose.
A one-line change that touched four hundred lines shows up only as a
number.

The author escalates to full detail unprompted, without waiting to be
asked, on any of: a test failure, scope expanding beyond the plan,
documentation found to contradict the code, or an ambiguous contract
or field-mapping question.

## The ladder

The checks run cheapest first.
Each rung runs only when its failure is possible for this change, which
is read for free from the plan and the summary.
A rung that cannot fail here is skipped, not performed for form.
When the cheap rungs come back clean and no expensive rung applies, the
hunt short-circuits and the change is signed off.

- Summary against plan: does it describe doing what was approved?
  Watch for overclaims ("complete", "all", a specific count) and for
  scope beyond the plan.
- Scope, from the stat: only the expected files, and a size
  proportionate to the plan?
  A disproportionate diff is stopped and flagged before any content is
  read.
- Signatures, by targeted diff or grep rather than reading whole files:
  is the substantive change the one that was specified?
- Claims against ground truth, run only when the summary makes a
  falsifiable claim such as a count, an "all", or a "complete":
  verify it against the repository, not the prose.
- Completeness, run only when the change contributes to a defined set
  whose tests discover their members dynamically: a missing required
  member raises no failure, so check the set against its inventory.
- Trap reasoning, run only when the change touches correctness-bearing
  logic: the failure classes a passing suite does not exercise, such as
  vacuous conditions, boundary inputs, one defect producing many
  errors, and misattributed errors.

## The probe kit

A few load-bearing reads, around fifteen lines total, confirm that
tests assert what was intended.
Derive the targets from the plan, which names the new symbol, the
removed token, and the assertions it promised:

- Grep `assert` in the changed test files to read the assertions
  themselves, not just the test names.
  This catches an assertion that a good name hides but that verifies
  little.
- Grep the source for the removed or old token to confirm the migration
  is complete and any trap pattern is gone.
  Empty output is the proof.
- Grep `test/` for the newly introduced symbol to confirm a test
  exercises it, rather than it being defined and never called.

Use `grep -I --include='*.py'` for Python, widening the include when
the change is in templates, stylesheets, or scripts.
Exclude generated and vendored trees so build output does not muddy the
results: `__pycache__/`, `_build/`, `prod/`, and `.venv/`.

These greps confirm the tests assert the right thing for the cases they
name.
That is their ceiling.
Extending confidence past the cases the author chose requires
independent ground truth: a real manifest, a real photo collection, or
a value computed by something other than the implementation under test.

## Deleting a rung

The strongest check is one that no longer needs a reviewer.
When a failure mode recurs, push it into a suite assertion so it goes
red on its own instead of costing a review pass.

For example, asserting that every rendered thumbnail links the web
variant means a regression to full-resolution links can never again
pass silently.
A recurring manual check is a missing test.

## Per-commit sign-off on fragile changes

Most changes are signed off as a unit.

A dependency-ordered change whose commits are preconditions for one
another is signed off per commit instead: plan the one commit, sign
off, implement, summarize, sign off, commit, then the next.
Binding a reader to an upstream contract, or a template cutover
spanning renderer, template, and tests, has this shape.
The per-commit rhythm prevents an out-of-order change that breaks an
intermediate tree.

Where such an ordering exists, encode it in the tracker section for
that change, with the reason each step precedes the next.

## The manual acceptance run

The green suite proves mechanical correctness on fixtures.
It does not prove the gallery behaves on real data, and it says nothing
at all about how the result looks.
Both gaps matter here, because this project's output is a rendered
page.

### On real data

For changes that touch the end-to-end path, the maintainer runs the
build on a real collection before the final sign-off.
Check what fixtures cannot: no dangling links, no missing thumbnails,
images open through the produced links, every photo in the manifest
present in the output, and the variant a link points at is the variant
intended.

The last of those is the one that matters most in this project.
A thumbnail reaching a full-resolution original is a defect a green
suite will happily report as a pass.

### In a browser

Any change with a visible effect gets looked at in a browser before the
change is submitted.
Markup and stylesheet diffs are a poor instrument for judging whether a
layout holds together, whether images arrive without the grid
reflowing, and whether the page reads well while being scrolled
quickly.

State in the submission that this run happened and what was observed.
"Looked right" is not an observation; name what was checked.

## The reviewer's own analysis is not exempt

The same standard the reviewer applies to the author's claims applies
to the reviewer's own reasoning.

A hazard the reviewer infers (a contract collision, a missing
dependency, an ordering risk) is a claim, not a finding, until it is
checked against the code or the contract document.
Do not escalate an inferred hazard to the maintainer as a decision
before reading the source that would confirm or dismiss it.
If the specification or the code already answers a question, read it;
do not ask the maintainer.
The maintainer's time is spent only on genuine direction calls, not on
questions the repository already answers.

When the reviewer is wrong, the correction is stated plainly once
("that was wrong; it is X") and the analysis moves on.
A corrected position is not restated as though it were the original
position, and the same fact is not re-explained in varying forms.
Both make a session impossible to track.

## Sign-off

A change is signed off when all of the following hold:

- Its commits match the plan.
- Its scope is contained and proportionate.
- Every falsifiable claim checks against ground truth.
- The applicable trap and completeness rungs found nothing.
- The manual acceptance run has happened where it applies, and what it
  observed has been stated.

Open items go back as specific, surgical requests, not as a direction
to start over.