#!/usr/bin/env bash
# Copies the real src/autofde_lab package tree (openclaw_bridge.py,
# openclaw_runtime.py, openclaw_http.py, and everything else the package
# needs to import) from the live ~/autofde-lab checkout into this build
# context, matching services/autofde-lab/prep.sh's own "capture real
# files at build time, no runtime access to the host repo" convention.
# See the Dockerfile's header comment for why this is a plain PYTHONPATH
# copy, not a `pip install -e .` / wheel build.
set -euo pipefail
cd "$(dirname "$0")"

SRC=${AUTOFDE_LAB_REPO:-$HOME/autofde-lab}

rm -rf src
mkdir -p src
cp -R "$SRC/src/autofde_lab" src/autofde_lab
find src -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true

echo "prep.sh: copied $SRC/src/autofde_lab -> ./src/autofde_lab"

# Real domain/solver registry: importlib.metadata.entry_points() needs a
# *.dist-info directory on the same sys.path entry as the package (see
# gen_entry_points.py and the Dockerfile's header comment for why this
# stands in for a full `pip install .`).
python3 gen_entry_points.py "$SRC" src/autofde_lab-0.0.0.dist-info
