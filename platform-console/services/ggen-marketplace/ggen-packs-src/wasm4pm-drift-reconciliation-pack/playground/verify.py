#!/usr/bin/env python3
"""Real, read-only verifier for wasm4pm-drift-reconciliation-pack's DriftClaim rows.

Never writes to any file it checks -- reports matches/contradicts per claim only.
Usage: python3 verify.py [--repo /path/to/wasm4pm] [--ontology /path/to/ontology.ttl]
"""
import argparse
import subprocess
import sys
from pathlib import Path

import rdflib

QUERY = """
PREFIX drc: <https://ggen.dev/ontology/wasm4pm-drift-reconciliation#>
SELECT ?s ?sourceDoc ?claimText ?checkKind ?checkTarget ?expectedResult WHERE {
  ?s a ?type ; drc:sourceDoc ?sourceDoc ; drc:claimText ?claimText ;
     drc:checkKind ?checkKind ; drc:checkTarget ?checkTarget ; drc:expectedResult ?expectedResult .
  FILTER(?type = drc:SourceContradictionClaim || ?type = drc:FilesystemFactClaim)
}
ORDER BY ?s
"""


def check_file_exists(repo: Path, target: str) -> bool:
    return (repo / target).exists()


def check_file_absent(repo: Path, target: str) -> bool:
    return not (repo / target).exists()


def check_grep_pattern(repo: Path, target: str) -> bool:
    path_part, pattern = target.split(":", 1)
    full = repo / path_part
    if not full.exists():
        return False
    return pattern in full.read_text(errors="replace")


def check_command_output_matches(repo: Path, target: str, expected: str) -> bool:
    result = subprocess.run(
        target, shell=True, cwd=repo, capture_output=True, text=True, timeout=180
    )
    combined = result.stdout + result.stderr
    return expected in combined


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=str(Path.home() / "wasm4pm"))
    ap.add_argument(
        "--ontology", default=str(Path(__file__).resolve().parent.parent / "ontology.ttl")
    )
    args = ap.parse_args()
    repo = Path(args.repo)

    g = rdflib.Graph()
    g.parse(args.ontology, format="turtle")
    rows = list(g.query(QUERY))

    n_match, n_contradict = 0, 0
    for r in rows:
        kind = str(r.checkKind)
        target = str(r.checkTarget)
        expected = str(r.expectedResult)
        try:
            if kind == "file_exists":
                ok = check_file_exists(repo, target)
            elif kind == "file_absent":
                ok = check_file_absent(repo, target)
            elif kind == "grep_pattern":
                ok = check_grep_pattern(repo, target)
            elif kind == "command_output_matches":
                ok = check_command_output_matches(repo, target, expected)
            else:
                print(f"UNKNOWN checkKind {kind!r} for {r.s}", file=sys.stderr)
                continue
        except Exception as e:  # real, visible failure, never silently "ok"
            print(f"ERROR checking {r.s}: {e}", file=sys.stderr)
            n_contradict += 1
            continue

        status = "MATCH" if ok else "CONTRADICT"
        if ok:
            n_match += 1
        else:
            n_contradict += 1
        subject = str(r.s).split("#")[-1]
        print(f"[{status}] {subject} :: {r.claimText}")

    print(f"\n{n_match} match, {n_contradict} contradict, {len(rows)} total")
    sys.exit(1 if n_contradict else 0)


if __name__ == "__main__":
    main()
