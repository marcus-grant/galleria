# script/vendor_pico.py
"""
Vendor a Pico CSS release into the package as data.

Usage: vendor_pico.py VERSION

Downloads the version's tarball from the public npm registry, verifies
it against the registry's dist.integrity, and copies css/pico.min.css
and LICENSE.md into src/galleria/vendor/pico/ byte for byte. It then
records the version and the b3c32 code of the copied file in pico.json
beside them. Any failure exits non-zero before the repository is
touched. Maintainer tool: the build never calls it.

Author: Marcus Grant
Created: 2026-11-20
License: AGPL-3.0-or-later
"""

import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import sys
import tarfile
import tempfile
import urllib.request

import b3c32

REGISTRY = "https://registry.npmjs.org/@picocss/pico"
CODE_BITS = 120
VENDOR_DIR = Path(__file__).resolve().parent.parent / "src/galleria/vendor/pico"

# Tarball member to the name it takes in the vendor directory.
MEMBERS = {
    "package/css/pico.min.css": "pico.min.css",
    "package/LICENSE.md": "LICENSE.md",
}


class VendorError(Exception):
    """A failure that stops vendoring before the repository is touched."""


def fetch(url: str) -> bytes:
    """GET url and return its body, raising VendorError on any failure."""
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read()
    except OSError as e:
        raise VendorError(f"request failed for {url}: {e}") from e


def verified_tarball(version: str) -> bytes:
    """Download the version's tarball and verify it against the registry."""
    meta = json.loads(fetch(f"{REGISTRY}/{version}"))
    integrity = meta.get("dist", {}).get("integrity", "")
    algo, _, expected = integrity.partition("-")
    if algo != "sha512" or not expected:
        raise VendorError(f"unsupported or missing dist.integrity: {integrity!r}")
    tarball = fetch(f"{REGISTRY}/-/pico-{version}.tgz")
    actual = base64.b64encode(hashlib.sha512(tarball).digest()).decode()
    if actual != expected:
        raise VendorError("tarball does not match the registry's dist.integrity")
    return tarball


def extract_members(tarball: bytes, scratch: Path) -> dict[str, Path]:
    """Write only the wanted members into scratch, keyed by target name."""
    found = {}
    with tarfile.open(fileobj=io.BytesIO(tarball), mode="r:gz") as tar:
        for member, name in MEMBERS.items():
            try:
                f = tar.extractfile(member)
            except KeyError:
                f = None
            if f is None:
                raise VendorError(f"tarball has no file {member}")
            path = scratch / name
            path.write_bytes(f.read())
            found[name] = path
    return found


def install(files: dict[str, Path], version: str, code: str) -> None:
    """Move the files and the record into VENDOR_DIR, each by rename."""
    VENDOR_DIR.mkdir(parents=True, exist_ok=True)
    record = json.dumps({"version": version, "code": code}, indent=2) + "\n"
    staged = {"pico.json": record.encode()}
    staged.update({name: path.read_bytes() for name, path in files.items()})
    for name, data in staged.items():
        tmp = VENDOR_DIR / f".{name}.tmp"
        tmp.write_bytes(data)
        os.replace(tmp, VENDOR_DIR / name)


def main(version: str) -> int:
    """Vendor the version and report what landed."""
    if not re.fullmatch(r"\d+\.\d+\.\d+", version):
        print(f"FAIL: not a version: {version!r}", file=sys.stderr)
        return 1
    try:
        tarball = verified_tarball(version)
        with tempfile.TemporaryDirectory() as tmp:
            files = extract_members(tarball, Path(tmp))
            css = files["pico.min.css"]
            code = b3c32.code_from_path(css, CODE_BITS)
            size = css.stat().st_size
            install(files, version, code)
    except VendorError as e:
        print(f"FAIL: {e}", file=sys.stderr)
        return 1
    print(f"vendored pico {version}: pico.min.css {size} bytes, code {code}")
    return 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("usage: vendor_pico.py VERSION", file=sys.stderr)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
