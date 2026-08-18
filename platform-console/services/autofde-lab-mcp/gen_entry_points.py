#!/usr/bin/env python3
"""Real, mechanical transform: reads the live autofde-lab pyproject.toml's
[project.entry-points.*] tables and writes a standard entry_points.txt
(the same file a real `pip install .` would generate inside the
package's *.dist-info), so importlib.metadata.entry_points() can find
autofde_lab's real registered domains/solvers without a full wheel build
(see the Dockerfile's header comment for why the wheel build itself is
skipped). Every name/value pair here is copied verbatim from the source
TOML -- nothing is invented, reordered, or filtered.

Also writes a minimal METADATA file (Name/Version only) -- the other
field importlib.metadata.distribution() needs to resolve entry_points
for a given distribution name.
"""
from __future__ import annotations

import pathlib
import sys
import tomllib

REPO = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else pathlib.Path.home() / "autofde-lab")
OUT = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else "dist-info")

pyproject = tomllib.loads((REPO / "pyproject.toml").read_text())
entry_points = pyproject["project"]["entry-points"]

OUT.mkdir(parents=True, exist_ok=True)

lines = []
for group, table in entry_points.items():
    lines.append(f"[{group}]")
    for name, value in table.items():
        lines.append(f"{name} = {value}")
    lines.append("")
(OUT / "entry_points.txt").write_text("\n".join(lines) + "\n")

(OUT / "METADATA").write_text(
    "Metadata-Version: 2.1\n"
    "Name: autofde-lab\n"
    "Version: 0.0.0+platform-console-mcp-sidecar\n"
)

print(f"gen_entry_points.py: wrote {OUT}/entry_points.txt "
      f"({sum(len(t) for t in entry_points.values())} entries across {len(entry_points)} groups) and {OUT}/METADATA")
