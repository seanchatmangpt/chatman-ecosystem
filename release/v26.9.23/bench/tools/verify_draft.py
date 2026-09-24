#!/usr/bin/env python3
"""Qualify bench/ontology-draft.ttl (scratch instrument, real collaborators only: rdflib + pyshacl + scipy).

1. parse the draft and the two candidate graphs;
2. pyshacl: data = draft + candidates, shapes = draft -> must conform;
3. evaluate every nlb:askQuery on the clean graph (truth table);
4. anti-vacuity: each mutation must make pyshacl report a violation and/or flip the targeted ASK to false;
5. anti-over-refusal: a lawful DISCOVERY-tier operational fixture must conform;
6. every ce23 design node traces to a proposition present in the candidates.
Exit 0 only when every expectation holds.
"""
import sys
from pathlib import Path

import rdflib
from pyshacl import validate
from scipy.stats import beta

BENCH = Path(__file__).resolve().parents[1]  # release/v26.9.23/bench
NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
CE = rdflib.Namespace("https://chatman.dev/release/v26.9.23#")
ES = rdflib.Namespace("https://ggen.dev/ontology/evidence-standing#")
PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
PFX = """@prefix nlb: <https://ggen.dev/nonllm-bench#> . @prefix ce23: <https://chatman.dev/release/v26.9.23#> .
@prefix es: <https://ggen.dev/ontology/evidence-standing#> . @prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix prov: <http://www.w3.org/ns/prov#> . """

fails = []


def load():
    g = rdflib.Graph()
    g.parse(BENCH / "ontology-draft.ttl")
    for f in sorted((BENCH / "candidates").glob("*.ttl")):
        g.parse(f)
    return g


def shacl(data):
    shapes = rdflib.Graph().parse(BENCH / "ontology-draft.ttl")
    conforms, rg, text = validate(data, shacl_graph=shapes, inference="none", advanced=True, allow_warnings=False)
    msgs = sorted({str(o) for o in rg.objects(None, rdflib.URIRef("http://www.w3.org/ns/shacl#resultMessage"))})
    return conforms, msgs


def asks(g):
    out = {}
    for s, q in g.subject_objects(NLB.askQuery):
        pid = str(g.value(s, NLB.predicateId))
        out[pid] = bool(g.query(str(q)).askAnswer)
    return out


def cp(n, x):
    if n == 0:
        return 1.0
    return float(beta.ppf(0.95, x + 1, n - x))


def expect(label, cond, detail=""):
    print(("PASS " if cond else "FAIL ") + label + (f"  [{detail}]" if detail else ""))
    if not cond:
        fails.append(label)


base = load()
print(f"parsed: {len(base)} triples (draft + candidates)")
ok, msgs = shacl(base)
expect("clean draft conforms to its shapes", ok, "; ".join(msgs)[:400])
table = asks(base)
for k in sorted(table):
    print(f"  ASK {k}: {table[k]}")
expect("all design ASK predicates evaluable (9)", len(table) == 9, str(len(table)))

# trace: every ce23 design node's prov:wasDerivedFrom target is a proposition in the candidates
props = set(base.subjects(rdflib.RDF.type, SJ.Proposition))
missing = [(s, o) for s, o in base.subject_objects(PROV.wasDerivedFrom) if o not in props]
expect("every prov:wasDerivedFrom target is an emitted sj:Proposition", not missing, str(missing[:3]))


def mutated(add="", remove=()):
    g = load()
    for t in remove:
        g.remove(t)
    if add:
        g.parse(data=PFX + add, format="turtle")
    return g


def lawful_operational(n, x, u, receipts, tier="nlb:tier-discovery", rows=True):
    recs = " ".join(f"ce23:fx-r{i} a <https://ggen-igniter.dev/ontology/semantic-jira#Receipt> ; nlb:subjectDigest \"sha256:{i:064x}\" ." for i in range(receipts))
    rl = ", ".join(f"ce23:fx-r{i}" for i in range(receipts)) if receipts else None
    row = f"ce23:fx-row a nlb:BoundRow ; nlb:boundN {n} ; nlb:boundDefects {x} ; nlb:exactUpperBound \"{cp(n, x):.6f}\"^^xsd:decimal ." if rows else ""
    body = f"""ce23:fx-standing a nlb:ClassStanding ; nlb:forClass ce23:class-elixir-format ; nlb:standingKind nlb:NON_LLM_OPERATIONAL_ALIVE ;
  es:standingState es:ALIVE ; nlb:tier {tier} ; nlb:n {n} ; nlb:defects {x} ; nlb:confidence "0.95"^^xsd:decimal ;
  nlb:upperFailureBound "{u}"^^xsd:decimal ; nlb:boundMethod "clopper-pearson-exact-one-sided" ; nlb:environmentScope "macOS arm64; OS=UNSUPPORTED" ;
  nlb:msaStanding es:ALIVE ; nlb:llmInvocations 0 ; nlb:replayDivergence 0 ; prov:wasDerivedFrom ce23:P-3951c3003b3ad270
  {('; nlb:unseenExecutionReceipt ' + rl) if rl else ''} .
{recs} {row}"""
    return body


