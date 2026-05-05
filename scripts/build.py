#!/usr/bin/env python3
"""Cross-platform build script — produces dist/efficiency_tracker.ankiaddon.

Usage:
    python scripts/build.py

An .ankiaddon file is just a zip archive of __init__.py, manifest.json and
anything else the add-on needs, all sitting at the root of the archive.
"""
from __future__ import annotations

import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "src" / "efficiency_tracker"
DIST = ROOT / "dist"
OUT = DIST / "efficiency_tracker.ankiaddon"

EXCLUDE_NAMES = {"__pycache__", "user_data.json", "active_session.json", "meta.json", ".DS_Store"}
EXCLUDE_SUFFIXES = {".pyc"}


def should_skip(path: Path) -> bool:
    if path.suffix in EXCLUDE_SUFFIXES:
        return True
    return any(part in EXCLUDE_NAMES for part in path.parts)


def main() -> int:
    if not SRC.is_dir():
        print(f"Error: source directory not found at {SRC}", file=sys.stderr)
        return 1

    DIST.mkdir(exist_ok=True)
    if OUT.exists():
        OUT.unlink()

    files = []
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(SRC.rglob("*")):
            if path.is_dir() or should_skip(path):
                continue
            arcname = path.relative_to(SRC)
            zf.write(path, arcname)
            files.append(str(arcname))

    print(f"Built: {OUT} ({OUT.stat().st_size:,} bytes)")
    print("Files included:")
    for f in files:
        print(f"  {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
