# Contributing to Galleria

This document is the canonical statement of how work is done in this
repository: how changes are planned, tested, committed, and documented.
It is the source of truth for these conventions.
Other documents point here rather than restating them, so the rules
live in one place and do not drift.

How a change is verified before it is submitted lives in `doc/QA.md`.
This document overviews that process and does not restate it.

Galleria is one component of a wider ecosystem.
It consumes a photo manifest produced by NormPic and emits a static
gallery to local output.
Deployment of that output is owned by a separate composer project and
is out of scope here.

## Security

This is the golden rule of this repository, above every other rule in
this document.

Never read shell environment variables.
This repository's history includes credentials for remote storage.
Reading the environment risks leaking a secret into logs, command
output, a commit, or a generated file.
Recovering from such a leak means rotating live credentials, which is
slow, disruptive, and entirely avoidable.
A leak into an assistant session is a leak.

There is no contribution that requires reading the environment.
The single exception is a `GALLERIA_*` path variable named explicitly
by the maintainer for a specific task, such as pointing a build at a
photo collection.
Never enumerate the environment.
Never read a variable the maintainer has not named.
Never echo one whose value is not a path.

## Ways of working

Every change moves through the same path: plan, review, implement,
verify, submit.
Three roles participate, whoever fills them:

- Author: writes the plan, implements it, and reports a short summary
  after each commit.
- Reviewer: signs off the plan before any code is written, and runs
  quality assurance before the change is submitted.
- Maintainer: sets direction, approves, and performs the merge.

Plan-first is the rule.
No implementation begins before the plan is reviewed and signed off.
The plan is also the baseline that review grades against, so the
effort spent making it precise is repaid at review time.

## Planning

A change begins as a written plan: an ordered task list precise enough
that following it top to bottom produces the change and satisfies the
conventions in this document.

A well-formed plan has this shape:

- The first task is branching.
  `git checkout -b <prefix>/<slug>` from the current head, using one of
  the branch prefixes below.
- The body is a sequence of spec-then-test-then-implement cycles,
  grouped by behavior rather than by category.
  Each cycle names the spec it satisfies, the test that pins it, and
  the implementation that makes the test pass.
  Related cases for one rule stay in one cycle, because they verify a
  single boundary and a reviewer should see them together.
- Where a behavior has a known boundary or trap (an empty manifest, a
  photo present in one variant set but not the other, a missing EXIF
  timestamp), the plan names the test that closes it.
  This is required wherever such a boundary exists, because a named
  boundary test is what allows the plan to be evaluated and what
  review verifies directly.
- The plan cites the spec source each cycle satisfies.
  For manifest consumption that source is the installed NormPic
  package: its shipped JSON schema and its contract document, read
  from the installed distribution rather than from a checkout path.
  It is never a copy of those facts held in this repository.
- The plan states scope concretely: which files change and roughly how
  much.
  A later diff that is disproportionate to this is a signal of drift.
- The change closes with two commits by default: a `Doc:` commit for
  any reference documentation the work added, changed, or invalidated,
  then a `Pln:` commit updating `doc/plan/TODO.md` and `doc/CHANGELOG.md`.
  Either is skipped when the change genuinely touched nothing in its
  scope, but both are the default and their absence should be
  deliberate.
  The `Pln:` commit is last, leaving the change ready to submit.

When a planned change is recorded in `doc/plan/TODO.md`, it takes the
same shape: a branch-named section, a short framing of the work, an
ordered task list that opens with the branch task, runs the cycles
through the middle, and closes with the Doc and Pln commits described
above.
A reader should be able to execute the section without reconstructing
the plan.

## Test-driven development

Test-driven development is the default discipline for any change that
alters behavior.

At the keyboard the rhythm is red, green, refactor: write a failing
test, make it pass, then improve the code with the test still green.
This is a working rhythm, not a commit boundary.
A single commit may contain several closely related cycles when they
form one coherent piece of work.

Build one behavior at a time, in small steps with clear logical breaks.
Run the relevant tests immediately after each testable addition.
Broken code is never committed: every commit leaves the suite green.
Before writing tests, know what already exists.
Read the `conftest.py` files covering the area you are working in,
and look at how neighboring test modules are laid out: what is
grouped into classes, what shares setup, and which helpers or
factories build the objects under test.
Fixtures are centralized so they can be reused, and a test that
rebuilds a fixture's work inline is a duplicate that drifts.
This costs a couple of minutes and is the difference between adding
to the suite and growing a parallel one beside it.

