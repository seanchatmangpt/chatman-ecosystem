#!/usr/bin/env python3
"""Run every gates/*.rq violation query against a release graph (rdflib runner).

Reused from packs/gym-autonomic-crown-pack/bin/run-gates.py (same contract: each
gate is a SELECT of VIOLATIONS, an empty result is a pass, exit 1 when any gate
returns a row). Extended so this second executor sees the same union graph a
native `ggen sync run` gates (ggen enforces pack gates only when the pack is
consumed through a consumer [packs] entry):

1. this pack's ontology.ttl;
2. the graph file given on the command line;
3. when that file's directory holds a ggen.toml: its [ontology].source (if it is
   another file) and every `extra_ontologies` file of every path pack entry;
4. Stage-2 enrich: every `construct:` frontmatter of this pack's
   templates/*.tmpl, in sorted order, single pass (the ggen sync semantics).

Usage: run-gates.py <graph.ttl> [gates_dir]
"""
from __future__ import annotations

import sys
import tomllib
from pathlib import Path

import yaml
from rdflib import Graph

PACK = Path(__file__).resolve().parent.parent


def union_graph(graph_path: Path) -> Graph:
    g = Graph()
    g.parse(PACK / "ontology.ttl", format="turtle")
    g.parse(graph_path, format="turtle")
    manifest = graph_path.resolve().parent / "ggen.toml"
    if manifest.is_file():
        config = tomllib.loads(manifest.read_text(encoding="utf-8"))
        source = manifest.parent / config.get("ontology", {}).get("source", graph_path.name)
        if source.resolve() != graph_path.resolve():
            g.parse(source, format="turtle")
        for entry in config.get("packs", {}).values():
            for extra in entry.get("extra_ontologies", []) if isinstance(entry, dict) else []:
                g.parse(manifest.parent / extra, format="turtle")
    for template in sorted((PACK / "templates").glob("*.tmpl")):
        text = template.read_text(encoding="utf-8")
        if not text.startswith("---"):
            continue
        front = yaml.safe_load(text.split("---", 2)[1]) or {}
        if front.get("construct"):
            for triple in g.query(front["construct"]):
                g.add(triple)
    return g


def main() -> int:
    graph_path = Path(sys.argv[1])
    gates_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else PACK / "gates"
    g = union_graph(graph_path)
    print(f"GRAPH {graph_path} triples={len(g)}")
    failed = 0
    for rq in sorted(gates_dir.glob("*.rq")):
        rows = list(g.query(rq.read_text(encoding="utf-8")))
        if rows:
            failed += 1
            print(f"GATE_VIOLATION {rq.name} rows={len(rows)}")
            for r in rows[:10]:
                print("    " + " | ".join(str(v) for v in r))
        else:
            print(f"GATE_PASS {rq.name}")
    print(f"RELEASE_GATES {'ALIVE' if failed == 0 else 'REFUSED'} failed={failed}")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
