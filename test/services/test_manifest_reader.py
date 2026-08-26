# test/services/test_manifest_reader.py
"""
Tests for reading a NormPic manifest into pic records.

Author: Marcus Grant
Created: 2026-08-17
License: AGPL-3.0-or-later
"""

from datetime import datetime, timezone
import json
from pathlib import Path
import re

import pytest

from galleria.services.manifest_reader import (
    _checked_version,
    _manifest_from_json,
    _pic_from_entry,
    _sorted_pics,
    ManifestError,
    MalformedField,
    MissingField,
    UnsupportedVersion,
    read_manifest,
)
from conftest import make_pic


class TestManifestErrors:
    """Tests for the manifest error types."""

    def test_missing_field_names_the_path_and_field(self):
        """The message carries the manifest path and the missing field."""
        assert "t.json" in str(err := MissingField(Path("t.json"), "version"))
        assert all(s in str(err) for s in ["version", "missing", "field", "required"])

    def test_missing_field_names_the_pic_index(self):
        """An indexed missing field names the pic it was missing from."""
        assert "t.json" in str(err := MissingField(Path("t.json"), "hash", 3))
        assert all(s in str(err) for s in ["hash", "missing", "field", "pic 3"])

    def test_unsupported_version_names_the_path_and_version(self):
        """The message carries the manifest path and the rejected version."""
        assert "t.json" in str(err := UnsupportedVersion(Path("t.json"), "0.2.0"))
        assert all(s in str(err) for s in ["0.2.0", "version", "expected", "0.1"])

    @pytest.mark.parametrize("error", [MissingField, UnsupportedVersion])
    def test_subclasses_are_catchable_as_manifest_error(self, error):
        """Each subclass is catchable as ManifestError."""
        with pytest.raises(ManifestError):
            raise error(Path("t.json"), "detail")

    def test_malformed_field_names_the_path_field_and_value(self):
        """The message carries the manifest path, the field and its value."""
        p, f, ts = "t.json", "mtime", "2026-08-17T08:00:00+01:00"
        assert "t.json" in str(err := MalformedField(Path(p), f, ts))
        assert all(s in str(err) for s in [f, ts, "malformed", "field"])

    def test_malformed_field_names_the_pic_index(self):
        """An indexed malformed field names the pic it was found in."""
        p, f, ts, i = "t.json", "mtime", "2026-08-17T08:00:00+01:00", 3
        assert "t.json" in str(err := MalformedField(Path(p), f, ts, i))
        assert all(s in str(err) for s in [f, ts, "malformed", "field", "pic 3"])


class TestCheckedVersion:
    """Tests for _check_version."""

    @pytest.mark.parametrize("version", ["0.1.0", "0.1.7"])
    def test_accepts_any_patch_of_the_supported_major_minor(self, version):
        """Any patch level within the supported major.minor is accepted."""
        _checked_version(version, Path("/foo.json"))

    @pytest.mark.parametrize("version", ["0.2.0", "1.0.0", "0.1"])
    def test_refuses_an_unrecognized_version(self, version):
        """A version outside the supported major.minor raises, naming it."""
        match = rf"foo\.json.*{re.escape(version)}"
        with pytest.raises(UnsupportedVersion, match=match):
            _checked_version(version, Path("foo.json"))


_UTC = timezone.utc
_OMIT = object()


def _make_pic_dict(**overrides) -> dict:
    """Creates a default test pic dict, overridden per keyword given."""
    defaults = {
        "hash": "b3c32:NW9MKEFNZ6GTD8209QN3DQ69",
        "relative_path": "2026/a.jpg",
        "size_bytes": 1024,
        "mtime": "2026-08-17T08:00:00Z",
    }
    return {**defaults, **overrides}


