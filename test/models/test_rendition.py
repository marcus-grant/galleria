"""
Tests for the rendition models.
Author: Marcus Grant
Created: 2026-08-26
License: AGPL-3.0-or-later
"""

import pytest

from galleria.models.rendition import Derivation


class TestDerivation:
    """Ordering and comparison guarantees."""

    def test_orders_source_to_deepest(self):
        """ORIGINAL precedes DISPLAY precedes PREVIEW precedes THUMB."""
        assert Derivation.ORIGINAL < Derivation.DISPLAY
        assert Derivation.DISPLAY < Derivation.PREVIEW
        assert Derivation.PREVIEW < Derivation.THUMB

    def test_reflected_and_filled_comparisons_hold(self):
        """Greater-than, and both inclusive forms, agree with __lt__."""
        assert Derivation.THUMB >= Derivation.THUMB
        assert Derivation.THUMB > Derivation.PREVIEW
        assert Derivation.PREVIEW >= Derivation.DISPLAY
        assert Derivation.ORIGINAL <= Derivation.DISPLAY
        assert Derivation.ORIGINAL <= Derivation.ORIGINAL

    @pytest.mark.parametrize("case", list(Derivation))
    def test_members_are_truthy(self, case):
        """Every member is truthy, including ORIGINAL."""
        assert case

    def test_members_are_hashable(self):
        """Members serve as dict keys, unbroken by ordering support."""
        d = {member: member.value for member in Derivation}
        assert all(d[member] == member.value for member in Derivation)
