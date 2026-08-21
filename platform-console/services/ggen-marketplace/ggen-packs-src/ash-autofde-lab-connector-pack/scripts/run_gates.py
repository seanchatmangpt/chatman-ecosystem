#!/usr/bin/env python3
"""Real SPARQL gate runner for ash-autofde-lab-connector-pack.

Loads ontology.ttl with rdflib and executes every gates/*.rq file against it.
Each gate's SELECT returns violation rows (this pack's established convention,
see gates/010_required.rq's header comment) -- zero rows means the gate passes.
Exits non-zero if any gate returns rows, so it can gate CI/regen the same way
verify.py gates the wasm4pm-drift-reconciliation-pack playground.
"""
import sys
from pathlib import Path

import rdflib

PACK_ROOT = Path(__file__).resolve().parent.parent
ONTOLOGY_PATH = PACK_ROOT / "ontology.ttl"
GATES_DIR = PACK_ROOT / "gates"


def run_gates() -> int:
    graph = rdflib.Graph()
    graph.parse(str(ONTOLOGY_PATH), format="turtle")

    gate_files = sorted(GATES_DIR.glob("*.rq"))
    if not gate_files:
        print(f"no gate files found in {GATES_DIR}")
        return 1

    total_violations = 0
    for gate_file in gate_files:
        query_text = gate_file.read_text()
        message_lines = [
            line[len("# MESSAGE:"):].strip()
            for line in query_text.splitlines()
            if line.startswith("# MESSAGE:")
        ]
        message = " ".join(message_lines) if message_lines else "(no MESSAGE header)"

        results = list(graph.query(query_text))
        if results:
            total_violations += len(results)
            print(f"FAIL {gate_file.name}: {len(results)} violation(s) -- {message}")
            for row in results:
                print(f"    {tuple(str(v) for v in row)}")
        else:
            print(f"PASS {gate_file.name}")

    print(f"\n{len(gate_files)} gate(s) run, {total_violations} total violation(s)")
    return 0 if total_violations == 0 else 1


if __name__ == "__main__":
    sys.exit(run_gates())
