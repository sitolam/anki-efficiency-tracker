#!/usr/bin/env bash
# Build script — creates dist/efficiency_tracker.ankiaddon
#
# An .ankiaddon file is a zip archive containing __init__.py, manifest.json
# and any other files needed by the add-on, all at the root of the archive.

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
SRC="$ROOT/src/efficiency_tracker"
DIST="$ROOT/dist"
OUT="$DIST/efficiency_tracker.ankiaddon"

if [[ ! -d "$SRC" ]]; then
    echo "Error: source directory not found at $SRC" >&2
    exit 1
fi

mkdir -p "$DIST"
rm -f "$OUT"

# Build from inside the source dir so files end up at the root of the zip
cd "$SRC"

# Exclude development artefacts that should never ship
zip -r "$OUT" . \
    -x "__pycache__/*" \
    -x "*.pyc" \
    -x "user_data.json" \
    -x "active_session.json" \
    -x "meta.json" \
    -x ".DS_Store"

echo
echo "Built: $OUT"
ls -lh "$OUT"
