#!/usr/bin/env python3
"""CE23-1 receipt probe: the skeptic's counterexample judged by a given court.py's own judge().

The counterexample (skeptic of 03de16bd, probe mutant P1): a synthetic two-commit repository
built exactly as the court's anti-vacuity harness builds it (base: release/v26.9.1 at the
pinned base commit; head: the committed slice of --root HEAD), then the committed
imports/fleet-classification.ttl replaced by an absolute symlink (mode 120000) to identical
bytes outside the repository and committed. Every byte, lock and render check still matches;
the committed subject carries no copy of its import.

    python3 probe_symlink.py --court PATH/court.py --work DIR [--root CHECKOUT]

--court is the court module to judge with (the canonical court, or an older court extracted
with `git show <sha>:release/v26.9.23/courts/ce23_1/{court.py,subject.toml}` into one dir);
--root is the checkout whose HEAD slice is judged (default: this file's repository).
Real git, tar and ggen run; nothing is replaced.

Exit: 0 the counterexample is REFUSED[SUBJECT_NOT_INDEPENDENT]; 3 it is admitted (ALIVE: the
defect); 1 refused or UNKNOWN for another reason, or the harness could not be built.
"""

from __future__ import annotations

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--court", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[3])
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location("ce23_1_court_probe", args.court)
    if spec is None or spec.loader is None:
        print(f"PROBE_HARNESS: cannot load {args.court}")
        return 1
    court = importlib.util.module_from_spec(spec)
    sys.modules["ce23_1_court_probe"] = court
    spec.loader.exec_module(court)
    if args.work.exists() and any(args.work.iterdir()):
        print(f"PROBE_HARNESS: {args.work} is not empty")
        return 1
    args.work.mkdir(parents=True, exist_ok=True)
    env = court.Env(args.work / "home")
    sdir, pred = court.SDIR, court.PRED_DIR
    scope = [pred, sdir, court.TOOLS["verify_release"], *court.TOOLS["support"]]

    repo = args.work / "repo"
    repo.mkdir()
    if env.git_(repo, "init", "-q", "-b", "main").returncode != 0:
        print("PROBE_HARNESS: git init failed")
        return 1
    env.archive(args.root, court.SUBJ["base_commit"], [pred], repo)
    base = env.commit_all(repo, "base: release/v26.9.1 at the pre-v26.9.23 base")
    for child in repo.iterdir():
        if child.name != ".git":
            shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
    head = env.out(args.root, "rev-parse", "HEAD")
    env.archive(args.root, str(head), scope, repo)
    env.commit_all(repo, f"subject: slice of {head}")

    imported = repo / sdir / court.SUBJ["classification_import"]
    outside = args.work / "external" / imported.name
    outside.parent.mkdir()
    outside.write_bytes(imported.read_bytes())
    imported.unlink()
    imported.symlink_to(outside)
    env.commit_all(repo, "counterexample: import an absolute symlink to identical bytes outside the repository")

    verdict = court.judge(repo, base, env, args.work / "judge")
    print(f"court {args.court} judging slice of {args.root}@{head}")
    for line in verdict.lines:
        print(line)
    if verdict.alive:
        print("PROBE ADMITTED: the counterexample is ALIVE (defect present)")
        return 3
    if "SUBJECT_NOT_INDEPENDENT" in verdict.refused:
        print(f"PROBE REFUSED {sorted(set(verdict.refused))}")
        return 0
    print(f"PROBE OTHER refused={sorted(set(verdict.refused))} unknown={sorted(set(verdict.unknowns))}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
