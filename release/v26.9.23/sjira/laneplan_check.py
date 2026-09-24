#!/usr/bin/env python3
"""Independent checker of the generated CE23 lane plan (lane CE-LANEPLAN, wave F1ce).

The lane plan is rendered by stock `mix ggen_igniter.sync` through
laneplan-pack/templates/lane_wave.json.eex (Elixir, oxigraph). This checker
re-derives what the render must satisfy from the same RDF with a second,
independent implementation (Python, rdflib) and refuses any difference:

  verify    --merged M --wave-dir D --root R
      runner contract (sm-lane-wave.js wave fields; `after` ids resolve to lanes
      of the same file and are acyclic), partition (every sj:WorkOrder under the
      plan root placed exactly once across the wave files, none dropped), trace
      (every lane names a root-child gate and its court; every order names its
      subject proposition and that proposition's span, and the span's bytes in
      the committed prose file R/<document> hash to the span sha256 and equal
      sj:sourceText), digest differential (each tuple_digest equals the
      mix xaas.stop_court contract digest recomputed here: Python
      json.dumps(sort_keys=True, separators=(",", ":"), ensure_ascii=False)),
      routing (lane orders are construct:* with an admitted capability,
      delegations release:*, unassigned construct:unassigned), dependencies
      (every live lp:GateDependency into a lane appears in its depends_on with
      its grounding proposition; after + lane preconditions = the live upstream
      lanes) and task text (every lane order's id, postcondition and digest).
  mutate    SPEC --merged M --out OUT
      writes a mutant of the merged graph (line-level on the N-Triples order
      lines; appended N-Triples for new facts); refuses a vacuous mutation.
  deletion-law --merged M --base D0 --mutant D1 --order IRI
      deleting one order removes exactly that order, its lane when it was the
      lane's last order, and the dependents' edges to a gate left without
      orders; nothing else in either wave file changes.

Exit: 0 holds; 1 refused (each reason printed as REFUSED: ...); 2 usage or a
vacuous mutation.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import RDF

SJ = Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
LP = Namespace("https://ggen-igniter.dev/ontology/lane-plan#")
DCT = Namespace("http://purl.org/dc/terms/")
CE = "https://ggen-igniter.dev/sjira/chatman-26.9.23#"
SJNS = str(SJ)
WAVE_FIELDS = ("wave", "repos", "ints", "base_branch", "worktree_root", "branch_prefix", "receipts_dir",
               "max_repairs", "context", "lanes")
LANE_FIELDS = ("id", "repo", "after", "gate", "task")
PLACEMENTS = {"root", "bootstrap", "unassigned", "court_only", "recipe_delegation", "delegation"}
TUPLE_SCALARS = (
    ("subject", SJ.subject),
    ("postcondition", SJ.postcondition),
    ("capability", None),
    ("evidence_ceiling", SJ.evidenceCeiling),
    ("authority_ceiling", SJ.authorityCeiling),
    ("consequence_class", SJ.consequenceClass),
)


class Refusal:
    def __init__(self) -> None:
        self.reasons: list[str] = []

    def __call__(self, reason: str) -> None:
        self.reasons.append(reason)

    def exit(self, ok_line: str) -> int:
        if self.reasons:
            for reason in self.reasons:
                print(f"REFUSED: {reason}")
            return 1
        print(ok_line)
        return 0


def load(path: Path) -> Graph:
    graph = Graph()
    graph.parse(path, format="turtle")
    return graph


def lexical(term) -> str:
    return str(term)


def plan_root(graph: Graph) -> URIRef:
    roots = sorted({o for p in graph.subjects(RDF.type, LP.LanePlan) for o in graph.objects(p, LP.root)})
    if len(roots) != 1:
        raise SystemExit(f"REFUSED: the merged graph names {len(roots)} lp:root values (expected 1)")
    return roots[0]


def lane_gate(graph: Graph, root: URIRef, gate: URIRef):
    """The root-child ancestor of gate, "root" for the root, None outside the plan."""
    if gate == root:
        return "root"
    chain = [gate]
    seen = {gate}
    while True:
        parents = list(graph.objects(chain[-1], SJ.checkpointOf))
        if len(parents) != 1:
            return None
        parent = parents[0]
        if parent == root:
            return chain[-1]
        if parent in seen:
            return None
        seen.add(parent)
        chain.append(parent)


def plan_orders(graph: Graph, root: URIRef) -> dict[URIRef, URIRef]:
    """sj:WorkOrder -> its checkpoint, for every order whose checkpoint is under the root."""
    out = {}
    for order in graph.subjects(RDF.type, SJ.WorkOrder):
        gates = list(graph.objects(order, SJ.checkpointOf))
        if len(gates) == 1 and lane_gate(graph, root, gates[0]) is not None:
            out[order] = gates[0]
    return out


def contract_tuple(graph: Graph, order: URIRef):
    """The mix xaas.stop_court order_tuple (lib/mix/tasks/xaas.stop_court.ex): ok tuple or a refusal."""
    tuple_ = {"exclusions": sorted(lexical(v) for v in graph.objects(order, SJ.exclusion))}
    for field, pred in TUPLE_SCALARS:
        if field == "capability":
            caps = list(graph.objects(order, SJ.requiresCapability))
            values = [lexical(v) for v in graph.objects(caps[0], SJ.capabilityId)] if len(caps) == 1 else caps
        else:
            values = [lexical(v) for v in graph.objects(order, pred)]
        if len(values) == 0:
            return ("incomplete", field)
        if len(values) > 1:
            return ("ambiguous", field)
        tuple_[field] = values[0]
    return ("ok", tuple_)


def contract_digest(tuple_: dict) -> str:
    body = dict(tuple_, exclusions=sorted(tuple_["exclusions"]))
    encoded = json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return "sha256:" + hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def gate_id(graph: Graph, gate: URIRef) -> str:
    ids = [lexical(v) for v in graph.objects(gate, DCT.identifier)]
    return ids[0] if len(ids) == 1 else str(gate)


def read_waves(wave_dir: Path) -> dict[str, dict]:
    waves = {}
    for path in sorted(wave_dir.glob("wave-*.json")):
        waves[path.name] = json.loads(path.read_text(encoding="utf-8"))
    return waves


# ── verify ────────────────────────────────────────────────────────────────────


def cmd_verify(args: argparse.Namespace) -> int:
    refuse = Refusal()
    graph = load(Path(args.merged))
    root = plan_root(graph)
    repo_root = Path(args.root)
    orders = plan_orders(graph, root)
    waves = read_waves(Path(args.wave_dir))
    expected_waves = sorted(
        lexical(v) for w in graph.subjects(RDF.type, LP.Wave) for v in graph.objects(w, LP.waveId)
    )
    if sorted(f"wave-{w}.json" for w in expected_waves) != sorted(waves):
        refuse(f"wave files {sorted(waves)} != lp:Wave ids {expected_waves}")

    placed: dict[str, list[tuple[str, dict]]] = {}
    lane_owner: dict[str, str] = {}
    lanes_by_file: dict[str, dict[str, dict]] = {}
    for name, doc in waves.items():
        for field in WAVE_FIELDS:
            if field not in doc:
                refuse(f"{name}: runner field {field} missing (sm-lane-wave.js wave spec)")
        repos = doc.get("repos", {})
        ints = doc.get("ints", {})
        lanes = {}
        for lane in doc.get("lanes", []):
            for field in LANE_FIELDS:
                if field not in lane:
                    refuse(f"{name}: lane {lane.get('id')} lacks {field}")
            lid = lane.get("id")
            if lid in lane_owner:
                refuse(f"lane {lid} appears in {lane_owner[lid]} and {name}")
            lane_owner[lid] = name
            lanes[lid] = lane
            if lane.get("repo") not in repos or lane.get("repo") not in ints:
                refuse(f"{name}: lane {lid} repo {lane.get('repo')} has no repos/ints entry")
            for wo in lane.get("work_orders", []):
                placed.setdefault(wo["work_order"], []).append((f"{name}:lane:{lid}", wo))
        lanes_by_file[name] = lanes
        for lid, lane in lanes.items():
            for dep in lane.get("after", []):
                if dep not in lanes:
                    refuse(f"{name}: lane {lid} after {dep}, which is not a lane of the same wave file (sm-lane-wave drops it)")
        # acyclic after
        state: dict[str, int] = {}

        def visit(lid: str, stack: list[str]) -> None:
            if state.get(lid) == 2:
                return
            if state.get(lid) == 1:
                refuse(f"{name}: after cycle {' -> '.join(stack + [lid])}")
                return
            state[lid] = 1
            for dep in lanes.get(lid, {}).get("after", []):
                if dep in lanes:
                    visit(dep, stack + [lid])
            state[lid] = 2

        for lid in sorted(lanes):
            visit(lid, [])
        for placement in doc.get("placements", []):
            if placement.get("placement") not in PLACEMENTS:
                refuse(f"{name}: placement {placement.get('placement')} of {placement.get('id')} is not typed")
            placed.setdefault(placement["work_order"], []).append((f"{name}:{placement.get('placement')}", placement))

    # partition: every order exactly once, nothing extra
    for order in sorted(orders):
        hits = placed.get(str(order), [])
        if len(hits) != 1:
            refuse(f"order {gate_id(graph, order)} <{order}> placed {len(hits)} times {[h[0] for h in hits]}")
    for iri in sorted(placed):
        if URIRef(iri) not in orders:
            refuse(f"placement of {iri}, which is not a work order under {gate_id(graph, root)}")

    live_gates = {}
    for order, gate in orders.items():
        live_gates.setdefault(lane_gate(graph, root, gate), []).append(order)

    for iri, hits in sorted(placed.items()):
        order = URIRef(iri)
        if order not in orders or len(hits) != 1:
            continue
        where, entry = hits[0]
        oid = gate_id(graph, order)
        if entry.get("id") != oid:
            refuse(f"{where}: id {entry.get('id')} != dcterms:identifier {oid}")
        # digest differential
        result = contract_tuple(graph, order)
        if result[0] != "ok":
            refuse(f"{where}: {oid} tuple {result[0]} {result[1]} was rendered")
            continue
        tuple_ = result[1]
        digest = contract_digest(tuple_)
        if entry.get("tuple_digest") != digest:
            refuse(f"{where}: {oid} tuple_digest {entry.get('tuple_digest')} != stop-court contract digest {digest}")
        if entry.get("capability") != tuple_["capability"]:
            refuse(f"{where}: {oid} capability {entry.get('capability')} != {tuple_['capability']}")
        # trace: order -> proposition span -> prose bytes
        subject = tuple_["subject"]
        if entry.get("subject") != subject:
            refuse(f"{where}: {oid} subject {entry.get('subject')} != sj:subject {subject}")
        prop = URIRef(subject)
        span = entry.get("span") or {}
        want = {
            "kind": [lexical(v) for v in graph.objects(prop, SJ.propositionKind)],
            "document": [lexical(v) for v in graph.objects(prop, SJ.sourceDocument)],
            "start": [int(v) for v in graph.objects(prop, SJ.sourceStart)],
            "end": [int(v) for v in graph.objects(prop, SJ.sourceEnd)],
            "sha256": [lexical(v) for v in graph.objects(prop, SJ.sourceSha256)],
        }
        texts = [lexical(v) for v in graph.objects(prop, SJ.sourceText)]
        if any(len(v) != 1 for v in want.values()) or len(texts) != 1:
            refuse(f"{where}: {oid} subject {subject} is not one admitted proposition span")
            continue
        for key, values in want.items():
            if span.get(key) != values[0]:
                refuse(f"{where}: {oid} span.{key} {span.get(key)!r} != proposition {values[0]!r}")
        doc_path = repo_root / want["document"][0]
        try:
            data = doc_path.read_bytes()
        except OSError as exc:
            refuse(f"{where}: {oid} span document {doc_path}: {exc}")
            continue
        if "sha256:" + hashlib.sha256(data).hexdigest() != want["sha256"][0]:
            refuse(f"{where}: {oid} {want['document'][0]} bytes do not hash to the span sha256")
        if data[want["start"][0]:want["end"][0]].decode("utf-8", errors="replace") != texts[0]:
            refuse(f"{where}: {oid} bytes [{want['start'][0]}, {want['end'][0]}) != sj:sourceText")
        # routing
        capability = tuple_["capability"]
        kind = where.split(":")[1]
        gate = orders[order]
        lg = lane_gate(graph, root, gate)
        boundary = {lexical(v) for v in graph.objects(order, SJ.boundaryClass)}
        if lg == "root":
            expect = "root"
        elif SJNS + "Bootstrap" in boundary:
            expect = "bootstrap"
        elif capability == "construct:unassigned":
            expect = "unassigned"
        else:
            expect = {"construct": "lane", "court": "court_only", "recipe": "recipe_delegation",
                      "release": "delegation"}.get(capability.split(":", 1)[0])
        if kind != expect:
            refuse(f"{where}: {oid} capability {capability} placed as {kind}, routing law says {expect}")
        if kind != "lane" and entry.get("gate") != (gate_id(graph, root) if lg == "root" else gate_id(graph, lg)):
            refuse(f"{where}: {oid} gate {entry.get('gate')} is not its root-child gate")

    # lanes: trace to gates, courts, task text, dependencies
    edges = []
    for edge in graph.subjects(RDF.type, LP.GateDependency):
        downs = list(graph.objects(edge, LP.downstream))
        ups = list(graph.objects(edge, LP.upstream))
        sources = list(graph.objects(edge, DCT.source))
        if len(downs) == 1 and len(ups) == 1:
            edges.append((edge, downs[0], ups[0], sources[0] if len(sources) == 1 else None))
    for name, lanes in lanes_by_file.items():
        for lid, lane in lanes.items():
            gate = URIRef(lane.get("checkpoint", ""))
            if gate_id(graph, gate) != lid or lane_gate(graph, root, gate) != gate:
                refuse(f"{name}: lane {lid} checkpoint {gate} is not the root-child gate {lid}")
                continue
            courts = [lexical(v) for v in graph.objects(gate, SJ.courtCommand)]
            if courts != [lane.get("gate")]:
                refuse(f"{name}: lane {lid} gate {lane.get('gate')!r} != sj:courtCommand {courts}")
            if not lane.get("work_orders"):
                refuse(f"{name}: lane {lid} traces to no work order")
            task = lane.get("task", "")
            for wo in lane.get("work_orders", []):
                order = URIRef(wo["work_order"])
                if order not in orders or lane_gate(graph, root, orders[order]) != gate:
                    refuse(f"{name}: lane {lid} order {wo['work_order']} is not an order of gate {lid}")
                    continue
                post = [lexical(v) for v in graph.objects(order, SJ.postcondition)]
                for needle in [wo["id"], wo["tuple_digest"], wo["work_order"]] + post:
                    if needle not in task:
                        refuse(f"{name}: lane {lid} task omits {needle[:80]!r}")
            for mentioned in re.findall(r"^Work order (WO-[0-9A-F]+) ", task, flags=re.M):
                if mentioned not in {wo["id"] for wo in lane.get("work_orders", [])}:
                    refuse(f"{name}: lane {lid} task names foreign order {mentioned}")
            # dependencies into this lane from the graph
            want_deps = set()
            for edge, down, up, source in edges:
                if lane_gate(graph, root, down) != gate:
                    continue
                up_lg = lane_gate(graph, root, up)
                if up_lg in (None, "root") or up_lg == gate or not live_gates.get(up_lg):
                    continue
                want_deps.add((str(edge), gate_id(graph, up_lg), str(source)))
                required = set(graph.objects(source, SJ.requiredBy)) if source is not None else set()
                kinds = list(graph.objects(source, SJ.propositionKind)) if source is not None else []
                if not kinds or not ({down, up, root} & required):
                    refuse(f"{name}: lane {lid} edge {edge} is not grounded by an admitted proposition of its gates or the root")
            got_deps = {(d.get("edge"), d.get("upstream"), d.get("source")) for d in lane.get("depends_on", [])}
            if got_deps != want_deps:
                refuse(f"{name}: lane {lid} depends_on {sorted(got_deps)} != live graph edges {sorted(want_deps)}")
            upstream_lanes = {u for _e, u, _s in want_deps if u in lane_owner}
            got_upstream = set(lane.get("after", [])) | {
                p.get("gate") for p in lane.get("preconditions", []) if p.get("kind") == "lane"
            }
            if got_upstream != upstream_lanes:
                refuse(f"{name}: lane {lid} after+lane preconditions {sorted(got_upstream)} != upstream lanes {sorted(upstream_lanes)}")
            for dep in lane.get("after", []):
                if lane_owner.get(dep) != name:
                    refuse(f"{name}: lane {lid} after {dep} of another wave")

    n_lanes = sum(len(v) for v in lanes_by_file.values())
    n_edges = len(edges)
    summary = ", ".join(f"{name} {len(lanes)} lanes" for name, lanes in sorted(lanes_by_file.items()))
    return refuse.exit(
        f"LANEPLAN_VERIFY OK: {len(orders)} work orders each placed once ({n_lanes} lanes: {summary}; "
        f"{len(orders) - sum(len(l['work_orders']) for ls in lanes_by_file.values() for l in ls.values())} typed non-lane placements); "
        f"every tuple_digest = the stop-court contract digest; every order traces to its proposition span "
        f"in the committed prose; {n_edges} gate dependencies grounded; runner contract holds"
    )


# ── mutate ────────────────────────────────────────────────────────────────────


def order_iri(frag: str) -> str:
    return f"<{CE}{frag}>"


def cmd_mutate(args: argparse.Namespace) -> int:
    text = Path(args.merged).read_text(encoding="utf-8")
    lines = text.split("\n")
    kind, _, rest = args.spec.partition(":")
    parts = rest.split(":") if rest else []
    removed = 0
    added: list[str] = []

    def drop(pred) -> list[str]:
        nonlocal removed
        keep = []
        for line in lines:
            if pred(line):
                removed += 1
            else:
                keep.append(line)
        return keep

    def edge_lines(name: str, down: str, up: str, source: str) -> list[str]:
        edge = f"<{CE}mutant-{name}>"
        return [
            f"{edge} <{RDF.type}> <{LP.GateDependency}> .",
            f"{edge} <{LP.downstream}> <{CE}{down}> .",
            f"{edge} <{LP.upstream}> <{CE}{up}> .",
            f'{edge} <{LP.dependencyType}> "mutant" .',
            f'{edge} <{LP.dependencyClass}> "semantic" .',
            f"{edge} <{DCT.source}> <{CE}{source}> .",
        ]

    if kind == "drop-field" and len(parts) == 2:
        subj, pred = order_iri(parts[0]), f"<{SJNS}{parts[1]}>"
        lines = drop(lambda l: l.startswith(f"{subj} {pred} "))
        vacuous = removed == 0
    elif kind == "dup-field" and len(parts) == 2:
        subj, pred = order_iri(parts[0]), f"<{SJNS}{parts[1]}>"
        vacuous = not any(l.startswith(f"{subj} {pred} ") for l in lines)
        added = [f'{subj} {pred} "mutant: a second {parts[1]} value" .']
    elif kind == "capability" and len(parts) >= 2:
        subj = order_iri(parts[0])
        capid = ":".join(parts[1:])
        lines = drop(lambda l: l.startswith(f"{subj} <{SJNS}requiresCapability> "))
        vacuous = removed == 0
        added = [f"{subj} <{SJNS}requiresCapability> <urn:laneplan-mutant:cap> .",
                 f'<urn:laneplan-mutant:cap> <{SJNS}capabilityId> "{capid}" .']
    elif kind == "repository" and len(parts) == 2:
        subj = order_iri(parts[0])
        lines = drop(lambda l: l.startswith(f"{subj} <{SJNS}repository> "))
        vacuous = removed == 0
        added = [f'{subj} <{SJNS}repository> "{parts[1]}" .']
    elif kind == "subject" and len(parts) == 2:
        subj = order_iri(parts[0])
        lines = drop(lambda l: l.startswith(f"{subj} <{SJNS}subject> "))
        vacuous = removed == 0
        added = [f'{subj} <{SJNS}subject> "{CE}{parts[1]}" .']
    elif kind == "delete-order" and len(parts) == 1:
        subj = order_iri(parts[0])
        prefix = subj[:-1] + "-"
        lines = drop(lambda l: l.startswith(subj + " ") or l.startswith(prefix))
        vacuous = removed == 0
    elif kind == "add-edge" and len(parts) == 4:
        name, down, up, source = parts
        vacuous = False
        added = edge_lines(name, down, up, source)
    else:
        print(f"usage: unknown mutation spec {args.spec!r}", file=sys.stderr)
        return 2
    if vacuous:
        print(f"VACUOUS MUTATION {args.spec}: no line of the merged graph matched", file=sys.stderr)
        return 2
    Path(args.out).write_text("\n".join(lines + added) + "\n", encoding="utf-8")
    print(f"MUTANT {args.spec}: removed {removed} line(s), added {len(added)}")
    return 0


# ── deletion law ──────────────────────────────────────────────────────────────


def cmd_deletion_law(args: argparse.Namespace) -> int:
    refuse = Refusal()
    graph = load(Path(args.merged))
    root = plan_root(graph)
    orders = plan_orders(graph, root)
    target = URIRef(args.order)
    if target not in orders:
        print(f"usage: {args.order} is not a work order under the root of {args.merged}", file=sys.stderr)
        return 2
    gate = lane_gate(graph, root, orders[target])
    gone = gate_id(graph, gate) if gate != "root" and [o for o, g in orders.items()
                                                         if lane_gate(graph, root, g) == gate] == [target] else None
    tid = gate_id(graph, target)
    base = read_waves(Path(args.base))
    mutant = read_waves(Path(args.mutant))
    if sorted(base) != sorted(mutant):
        refuse(f"wave files differ: {sorted(base)} vs {sorted(mutant)}")
    for name in sorted(set(base) & set(mutant)):
        b, m = base[name], mutant[name]
        for key in b:
            if key in ("lanes", "placements"):
                continue
            if b[key] != m.get(key):
                refuse(f"{name}: wave field {key} changed")
        if set(m) != set(b):
            refuse(f"{name}: wave keys changed {sorted(set(b) ^ set(m))}")
        want_places = [p for p in b.get("placements", []) if p["work_order"] != args.order]
        if m.get("placements", []) != want_places:
            refuse(f"{name}: placements differ beyond removing {tid}")
        b_lanes = {l["id"]: l for l in b.get("lanes", [])}
        m_lanes = {l["id"]: l for l in m.get("lanes", [])}
        for lid, bl in b_lanes.items():
            if lid == gone:
                if lid in m_lanes:
                    refuse(f"{name}: lane {lid} survives the deletion of its only order {tid}")
                continue
            ml = m_lanes.get(lid)
            if ml is None:
                refuse(f"{name}: lane {lid} vanished although it did not lose its last order")
                continue
            want_orders = [w for w in bl["work_orders"] if w["work_order"] != args.order]
            if ml["work_orders"] != want_orders:
                refuse(f"{name}: lane {lid} work_orders differ beyond removing {tid}")
            for key in ("repo", "gate", "checkpoint"):
                if ml.get(key) != bl.get(key):
                    refuse(f"{name}: lane {lid} {key} changed")
            want_deps = [d for d in bl.get("depends_on", []) if d.get("upstream") != gone]
            if ml.get("depends_on") != want_deps:
                refuse(f"{name}: lane {lid} depends_on {[d['upstream'] for d in ml.get('depends_on', [])]} != "
                       f"{[d['upstream'] for d in want_deps]} (only edges to {gone} may vanish)")
            want_after = [a for a in bl.get("after", []) if a != gone]
            if ml.get("after") != want_after:
                refuse(f"{name}: lane {lid} after {ml.get('after')} != {want_after}")
            want_pre = [p for p in bl.get("preconditions", [])
                        if p.get("gate") != gone and args.order not in json.dumps(p)]
            got_pre = ml.get("preconditions", [])
            if [p for p in got_pre if tid not in p.get("work_orders", [])] != got_pre:
                refuse(f"{name}: lane {lid} precondition still names {tid}")
            if len(got_pre) != len([p for p in bl.get("preconditions", []) if p.get("gate") != gone]) and gone:
                refuse(f"{name}: lane {lid} preconditions {len(got_pre)} != {len(want_pre)} after removing {gone}")
            if tid in ml.get("task", "") or args.order in ml.get("task", ""):
                refuse(f"{name}: lane {lid} task still names {tid}")
            b_lines = set(bl["task"].split("\n"))
            m_lines = set(ml["task"].split("\n"))
            extra = {l for l in m_lines - b_lines if not l.startswith("After (same wave): ")}
            if extra:
                refuse(f"{name}: lane {lid} task gained lines {sorted(extra)[:2]}")
            lost = {l for l in b_lines - m_lines
                    if not (l.startswith("After (same wave): ") or l.startswith("Preconditions (")
                            or (gone and f" {gone} " in f" {l} ") or tid in l or args.order in l)}
            if lost and ml["work_orders"] == bl["work_orders"]:
                refuse(f"{name}: lane {lid} task lost unrelated lines {sorted(lost)[:2]}")
        for lid in m_lanes:
            if lid not in b_lanes:
                refuse(f"{name}: lane {lid} appeared after a deletion")
    return refuse.exit(
        f"DELETION_LAW OK: deleting {tid} removed exactly that order"
        + (f", its lane {gone} and the dependents' edges to {gone}" if gone else " (its gate keeps other orders)")
        + "; every other lane, placement and wave field is unchanged"
    )


def main(argv: list[str]) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("verify")
    v.add_argument("--merged", required=True)
    v.add_argument("--wave-dir", required=True)
    v.add_argument("--root", required=True, help="repository root the span documents are relative to")
    mu = sub.add_parser("mutate")
    mu.add_argument("spec")
    mu.add_argument("--merged", required=True)
    mu.add_argument("--out", required=True)
    d = sub.add_parser("deletion-law")
    d.add_argument("--merged", required=True)
    d.add_argument("--base", required=True)
    d.add_argument("--mutant", required=True)
    d.add_argument("--order", required=True)
    args = parser.parse_args(argv)
    return {"verify": cmd_verify, "mutate": cmd_mutate, "deletion-law": cmd_deletion_law}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
