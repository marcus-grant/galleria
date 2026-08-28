# src/galleria/config/__init__.py
"""
Canonical configuration for a Galleria build.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Unpack, TypedDict

from src.galleria.config.default import OUTPUT_DIR, RENDITION_SPECS
from src.galleria.models.rendition import Derivation
from src.galleria.models.spec import RenditionSpec


class MissingConfigError(Exception):
    """Raised when required configuration has no value in any layer.

    Names what was not found, so a run reports the full gap rather
    than one key per invocation.
    """


class Overrides(TypedDict, total=False):
    """CLI-supplied overrides, each absent when the option is unset."""

    original_manifest: Path | None
    display_manifest: Path | None
    output_dir: Path | None


@dataclass(frozen=True)
class Config:
    """Configuration for one build, constructed at the CLI boundary.

    Passed down to every stage rather than reached for as global
    state. Holds no resolution logic beyond layering overrides over
    program defaults: the wider precedence chain belongs to a
    dedicated library.
    """

    original_manifest: Path | None
    display_manifest: Path | None
    output_dir: Path
    specs: dict[Derivation, RenditionSpec]

    def has_manifest(self) -> bool:
        """Whether at least one variant manifest is configured.

        Either variant alone is sufficient for a build; neither is
        not."""
        return any((self.original_manifest, self.display_manifest))

    @classmethod
    def from_overrides(cls, **overrides: Unpack[Overrides]) -> "Config":
        """Build a Config from program defaults with overrides applied.

        An override whose value is None is treated as absent, so a CLI
        option left unset falls through to the default layer.
        """
        cfg = cls(
            original_manifest=overrides.get("original_manifest"),
            display_manifest=overrides.get("display_manifest"),
            output_dir=overrides.get("output_dir") or OUTPUT_DIR,
            specs=RENDITION_SPECS,
        )
        if not cfg.has_manifest():
            msg = "No manifest configured: supply original_manifest, "
            msg += "display_manifest, or both."
            raise MissingConfigError(msg)
        return cfg
