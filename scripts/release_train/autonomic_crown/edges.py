"""Edge-graph court (RFC-0005 §5, §6) and the edge-derived gates U-01..U-04.

``edges.json`` is the honest inventory of the recurring release path: who operates each
edge today. The court never trusts a stored digest: every ``evidence.sha256`` is
recomputed from the located bytes (§6.5). A machine-owned edge must be witnessed by
machine evidence (a workflow, a run or a receipt); a test fixture or a hand-kept log
cannot witness machine ownership (``OWNER_KIND_UNWITNESSED``). A machine edge that
grants itself authority is ``AUTHORITY_AMPLIFICATION`` (§5: only a declared human grant
is an authority gate).

``owner_kinds`` (an additive field) lists every kind that operates the edge; the RFC's
``owner_kind`` is its first element. U-01..U-03 range over recurring edges; U-01's
denominator excludes edges whose only human act is a declared authority grant (§5, §6.2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .locate import Source, Unresolved
from .model import (
    EVIDENCE_KINDS,
    MACHINE_WITNESS_KINDS,
    OWNER_KINDS,
    SCHEMA_EDGES,
    STAGES,
    Finding,
    GateResult,
    sha256_bytes,
)

# Evidence kinds the RFC schema does not list and this court cannot recompute (CAPABILITY_GAP).
UNSUPPORTED_KINDS = ("attestation", "sbom", "provenance")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")


@dataclass
class EdgeReport:
    findings: list[Finding] = field(default_factory=list)
    resolved: dict[str, str] = field(default_factory=dict)  # edge id -> recomputed sha256
    unresolved: dict[str, str] = field(default_factory=dict)  # edge id -> code
    edges: list[dict[str, Any]] = field(default_factory=list)


def owner_kinds(edge: dict[str, Any]) -> list[str]:
    kinds = edge.get("owner_kinds")
    if isinstance(kinds, list) and kinds:
        return kinds
    return [edge.get("owner_kind")]


def is_authority_gate_only(edge: dict[str, Any]) -> bool:
    """A human edge whose only human act is a declared grant (§5 HumanAuthorityGate)."""
    return owner_kinds(edge) == ["human"] and isinstance(edge.get("authority_gate"), dict)


def is_operational_dependency(edge: dict[str, Any]) -> bool:
    """§5 classification: human involvement not declared as a grant is operational."""
    return "human" in owner_kinds(edge) and not is_authority_gate_only(edge)


def check(doc: dict[str, Any], source: Source, crown_subject: str | None = None) -> EdgeReport:
    rep = EdgeReport()
    if not isinstance(doc, dict) or doc.get("schema") != SCHEMA_EDGES or not isinstance(doc.get("edges"), list):
        rep.findings.append(Finding("EDGE_MALFORMED", "edges.json", "schema edges.v1 with an edges list"))
        return rep
    subject = doc.get("crown_subject")
    if not isinstance(subject, str) or not _HEX40.match(subject):
        rep.findings.append(Finding("EDGE_MALFORMED", "crown_subject", repr(subject)))
    elif crown_subject is not None and subject != crown_subject:
        rep.findings.append(Finding("SUBJECT_SPLIT", "crown_subject", f"edges={subject} crown={crown_subject}"))
    seen: set[str] = set()
    stages: set[str] = set()
    for index, edge in enumerate(doc["edges"]):
        eid = edge.get("id") if isinstance(edge, dict) else None
        name = eid if isinstance(eid, str) and eid else f"edges[{index}]"
        bad = _malformed(edge)
        if isinstance(eid, str) and eid in seen:
            bad.append("duplicate id")
        if bad:
            rep.findings.extend(Finding("EDGE_MALFORMED", name, b) for b in bad)
            continue
        seen.add(eid)
        stages.add(edge["stage"])
        rep.edges.append(edge)
        kinds = owner_kinds(edge)
        ev = edge["evidence"]
        gate = edge.get("authority_gate")
        if kinds[0] == "machine" and ev["kind"] not in MACHINE_WITNESS_KINDS:
            rep.findings.append(
                Finding("OWNER_KIND_UNWITNESSED", name, f"machine owner witnessed only by {ev['kind']}")
            )
        if isinstance(gate, dict) and "human" not in kinds:
            rep.findings.append(
                Finding("AUTHORITY_AMPLIFICATION", name, f"{kinds} edge holds authority_gate {gate.get('grant')!r}")
            )
        if ev["kind"] in UNSUPPORTED_KINDS:
            rep.unresolved[name] = "UNSUPPORTED_EVIDENCE_KIND"
            rep.findings.append(
                Finding("UNSUPPORTED_EVIDENCE_KIND", name, f"evidence kind {ev['kind']} is not recomputable")
            )
            continue
        try:
            data = source.resolve(ev["locator"])
        except Unresolved as exc:
            rep.unresolved[name] = exc.code
            rep.findings.append(Finding(exc.code, name, exc.detail))
            continue
        got = sha256_bytes(data)
        rep.resolved[name] = got
        if got != ev["sha256"]:
            rep.findings.append(Finding("EVIDENCE_DIGEST_MISMATCH", name, f"declared={ev['sha256']} recomputed={got}"))
    for stage in STAGES:
        if stage not in stages:
            rep.findings.append(Finding("STAGE_UNCOVERED", stage, "no edge names this stage"))
    return rep


def _malformed(edge: Any) -> list[str]:
    if not isinstance(edge, dict):
        return ["not an object"]
    bad = []
    for key in ("id", "from", "to"):
        if not isinstance(edge.get(key), str) or not edge[key].strip():
            bad.append(key)
    if edge.get("stage") not in STAGES:
        bad.append(f"stage={edge.get('stage')!r}")
    kinds = owner_kinds(edge)
    if any(k not in OWNER_KINDS for k in kinds) or len(set(kinds)) != len(kinds):
        bad.append(f"owner_kinds={kinds!r}")
    if edge.get("owner_kind") != kinds[0]:
        bad.append("owner_kind != owner_kinds[0]")
    gate = edge.get("authority_gate")
    if gate is not None and not (
        isinstance(gate, dict)
        and set(gate) == {"grantor", "grant"}
        and all(isinstance(v, str) and v.strip() for v in gate.values())
    ):
        bad.append("authority_gate")
    if not isinstance(edge.get("recurring"), bool):
        bad.append("recurring")
    ev = edge.get("evidence")
    if not isinstance(ev, dict):
        bad.append("evidence")
    else:
        if ev.get("kind") not in EVIDENCE_KINDS + UNSUPPORTED_KINDS:
            bad.append(f"evidence.kind={ev.get('kind')!r}")
        if not isinstance(ev.get("locator"), str):
            bad.append("evidence.locator")
        if not isinstance(ev.get("sha256"), str) or not _HEX64.match(ev["sha256"]):
            bad.append("evidence.sha256")
    return bad


def _evidence(rep: EdgeReport, doc: dict[str, Any]) -> dict[str, str]:
    from .model import digest

    return {"kind": "edges.json", "digest": digest(doc)}


def gate_results(doc: dict[str, Any], rep: EdgeReport) -> list[GateResult]:
    recurring = [e for e in rep.edges if e["recurring"]]
    denominator = [e for e in recurring if not is_authority_gate_only(e)]
    machine = [e for e in denominator if owner_kinds(e) == ["machine"]]
    non_machine = sorted(e["id"] for e in denominator if owner_kinds(e) != ["machine"])
    ops = sorted(e["id"] for e in recurring if is_operational_dependency(e))
    llm = sorted(e["id"] for e in recurring if "llm" in owner_kinds(e))
    exact = sorted(e["id"] for e in rep.edges if rep.resolved.get(e["id"]) == e["evidence"]["sha256"])
    inexact = sorted(e["id"] for e in rep.edges if e["id"] not in exact)
    ev = _evidence(rep, doc)
    out = []
    ratio = f"{len(machine)}/{len(denominator)}"
    if denominator and not non_machine:
        out.append(GateResult("U-01", "PASS", ratio, "100%", evidence=ev))
    else:
        out.append(
            GateResult(
                "U-01",
                "BLOCKED",
                ratio,
                "100%",
                "HUMAN_OR_LLM_EDGE",
                f"non-machine recurring edges: {non_machine}",
                findings=non_machine,
            )
        )
    if not ops:
        out.append(GateResult("U-02", "PASS", 0, "0", evidence=ev))
    else:
        out.append(
            GateResult(
                "U-02",
                "BLOCKED",
                len(ops),
                "0",
                "HUMAN_OPERATIONAL_DEPENDENCY",
                f"human operational dependencies: {ops}",
                findings=ops,
            )
        )
    if not llm:
        out.append(GateResult("U-03", "PASS", 0, "0", evidence=ev))
    else:
        out.append(
            GateResult(
                "U-03",
                "BLOCKED",
                len(llm),
                "0",
                "GENERAL_LLM_ON_RECURRING_PATH",
                f"LLM-operated recurring edges: {llm}",
                findings=llm,
            )
        )
    measured = f"{len(exact)}/{len(rep.edges)}"
    if rep.edges and not inexact:
        out.append(GateResult("U-04", "PASS", measured, "100%", evidence=ev))
    else:
        detail = {e: rep.unresolved.get(e, "EVIDENCE_DIGEST_MISMATCH") for e in inexact}
        out.append(
            GateResult(
                "U-04",
                "BLOCKED",
                measured,
                "100%",
                "EVIDENCE_NOT_EXACT",
                f"edges without a recomputed durable digest: {detail}",
                findings=inexact,
            )
        )
    return out
