# test/models/test_rendition.py
"""
Tests for the rendition models.
Author: Marcus Grant
Created: 2026-08-26
License: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from galleria.models.rendition import Derivation, PicRenditions
from conftest import make_pic


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


class TestPicRenditions:
    """Construction and ordered access."""

    def test_rejects_an_empty_record(self):
        """A record with no renditions raises."""
        key = "foobar"
        with pytest.raises(ValueError, match=rf"(?=.*PicRenditions)(?=.*{key})"):
            PicRenditions(Path(key))

    @pytest.mark.parametrize(
        "fields,expected",
        [
            (["thumb", "original"], [Derivation.DISPLAY, Derivation.PREVIEW]),
            (["display"], [Derivation.ORIGINAL, Derivation.PREVIEW, Derivation.THUMB]),
            (["thumb", "preview", "display", "original"], []),
            (["original"], [Derivation.DISPLAY, Derivation.PREVIEW, Derivation.THUMB]),
        ],
    )
    def test_absent_yields_the_missing_derivations(self, fields, expected):
        """A record reports the derivations it lacks, shallowest first."""
        rends = PicRenditions(Path("2026/a"), **{f: make_pic() for f in fields})
        assert rends.absent == expected

    @pytest.mark.parametrize(
        "fields,expected",
        [
            (["thumb", "original"], [Derivation.ORIGINAL, Derivation.THUMB]),
            (["preview", "display"], [Derivation.DISPLAY, Derivation.PREVIEW]),
            (["thumb", "preview", "display", "original"], list(Derivation)),
        ],
    )
    def test_present_yields_in_derivation_order(self, fields, expected):
        """Renditions come back shallowest first, holding only what is set."""
        rends = PicRenditions(Path("2026/a"), **{f: make_pic() for f in fields})
        assert [d for d, _ in rends.present] == expected

    @pytest.mark.parametrize("field", ["original", "display", "preview", "thumb"])
    def test_accepts_any_single_rendition(self, field):
        """One rendition at any derivation is enough."""
        rends = PicRenditions(Path("2026/a"), **{field: (pic := make_pic())})
        assert getattr(rends, field) is pic

    def test_taken_at_prefers_a_timestamp_at_any_depth(self):
        """A thumb with a timestamp wins over an original without one."""
        stamped = make_pic(timestamp=datetime(2026, 8, 17, 6, 0, tzinfo=timezone.utc))
        rends = PicRenditions(Path("2026/a"), original=make_pic(), thumb=stamped)
        assert rends.taken_at == stamped.timestamp
