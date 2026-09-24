#!/bin/sh
# CE23-12-BenchmarkDesign court: CE23-12 conjunct BenchmarkDesign (release/v26.9.23/sjira/goal.ttl ce:CE23-12-BenchmarkDesign).
# Run from the chatman-ecosystem root by the CE23 root court. Exit 0 = ALIVE; exit 75 = machinery,
# a tool or a canonical checkout absent (standing UNKNOWN); exit 1 carries typed REFUSED[<code>] lines
# naming the counterexample; any other exit = the court ran and witnessed nothing (standing UNKNOWN).
# Machinery (step CE23-12, orders CE23-12-BD-02/05/06/07): release/v26.9.23/courts/ce23_12/court.py bd
# judges the exact committed head: design capital unedited (K0), both prose units byte-pinned (P1)
# and span-verified by the frozen xaas prose_spans.py (P2), imports / kernel / lift outputs reproduce
# (I1 K1 L1), ggen 26.9.18 renders the committed out/ byte-identically twice with every pack gate
# admitting (G0 G1), every artifact carries a GENERATED header (G2), every proposition required by
# CE23-12-BenchmarkDesign is traced by design nodes that cite only committed propositions (T1), the
# nine design ASK predicates hold on rdflib and pyoxigraph (D2), the in-repo
# nonllm-class-qualification-pack admits the good fixtures and refuses every registered mutant on five
# instruments (D1), no operational standing is implied (X2); then the anti-vacuity corpus in synthetic
# git repositories. Pins: ce23_12/pins.toml; mutants: ce23_12/mutations.toml.
here=$(cd "$(dirname "$0")" && pwd)
command -v python3 >/dev/null 2>&1 || { echo "UNKNOWN[TOOL_MISSING] CE23-12-BenchmarkDesign: python3 not on PATH"; exit 75; }
[ -f "$here/ce23_12/court.py" ] || { echo "UNKNOWN[MACHINERY_ABSENT] CE23-12-BenchmarkDesign: $here/ce23_12/court.py"; exit 75; }
PYTHONDONTWRITEBYTECODE=1 exec python3 "$here/ce23_12/court.py" bd "$@"
