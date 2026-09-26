"""U-12 premise-set test (RFC-0005 §10.4): Berthier recompile for {RFC-0004, RFC-0005}.

The strategic compiler (``root_crown.projector.compile_graph`` + ``berthier.judge``,
unchanged) recompiles the committed v26.9.25 objective graph from both premises:

1. single-premise identity: compiling RFC-0004 alone reproduces the committed
   ``berthier.json`` byte for byte (§10.3);
2. premise-set recompile: the RFC-0005 gate rows are *derived* from RFC-0005 §7 by
   ``gates.project`` (never hand-written), the graph is recompiled from the premise set,
   and the Berthier court is ALIVE with packets covering exactly the affected owners;
3. objective mutation: one RFC-0005 §7 change makes the premise-set graph refuse
   STALE_PROJECTION for exactly its dependents, and the recompile from the mutated
   premise is ALIVE again;
4. ManualRestatementCount = 0: no hand-written input (requirements.json, pins.json)
   changes digest across 2 and 3;
5. refusing mutants (anti-vacuity): OMITTED_SUBJECT, STALE_PROJECTION, PREMISE_UNBOUND
   and AUTHORITY_INCREASE are each emitted on their mutant and absent on the control.
"""

from __future__ import annotations

import copy
import json
from dataclasses import replace
from typing import Any

from scripts.release_train.root_crown import berthier, projector
from scripts.release_train.root_crown.model import Requirement, sha256_bytes

from . import gates
from .model import ROOT_REPOSITORY, digest

MUTATION_NOTE = "\n(mutated once: autonomic objective changed)"
MUTANT_TOKENS = ("OMITTED_SUBJECT", "STALE_PROJECTION", "PREMISE_UNBOUND", "AUTHORITY_INCREASE")


def gate_requirements(rfc5_text: str, owner: str = ROOT_REPOSITORY) -> tuple[Requirement, ...]:
    """RFC-0005 gate rows as Berthier requirements, derived from the premise table."""
    return tuple(
        Requirement(
            id=row["id"],
            kind="AC",
            term="U",
            owner_repo=owner,
            acceptance=f"{row['name']}: {row['metric']} = {row['threshold']}",
            evidence_kind=row["evidence_kind"],
            evidence_locator=f"autonomic-receipt#{row['id']}",
            premise_refs=("RFC-0005§7",),
        )
        for row in gates.project(rfc5_text)["gates"]
    )


def _current(texts: Any, reqs: tuple[Requirement, ...], outputs: dict[str, bytes]) -> dict[str, str]:
    cur = berthier.source_digests(texts, reqs)
    for name in berthier.PROJECTED_OUTPUTS:
        cur[f"proj:{name}"] = sha256_bytes(outputs[name])
    return cur


def _compile(inputs: projector.Inputs, texts: Any) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, bytes]]:
    outputs = projector.compile_graph(inputs, rfc_text=texts)
    return json.loads(outputs["berthier.json"]), json.loads(outputs["out/packets.json"])["packets"], outputs


def _judge(graph: dict[str, Any], current: dict[str, str], packets: list[dict[str, Any]]) -> berthier.BerthierVerdict:
    return berthier.judge(berthier.edges_from_json(graph["edges"]), current, packets, graph["baseline"], None)


