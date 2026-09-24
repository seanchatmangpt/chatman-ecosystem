#!/bin/sh
# CE23-2 court: Crosswalk the old constitutional graph (release/v26.9.23/sjira/goal.ttl ce:CE23-2).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE;
# exit 75 = machinery or a canonical checkout absent (standing UNKNOWN); exit 1 carries
# typed REFUSED[<code>] lines naming the counterexample; any other exit = the court ran
# and witnessed nothing (standing UNKNOWN).
# Machinery (lane CE23-2): release/v26.9.23/courts/ce23_2/court.py judges the exact
# committed head: every one of the required roles of release/v26.9.1/manifest.toml (read
# from the base blob, never the render) has exactly one row in the vendored
# chatman-ecosystem-release-pack's render out/legacy-role-crosswalk.toml with one of
# REQUIRED | SUCCESSOR | BLOCKED | UNSUPPORTED | REFUSED, its own legacy component, a reason
# and derived_by/decided_by provenance; out/crosswalk.ttl and out/role-derivations.toml
# agree; the render reproduces (sync writes nothing; two fresh renders byte-identical); the
# pack gates admit it under ggen and rdflib; the legacy import is the pack's lift of the
# base manifest blob; the court-reference import is a fresh observation of the xaas
# GC-26.9.23 courts; the court's own executor of the disposition rule agrees; every explicit
# decision is admitted by ce23_2/crosswalk.toml; then the anti-vacuity corpus (control
# ALIVE, 18 mutants in synthetic git repos refused). Clauses: ce23_2/court.py.
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-2: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_2/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-2: $here/ce23_2/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_2/court.py" "$@"
