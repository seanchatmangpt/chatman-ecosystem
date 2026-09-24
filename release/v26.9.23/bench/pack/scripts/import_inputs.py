#!/usr/bin/env python3
"""Byte-identical imports of a consumer's out-of-project inputs (nonllm-class-qualification-pack 0.1.0).

ggen refuses '..' in extra_ontologies (FM-CONFIG-003 invalid_path). A consumer whose design reads
graphs from elsewhere in its repository (operator-prose candidates, a goal graph, compiled orders)
lists them in bench.toml [imports] as destination = source; this script copies each source to its
destination (default) or, with --check, refuses any destination whose bytes differ from its source.
Sources must resolve inside the consumer's repository root (the directory holding .git above it).
Exit: 0 ok; 1 REFUSED; 2 usage.
"""
from __future__ import annotations

import argparse
import hashlib
import shutil
import tomllib
from pathlib import Path


def repo_root(start: Path) -> Path:
    for d in [start, *start.parents]:
        if (d / ".git").exists():
            return d
    raise SystemExit("REFUSED[import_no_repository] no .git above the consumer")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consumer", required=True, type=Path)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    consumer = args.consumer.resolve()
    root = repo_root(consumer)
    imports = tomllib.loads((consumer / "bench.toml").read_text(encoding="utf-8")).get("imports", {})
    fails = 0
    for dest_rel, src_rel in sorted(imports.items()):
        src = (consumer / src_rel).resolve()
        dest = consumer / dest_rel
        if root not in src.parents:
            print(f"REFUSED[import_outside_repository] {src_rel}")
            fails += 1
            continue
        if not src.is_file() or src.is_symlink():
            print(f"REFUSED[import_source_missing] {src_rel}")
            fails += 1
            continue
        if args.check:
            if dest.is_symlink() or not dest.is_file() or dest.read_bytes() != src.read_bytes():
                print(f"REFUSED[import_drift] {dest_rel} is not a byte copy of {src_rel}")
                fails += 1
            else:
                print(f"IMPORT OK {dest_rel} = {src_rel} sha256:{hashlib.sha256(src.read_bytes()).hexdigest()}")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(src, dest)
            print(f"IMPORT WROTE {dest_rel} <- {src_rel}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
