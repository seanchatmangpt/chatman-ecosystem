#!/usr/bin/env python3
"""Real, read-only gap detector for wasm4pm-drift-reconciliation-pack.

The pack's ontology.ttl encodes 7 DriftClaim/FilesystemFactClaim rows, each with a
drc:sourceDoc naming the file whose stale claim was fixed. That list is hand-authored
and static -- it does not grow when new "fix:"/"correct" commits land on wasm4pm.

This script closes that gap mechanically: it greps `git log` on the target repo for
commit subjects that look like drift fixes (fix:, correct, re-verif), extracts any
file path each commit subject or diff touches under docs/ or a doc-like extension,
and reports which of those are NOT already covered by a drc:sourceDoc in the
ontology. It writes nothing -- it only reports untracked candidates so a human/agent
can decide whether to add a new DriftClaim row.

Usage: python3 find_untracked_fixes.py [--repo ~/wasm4pm] [--ontology ../ontology.ttl] [--since <rev>]
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path

import rdflib

FIX_PATTERN = re.compile(r"\b(fix|correct|re-verif)", re.IGNORECASE)
DOC_EXT = re.compile(r"\.(md|txt|toml)$", re.IGNORECASE)


def tracked_source_docs(ontology: Path) -> set[str]:
    g = rdflib.Graph()
    g.parse(ontology, format="turtle")
    q = """
    PREFIX drc: <https://ggen.dev/ontology/wasm4pm-drift-reconciliation#>
    SELECT DISTINCT ?doc WHERE { ?s drc:sourceDoc ?doc . }
    """
    return {str(r.doc) for r in g.query(q)}


def fix_commits(repo: Path, since: str | None) -> list[tuple[str, str]]:
    rev_range = f"{since}..HEAD" if since else "-30"
    cmd = ["git", "log", "--oneline"] + ([rev_range] if since else [rev_range])
    out = subprocess.run(cmd, cwd=repo, capture_output=True, text=True, check=True).stdout
    commits = []
    for line in out.splitlines():
        sha, _, subject = line.partition(" ")
        if FIX_PATTERN.search(subject):
            commits.append((sha, subject))
    return commits


def files_touched(repo: Path, sha: str) -> list[str]:
    out = subprocess.run(
        ["git", "show", "--name-only", "--pretty=format:", sha],
        cwd=repo, capture_output=True, text=True, check=True,
    ).stdout
    return [f for f in out.splitlines() if f.strip() and DOC_EXT.search(f)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path.home() / "wasm4pm"))
    ap.add_argument(
        "--ontology", default=str(Path(__file__).resolve().parent.parent / "ontology.ttl")
    )
    ap.add_argument("--since", default=None, help="git rev to scan forward from, e.g. a tag/sha")
    args = ap.parse_args()
    repo = Path(args.repo)

    tracked = tracked_source_docs(Path(args.ontology))
    commits = fix_commits(repo, args.since)

    untracked_by_commit: dict[str, list[str]] = {}
    for sha, subject in commits:
        for f in files_touched(repo, sha):
            if f not in tracked:
                untracked_by_commit.setdefault(f"{sha} {subject}", []).append(f)

    if not untracked_by_commit:
        print("No untracked doc-fix commits found -- ontology.ttl is current.")
        sys.exit(0)

    print(f"{len(untracked_by_commit)} fix commit(s) touch doc files not yet tracked as drc:sourceDoc:\n")
    for commit, files in untracked_by_commit.items():
        print(f"  {commit}")
        for f in files:
            print(f"    - {f}")
    print(
        "\nThese are CANDIDATES for new DriftClaim rows, not proof a claim needs one -- "
        "inspect each commit before adding an ontology row."
    )
    sys.exit(1)


if __name__ == "__main__":
    main()
