#!/usr/bin/env python3
"""Qualification driver of the nonllm-class-qualification-pack: five instruments, one corpus.

Judges a consumer's design graph (its ggen.toml ontology source, every extra_ontologies input and the
pack ontology, i.e. the union a `ggen sync run` sees) and a registered corpus of good fixtures and bad
mutants (a TOML file) with five instruments that implement the same laws independently:

  shacl            pyshacl over shacl/nlb-shapes.ttl
  sparql-rdflib    the design's ASK acceptance predicates + gates/*.rq, rdflib engine
  sparql-oxigraph  the same queries, pyoxigraph engine
  native           scripts/native_predicates.py (imperative, no SPARQL, no SHACL)
  ggen             `ggen sync run` of a scratch consumer copy whose design.ttl is the artifact (the pack's
                   gates enforced by ggen itself); optional (--ggen), slowest

The instruments are fixed: ASK texts come from the committed design, never from the artifact under
judgement. Every good artifact must be admitted and every bad artifact refused by every instrument,
and every instrument that attributes laws must name the mutant's registered law (attribution).

Usage: verify.py --consumer DIR --mutations TOML [--ggen] [--json OUT] [--only ID,ID]
Exit: 0 all expectations hold; 1 an expectation failed (FAIL lines); 2 usage; 75 a tool is absent.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

import rdflib
from rdflib.namespace import RDF

# Never write bytecode into the pack: ggen's pack content hash (ggen.lock, FM-PACK-008) covers every
# file under the pack directory, so a __pycache__ there would break the consumer's lock.
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent))
import native_predicates  # noqa: E402

PACK = Path(__file__).resolve().parent.parent
NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
PREFIXES = {
    "nlb": "https://ggen.dev/nonllm-bench#",
    "ce23": "https://chatman.dev/release/v26.9.23#",
    "ce": "https://ggen-igniter.dev/sjira/chatman-26.9.23#",
    "es": "https://ggen.dev/ontology/evidence-standing#",
    "sj": "https://ggen-igniter.dev/ontology/semantic-jira#",
    "prov": "http://www.w3.org/ns/prov#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "dflss": "https://ggen.dev/dflss#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "dcterms": "http://purl.org/dc/terms/",
}
TURTLE_PREFIXES = "".join(f"@prefix {k}: <{v}> .\n" for k, v in PREFIXES.items())
ASK_LAW = {
    "BD-D2": "CLASS", "BD-D3": "CLASS", "BD-D4": "CLASS", "BD-D5": "CLASS", "BD-D6": "CTQ", "BD-M1": "MEASURE",
    "BD-M2": "MSA", "BD-A3": "SPLIT", "BD-X1": "STANDING",
}
GATE_LAW = {
    "010": "CLASS", "020": "BOUNDARY", "030": "FACTOR", "040": "STANDING", "050": "TRACE", "060": "SPLIT",
    "070": "CTQ", "080": "MEASURE", "090": "MSA", "100": "PLAN",
}
SHAPE_LAW = {
    "ClassStandingShape": "STANDING", "OperationalStandingShape": "STANDING", "KnownClassShape": "CLASS",
    "KnownClassCountShape": "CLASS", "NearMissShape": "BOUNDARY", "NegativeControlShape": "BOUNDARY",
    "FactorShape": "FACTOR", "TraceShape": "TRACE", "CtqShape": "CTQ", "CtqTreeShape": "CTQ",
    "StageShape": "MEASURE", "MeasurementModelShape": "MEASURE", "MSAPropertyShape": "MSA",
    "MSACourtStatusShape": "MSA", "SplitShape": "SPLIT", "CorpusPlanShape": "SPLIT", "FamilyShape": "PLAN",
    "CapabilityGapShape": "PLAN", "PlanSourceCodeShape": "PLAN", "ClassCodeShape": "PLAN",
    "QualificationPlanShape": "PLAN", "PlanEntryShape": "PLAN",
}
DESIGN_GATES = ("010", "020", "030", "040", "050", "060", "070", "080", "090")
INSTRUMENTS = ("shacl", "sparql-rdflib", "sparql-oxigraph", "native", "ggen")


def consumer_inputs(consumer: Path) -> list[Path]:
    config = tomllib.loads((consumer / "ggen.toml").read_text(encoding="utf-8"))
    paths = [PACK / "ontology.ttl", consumer / config["ontology"]["source"]]
    for entry in config.get("packs", {}).values():
        if isinstance(entry, dict):
            paths += [consumer / p for p in entry.get("extra_ontologies", [])]
    return paths


def load_union(consumer: Path, design_text: str | None = None) -> rdflib.Graph:
    g = rdflib.Graph()
    config = tomllib.loads((consumer / "ggen.toml").read_text(encoding="utf-8"))
    source = consumer / config["ontology"]["source"]
    for path in consumer_inputs(consumer):
        if design_text is not None and path == source:
            g.parse(data=design_text, format="turtle")
        else:
            g.parse(path, format="turtle")
    return g


def term(text: str):
    if text == "*":
        return None
    if text.startswith('"') and text.endswith('"'):
        return rdflib.Literal(text[1:-1])
    if text.startswith("<") and text.endswith(">"):
        return rdflib.URIRef(text[1:-1])
    prefix, _, local = text.partition(":")
    if prefix in PREFIXES:
        return rdflib.URIRef(PREFIXES[prefix] + local)
    raise ValueError(f"unknown term {text!r}")


def standing_fixture(spec: dict) -> str:
    n, x, u = int(spec["n"]), int(spec["x"]), str(spec["u"])
    receipts = int(spec.get("receipts", n))
    tier = spec.get("tier", "nlb:tier-discovery")
    kind = spec.get("kind", "nlb:NON_LLM_OPERATIONAL_ALIVE")
    state = spec.get("state", "es:ALIVE")
    rlist = " , ".join(f"ce23:fx-r{i}" for i in range(receipts))
    recs = "\n".join(f'ce23:fx-r{i} a sj:Receipt ; nlb:subjectDigest "sha256:{i:064x}" .' for i in range(receipts))
    body = (
        f"ce23:fx-standing a nlb:ClassStanding ; nlb:forClass ce23:class-elixir-format ; nlb:standingKind {kind} ;\n"
        f"  es:standingState {state} ; nlb:tier {tier} ; nlb:n {n} ; nlb:defects {x} ; "
        f'nlb:confidence "0.95"^^xsd:decimal ;\n  nlb:upperFailureBound "{u}"^^xsd:decimal ; '
        f'nlb:boundMethod "clopper-pearson-exact-one-sided" ; nlb:environmentScope "macOS arm64; OS=UNSUPPORTED" ;\n'
        f"  nlb:msaStanding es:ALIVE ; nlb:llmInvocations 0 ; nlb:replayDivergence 0 ; "
        f"prov:wasDerivedFrom ce:P-3951c3003b3ad270"
    )
    if receipts:
        body += f" ;\n  nlb:unseenExecutionReceipt {rlist}"
    return body + " .\n" + recs + "\n"


class Artifact:
    def __init__(self, spec: dict, good: bool):
        self.id = spec["id"]
        self.good = good
        self.law = spec.get("law")
        self.description = spec.get("description", "")
        self.remove = [tuple(term(t) for t in triple) for triple in spec.get("remove", [])]
        add = spec.get("add", "")
        if "standing" in spec:
            add += "\n" + standing_fixture(spec["standing"])
        self.add = add

    def apply(self, graph: rdflib.Graph) -> rdflib.Graph:
        g = rdflib.Graph()
        for t in graph:
            g.add(t)
        for pattern in self.remove:
            matched = list(g.triples(pattern))
            if not matched:
                raise ValueError(f"{self.id}: removal pattern {pattern} matches nothing (vacuous mutant)")
            for t in matched:
                g.remove(t)
        if self.add.strip():
            g.parse(data=TURTLE_PREFIXES + self.add, format="turtle")
        return g

    def apply_design(self, design_text: str) -> str:
        g = rdflib.Graph()
        g.parse(data=design_text, format="turtle")
        for pattern in self.remove:
            for t in list(g.triples(pattern)):
                g.remove(t)
        if self.add.strip():
            g.parse(data=TURTLE_PREFIXES + self.add, format="turtle")
        return g.serialize(format="nt")


def load_corpus(path: Path) -> list[Artifact]:
    data = tomllib.loads(path.read_text(encoding="utf-8"))
    corpus = [Artifact({"id": "G0", "description": "the committed design, unmutated"}, True)]
    corpus += [Artifact(f, True) for f in data.get("fixture", [])]
    corpus += [Artifact(m, False) for m in data.get("mutation", [])]
    return corpus


class Instruments:
    def __init__(self, consumer: Path, design_graph: rdflib.Graph):
        from pyshacl import validate  # noqa: F401  (import check)
        import pyoxigraph  # noqa: F401
        self.consumer = consumer
        self.shapes = rdflib.Graph().parse(PACK / "shacl" / "nlb-shapes.ttl", format="turtle")
        self.shape_parent = {}
        SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
        for node_shape, prop_shape in self.shapes.subject_objects(SH.property):
            self.shape_parent[prop_shape] = node_shape
        self.asks = {}
        for s, q in design_graph.subject_objects(NLB.askQuery):
            self.asks[str(design_graph.value(s, NLB.predicateId))] = str(q)
        if set(self.asks) != set(ASK_LAW):
            raise SystemExit(f"UNKNOWN[ask_set] the committed design's ASK predicates are {sorted(self.asks)}")
        self.gates = {}
        for rq in sorted((PACK / "gates").glob("*.rq")):
            key = rq.name[:3]
            if key in DESIGN_GATES:
                self.gates[key] = rq.read_text(encoding="utf-8")
        self.plan_gate = (PACK / "gates" / "100_plan_coverage.rq").read_text(encoding="utf-8")
        self.constructs = []
        for tmpl in sorted((PACK / "templates").glob("*.tmpl")):
            text = tmpl.read_text(encoding="utf-8")
            if text.startswith("---"):
                import yaml
                front = yaml.safe_load(text.split("---", 2)[1]) or {}
                if front.get("construct"):
                    self.constructs.append(front["construct"])

    def shacl(self, g: rdflib.Graph) -> tuple[bool, set[str], list[str]]:
        from pyshacl import validate
        conforms, report, _ = validate(g, shacl_graph=self.shapes, inference="none", advanced=True, allow_warnings=False)
        SH = rdflib.Namespace("http://www.w3.org/ns/shacl#")
        laws, detail = set(), []
        for result in report.subjects(RDF.type, SH.ValidationResult):
            src = report.value(result, SH.sourceShape)
            node_shape = self.shape_parent.get(src, src)
            name = str(node_shape).rsplit("#", 1)[-1]
            laws.add(SHAPE_LAW.get(name, "UNMAPPED:" + name))
            detail.append(f"{name} {report.value(result, SH.focusNode)}")
        return bool(conforms), laws, sorted(detail)[:20]

    def _sparql(self, runner, enrich) -> tuple[bool, set[str], list[str]]:
        laws, detail = set(), []
        for pid, q in sorted(self.asks.items()):
            if not runner(q, ask=True):
                laws.add(ASK_LAW[pid])
                detail.append(f"ASK {pid} false")
        for key, q in sorted(self.gates.items()):
            rows = runner(q, ask=False)
            if rows:
                laws.add(GATE_LAW[key])
                detail.append(f"gate {key} rows={rows}")
        # ggen semantics: Stage 2 enrich (every template construct:, single pass), then gate 100.
        enrich(self.constructs)
        rows = runner(self.plan_gate, ask=False)
        if rows:
            laws.add(GATE_LAW["100"])
            detail.append(f"gate 100 rows={rows}")
        return not laws, laws, detail

    def sparql_rdflib(self, g: rdflib.Graph):
        g = rdflib.Graph() + g

        def run(q, ask):
            res = g.query(q)
            return bool(res.askAnswer) if ask else len(list(res))

        def enrich(constructs):
            added = [list(g.query(c)) for c in constructs]
            for triples in added:
                for t in triples:
                    g.add(t)
        return self._sparql(run, enrich)

    def sparql_oxigraph(self, g: rdflib.Graph):
        import pyoxigraph as ox
        store = ox.Store()
        store.load(g.serialize(format="nt").encode("utf-8"), format=ox.RdfFormat.N_TRIPLES)

        def run(q, ask):
            res = store.query(q)
            return bool(res) if ask else len(list(res))

        def enrich(constructs):
            added = [list(store.query(c)) for c in constructs]
            for triples in added:
                for t in triples:
                    store.add(ox.Quad(t.subject, t.predicate, t.object))
        return self._sparql(run, enrich)

    def native(self, g: rdflib.Graph):
        verdict = native_predicates.evaluate(g)
        laws = {law for law, v in verdict.items() if v}
        detail = [f"{law}: {msg}" for law, v in sorted(verdict.items()) for msg in v[:3]]
        return not laws, laws, detail

    def ggen(self, artifact: Artifact, design_text: str):
        ggen_bin = shutil.which("ggen")
        if ggen_bin is None:
            raise SystemExit("UNKNOWN[TOOL_MISSING] ggen not on PATH")
        with tempfile.TemporaryDirectory(prefix="nlb-ggen-") as tmp:
            dest = Path(tmp) / "consumer"
            shutil.copytree(self.consumer, dest, ignore=shutil.ignore_patterns(".ggen", ".ggen-v2", "out", "__pycache__"))
            config = tomllib.loads((dest / "ggen.toml").read_text(encoding="utf-8"))
            (dest / config["ontology"]["source"]).write_text(
                design_text if artifact.good and not artifact.add and not artifact.remove else artifact.apply_design(design_text),
                encoding="utf-8")
            proc = subprocess.run([ggen_bin, "sync", "run"], cwd=dest, capture_output=True, text=True, timeout=600)
            text = proc.stdout + proc.stderr
            laws = set()
            for key, law in GATE_LAW.items():
                if f"gate `{key}_" in text:
                    laws.add(law)
            if proc.returncode != 0 and not laws:
                laws.add("GGEN_REFUSED")
            tail = [line for line in text.splitlines() if "ERROR" in line or "FM-" in line][:3]
            return proc.returncode == 0, laws, tail


def judge(consumer: Path, corpus: list[Artifact], use_ggen: bool, only: set[str] | None) -> dict:
    base = load_union(consumer)
    design_path = consumer / tomllib.loads((consumer / "ggen.toml").read_text(encoding="utf-8"))["ontology"]["source"]
    design_text = design_path.read_text(encoding="utf-8")
    inst = Instruments(consumer, rdflib.Graph().parse(design_path, format="turtle"))
    results = []
    for art in corpus:
        if only and art.id not in only:
            continue
        g = art.apply(base)
        row = {"id": art.id, "good": art.good, "law": art.law, "description": art.description, "instruments": {}}
        runs = [("shacl", lambda: inst.shacl(g)), ("sparql-rdflib", lambda: inst.sparql_rdflib(g)),
                ("sparql-oxigraph", lambda: inst.sparql_oxigraph(g)), ("native", lambda: inst.native(g))]
        if use_ggen:
            runs.append(("ggen", lambda: inst.ggen(art, design_text)))
        for name, fn in runs:
            t0 = time.monotonic()
            accept, laws, detail = fn()
            row["instruments"][name] = {"accept": accept, "laws": sorted(laws), "detail": detail,
                                        "seconds": round(time.monotonic() - t0, 3)}
        results.append(row)
    return {"artifacts": results}


def expectations(report: dict) -> list[str]:
    fails = []
    for row in report["artifacts"]:
        for name, v in row["instruments"].items():
            if row["good"] and not v["accept"]:
                fails.append(f"FAIL {row['id']} ({row['description']}): {name} refused a good artifact: {v['detail'][:3]}")
            if not row["good"]:
                if v["accept"]:
                    fails.append(f"FAIL {row['id']} ({row['description']}): {name} admitted a registered mutant")
                elif row["law"] and name != "ggen" and row["law"] not in v["laws"]:
                    fails.append(f"FAIL {row['id']}: {name} refused under {v['laws']}, not the registered law {row['law']}")
                elif name == "ggen":
                    # ggen stops at the first refusing gate (sorted): its one reported law must be one the
                    # attributing instruments also name for this mutant.
                    named = set().union(*(set(o["laws"]) for k, o in row["instruments"].items() if k != "ggen"))
                    if not set(v["laws"]) & named:
                        fails.append(f"FAIL {row['id']}: ggen refused under {v['laws']}, a law no other instrument names ({sorted(named)})")
    return fails


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--consumer", required=True, type=Path)
    parser.add_argument("--mutations", required=True, type=Path)
    parser.add_argument("--ggen", action="store_true")
    parser.add_argument("--json", type=Path)
    parser.add_argument("--only")
    args = parser.parse_args()
    try:
        import pyoxigraph  # noqa: F401
        import pyshacl  # noqa: F401
    except ImportError as exc:
        print(f"UNKNOWN[TOOL_MISSING] {exc}")
        return 75
    corpus = load_corpus(args.mutations)
    only = set(args.only.split(",")) if args.only else None
    report = judge(args.consumer.resolve(), corpus, args.ggen, only)
    for row in report["artifacts"]:
        verdicts = " ".join(f"{k}={'ADMIT' if v['accept'] else 'REFUSE'}{v['laws'] if v['laws'] else ''}"
                            for k, v in row["instruments"].items())
        print(f"{'GOOD' if row['good'] else 'BAD '} {row['id']:<5} {row['law'] or '-':<9} {verdicts}")
    fails = expectations(report)
    for f in fails:
        print(f)
    good = sum(1 for r in report["artifacts"] if r["good"])
    bad = len(report["artifacts"]) - good
    print(f"PACK QUALIFICATION {'ALIVE' if not fails else 'REFUSED'}: {good} good admitted, {bad} mutants refused "
          f"by {len(report['artifacts'][0]['instruments']) if report['artifacts'] else 0} instruments; failures {len(fails)}")
    if args.json:
        args.json.write_text(json.dumps(report, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
