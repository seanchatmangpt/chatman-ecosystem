#!/usr/bin/env python3
"""CE23-9 repair probe (skeptic reason 3): does any declared judging-court file (root.toml court_files at
<rev>) name a path under the retired shadow tree? Same needles as tests/test_ce23_9_court.py
ValidatorPinCase.test_judging_court_names_no_shadow_tree_path; read from git objects only.

    python3 probe_court_files_shadow.py <rev> [<rev> ...]
"""
import subprocess
import sys
import tomllib
from pathlib import Path

NEEDLES = (str(Path.home() / "wt") + "/", "~/" + "wt/", "$HOME/" + "wt/")
bad = 0
for rev in sys.argv[1:]:
    pins = tomllib.loads(subprocess.run(["git", "show", f"{rev}:release/v26.9.23/courts/ce23_9/root.toml"],
                                        capture_output=True, text=True, check=True).stdout)
    files = pins["subject"]["court_files"]
    hits = []
    for rel in files:
        data = subprocess.run(["git", "show", f"{rev}:{rel}"], capture_output=True).stdout
        hits += [f"{rel}: {n}" for n in NEEDLES if n.encode() in data]
    print(f"{rev}: {len(files)} court files, shadow-tree hits {hits}")
    bad += bool(hits)
sys.exit(1 if bad else 0)
