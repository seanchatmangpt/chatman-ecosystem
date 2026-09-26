"""The autonomic crown court: inputs, one evaluation, the gate table U-01..U-18.

``evaluate`` is pure over its ``Inputs`` apart from reads through ``inputs.source``
(read-only). With ``self_attack=True`` it also runs the §8 self-attack (U-05/U-06), the
semantic mutants (U-07) and the premise-set test (U-12); those nested evaluations run
with ``self_attack=False`` and never recurse.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from scripts.release_train.root_crown import crown as root_crown
from scripts.release_train.root_crown import projector

from . import durability, edges, gates, workflow_scan
from .locate import Source, Unresolved, git_blob_id
from .model import (
    CODES,
    GATE_IDS,
    ROOT_REPOSITORY,
    Finding,
    GateResult,
    digest,
    sha256_bytes,
)
from .standing import authority_of, autonomy_of, execution_of, governance_gaps, legality

NESTED = ("U-05", "U-06", "U-07", "U-12")
INPUT_NAMES = ("crown_receipt", "observations", "chain", "workflow")
BACK_EDGE_STAGES = ("repair", "continue")


@dataclass
class Inputs:
    release_dir: Path
    gates_doc: dict[str, Any]
    edges_doc: dict[str, Any]
    rfc5_text: str
    imports: list[tuple[dict[str, Any], bytes]]
    locators: dict[str, str]  # INPUT_NAMES -> durable locator (``{crown_sha}`` template allowed)
    source: Source
    overrides: dict[str, bytes] = field(default_factory=dict)  # INPUT_NAMES -> bytes from a file
    governance: dict[str, Any] | None = None
    evaluated_heads: dict[str, str] = field(default_factory=dict)  # re-evaluation overrides (NEW_HEAD)
    hypothesis: str = ""


@dataclass
class Evaluation:
    findings: list[Finding]
    gates: list[GateResult]
    execution: dict[str, str]
    autonomy: str
    authority: str
    authority_detail: str
    crown_receipt: dict[str, Any] | None
    input_digests: dict[str, dict[str, str]]
    reports: dict[str, Any]

    @property
    def codes(self) -> set[str]:
        return {f.code for f in self.findings}

    @property
    def refused(self) -> bool:
        return any(f.severity == "REFUSED" for f in self.findings)

    def gate(self, gid: str) -> GateResult:
        return next(g for g in self.gates if g.id == gid)

    def fingerprint(self, exclude: tuple[str, ...] = NESTED) -> dict[str, Any]:
        return {
            "gates": {g.id: g.as_dict() for g in self.gates if g.id not in exclude},
            "execution": self.execution,
            "autonomy": self.autonomy,
            "authority": self.authority,
            "codes": sorted(str(f) for f in self.findings),
        }


def _read(inputs: Inputs, name: str, crown_sha: str | None) -> tuple[bytes | None, Finding | None, str]:
    if name in inputs.overrides:
        return inputs.overrides[name], None, f"file:{name}"
    locator = inputs.locators.get(name)
    if not locator:
        return None, Finding("EVIDENCE_UNRESOLVED", name, "no locator"), ""
    if "{crown_sha}" in locator:
        if not crown_sha:
            return None, Finding("EVIDENCE_UNRESOLVED", name, "crown_sha unknown"), locator
        locator = locator.replace("{crown_sha}", crown_sha)
    try:
        return inputs.source.resolve(locator), None, locator
    except Unresolved as exc:
        return None, Finding(exc.code, name, exc.detail), locator


def _json(data: bytes | None) -> Any:
    if data is None:
        return None
    try:
        return json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return None


def check_imports(imports: list[tuple[dict[str, Any], bytes]]) -> list[Finding]:
    out = []
    for row, data in imports:
        if sha256_bytes(data) != row.get("sha256") or git_blob_id(data) != row.get("source_blob_sha1"):
            out.append(Finding("IMPORT_DIGEST_MISMATCH", row.get("path", "?"), "copy does not recompute"))
    return out


def check_chain(chain: dict[str, Any] | None, receipt: dict[str, Any] | None) -> list[Finding]:
    if chain is None or receipt is None:
        return []
    entries = chain.get("entries") or []
    out = []
    for prev, entry in zip(entries, entries[1:]):
        if entry.get("previous_receipt_digest") != prev.get("receipt_digest"):
            out.append(Finding("CHAIN_FORGED", str(entry.get("run_id")), "previous_receipt_digest does not link"))
    if entries and chain.get("head") != entries[-1].get("receipt_digest"):
        out.append(Finding("CHAIN_FORGED", "head", "head is not the last entry"))
    digest_ = receipt.get("receipt_digest")
    member = next((e for e in entries if e.get("receipt_digest") == digest_), None)
    if member is not None:
        if member.get("previous_receipt_digest") != receipt.get("previous_receipt_digest") or member.get(
            "crown_sha"
        ) != receipt.get("crown_sha"):
            out.append(Finding("CHAIN_FORGED", str(member.get("run_id")), "entry disagrees with the receipt"))
    elif receipt.get("previous_receipt_digest") != chain.get("head"):
        out.append(Finding("CHAIN_FORGED", "receipt", "receipt is neither chained nor a child of the chain head"))
    return out


def check_dependencies(
    receipt: dict[str, Any] | None, observations: dict[str, Any] | None, overrides: dict[str, str]
) -> list[Finding]:
    """Observed heads vs the heads the crown evaluated: local NEW_HEAD (R) vs remote producer (U)."""
    if receipt is None or observations is None:
        return []
    observed: dict[str, str] = {}
    for block in (observations.get("repos") or {}, (observations.get("private_repos") or {}).get("repos") or {}):
        for repo, row in block.items():
            if isinstance(row, dict) and isinstance(row.get("head_sha"), str):
                observed[repo] = row["head_sha"]
    evaluated = dict(receipt.get("heads") or {})
    evaluated.update(overrides)
    out = []
    for repo, sha in sorted(evaluated.items()):
        seen = observed.get(repo)
        if seen is None or seen == sha:
            continue
        code = "NEW_HEAD" if repo == ROOT_REPOSITORY else "WAITING_PRODUCER"
        out.append(Finding(code, repo, f"evaluated={sha} observed={seen}"))
    return out


def check_model(doc: dict[str, Any]) -> list[Finding]:
    """The edge graph may cycle only through a repair or continue edge; any other cycle is a
    counterexample to the loop model (a livelock) and is preserved in the finding."""
    graph: dict[str, list[str]] = {}
    for e in doc.get("edges") or []:
        if isinstance(e, dict) and e.get("stage") not in BACK_EDGE_STAGES and isinstance(e.get("from"), str):
            graph.setdefault(e["from"], []).append(e["to"])
    state: dict[str, int] = {}
    stack: list[str] = []
    found: list[list[str]] = []

    def visit(node: str) -> None:
        state[node] = 1
        stack.append(node)
        for nxt in sorted(graph.get(node, [])):
            if state.get(nxt) == 1:
                found.append(stack[stack.index(nxt) :] + [nxt])
            elif state.get(nxt) is None:
                visit(nxt)
        stack.pop()
        state[node] = 2

    for node in sorted(graph):
        if state.get(node) is None:
            visit(node)
    return [Finding("MODEL_COUNTEREXAMPLE", "edges", "cycle without repair/continue: " + " -> ".join(c)) for c in found]


def _blocked(
    gid: str, measured: Any, threshold: str, code: str, detail: str, findings: list[str] | None = None
) -> GateResult:
    return GateResult(gid, "BLOCKED", measured, threshold, code, detail, findings=findings or [])


def evaluate(inputs: Inputs, self_attack: bool = True) -> Evaluation:
    findings: list[Finding] = []
    findings += gates.coverage(inputs.gates_doc, inputs.rfc5_text)
    findings += check_imports(inputs.imports)

    raw: dict[str, bytes | None] = {}
    located: dict[str, str] = {}
    data, problem, loc = _read(inputs, "crown_receipt", None)
    raw["crown_receipt"], located["crown_receipt"] = data, loc
    if problem:
        findings.append(problem)
    receipt = _json(data)
    if data is not None and not (isinstance(receipt, dict) and root_crown.verify_receipt(receipt)):
        findings.append(Finding("RECEIPT_UNVERIFIED", "crown_receipt", "receipt digest does not recompute"))
        receipt = None
    # A refused receipt names no subject: bind to the inventory's subject so independent
    # gates keep evaluating (RFC-0005 §8 U: continue every independent edge).
    crown_sha = receipt.get("crown_sha") if receipt else inputs.edges_doc.get("crown_subject")
    docs: dict[str, Any] = {}
    for name in ("observations", "chain", "workflow"):
        data, problem, loc = _read(inputs, name, crown_sha)
        raw[name], located[name] = data, loc
        if problem:
            findings.append(problem)
        docs[name] = data
    observations = _json(docs["observations"])
    chain = _json(docs["chain"])
    workflow_text = docs["workflow"].decode("utf-8") if docs["workflow"] is not None else None
    findings += check_chain(chain, receipt)
    findings += check_dependencies(receipt, observations, inputs.evaluated_heads)
    findings += check_model(inputs.edges_doc)

    rep = edges.check(inputs.edges_doc, inputs.source, receipt.get("crown_sha") if receipt else None)
    findings += rep.findings
    results = edges.gate_results(inputs.edges_doc, rep)

    scan = workflow_scan.scan(workflow_text) if workflow_text is not None else None
    wf_ev = {"kind": "workflow", "digest": "sha256:" + sha256_bytes(docs["workflow"])} if scan else None
    governance = inputs.governance

    # U-05, U-06, U-07, U-12: self-attack, mutants, premise set (top level only).
    reports: dict[str, Any] = {}
    if self_attack:
        from . import faults, mutants, premise

        fault_report = faults.run(inputs)
        reports["self_attack"] = fault_report
        results.append(_fault_gate("U-05", "R", fault_report))
        results.append(_fault_gate("U-06", "U", fault_report))
        mutant_report = mutants.run(inputs)
        reports["mutants"] = mutant_report
        survivors = sorted(n for n, m in mutant_report["mutants"].items() if not m["killed"])
        killed = f"{mutant_report['killed']}/{mutant_report['total']}"
        results.append(
            GateResult(
                "U-07", "PASS", killed, "100%", evidence={"kind": "mutation receipts", "digest": digest(mutant_report)}
            )
            if not survivors and mutant_report["total"]
            else _blocked("U-07", killed, "100%", "MUTANT_SURVIVED", f"survivors: {survivors}", survivors)
        )
        premise_report = premise.run(projector.load_inputs(inputs.release_dir), inputs.rfc5_text)
        reports["premise_set"] = premise_report
        results.append(
            GateResult(
                "U-12",
                "PASS",
                f"ManualRestatementCount={premise_report['manual_restatement_count']}",
                "100%",
                evidence={"kind": "premise-set receipts", "digest": digest(premise_report)},
            )
            if premise_report["ok"]
            else _blocked(
                "U-12",
                premise_report["manual_restatement_count"],
                "100%",
                "PREMISE_SET_FAILED",
                "premise-set test failed",
            )
        )
    else:
        for gid in NESTED:
            results.append(_blocked(gid, None, "-", "UNMEASURED", "nested evaluation (self-attack does not recurse)"))

    # U-08 authority amplification: operator-only gates (§12, §13) + no accepted amplification.
    amplified = sorted(f.subject for f in findings if f.code == "AUTHORITY_AMPLIFICATION")
    gaps = governance_gaps(governance) if governance else ["governance unobserved"]
    if not gaps and not amplified:
        results.append(
            GateResult("U-08", "PASS", 0, "0", evidence={"kind": "governance", "digest": digest(governance)})
        )
    else:
        results.append(
            _blocked(
                "U-08",
                len(amplified),
                "0",
                "AUTHORITY_CONFIGURATION",
                "; ".join(gaps + [f"amplified: {amplified}"] * bool(amplified)),
                amplified,
            )
        )
    no_brce = "no BRCE reconciliation receipts on the crown path"
    results.append(_blocked("U-09", None, "0", "UNMEASURED", no_brce))
    results.append(_blocked("U-10", None, "100%", "UNMEASURED", no_brce + "; no kill-injection receipts"))

    # U-11 cold reconstruction and U-14 hidden local state.
    if scan is None:
        results.append(_blocked("U-11", None, "100%", "EVIDENCE_UNRESOLVED", "workflow unresolved"))
    else:
        nd = durability.non_durable_receipts(workflow_text or "", rep.edges)
        results.append(
            _blocked("U-11", len(nd), "100%", "NON_DURABLE_RECEIPT_STORE", f"retention-bound receipts: {nd}", nd)
            if nd
            else GateResult("U-11", "PASS", 0, "100%", evidence=wf_ev)
        )
    hidden = durability.hidden_local_state(observations or {}, rep.edges)
    if observations is None:
        results.append(_blocked("U-14", None, "0", "EVIDENCE_UNRESOLVED", "observations unresolved"))
    elif hidden:
        results.append(
            _blocked("U-14", len(hidden), "0", "HIDDEN_LOCAL_STATE", f"operator-host state: {hidden}", hidden)
        )
    else:
        results.append(
            GateResult("U-14", "PASS", 0, "0", evidence={"kind": "observations", "digest": digest(observations)})
        )

    # U-13 pinned toolchain, U-16 internal blockers, U-17 scheduler independence.
    if scan is None:
        for gid, thr in (("U-13", "0"), ("U-16", "0"), ("U-17", "false")):
            results.append(_blocked(gid, None, thr, "EVIDENCE_UNRESOLVED", "workflow unresolved"))
    else:
        results.append(
            _blocked("U-13", len(scan.violations), "0", "UNPINNED_TOOLCHAIN", f"{scan.violations}", scan.violations)
            if scan.violations
            else GateResult("U-13", "PASS", 0, "0", evidence=wf_ev)
        )
        internal = [r.get("id", "?") for r in (receipt or {}).get("remaining", [])]
        if scan.warns_on_blocked:
            results.append(
                _blocked(
                    "U-16",
                    len(internal),
                    "0",
                    "BLOCKED_ONLY_WARNS",
                    "exit 3 (typed BLOCKED) is a warning, not a failure",
                )
            )
        elif internal or receipt is None:
            results.append(
                _blocked(
                    "U-16", len(internal), "0", "INTERNAL_SUBJECT_NOT_AUTONOMIC", f"remaining: {internal}", internal
                )
            )
        else:
            results.append(GateResult("U-16", "PASS", 0, "0", evidence=wf_ev))
        independent = scan.independent_triggers
        stops = not independent
        results.append(
            _blocked(
                "U-17",
                stops,
                "false",
                "SINGLE_SCHEDULER",
                f"schedulers={scan.schedulers}; no unconditional secondary machine trigger (triggers={sorted(scan.triggers)})",
            )
            if stops
            else GateResult("U-17", "PASS", False, "false", evidence=wf_ev)
        )
    results.append(
        _blocked("U-15", None, "0", "UNMEASURED", "run history is not durable (the chain holds only committed runs)")
    )

    # U-18 independent clean cycles: distinct subjects among ALIVE chain entries.
    clean = sorted({e.get("crown_sha") for e in (chain or {}).get("entries", []) if e.get("standing") == "ALIVE"})
    measured = f"{min(len(clean), 3)}/3"
    results.append(
        GateResult("U-18", "PASS", measured, "3/3", evidence={"kind": "cycle receipts", "digest": digest(chain)})
        if len(clean) >= 3 and chain is not None
        else _blocked("U-18", measured, "3/3", "INSUFFICIENT_CLEAN_CYCLES", f"distinct ALIVE subjects: {clean}", clean)
    )

    results.sort(key=lambda g: g.id)
    findings += gates.admit(results)
    execution = execution_of(receipt, findings)
    autonomy, auto_findings = autonomy_of(results, execution["state"])
    findings += auto_findings
    authority, authority_detail = authority_of(governance, findings)
    findings += legality(execution["state"], autonomy, authority)
    findings = sorted(set(findings), key=lambda f: (f.code, f.subject, f.detail))
    assert all(f.code in CODES for f in findings)
    input_digests = {
        name: {
            "locator": located.get(name, ""),
            "sha256": sha256_bytes(raw[name]) if raw.get(name) is not None else "UNRESOLVED",
        }
        for name in INPUT_NAMES
    }
    reports["edges"] = {
        "total": len(rep.edges),
        "recurring": sum(1 for e in rep.edges if e["recurring"]),
        "resolved": dict(sorted(rep.resolved.items())),
        "unresolved": dict(sorted(rep.unresolved.items())),
    }
    reports["workflow_scan"] = scan.as_dict() if scan else None
    return Evaluation(
        findings, results, execution, autonomy, authority, authority_detail, receipt, input_digests, reports
    )


def _fault_gate(gid: str, rec: str, report: dict[str, Any]) -> GateResult:
    rows = {k: v for k, v in report["faults"].items() if v["recoverability"] == rec}
    ok = sorted(k for k, v in rows.items() if v["ok"])
    bad = sorted(k for k, v in rows.items() if not v["ok"])
    measured = f"{len(ok)}/{len(rows)}"
    if rows and not bad:
        return GateResult(
            gid, "PASS", measured, "100%", evidence={"kind": "fault-injection receipts", "digest": digest(rows)}
        )
    return _blocked(
        gid, measured, "100%", "FAULT_UNREPAIRED" if rec == "R" else "FAULT_UNCONTAINED", f"failed: {bad}", bad
    )


def gate_ids() -> tuple[str, ...]:
    return GATE_IDS


def load_inputs(
    root: Path,
    release: str,
    repos_root: Path | None,
    overrides: dict[str, bytes] | None = None,
    governance: dict[str, Any] | None = None,
) -> Inputs:
    """Inputs from ``release/<v>/autonomy`` (edges, gates, imports, evaluation locators)."""
    from .locate import CachingSource, EvidenceResolver, load_imports

    release_dir = root / "release" / release
    autonomy = release_dir / "autonomy"
    imports = load_imports([autonomy])
    source = CachingSource(EvidenceResolver(repos_root, imports + load_imports([release_dir])))
    evaluation = json.loads((autonomy / "evaluation.json").read_text(encoding="utf-8"))
    return Inputs(
        release_dir=release_dir,
        gates_doc=json.loads((autonomy / "gates.json").read_text(encoding="utf-8")),
        edges_doc=json.loads((autonomy / "edges.json").read_text(encoding="utf-8")),
        rfc5_text=(autonomy / "imports" / "RFC-0005.md").read_text(encoding="utf-8"),
        imports=imports,
        locators={k: evaluation["locators"][k] for k in INPUT_NAMES},
        source=source,
        overrides=dict(overrides or {}),
        governance=governance,
    )
