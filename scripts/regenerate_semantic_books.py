#!/usr/bin/env python3
"""Regenerate generator-owned books and apply the semantic publication layer.

This is the canonical regeneration entry point for book projections that are
manufactured by Python generators in this repository. It deliberately runs the
primary generators first, then the deterministic semantic-enrichment stage.
A clean exact-head run must leave docs/ and books/ unchanged.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(script: str, *args: str) -> None:
    subprocess.run(
        [sys.executable, str(ROOT / "scripts" / script), *args],
        cwd=ROOT,
        check=True,
    )


def main() -> int:
    # These are the two explicit book generators currently owned by scripts/.
    # Chateco and the platform handbook are canonical checked-in Markdown; the
    # final enrichment stage can still repair their published weak pages.
    run("generate_dyson_sphere_book.py")
    run("generate_hditc_book.py")
    run("enrich_published_pages.py", "--write")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
