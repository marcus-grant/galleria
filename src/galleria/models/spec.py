"""
Specifications for derived renditions.
Author: Marcus Grant
Created: 2026-08-26
License: AGPL-3.0-or-later
"""

from dataclasses import dataclass
from enum import Enum, nonmember


class RenditionSpecError(ValueError):
    """A rendition spec that cannot describe an encode."""


class Format(Enum):
    """Output formats a rendition can be encoded to."""

    JPEG = "jpeg"
    PJPEG = "pjpeg"
    WEBP = "webp"

    ALIASES = nonmember(
        {
            "jpg": "JPEG",
            "jpeg": "JPEG",
            "pjpg": "PJPEG",
            "pjpeg": "PJPEG",
            "progjpg": "PJPEG",
            "progjpeg": "PJPEG",
            "progressivejpeg": "PJPEG",
            "webp": "WEBP",
        }
    )

    @classmethod
    def _error_message(cls, value) -> str:
        return f"format {value!r} unknown"

    @classmethod
    def _coerce(cls, value: str) -> "Format":
        """Resolve a config string to a member, or raise RenditionSpecError."""
        key = value.strip().lower().lstrip(".")
        key = key.replace("-", "").replace("_", "")
        name = cls.ALIASES.get(key)
        if name is None:
            raise RenditionSpecError(cls._error_message(value))
        return cls[name]

    @classmethod
    def _missing_(cls, value: object) -> "Format | None":
        """Coerce a string alias to a member, ignoring case and separators."""
        if not isinstance(value, str):
            raise RenditionSpecError(cls._error_message(value))
        return cls._coerce(value)


@dataclass
class RenditionSpec:
    """How one rendition kind is produced."""

    format: Format
    max_dimension: int
    quality: int

    def __post_init__(self) -> None:
        """Reject a spec that cannot describe an encode."""
        if (self.quality < 1) or (self.quality > 95):
            raise RenditionSpecError(f"quality {self.quality} outside 1-95")
        if self.max_dimension < 1:
            raise RenditionSpecError(f"max_dimension {self.max_dimension} less than 1")
