# src/galleria/models/rendition.py
"""
Records for a photo's renditions.

Author: Marcus Grant
Created: 2026-08-21
Revisions: [2026-08-26]
License: AGPL-3.0-or-later
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import total_ordering
from pathlib import Path

from galleria.models.normpic import Pic


@total_ordering
class Derivation(Enum):
    """Rendition kinds ordered by derivation, source first.

    Ordering is by derivation depth: ORIGINAL is the archive and each
    later member derives from a shallower one. Members are always
    truthy, so a guard cannot silently skip the archive.
    This ensures the rendition class most likely to be manifested...
    carries the most provenance on metadata and fidelity.
    I.e. An 'original' is more lilkely to have the best quality and metadata than
    a 'thumb'nail generated from it.
    """

    ORIGINAL = 1
    DISPLAY = 2
    PREVIEW = 3
    THUMB = 4

    def __lt__(self, other: "Derivation") -> bool:
        """Order by derivation depth, shallower first."""
        return self.value < other.value


@dataclass(frozen=True)
class PicRenditions:
    """One photo's renditions, sharing a pairing key.

    Renditions are ordered by derivation. An absence deeper than
    a present rendition is generated from it.
    An absence shallower aliases to the nearest present one.
    That's because fidelity can't be recovered, only reduced.
    That ordering is what lets a record be useful without knowing
    which of its renditions were manifested and which were derived.

    Manifests are the only source of picture data.
    That fact is proven in this class's validator,
    requiring at least on rendition on construction.
    The fact shallower derivations are aliases to lower ones when absent...
    means we know the least derived class carries manifested, not generated data.
    So a use of this class only on manifested data, uses this constraint as fact.
    So this model with absent renditions means it's the manifested version only.
    Then fully occupied versions means either only manifested or manifest with derived.
    """

    key: Path
    original: Pic | None = None
    display: Pic | None = None
    preview: Pic | None = None
    thumb: Pic | None = None

    def __post_init__(self) -> None:
        """Reject a record with no renditions at all."""
        if len(self.present) <= 0:
            raise ValueError(f"PicRenditions for {self.key} has no variants")

    @property
    def absent(self) -> list[Derivation]:
        """Derivations this record does not hold, in derivation order."""
        return [d for d in Derivation if getattr(self, d.name.lower()) is None]

    @property
    def present(self) -> list[tuple[Derivation, Pic]]:
        """Renditions this record holds, in derivation order, shallowest first."""
        return [
            (d, pic)
            for d in Derivation
            if (pic := getattr(self, d.name.lower())) is not None
        ]

    @property
    def taken_at(self) -> datetime:
        """From the shallowest present rendition, prefer timestamp over mtime."""
        for _, pic in self.present:
            if pic.timestamp:
                return pic.timestamp
        most_original_pic = self.present[0][1]
        return most_original_pic.mtime
