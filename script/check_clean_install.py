# script/check_clean_install.py
"""
Build the fixture collection with the installed galleria console script.

Run by `just clean-install` inside an isolated environment, from a
directory outside the repository. It imports nothing from galleria, so
it can only see what the installed package produces: a wheel missing its
templates or other package data fails here, where `build --help` would
pass.

Usage: check_clean_install.py MANIFEST
"""

import json
from html.parser import HTMLParser
from pathlib import Path
import subprocess
import sys
import tempfile

COLLECTION = "fixture"
SENTINEL = "__STEM__"


class ImgSrcs(HTMLParser):
    """Collect every img src in a page."""

    def __init__(self) -> None:
        super().__init__()
        self.srcs: list[str] = []

    def handle_starttag(self, tag: str, attrs: list) -> None:
        """Record an img tag's src."""
        if tag == "img":
            self.srcs.append(dict(attrs).get("src") or "")


def expected_files(keys: list[Path]) -> list[str]:
    """Output-relative paths that must exist, one entry per requirement.

    The list ft/gallery-styling extends with its stylesheet.
    """
    site = f"gallery/{COLLECTION}"
    files = [f"{site}/page1.html", f"{site}/index.html"]
    files += [f"{site}/pic/{key.name}.html" for key in keys]
    return files


def missing_outputs(out: Path, keys: list[Path]) -> list[str]:
    """Describe every expected output that is absent or empty."""
    missing = []
    for rel in expected_files(keys):
        path = out / rel
        if not path.is_file() or path.stat().st_size == 0:
            missing.append(f"missing or empty: {rel}")
    site = out / "gallery" / COLLECTION
    if len(list(site.glob("grid-index-*.json"))) != 1:
        missing.append(f"expected one grid-index-*.json in gallery/{COLLECTION}")
    for kind in ("thumb", "preview"):
        for key in keys:
            parent = out / "pics" / COLLECTION / kind / key.parent
            if not list(parent.glob(f"{key.name}.*")):
                missing.append(f"no {kind} rendition for {key}")
    return missing + missing_thumb_links(site, len(keys))


def missing_thumb_links(site: Path, count: int) -> list[str]:
    """Check page 1 links one existing thumbnail per pic."""
    page = site / "page1.html"
    if not page.is_file():
        return []
    parser = ImgSrcs()
    parser.feed(page.read_text())
    thumbs = [s for s in parser.srcs if "/thumb/" in s and SENTINEL not in s]
    problems = []
    if len(thumbs) != count:
        problems.append(f"page1.html has {len(thumbs)} thumbnails, want {count}")
    for src in thumbs:
        if not (site / src).is_file():
            problems.append(f"page1.html thumbnail does not resolve: {src}")
    return problems


def main(manifest: Path) -> int:
    """Build the fixture and report every problem found."""
    exe = Path(sys.executable).parent / "galleria"
    if not exe.is_file():
        print(f"FAIL: console script not installed at {exe}", file=sys.stderr)
        return 1
    keys = [
        Path(p["relative_path"]).with_suffix("")
        for p in json.loads(manifest.read_text())["pic"]
    ]
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp)
        cmd = [str(exe), "build", "--derive"]
        cmd += ["--original-manifest", str(manifest), "--output-dir", str(out)]
        run = subprocess.run(cmd, capture_output=True, text=True)
        if run.returncode != 0:
            print(f"FAIL: galleria build exited {run.returncode}", file=sys.stderr)
            print(run.stdout + run.stderr, file=sys.stderr)
            return 1
        problems = missing_outputs(out, keys)
    for problem in problems:
        print(f"FAIL: {problem}", file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