### Front-end work

Templates, stylesheets, and client-side scripts get the same
discipline with narrower ambition.
Pin what carries meaning and would break silently if it changed:
the structural elements and attributes another part of the system
depends on, the presence of a class a stylesheet targets, a link
pointing at the intended variant, a lazy-loading attribute, the
ordering of rendered items.
BeautifulSoup structural assertions are the mechanism for markup.

Do not pin what is merely visual.
Exact pixel values, color literals, spacing, and font choices change
often, and asserting them produces tests that fail on every design
tweak without ever catching a defect.
The suite says the structure is right; a human eye says it looks right.
The manual acceptance run in `doc/QA.md` is where the second half of
that happens, and it is required for any change with a visible effect.

## Commits and branches

### The pre-commit quality gate

Before every commit, all applicable checks must pass, in this order:

1. `uv run ruff check`
2. `uv run pyright`
3. `uv run pytest` (the full suite, not a single file)

This list is the definition of the gate.
When a task-runner recipe wraps it, the recipe follows this list, so a
change here requires the same change there.

Use `uv run`, never a bare interpreter.
Run a focused file with `uv run pytest test/test_name.py -v` during
development, but always run the full suite before committing.

### Commit sizing

Group commits by logical coherence.
A commit is a self-contained unit of related work that leaves the tree
green.

Sizes below are guidelines, not gates:

- A code commit around 300 lines is a soft ceiling.
  Going well past it usually means the work was divided badly, though
  not always.
  Staying under it is normal and is not a target to pad toward.
- Roughly two to eight commits per change.
  Added complexity can justify exceeding this.

A coherent, slightly larger unit is better than fragmenting one
behavior across many tiny commits or changes.

### Commit message format

- Title: at most 50 characters including the prefix.
- Title starts with a capital letter or a digit after the prefix and
  colon.
- Body: lines at most 72 characters, using "-" bullets with nested
  detail.
- Even-spaced indentation on every body line, no wrapped continuation
  lines, no soft wrapping.
- No signature block: no emoji, links, or co-authored-by lines.

Commit prefixes:

- `Pln:` planning and task tracker updates
- `Ft:` new feature or capability
- `Fix:` bug fix
- `Ref:` pure refactor, no new behavior
- `Doc:` documentation
- `Chr:` chore and maintenance
- `Tst:` test-only changes

### Branch names

Branches use a lowercase prefix, a slash, and a kebab-case slug:
`pln/`, `ft/`, `fix/`, `ref/`, `doc/`, `chr/`, `tst/`.
Examples: `ft/manifest-reader`, `ft/lazy-scroll`.
Refer to other work by branch name, never by an ordinal position,
which loses meaning when the sequence shifts.

## Quality assurance

Quality assurance is a gated, progressive hunt run before a change is
submitted.
Its premise is that the green suite already proves mechanical
correctness, so review never re-derives that the code works.
Review spends its effort only on what tests cannot catch: a misread
spec, a missing but required thing, a false claim, and a latent trap.
It grades commits against the approved plan, not against the
specification directly, and it starts from the author's summary before
any repository read.

Three things block submission: the plan is signed off before code is
written, the QA ladder finds nothing on the rungs that apply, and any
change with a visible effect has been looked at in a browser.

`doc/QA.md` is the source of truth for how all of this is run: the
author's per-commit summary, the ladder and when each rung applies, the
probe kit, per-commit sign-off on dependency-ordered changes, the
manual acceptance run, and the conditions for sign-off.
Read it before reviewing.
It is not restated here.

## Coordinating work across roles

The reviewer role is often a coordinator: a conduit between an author
and the review standard in these documents.
The author writes plans and implements; the coordinator grades against
the plan, runs QA, and relays sign-offs and surgical change requests;
the maintainer merges.

### Relay mechanics

- The author reports plans and per-commit summaries; the coordinator
  reviews against the repository, never against the prose alone.
- Shell output moves by clipboard relay: the maintainer runs commands
  and pastes results back, so coordinator requests should be targeted
  (specific greps and line ranges), not "send me the whole file".
- One command per exchange.
  Multi-command blocks are brace-grouped before the pipe.
  Never issue a `cd` command; shell directory state cannot be tracked
  across the relay.
