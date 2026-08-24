# test/services/test_rendition.py
"""
Tests for merging variant manifests into rendition records.

Author: Marcus Grant
Created: 2026-08-21
License: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
from pathlib import Path

from galleria.models.normpic import NormpicManifest
from galleria.services.rendition import merge_variants
from conftest import make_pic

_UTC = timezone.utc


def _make_manifest(**overrides) -> NormpicManifest:
    """Creates a test manifest record carrying default _make_pic pics."""
    defaults = {
        "version": "0.1.0",
        "collection_name": "wedding",
        "collection_root": Path("."),
        "generated_at": datetime(2026, 8, 17, 9, 0, tzinfo=_UTC),
        "pics": [make_pic()],
    }
    return NormpicManifest(**{**defaults, **overrides})


class TestMergeVariants:
    """Tests for merge_variants."""

    def test_merges_a_photo_present_in_both(self):
        """A relative path in both manifests yields one record with both."""
        a, b = _make_manifest(), _make_manifest(pics=[make_pic(size_bytes=5000)])
        rendition = (renditions := merge_variants(a, b))[0]
        assert len(renditions) == 1
        assert rendition.original is not None
        assert rendition.display is not None
        assert rendition.relative_path == rendition.original.relative_path
        assert rendition.relative_path == rendition.display.relative_path

    def test_carries_a_photo_missing_its_display(self):
        """A relative path only in the original manifest has no display."""
        a_pic, b_pic = make_pic(), make_pic(relative_path=Path("2026/b.png"))
        a, b = _make_manifest(pics=[a_pic, b_pic]), _make_manifest(pics=[a_pic])
        assert len(renditions := merge_variants(a, b)) == 2
        by_path = {r.relative_path: r for r in renditions}
        assert by_path[Path("2026/b.png")].display is None
        assert by_path[Path("2026/b.png")].original is not None

    def test_carries_a_photo_missing_its_original(self):
        """A relative path only in the display manifest has no original."""
        a_pic, b_pic = make_pic(), make_pic(relative_path=Path("2026/b.png"))
        a, b = _make_manifest(pics=[a_pic]), _make_manifest(pics=[a_pic, b_pic])
        assert len(renditions := merge_variants(a, b)) == 2
        by_path = {r.relative_path: r for r in renditions}
        assert by_path[Path("2026/b.png")].display is not None
        assert by_path[Path("2026/b.png")].original is None

    def test_returns_records_in_capture_order(self):
        """Records are ordered by capture time across both manifests."""
        early = make_pic(
            relative_path=Path("2026/b.png"),
            timestamp=datetime(2026, 8, 17, 6, 0, tzinfo=_UTC),
        )
        late = make_pic(timestamp=datetime(2026, 8, 17, 10, 0, tzinfo=_UTC))
        a, b = _make_manifest(pics=[late]), _make_manifest(pics=[early])
        renditions = merge_variants(a, b)
        assert [r.relative_path for r in renditions] == [
            Path("2026/b.png"),
            Path("2026/a.jpg"),
        ]