class TestPicFromEntry:
    """Tests for _pic_from_entry."""

    def test_carries_required_fields_onto_the_record(self):
        """The record carries hash, relative_path, size_bytes and mtime."""
        entry = _make_pic_dict()
        pic = _pic_from_entry(entry, Path("manifest.json"), 0)
        assert pic.hash == entry["hash"]
        assert pic.relative_path == Path(entry["relative_path"])
        assert pic.size_bytes == entry["size_bytes"]
        assert pic.mtime == datetime(2026, 8, 17, 8, 0, tzinfo=timezone.utc)

    @pytest.mark.parametrize("field", ["hash", "relative_path", "size_bytes", "mtime"])
    def test_raises_naming_the_missing_field(self, field):
        """An entry missing a required field raises, naming that field."""
        del (entry := _make_pic_dict())[field]
        with pytest.raises(MissingField, match=field):
            _pic_from_entry(entry, Path("manifest.json"), 0)

    def test_tolerates_an_unknown_field(self):
        """An unrecognized field on an entry does not prevent building."""
        entry = _make_pic_dict()
        unknown = _make_pic_dict(foobar=42)
        expect = _pic_from_entry(entry, Path("manifest.json"), 0)
        assert _pic_from_entry(unknown, Path("manifest.json"), 0) == expect

    @pytest.mark.parametrize("field", ["timestamp", "timestamp_source"])
    @pytest.mark.parametrize("value", [None, _OMIT])
    def test_absent_or_null_optional_scalars_read_as_none(self, field, value):
        """An absent or null optional scalar field reads as None."""
        entry = _make_pic_dict() if value is _OMIT else _make_pic_dict(**{field: None})
        assert getattr(_pic_from_entry(entry, Path("foo.json"), 0), field) is None

    def test_carries_optional_scalars_when_present(self):
        """A present timestamp parses to a datetime, its source stays a string."""
        ts = "2026-08-17T07:45:12.001Z"
        d = _make_pic_dict(timestamp=ts, timestamp_source="exif")
        expect = datetime(2026, 8, 17, 7, 45, 12, microsecond=1000, tzinfo=_UTC)
        assert (p := _pic_from_entry(d, Path("t.json"), 0)).timestamp == expect
        assert p.timestamp_source == "exif"

    @pytest.mark.parametrize("field", ["mtime", "timestamp"])
    def test_refuses_an_offset_timestamp(self, field):
        """A timestamp with a numeric offset rather than Z raises."""
        bad = _make_pic_dict(**{field: "2026-08-17T08:00:00+01:00"})
        with pytest.raises(MalformedField, match=rf"t\.json.*{field}"):
            _pic_from_entry(bad, Path("t.json"), 0)


class TestPic:
    """Tests for the Pic record."""

    def test_taken_at_prefers_the_timestamp(self):
        """A pic with a timestamp reports it as the capture time."""
        pic = make_pic(timestamp=datetime(2026, 8, 17, 7, 45, 12, tzinfo=_UTC))
        assert pic.taken_at == datetime(2026, 8, 17, 7, 45, 12, tzinfo=_UTC)

    def test_taken_at_falls_back_to_mtime(self):
        """A pic with no timestamp reports mtime as the capture time."""
        assert make_pic().taken_at == datetime(2026, 8, 17, 8, 0, tzinfo=_UTC)


class TestManifestFromJson:
    """Tests for _manifest_from_json."""

    def _make_manifest_dict(self, overrides: dict | None = None) -> dict:
        """Creates default test manifest dict with default pics list.
        Allows overrides of pics and manifest top level fields"""
        overrides = overrides if overrides is not None else {}
        default = {
            "version": "0.1.0",
            "collection_name": "wedding-full",
            "generated_at": "2026-08-17T09:00:00Z",
            "collection_root": ".",
            "pic": [],
        }
        return {**default, **overrides}

    def test_carries_top_level_fields_onto_the_record(self):
        """The record carries version, collection_name and generated_at."""
        expect = self._make_manifest_dict()
        result = _manifest_from_json(expect, Path("."), pics=[])
        assert result.version == expect["version"]
        assert result.collection_name == expect["collection_name"]
        assert result.generated_at == datetime(2026, 8, 17, 9, 0, tzinfo=_UTC)
        assert result.pics == []

    @pytest.mark.parametrize("root", [None, ".", _OMIT])
    def test_defaults_an_absent_collection_root(self, root):
        """An absent or null collection_root reads as the current directory."""
        man_dict = self._make_manifest_dict(overrides={"collection_root": root})
        if root == _OMIT:
            del man_dict["collection_root"]
        assert _manifest_from_json(man_dict, Path("/"), []).collection_root == Path(".")

    @pytest.mark.parametrize("f", ["version", "collection_name", "generated_at"])
    def test_raises_naming_the_missing_field(self, f):
        """A manifest missing a required field raises, naming that field."""
        del (bad_manifest := self._make_manifest_dict())[f]
        with pytest.raises(MissingField, match=rf"t\.json.*{f}"):
            _manifest_from_json(bad_manifest, Path("t.json"), [])

    def test_tolerates_an_unknown_field(self):
        """An unrecognized top-level field does not prevent building."""
        bad, args = self._make_manifest_dict({"foobar": 42}), (Path("/"), [])
        strict = self._make_manifest_dict()
        unknown = self._make_manifest_dict(overrides=bad)
        assert _manifest_from_json(strict, *args) == _manifest_from_json(unknown, *args)

    def test_refuses_an_unsupported_version(self):
        """A manifest at an unrecognized version raises, naming it."""
        bad = self._make_manifest_dict({"version": "2.0.1"})
        with pytest.raises(UnsupportedVersion, match="2.0.1"):
            _manifest_from_json(bad, Path("/"), [])

    def test_refuses_an_offset_generated_at(self):
        """A generated_at with a numeric offset rather than Z raises."""
        bad = self._make_manifest_dict({"generated_at": "2026-08-17T09:00:00+01:00"})
        with pytest.raises(MalformedField, match="generated_at"):
            _manifest_from_json(bad, Path("foo.json"), [])