def run(inputs: projector.Inputs, rfc5_text: str) -> dict[str, Any]:
    rows_before = digest(inputs.requirements_doc)
    pins_before = digest(inputs.pins)
    committed = inputs.release_dir / "berthier.json"
    single = projector.compile_graph(inputs)["berthier.json"]
    single_identical = committed.is_file() and committed.read_bytes() == single

    texts = {"RFC-0004": inputs.rfc_text, "RFC-0005": rfc5_text}
    set_inputs = replace(inputs, requirements=inputs.requirements + gate_requirements(rfc5_text))
    graph, packets, outputs = _compile(set_inputs, texts)
    current = _current(texts, set_inputs.requirements, outputs)
    verdict = _judge(graph, current, packets)
    changed = berthier.delta(graph["baseline"], graph["compiled"])
    affected_owners = sorted({r.owner_repo for r in set_inputs.requirements if berthier.req_key(r.id) in changed})

    # Objective mutation: RFC-0005 §7 once.
    from scripts.release_train.root_crown.requirements import premise_sections

    section = premise_sections(rfc5_text)["§7"]
    mutated5 = rfc5_text.replace(section, section + MUTATION_NOTE, 1)
    mutated_texts = {"RFC-0004": inputs.rfc_text, "RFC-0005": mutated5}
    mutated_current = _current(mutated_texts, set_inputs.requirements, outputs)
    stale = _judge(graph, mutated_current, packets)
    dependents = sorted(r.id for r in set_inputs.requirements if "RFC-0005§7" in r.premise_refs)
    expected_stale = {berthier.req_key(rid) for rid in dependents}
    expected_stale |= {berthier.packet_key(ROOT_REPOSITORY)} | {f"proj:{o}" for o in berthier.PROJECTED_OUTPUTS}
    expected_stale |= {berthier.artifact_key(f"autonomic-receipt#{rid}") for rid in dependents}
    prior_inputs = replace(set_inputs, prior_berthier=graph)
    graph2, packets2, outputs2 = _compile(prior_inputs, mutated_texts)
    after = _judge(graph2, _current(mutated_texts, set_inputs.requirements, outputs2), packets2)
    restatements = int(digest(inputs.requirements_doc) != rows_before) + int(digest(inputs.pins) != pins_before)

    mutants = _mutants(graph, current, packets, inputs, set_inputs.requirements, stale)
    ok = (
        single_identical
        and not verdict.refusals
        and list(verdict.required_owners) == affected_owners
        and set(stale.stale) == expected_stale
        and not after.refusals
        and list(after.required_owners) == [ROOT_REPOSITORY]
        and restatements == 0
        and all(m["killed"] for m in mutants.values())
    )
    return {
        "premise_set": {rfc: sha256_bytes(t.encode("utf-8")) for rfc, t in sorted(texts.items())},
        "premise_set_digest": berthier.premise_set_digest(texts),
        "single_premise_identical": single_identical,
        "recompile": {
            "standing": verdict.standing,
            "refusals": list(verdict.refusals),
            "strategic_delta": len(changed),
            "required_owners": list(verdict.required_owners),
            "affected_owners": affected_owners,
            "packets_digest": digest(packets),
        },
        "objective_mutation": {
            "section": "RFC-0005§7",
            "dependents": dependents,
            "stale_matches_dependents": set(stale.stale) == expected_stale,
            "stale": len(stale.stale),
            "recompile_standing": after.standing,
            "recompile_refusals": list(after.refusals),
            "required_owners": list(after.required_owners),
        },
        "manual_restatement_count": restatements,
        "mutants": mutants,
        "ok": ok,
    }


def _mutants(
    graph: dict[str, Any],
    current: dict[str, str],
    packets: list[dict[str, Any]],
    inputs: projector.Inputs,
    reqs: tuple[Requirement, ...],
    stale: berthier.BerthierVerdict,
) -> dict[str, dict[str, Any]]:
    control = set(_judge(graph, current, packets).refusals)

    omitted = [p for p in packets if p["subject"]["repository"] != ROOT_REPOSITORY]
    amplified = copy.deepcopy(packets)
    for p in amplified:
        p["authority_ceiling"] = "DO"
    unbound = {k: v for k, v in current.items() if not k.startswith("premise:RFC-0005#")}
    emitted = {
        "OMITTED_SUBJECT": set(_judge(graph, current, omitted).refusals),
        "STALE_PROJECTION": set(stale.refusals),
        "PREMISE_UNBOUND": set(_judge(graph, unbound, packets).refusals),
        "AUTHORITY_INCREASE": set(_judge(graph, current, amplified).refusals),
    }
    out = {}
    for token in MUTANT_TOKENS:
        hit = any(f":{token}:" in r for r in emitted[token])
        leak = any(f":{token}:" in r for r in control)
        out[token] = {"killed": hit and not leak, "emitted": hit, "control_emitted": leak}
    return out
