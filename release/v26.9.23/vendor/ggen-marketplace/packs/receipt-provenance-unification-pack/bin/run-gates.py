#!/usr/bin/env python3
"""Run every gates/*.rq violation query against a crown graph.

Each gate is a SELECT of VIOLATIONS: an empty result set is a pass. Any row is
a refusal to render the receipt. Exit 1 on the first non-empty gate.

Usage: run-gates.py <graph.ttl> [gates_dir]
"""
from __future__ import annotations

import sys
from pathlib import Path

from rdflib import Graph


def main() -> int:
    graph_path = Path(sys.argv[1])
    gates_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(__file__).resolve().parent.parent / "gates"
    g = Graph()
    g.parse(graph_path, format="turtle")
    print(f"GRAPH {graph_path} triples={len(g)}")
    failed = 0
    for rq in sorted(gates_dir.glob("*.rq")):
        rows = list(g.query(rq.read_text()))
        if rows:
            failed += 1
            print(f"GATE_VIOLATION {rq.name} rows={len(rows)}")
            for r in rows[:10]:
                print(f"    {r}")
        else:
            print(f"GATE_PASS {rq.name}")
    print(f"CROWN_GATES {'ALIVE' if failed == 0 else 'BLOCKED'} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
