#!/usr/bin/env python3
"""Project per-prose-unit goal views out of the CE23 goal graph (lane CE-INTAKE).

ggen_igniter `mix semantic_jira.compile_prose` reads ONE root GoalCheckpoint
from `--goal` (children, no parent, not a successor bucket), pins it to ONE
source digest (root sj:sourceSha256), refuses a proposition required by a
checkpoint outside the root's direct gates (foreign_requirements.rq) and
refuses unless every direct gate is required by an admitted proposition of
THAT source (uncovered_gates.rq). The CE23 graph (goal.ttl) is defined by
three prose units: chatman-ce23.md defines the root and CE23-0 .. CE23-11,
the bench prose defines CE23-12, the standings prose defines CE23-12's three
conjunct gates. This script is the deterministic projection that lets the
frozen compiler judge each unit against exactly the gates it defines:

  view(U) = root  P  := the common sj:checkpointOf parent of G_U, with its own
                       identifier/label/description, sj:checkpointOf dropped,
                       sj:repository / sj:baseSha / sj:evidenceHorizon /
                       sj:successorPolicy / sj:authorityCeiling inherited from
                       the goal root when P lacks them, dcterms:source U and
                       sj:sourceSha256 sha256(U) (so a candidate of any other
                       prose is refused), and a stop query that is false by
                       construction (a view is never a stop object);
            gates G_U := every GoalCheckpoint of goal.ttl whose dcterms:source
                       is U (identifier, label, description, boundary class,
                       court command; sj:checkpointOf P);
            every sj:Capability of goal.ttl (id, label, description).

Refusals: G_U empty, G_U with more than one parent, a gate whose
sj:sourceSha256 differs from the unit's bytes, a goal without exactly one
root. `partition` refuses unless the declared units' gate sets partition
every GoalCheckpoint under the root (sj:checkpointOf+), so no gate escapes
the per-unit coverage law.

  emit      --goal G --unit REL --source FILE --out VIEW
  check     --goal G --unit REL --source FILE --out VIEW
  partition --goal G --unit REL [--unit REL ...]

Output: a header of `#` lines, then sorted N-Triples (valid Turtle).
Deterministic: rdflib + standard library; no clock, network or LLM.
Exit 0 ok; 1 refusals ("REFUSED <subject>: <code>: <detail>"); 2 usage.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

from rdflib import Graph, Literal, URIRef
from rdflib.namespace import RDF, RDFS

SJ = "https://ggen-igniter.dev/ontology/semantic-jira#"
DCT = "http://purl.org/dc/terms/"


def sj(name: str) -> URIRef:
    return URIRef(SJ + name)


def dct(name: str) -> URIRef:
    return URIRef(DCT + name)


GATE_PROPS = (dct("identifier"), RDFS.label, dct("description"), sj("boundaryClass"), sj("courtCommand"))
ROOT_OWN_PROPS = (dct("identifier"), RDFS.label, dct("description"))
ROOT_INHERITED = (sj("repository"), sj("baseSha"), sj("evidenceHorizon"), sj("successorPolicy"), sj("authorityCeiling"))
CAP_PROPS = (sj("capabilityId"), RDFS.label, dct("description"))


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def load(goal_path: str, refusals: list[str]) -> Graph | None:
    graph = Graph()
    try:
        graph.parse(goal_path, format="turtle")
    except Exception as exc:  # rdflib raises several parser exception types
        refusals.append(f"REFUSED {goal_path}: goal_unparseable: {type(exc).__name__}: {exc}")
        return None
    return graph


def goal_root(graph: Graph, refusals: list[str]) -> URIRef | None:
    roots = set()
    for gate, parent in graph.subject_objects(sj("checkpointOf")):
        if (gate, RDF.type, sj("GoalCheckpoint")) not in graph:
            continue
        if (parent, RDF.type, sj("GoalCheckpoint")) not in graph:
            continue
        if graph.value(parent, sj("checkpointOf")) is not None:
            continue
        if graph.value(parent, sj("boundaryClass")) == sj("Successor"):
            continue
        roots.add(parent)
    if len(roots) != 1:
        refusals.append(f"REFUSED goal: goal_root: expected exactly one root GoalCheckpoint, found {len(roots)}")
        return None
    return next(iter(roots))


def descendants(graph: Graph, root: URIRef) -> set[URIRef]:
    found: set[URIRef] = set()
    frontier = [root]
    while frontier:
        node = frontier.pop()
        for child in graph.subjects(sj("checkpointOf"), node):
            if (child, RDF.type, sj("GoalCheckpoint")) in graph and child not in found:
                found.add(child)
                frontier.append(child)
    return found


def unit_gates(graph: Graph, root: URIRef, unit: str) -> list[URIRef]:
    return sorted(g for g in descendants(graph, root) if graph.value(g, dct("source")) == Literal(unit))


def ntriple(s, p, o) -> str:
    return f"{s.n3()} {p.n3()} {o.n3()} ."


def view(goal_path: str, unit: str, source: bytes, refusals: list[str]) -> str | None:
    graph = load(goal_path, refusals)
    if graph is None:
        return None
    root = goal_root(graph, refusals)
    if root is None:
        return None
    sha = digest(source)
    gates = unit_gates(graph, root, unit)
    if not gates:
        refusals.append(f"REFUSED {unit}: unit_empty: no GoalCheckpoint under the root has dcterms:source {unit!r}")
        return None
    parents = sorted({graph.value(g, sj("checkpointOf")) for g in gates}, key=str)
    if len(parents) != 1:
        refusals.append(f"REFUSED {unit}: unit_parents: gates of the unit have {len(parents)} parents {parents}")
        return None
    for gate in gates:
        pinned = graph.value(gate, sj("sourceSha256"))
        if pinned is None or str(pinned) != sha:
            refusals.append(f"REFUSED {gate}: source_sha256_mismatch: gate pins {pinned}, unit bytes are {sha}")
    if refusals:
        return None
    parent = parents[0]
    triples: set[str] = set()

    def add(s, p, o):
        triples.add(ntriple(s, p, o))

    add(parent, RDF.type, sj("GoalCheckpoint"))
    for prop in ROOT_OWN_PROPS:
        for value in graph.objects(parent, prop):
            add(parent, prop, value)
    for prop in ROOT_INHERITED:
        values = list(graph.objects(parent, prop)) or list(graph.objects(root, prop))
        for value in values:
            add(parent, prop, value)
    add(parent, dct("source"), Literal(unit))
    add(parent, sj("sourceSha256"), Literal(sha))
    add(
        parent,
        sj("stopQuery"),
        Literal(
            "# Compile view of one prose unit (release/v26.9.23/sjira/unit_goal.py); never a stop object.\n"
            "# The governing stop query is the root's in release/v26.9.23/sjira/goal.ttl.\n"
            "ASK { FILTER(false) }"
        ),
    )
    for gate in gates:
        add(gate, RDF.type, sj("GoalCheckpoint"))
        add(gate, sj("checkpointOf"), parent)
        for prop in GATE_PROPS:
            for value in graph.objects(gate, prop):
                add(gate, prop, value)
    for cap in sorted(graph.subjects(RDF.type, sj("Capability"))):
        add(cap, RDF.type, sj("Capability"))
        for prop in CAP_PROPS:
            for value in graph.objects(cap, prop):
                add(cap, prop, value)
    ids = ", ".join(str(graph.value(g, dct("identifier"))) for g in gates)
    header = [
        "# GENERATED by release/v26.9.23/sjira/unit_goal.py emit from release/v26.9.23/sjira/goal.ttl; do not edit.",
        f"# unit: {unit} {sha}",
        f"# view root: {parent} ({graph.value(parent, dct('identifier'))}); gates ({len(gates)}): {ids}",
    ]
    return "\n".join(header) + "\n\n" + "".join(t + "\n" for t in sorted(triples))


def cmd_view(args: argparse.Namespace) -> int:
    refusals: list[str] = []
    source = Path(args.source).read_bytes()
    text = view(args.goal, args.unit, source, refusals)
    out = Path(args.out)
    if text is not None and args.cmd == "check":
        if not out.is_file() or out.read_bytes() != text.encode("utf-8"):
            refusals.append(f"REFUSED {args.out}: output_drift: the committed view differs from the projection of goal.ttl")
    if refusals or text is None:
        sys.stdout.write("".join(r + "\n" for r in refusals))
        sys.stdout.write(f"VIEW REFUSED: {len(refusals)} refusal(s)\n")
        return 1
    data = text.encode("utf-8")
    if args.cmd == "emit":
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
    verb = "EMIT" if args.cmd == "emit" else "CHECK OK"
    sys.stdout.write(f"VIEW {verb}: {args.unit} -> {args.out} sha256:{hashlib.sha256(data).hexdigest()}\n")
    return 0


def cmd_partition(args: argparse.Namespace) -> int:
    refusals: list[str] = []
    graph = load(args.goal, refusals)
    root = goal_root(graph, refusals) if graph is not None else None
    if root is None:
        sys.stdout.write("".join(r + "\n" for r in refusals))
        return 1
    under = descendants(graph, root)
    owner: dict[URIRef, str] = {}
    for unit in args.unit:
        gates = unit_gates(graph, root, unit)
        if not gates:
            refusals.append(f"REFUSED {unit}: unit_empty: the unit defines no gate")
        for gate in gates:
            if gate in owner:
                refusals.append(f"REFUSED {gate}: partition_overlap: {owner[gate]} and {unit}")
            owner[gate] = unit
    for gate in sorted(under - set(owner)):
        refusals.append(
            f"REFUSED {gate}: partition_gap: dcterms:source {graph.value(gate, dct('source'))} names no declared unit"
        )
    if refusals:
        sys.stdout.write("".join(r + "\n" for r in refusals))
        sys.stdout.write(f"PARTITION REFUSED: {len(refusals)} refusal(s)\n")
        return 1
    tally = " ".join(f"{u}={sum(1 for v in owner.values() if v == u)}" for u in args.unit)
    sys.stdout.write(f"PARTITION OK: {len(under)} GoalCheckpoints under {root} partitioned by {len(args.unit)} units ({tally})\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest="cmd", required=True)
    for name in ("emit", "check"):
        p = sub.add_parser(name)
        p.add_argument("--goal", required=True)
        p.add_argument("--unit", required=True, help="repo-relative prose path named by dcterms:source")
        p.add_argument("--source", required=True, help="the prose file (its bytes are pinned)")
        p.add_argument("--out", required=True)
    p = sub.add_parser("partition")
    p.add_argument("--goal", required=True)
    p.add_argument("--unit", action="append", required=True)
    args = parser.parse_args(argv)
    if args.cmd == "partition":
        return cmd_partition(args)
    return cmd_view(args)


if __name__ == "__main__":
    sys.exit(main())
