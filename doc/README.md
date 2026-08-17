# Galleria documentation

Galleria generates a static photo gallery from a NormPic manifest.
It reads manifests and photos from paths given to it at invocation,
and writes a self-contained site to a local output directory.
It does not deploy that output.

This directory holds Galleria's documentation.
Each subdirectory has a README acting as its index; this file indexes
those, and links the standing documents that live at this level.

## Core documents

- [CONTRIBUTE](CONTRIBUTE.md).
  How work is done here: planning, test-driven development, commits,
  branches, style, and documentation discipline.
  Read before making a change.
- [QA](QA.md).
  How a change is verified before it is submitted: the review ladder,
  the probe kit, and the manual acceptance run.
- [CHANGELOG](CHANGELOG.md).
  What has landed, most recent first.
- [Plan](plan/).
  The task tracker and the post-MVP roadmap.
  What is being worked on now and what is being considered later.

## Topics

- [Architecture](architecture/).
  System design, component structure, and the seams between them.
- [Command](command/).
  The command-line interface: each command's usage, options, and
  workflows.
- [Services](services/).
  The service layer and its components.
- [Testing](testing/).
  Test infrastructure, fixtures, and patterns.
- [Guides](guides/).
  Setup and configuration walkthroughs.
- [Deployment](deployment/).
  Deployment procedures.
  Superseded in part: marcustack now owns deploy and CDN upload, and
  this material is being reconciled against that.
- [Utilities](util/).
  Utility functions, implementation notes, and technical research.
- [Changelog archive](changelog/).
  Older changelog entries, rotated out of live changelog & split by version.

## Related projects

Galleria is one component of a wider ecosystem, and is better
understood alongside the projects it depends on and feeds.

- NormPic.
  Produces the photo manifests Galleria consumes.
  Owns the manifest contract; Galleria copies none of it, and points
  at the tagged contract document instead.
  Status: v0.1.1 published, v0.1.0 contract frozen.
- marcustack.
  Composer and orchestration layer.
  Runs NormPic, then Galleria, and owns deploy and CDN upload.
  Supplies Galleria its manifest and output paths at invocation.
  Status: bootstrapped; runs NormPic as a verified pipeline stage.
- retro-theme.
  Shared CSS design system Galleria consumes once it exists.
  Galleria's stylesheet keeps its values in CSS custom properties so
  adopting it is an override rather than a rewrite.
  Status: parked pre-bootstrap, documentation only.
- personal-site.
  The 11ty site renderer.
  Galleria's static output is integrated at a gallery subdomain, and a
  future 11ty plugin would bring Galleria into its build.
  Status: bootstrapped and parked.