class TestSortedPics:
    """Tests for _sorted_pics."""

    def test_orders_by_capture_time(self):
        """Pics are returned oldest first regardless of input order."""
        a = make_pic(timestamp=datetime(2026, 1, 1, 1, 1, tzinfo=_UTC))
        b = make_pic(timestamp=datetime(2026, 1, 1, 1, 1, microsecond=1, tzinfo=_UTC))
        c = make_pic(mtime=datetime(2026, 8, 17, 7, 45, microsecond=2, tzinfo=_UTC))
        assert _sorted_pics([c, b, a]) == [a, b, c]

    def test_breaks_ties_on_relative_path(self):
        """Pics sharing a capture time order by relative path."""
        dt_a, p_a = datetime(2026, 1, 1, 1, 1, tzinfo=_UTC), Path("2026/1.jpg")
        dt_b, p_b = datetime(2026, 1, 1, 1, 1, tzinfo=_UTC), Path("2026/2.jpg")
        a = make_pic(timestamp=dt_a, relative_path=p_a)
        b = make_pic(timestamp=dt_b, relative_path=p_b)
        assert _sorted_pics([b, a]) == [a, b]


class TestReadManifest:
    """Tests for read_manifest."""

    def _write_manifest(self, tmp_path, manifest: dict) -> Path:
        """Writes a manifest dict to tmp_path and returns its path."""
        (path := tmp_path / "manifest.json").write_text(json.dumps(manifest))
        return path

    def _make_manifest_dict(self, pic: list[dict] | None = None) -> dict:
        """Creates a default test manifest dict with a two pic array."""
        return {
            "version": "0.1.0",
            "collection_name": "wedding-full",
            "generated_at": "2026-08-17T09:00:00Z",
            "collection_root": ".",
            "pic": [_make_pic_dict(), _make_pic_dict(relative_path="2026/b.png")]
            if pic is None
            else pic,
        }

    def test_returns_a_record_per_pic_entry(self, tmp_path):
        """A manifest with two pics reads into two records."""
        manifest = self._make_manifest_dict()
        path = self._write_manifest(tmp_path, manifest)
        assert len(read_manifest(path).pics) == len(manifest["pic"])

    def test_reads_an_empty_pic_array(self, tmp_path):
        """A manifest with no pics reads into an empty collection."""
        path = self._write_manifest(tmp_path, self._make_manifest_dict(pic=[]))
        assert read_manifest(path).pics == []

    def test_raises_naming_a_missing_pic_array(self, tmp_path):
        """A manifest with no pic array raises, naming the field."""
        del (bad := self._make_manifest_dict())["pic"]
        with pytest.raises(ManifestError, match=r"manifest\.json.*pic"):
            read_manifest(self._write_manifest(tmp_path, bad))

    def test_returns_pics_in_capture_order(self, tmp_path):
        """A manifest whose pic array is out of order reads back sorted."""
        (manifest := self._make_manifest_dict())["pic"].reverse()
        path = self._write_manifest(tmp_path, manifest)
        expect = [Path("2026/a.jpg"), Path("2026/b.png")]
        assert [p.relative_path for p in read_manifest(path).pics] == expect
