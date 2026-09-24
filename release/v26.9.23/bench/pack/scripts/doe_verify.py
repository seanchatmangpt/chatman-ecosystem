#!/usr/bin/env python3
"""Independent qualification of a generated 2^(k-p) design (nonllm-class-qualification-pack 0.1.0).

Reads only the generated matrices (never the RDF or the template), computes from the runs alone:
balance, pairwise orthogonality of main effects, the defining relation (every factor subset whose
column product is constant), the resolution and the two-factor alias chains, and checks them
against the matrix's own declaration (run count, resolution, defining relation). Every factor in a
run must be VARIED; an UNSUPPORTED or PARTIAL factor (listed in not_varied) must be absent from every
run. With --ci, the CI matrix must be the same design (one include row per run, level high <=> +1)
with the same not_varied list, one runner, and no OS key.

Usage: doe_verify.py DESIGN_MATRIX.json [--ci CI_MATRIX.json] [--min-resolution 4]
Exit: 0 ADMITTED; 3 REFUSED(<reason>) lines; 2 usage.
Origin: BENCH-B3 verify_design.py (scratch instrument), retired into the pack.
"""
from __future__ import annotations

import argparse
import itertools
import json
import math
import sys


def analyse(design: dict) -> dict:
    factors = design["factors"]
    letters = [f["column"] for f in factors]
    runs = design["runs"]
    n = len(runs)
    col = {x: [r["coded"][x] for r in runs] for x in letters}

    def prod(subset):
        return [math.prod(col[x][i] for x in subset) for i in range(n)]

    balanced = all(sum(col[x]) == 0 for x in letters)
    orthogonal = all(sum(a * b for a, b in zip(col[x], col[y])) == 0 for x, y in itertools.combinations(letters, 2))
    words = []
    for k in range(1, len(letters) + 1):
        for subset in itertools.combinations(letters, k):
            p = prod(subset)
            if len(set(p)) == 1:
                words.append(("-" if p[0] < 0 else "") + "".join(subset))
    resolution = min(len(w.lstrip("-")) for w in words) if words else None

    def key(subset):
        p = prod(subset)
        return tuple(p) if p[0] > 0 else tuple(-x for x in p)

    chains: dict = {}
    for size in (1, 2, 3):
        for subset in itertools.combinations(letters, size):
            chains.setdefault(key(subset), []).append("".join(subset))
    fi = sorted({tuple(sorted(t for t in c if len(t) == 2)) for c in chains.values() if any(len(t) == 2 for t in c)})
    distinct_runs = len({tuple(r["coded"][x] for x in letters) for r in runs})
    return {
        "runs": n, "distinct_runs": distinct_runs, "balanced": balanced, "orthogonal": orthogonal,
        "defining_relation": "=".join(["I"] + words), "resolution": resolution,
        "two_factor_alias_chains": ["=".join(c) for c in fi], "letters": letters,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("design")
    parser.add_argument("--ci")
    parser.add_argument("--min-resolution", type=int, default=4)
    args = parser.parse_args()
    design = json.load(open(args.design, encoding="utf-8"))
    refusals = []
    for f in design["factors"]:
        if f.get("support") != "VARIED":
            refusals.append(f"REFUSED(non_varied_factor_in_design) {f.get('column')} {f.get('factor')} is {f.get('support')}")
    not_varied = {nv["factor"] for nv in design.get("not_varied", [])}
    for f in design["factors"]:
        if f["factor"] in not_varied:
            refusals.append(f"REFUSED(not_varied_factor_in_runs) {f['factor']}")
    columns = {f["column"] for f in design["factors"]}
    for r in design["runs"]:
        if set(r["coded"]) != columns:
            refusals.append(f"REFUSED(run_columns) run {r['run']} columns {sorted(r['coded'])} != {sorted(columns)}")
            break
        if any(v not in (1, -1) for v in r["coded"].values()):
            refusals.append(f"REFUSED(coded_level) run {r['run']}")
            break
    a = analyse(design)
    declared = design.get("declared", {})
    k = len(a["letters"])
    p = k - int(round(math.log2(a["runs"]))) if a["runs"] else None
    if a["runs"] != design.get("runs_total") or a["runs"] != declared.get("run_count"):
        refusals.append(f"REFUSED(run_count) computed {a['runs']} declared {declared.get('run_count')} total {design.get('runs_total')}")
    if a["distinct_runs"] != a["runs"]:
        refusals.append(f"REFUSED(duplicate_runs) {a['runs'] - a['distinct_runs']} duplicated treatment combinations")
    if design.get("design") != f"2^({k}-{p})":
        refusals.append(f"REFUSED(design_label) {design.get('design')} != 2^({k}-{p})")
    if not a["balanced"] or not a["orthogonal"]:
        refusals.append(f"REFUSED(not_orthogonal) balanced={a['balanced']} orthogonal={a['orthogonal']}")
    if a["resolution"] is None or a["resolution"] < args.min_resolution:
        refusals.append(f"REFUSED(resolution_below_required) computed {a['resolution']} < {args.min_resolution}")
    if a["resolution"] != declared.get("resolution"):
        refusals.append(f"REFUSED(resolution_declaration) computed {a['resolution']} declared {declared.get('resolution')}")
    if a["defining_relation"] != declared.get("defining_relation"):
        refusals.append(f"REFUSED(defining_relation) computed {a['defining_relation']} declared {declared.get('defining_relation')}")
    if args.ci:
        ci = json.load(open(args.ci, encoding="utf-8"))
        include = ci["strategy"]["matrix"]["include"]
        if len(include) != a["runs"]:
            refusals.append(f"REFUSED(ci_run_count) {len(include)} != {a['runs']}")
        for row, run in zip(include, design["runs"]):
            want = {k: ("high" if v == 1 else "low") for k, v in run["coded"].items()}
            got = {k: v for k, v in row.items() if k != "run"}
            if row.get("run") != run["run"] or got != want:
                refusals.append(f"REFUSED(ci_matrix_differs) run {run['run']}")
                break
        if set(ci.get("not_varied", [])) != not_varied:
            refusals.append(f"REFUSED(ci_not_varied) {ci.get('not_varied')} != {sorted(not_varied)}")
        if not isinstance(ci.get("runs-on"), str) or any(k.lower() in ("os", "runs-on") for k in (include[0] if include else {})):
            refusals.append("REFUSED(ci_os_varied) the CI matrix varies the runner/OS")
    a["standing"] = "ADMITTED" if not refusals else "REFUSED"
    a["refusals"] = refusals
    print(json.dumps(a, indent=1, sort_keys=True))
    for r in refusals:
        print(r)
    return 0 if not refusals else 3


if __name__ == "__main__":
    sys.exit(main())