- Shell commands carry no inline comments.
- When a commit is ready, the coordinator provides the shell commands
  and the commit message as separate blocks, so the message can be
  pasted without being embedded in a command.
- The coordinator writes commit messages; the author does not.
- Every proposed code or text change is delivered in a fenced block
  with its destination stated adjacent to the fence: the file path in
  backticks, and enough surrounding context to place it (the section
  name, or the exact lines it replaces).
  A fence with no stated destination is incomplete.
- A fenced block containing an inner code fence uses four or five
  backticks on the outer fence, so copy and paste does not break.

### Communication norms

- Terse and direct; one topic at a time.
- Questions front-loaded, never buried in prose, never batched.
- A single concrete recommendation, not a menu of options.
- State a correction once and move on; do not restate a settled call.
- Recalibrate immediately when the maintainer flags drift, without
  re-litigating.
- Escalate a scope change rather than folding it in silently.
- Read the code before making a claim about it.
  Never infer behavior from a name alone.

## Style and formatting

These rules apply to all text in the repository: code, comments,
docstrings, commit messages, and pull request descriptions.

- ASCII only.
  No em dashes, no arrows, no emoji, no decorative Unicode.
  Where a sentence wants an em dash, end the sentence and start
  another.
- Line length depends on context:
  - Commit body lines at most 72 characters (enforced).
  - Prose and documentation lines at most 80 characters.
  - Python code lines at most 88 characters (ruff default).
- In prose, sentence-ending punctuation is followed by a newline.
  A sentence longer than the prose limit breaks at a natural point
  before the limit.
- Singular directory and field names by default: `doc/` not `docs/`,
  `test/` not `tests/`, `asset/` not `assets/`.

Code conventions:

- Functions carry a docstring.
- Code is type annotated; prefer dataclasses for basic data structures.
- Match the patterns and formatting of neighboring files.
- Verify a library is available before using it.
- Follow PEP 8 and ruff: no trailing whitespace, a blank line at end of
  file, two blank lines between top-level definitions, one between
  methods, spaces around operators and after commas.
- Two-space indentation in templates, stylesheets, and JavaScript.
  Python keeps four.

## Documentation discipline

### Single source of truth

A fact lives in exactly one place.

Galleria owns no manifest contract.
The manifest's fields, semantics, and canonical forms are NormPic's,
and the authoritative statements of them are the schema and contract
document shipped inside the installed NormPic package.
Never copy a schema, a field list, or a set of semantics into this
repository.
A code-side copy sitting alongside a canonical artifact drifts apart
silently, and that failure has already occurred once in this
ecosystem.
Read from the installed package and point at it.

Facts that Galleria does own, such as its output layout and its
configuration surface, live in one document each under `doc/`.
Do not restate them elsewhere.

### Documentation hierarchy

Every document is reachable from the root README through a chain of
links.
The top-level README gives the overview and links into `doc/README.md`.
Each directory has a README acting as its index.
A document links to peers at its own level or to a subdirectory README
one level down, never deeper.
No document is an orphan.

### Writing for readers

Documentation is written for a developer reading it cold, with no
knowledge of how it was produced.
Never reference assistant conversations, sessions, or any structure
that exists only because work was split across them.
This applies to every document, README, design note, and code comment.

Every design document carries a "Related projects" section naming its
cross-references and each one's current status: exists, planned, or
deferred.
A reader should always be able to see that this project sits inside a
wider ecosystem.

### Maintaining state during a change

`doc/plan/TODO.md` and `doc/CHANGELOG.md` are maintained throughout,
treated as append-and-prune.
Do not read either file end to end to make an edit.
Find the section with `grep -n`, view a few lines around it, and edit
surgically.

Where the CHANGELOG entry is written depends on the change's span.
A change spanning multiple sessions appends one concise line after each
commit, under today's date header, so the record survives a session
ending mid-change.
The final commit then consolidates those lines into one summary block
and deletes the granular ones.

A change completed within a single session skips the running lines and
writes its CHANGELOG entry once, in the final commit.
Writing lines only to delete them in the same sitting is churn, not a
record.

The final commit deletes completed task lines from `doc/plan/TODO.md`
rather than marking them done.
The CHANGELOG is the record of what was done; TODO is the record of
what remains.
