# src/services/manifest_reader.py
"""
Read a NormPic manifest into pic records.

Author: Marcus Grant
Created: 2026-08-17
License: AGPL-3.0-or-later
"""

import json
from datetime import datetime
from pathlib import Path

from src.models.normpic import NormpicManifest, Pic


class ManifestError(Exception):
    """Raised when a manifest cannot be read as a conformant NormPic manifest."""

    def __init__(self, path: Path, field: str, index: int | None = None) -> None:
        msg = f"Manifest at {path} "
        if index is None:
            msg += f"is missing required field '{field}'"
        else:
            msg += f"has a 'pic' of index {index} missing required field '{field}'"
        super().__init__(msg)


def _pic_from_entry(entry: dict, path: Path, index: int) -> Pic:
    """Build a Pic from one entry of a manifest's pic array."""
    try:
        pic = Pic(
            hash=entry["hash"],
            relative_path=Path(entry["relative_path"]),
            size_bytes=entry["size_bytes"],
            mtime=datetime.fromisoformat(entry["mtime"]),
        )
    except KeyError as err:
        raise ManifestError(path, err.args[0], index) from err
    return pic


def _manifest_from_json(data: dict, path: Path, pics: list[Pic]) -> NormpicManifest:
    """Build a NormPicManifest from a manifest's top-level fields."""
    try:
        result = NormpicManifest(
            pics=pics,
            version=data["version"],
            collection_name=data["collection_name"],
            collection_root=Path(data.get("collection_root") or "."),
            generated_at=datetime.fromisoformat(data["generated_at"]),
        )
    except KeyError as err:  # Raise on missing requireds
        raise ManifestError(path, err.args[0]) from err
    return result


def read_manifest(path: Path) -> NormpicManifest:
    """Read the manifest at path into a Collection of Pic records."""
    json_manifest = json.loads(path.read_text())  # Parse the JSON data
    if "pic" not in json_manifest:  # Raise if no 'pic' field
        raise ManifestError(path, "pic")
    pics = [_pic_from_entry(x, path, i) for i, x in enumerate(json_manifest["pic"])]
    return _manifest_from_json(json_manifest, path, pics)
