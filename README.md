# Galleria

A static photo gallery generator.

Galleria reads photo manifests produced by
[NormPic](https://github.com/marcus-grant/normpic) and generates a
self-contained static gallery: a thumbnail grid, per-photo previews,
and links to larger renditions.
It generates its own thumbnails at build time and writes everything
to a local output directory.

Galleria does not deploy what it builds, and does not process or
modify photos.
Those belong to other projects in the ecosystem.

## Status

Pre-v0.1, under active development.
The manifest-consuming interface is being built; the current code
predates the split of this repository into NormPic, marcustack, and
b3c32, and parts of it are residue awaiting removal.

See [doc/plan/TODO.md](doc/plan/TODO.md) for what is being worked on
now.

## Documentation

[doc/README.md](doc/README.md) is the documentation index and the
place to start.

The documents worth knowing about directly:

- [CONTRIBUTE](doc/CONTRIBUTE.md).
  How work is done here.
  Read before making a change.
- [TODO](doc/plan/TODO.md).
  Planned, active, and imminent tasks.
- [ROADMAP](doc/plan/ROADMAP.md).
  Post-MVP direction.

## Ecosystem

Galleria is one component of a wider ecosystem, and the whole is more
than the sum of its parts.
NormPic produces the manifests it consumes; marcustack orchestrates
the pipeline and owns deployment.
[doc/README.md](doc/README.md) describes each relationship.

## License

GNU Affero General Public License v3.0 or later.
See [LICENSE](LICENSE).
