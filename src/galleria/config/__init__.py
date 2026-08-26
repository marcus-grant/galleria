# src/galleria/config/__init__.py
"""
Canonical configuration for a Galleria build.
Author: Marcus Grant
Created: 2026-08-24
License: AGPL-3.0-or-later
"""

from dataclasses import dataclass
from pathlib import Path

from src.galleria.config.default import OUTPUT_DIR


class MissingConfigError(Exception):
    """Raised when required configuration has no value in any layer.

    Names what was not found, so a run reports the full gap rather
    than one key per invocation.
    """


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

    def has_manifest(self) -> bool:
        """Whether at least one variant manifest is configured.

        Either variant alone is sufficient for a build; neither is
        not."""
        return any((self.original_manifest, self.display_manifest))

    @classmethod
    def from_overrides(cls, **overrides: Path | None) -> "Config":
        """Build a Config from program defaults with overrides applied.

        An override whose value is None is treated as absent, so a CLI
        option left unset falls through to the default layer.
        """
        override_cfgs = {k: v for k, v in overrides.items() if v is not None}
        cfg = cls(
            original_manifest=override_cfgs.get("original_manifest"),
            display_manifest=override_cfgs.get("display_manifest"),
            output_dir=override_cfgs.get("output_dir", OUTPUT_DIR),
        )
        if not cfg.has_manifest():
            msg = "No manifest configured: supply original_manifest, "
            msg += "display_manifest, or both."
            raise MissingConfigError(msg)
        return cfg