# anti-over-refusal: lawful DISCOVERY tuple (n=30, x=0, u = exact bound 0.095034 rounded up)
ok, msgs = shacl(mutated(lawful_operational(30, 0, "0.095034", 30)))
expect("lawful DISCOVERY operational tuple (n=30, 30 distinct receipts, u=exact) conforms", ok, "; ".join(msgs)[:300])

MUT = [
    ("M1 near-miss expects ALIVE", dict(add="ce23:nm-ex-syntax nlb:expectedStanding es:ALIVE .",
        remove=[(CE["nm-ex-syntax"], NLB.expectedStanding, ES.UNKNOWN)]), None),
    ("M2 overclaim n=31 x=0 u=0.05 (exact 0.092114)", dict(add=lawful_operational(31, 0, "0.05", 31)), None),
    ("M3 overclaim n=30 x=1 u=0.01 (exact 0.148596)", dict(add=lawful_operational(30, 1, "0.01", 30)), None),
    ("M4 pseudo-replication n=30 with 1 distinct receipt", dict(add=lawful_operational(30, 0, "0.095034", 1)), None),
    ("M5 tier overclaim n=20 at DISCOVERY", dict(add=lawful_operational(20, 0, "0.139108", 20)), None),
    ("M6 no generated BoundRow for (n, x)", dict(add=lawful_operational(45, 0, "0.07", 45, rows=False)), None),
    ("M7 OS factor given a column", dict(add='ce23:factor-os nlb:column "G" .'), None),
    ("M8 independent verifier same family as repair (python)", dict(add='ce23:ver-cpython-ast nlb:implementationFamily "ruff-rust" .',
        remove=[(CE["ver-cpython-ast"], NLB.implementationFamily, rdflib.Literal("cpython-ast"))]), "BD-D4"),
    ("M9 untraced CTQ", dict(remove=[(CE["ctq-human"], PROV.wasDerivedFrom, CE["P-631296cc71d3da82"])]), "BD-D6"),
    ("M10 operational ALIVE without evidence", dict(add="ce23:standing-elixir-format es:standingState es:ALIVE .",
        remove=[(CE["standing-elixir-format"], ES.standingState, ES.UNKNOWN)]), "BD-X1"),
    ("M11 label-only membership (ggen class)", dict(remove=[(CE["class-ggen-projection"], NLB.membershipClause, CE["mc-gg-1"])]), "BD-D3"),
    ("M12 demote json to PRESERVED", dict(add='ce23:class-json-canonical nlb:claimStatus "PRESERVED" .',
        remove=[(CE["class-json-canonical"], NLB.claimStatus, rdflib.Literal("KNOWN_CANDIDATE"))]), "BD-D2"),
    ("M13 train/test leak by patch-id", dict(add="""ce23:fx-a a nlb:BenchmarkCase ; nlb:inClass ce23:class-elixir-format ; nlb:split nlb:Train ; nlb:patchId "b6fbdc214847" .
ce23:fx-b a nlb:BenchmarkCase ; nlb:inClass ce23:class-elixir-format ; nlb:split nlb:Test ; nlb:patchId "b6fbdc214847" ."""), "BD-A3"),
    ("M14 Admit stage loses its event type", dict(remove=[(CE["stage-admit"], NLB.ocelEventType, None)]), "BD-M1"),
    ("M15 M2 receipt-currency court deleted", dict(remove=[(CE["M2"], None, None)]), "BD-M2"),
    ("M16 near-misses of rust drop to 2", dict(remove=[(CE["nm-rs-edition"], None, None), (CE["nm-rs-config"], None, None)]), "BD-D5"),
]

for label, kw, ask_id in MUT:
    g = mutated(**kw)
    ok, msgs = shacl(g)
    flipped = None
    if ask_id:
        flipped = asks(g).get(ask_id) is False
    refused = (not ok) or bool(flipped)
    detail = f"shacl_conforms={ok}" + (f" {ask_id}={not flipped}" if ask_id else "") + (f" msg={msgs[0][:90]}" if msgs else "")
    expect(f"{label} is refused", refused, detail)

print(f"RESULT: {'ALL CHECKS PASS' if not fails else 'FAILURES: ' + ', '.join(fails)}")
sys.exit(1 if fails else 0)
