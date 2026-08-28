# src/galleria/services/manifest_reader.py
"""
Read a NormPic manifest into pic records.

Author: Marcus Grant
Created: 2026-08-17
License: AGPL-3.0-or-later
"""

import json
from datetime import datetime
from pathlib import Path

from galleria.models.normpic import NormpicManifest, Pic

dt_from_iso = datetime.fromisoformat  # Shorter alias

SUPPORTED_VERSION = "0.1"  # The only major.minor version we support


# Errors the manifest reader can raise
class ManifestError(Exception):
    """Base for failures reading a manifest, carrying the manifest's path."""

    def __init__(self, path: Path, detail: str) -> None:
        super().__init__(f"Manifest at {path} {detail}")


class MissingField(ManifestError):
    """Raised when a required field is absent from a manifest."""

    def __init__(self, path: Path, field: str, index: int | None = None) -> None:
        where = "" if index is None else f" in pic {index}"
        super().__init__(path, f"missing required field '{field}'{where}")


class UnsupportedVersion(ManifestError):
    """Raised when a manifest's major.minor is not the supported one."""

    def __init__(self, path: Path, version: str) -> None:
        msg = f"has version {version}, expected {SUPPORTED_VERSION}.x"
        super().__init__(path, msg)


class MalformedField(ManifestError):
    """Raised when a field's value violates the contract's canonical form."""

    def __init__(
        self, path: Path, field: str, value: str, index: int | None = None
    ) -> None:
        where = "" if index is None else f" in pic {index}"
        super().__init__(path, f"has malformed field '{field}': '{value}'{where}")


def _optional_timestamp(
    entry: dict, field: str, path: Path, index: int | None = None
) -> datetime | None:
    """Return entry's field as a timestamp, or None when absent or null."""
    if not (ts := entry.get(field)):
        return None
    return _checked_timestamp(ts, path, field, index)


def _checked_timestamp(
    value: str, path: Path, field: str, index: int | None = None
) -> datetime:
    """Return value parsed as an RFC 3339 UTC timestamp, raise if malformed."""
    if not value.endswith("Z"):
        raise MalformedField(path, field, value, index)
    return dt_from_iso(value)


def _pic_from_entry(entry: dict, path: Path, index: int) -> Pic:
    """Build a Pic from one entry of a manifest's pic array."""
    try:  # Assign and ensure required fields are present
        pic = Pic(
            hash=entry["hash"],
            relative_path=Path(entry["relative_path"]),
            size_bytes=entry["size_bytes"],
            mtime=_checked_timestamp(entry["mtime"], path, "mtime", index),
            timestamp=_optional_timestamp(entry, "timestamp", path, index),
            timestamp_source=entry.get("timestamp_source"),
        )
    except KeyError as err:  # Raise on missing required fields
        raise MissingField(path, err.args[0], index) from err
    return pic


def _checked_version(version: str, path: Path) -> str:
    """Return version if its major.minor is the supported one,
    else raise UnsupportedVersion"""
    parts = version.split(".")
    if len(parts) != 3 or ".".join(parts[:2]) != SUPPORTED_VERSION:
        raise UnsupportedVersion(path, version)
    return version


def _sorted_pics(pics: list[Pic]) -> list[Pic]:
    """Return pics ordered by capture time then normpic ordered relative path."""
    return sorted(pics, key=lambda p: (p.taken_at, p.relative_path))


def _manifest_from_json(data: dict, path: Path, pics: list[Pic]) -> NormpicManifest:
    """Build a NormPicManifest from a manifest's top-level fields."""
    try:  # Assign and ensure required fields are present
        result = NormpicManifest(
            pics=_sorted_pics(pics),
            version=_checked_version(data["version"], path),
            collection_name=data["collection_name"],
            collection_root=path.parent / Path(data.get("collection_root") or "."),
            generated_at=_checked_timestamp(data["generated_at"], path, "generated_at"),
        )
    except KeyError as err:  # Raise on missing required fields
        raise MissingField(path, err.args[0]) from err
    return result


def read_manifest(path: Path) -> NormpicManifest:
    """Read the manifest at path into a Collection of Pic records."""
    json_manifest = json.loads(path.read_text())  # Parse the JSON data
    if "pic" not in json_manifest:  # Raise if no 'pic' field
        raise MissingField(path, "pic")
    pics = [_pic_from_entry(x, path, i) for i, x in enumerate(json_manifest["pic"])]
    return _manifest_from_json(json_manifest, path, pics)
