"""Semantic mutants of the autonomic crown and its gates (U-07, anti-vacuity).

Each mutant breaks exactly one thing in the court's inputs or in a verdict it would
admit, and is *killed* only when the real court emits the expected code on the mutant
and does not emit it on the unmutated control. A court that crashes on a mutant is a
survivor (typed), never a kill.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, replace
from typing import Any, Callable

from . import gates, standing
from .locate import ResolverWithOverlay
from .model import GATE_IDS, GateResult, digest


@dataclass(frozen=True)
class Mutant:
    name: str
    expected: str
    build: Callable[[Any], Any] | None = None  # inputs -> mutated inputs (evaluated by the court)
    verdict: Callable[[Any, bool], set[str]] | None = None  # (base evaluation, mutated?) -> emitted codes
    control: Callable[[Any], Any] | None = None  # inputs -> control inputs (default: unmutated)


def _edge(eid: str, fn: Callable[[dict[str, Any]], None]) -> Callable[[Any], Any]:
    def build(inputs: Any) -> Any:
        doc = copy.deepcopy(inputs.edges_doc)
        for edge in doc["edges"]:
            if edge["id"] == eid:
                fn(edge)
        return replace(inputs, edges_doc=doc)

    return build


def _gate_row(gid: str, key: str, value: Any) -> Callable[[Any], Any]:
    def build(inputs: Any) -> Any:
        doc = copy.deepcopy(inputs.gates_doc)
        for row in doc["gates"]:
            if row["id"] == gid:
                row[key] = value
        return replace(inputs, gates_doc=doc)

    return build


def _drop_gate(gid: str) -> Callable[[Any], Any]:
    def build(inputs: Any) -> Any:
        doc = copy.deepcopy(inputs.gates_doc)
        doc["gates"] = [r for r in doc["gates"] if r["id"] != gid]
        return replace(inputs, gates_doc=doc)

    return build


# A clean, fully pinned controller workflow: the control for the U-13 scanner mutants, so each
# mutant's violation is absent on the control by construction (the evaluated tag-time workflow
# already violates U-13 and could not show a kill).
CLEAN_WORKFLOW = """on:
  schedule:
    - cron: '7,37 * * * *'
  push:
    branches: [main]
jobs:
  crown:
    runs-on: crown-runner
    container:
      image: ghcr.io/example/crown@sha256:%s
    steps:
      - uses: actions/checkout@d23441a48e516b6c34aea4fa41551a30e30af803
      - uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1
        with:
          python-version: '3.12.14'
""" % ("0" * 64)


def _workflow(old: str | None, new: str | None) -> Callable[[Any], Any]:
    """Serve CLEAN_WORKFLOW (old=None: the control) or it with one edit at the workflow locator."""

    def build(inputs: Any) -> Any:
        from .faults import _resolved

        locator, _ = _resolved(inputs, "workflow")
        text = CLEAN_WORKFLOW if old is None else CLEAN_WORKFLOW.replace(old, new or "", 1)
        assert old is None or old in CLEAN_WORKFLOW, f"anchor drift: {old!r}"
        data = text.encode("utf-8")
        return replace(inputs, source=ResolverWithOverlay(inputs.source, {locator: lambda n: data}, f"workflow:{new}"))

    return build


def _json_input(name: str, fn: Callable[[Any], None]) -> Callable[[Any], Any]:
    def build(inputs: Any) -> Any:
        from .faults import _resolved

        locator, data = _resolved(inputs, name)
        doc = json.loads(data)
        fn(doc)
        mutated = json.dumps(doc).encode("utf-8")
        return replace(
            inputs, source=ResolverWithOverlay(inputs.source, {locator: lambda n: mutated}, f"{name}:mutant")
        )

    return build


def _import_tamper(inputs: Any) -> Any:
    rows = [
        (row, data + b"\n") if row.get("path", "").endswith("RFC-0005.md") else (row, data)
        for row, data in inputs.imports
    ]
    return replace(inputs, imports=rows)


def _pass_without_evidence(base: Any, mutated: bool) -> set[str]:
    results = [copy.deepcopy(g) for g in base.gates]
    if mutated:
        target = next(g for g in results if g.state != "PASS")
        target.state, target.evidence, target.code = "PASS", None, None
    return {f.code for f in gates.admit(results)}


def _autonomic_without_alive(base: Any, mutated: bool) -> set[str]:
    results = [GateResult(gid, "PASS", 0, "0", evidence={"kind": "x", "digest": digest(gid)}) for gid in GATE_IDS]
    execution = "BLOCKED" if mutated else "ALIVE"
    _, found = standing.autonomy_of(results, execution)
    claimed = {f.code for f in standing.legality(execution, "AUTONOMIC", base.authority)}
    return {f.code for f in found} | claimed


def _illegal_triple(base: Any, mutated: bool) -> set[str]:
    return {f.code for f in standing.legality("ALIVE", "SELF_DECLARED" if mutated else "NOT_AUTONOMIC", base.authority)}


def catalog() -> tuple[Mutant, ...]:
    return (
        Mutant("gate_row_dropped", "GATE_COVERAGE_GAP", _drop_gate("U-13")),
        Mutant("gate_threshold_relaxed", "GATE_COVERAGE_GAP", _gate_row("U-02", "threshold", "1")),
        Mutant(
            "hand_supply_relabeled_machine",
            "OWNER_KIND_UNWITNESSED",
            _edge("E-REP-01", lambda e: e.update(owner_kind="machine", owner_kinds=["machine"])),
        ),
        Mutant(
            "locator_scratch_path",
            "LOCATOR_NOT_DURABLE",
            _edge("E-VER-01", lambda e: e["evidence"].update(locator="/private/tmp/crown-receipt.json")),
        ),
        Mutant(
            "evidence_digest_forged",
            "EVIDENCE_DIGEST_MISMATCH",
            _edge("E-DEC-01", lambda e: e["evidence"].update(sha256="f" * 64)),
        ),
        Mutant("edge_stage_unknown", "EDGE_MALFORMED", _edge("E-OBS-01", lambda e: e.update(stage="observe-ish"))),
        Mutant(
            "container_unpinned",
            "UNPINNED_CONTAINER",
            _workflow("@sha256:" + "0" * 64, ":latest"),
            control=_workflow(None, None),
        ),
        Mutant("stage_uncovered", "STAGE_UNCOVERED", _edge("E-CONT-01", lambda e: e.update(stage="replay"))),
        Mutant(
            "machine_self_grant",
            "AUTHORITY_AMPLIFICATION",
            _edge("E-VER-01", lambda e: e.update(authority_gate={"grantor": "root-crown", "grant": "tag"})),
        ),
        Mutant(
            "subject_split", "SUBJECT_SPLIT", lambda i: replace(i, edges_doc={**i.edges_doc, "crown_subject": "7" * 40})
        ),
        Mutant("import_copy_tampered", "IMPORT_DIGEST_MISMATCH", _import_tamper),
        Mutant(
            "action_by_tag",
            "UNPINNED_ACTION",
            _workflow(
                "uses: actions/setup-python@ece7cb06caefa5fff74198d8649806c4678c61a1", "uses: actions/setup-python@v6"
            ),
            control=_workflow(None, None),
        ),
        Mutant(
            "python_inexact",
            "INEXACT_TOOLCHAIN",
            _workflow("python-version: '3.12.14'", "python-version: '3.12'"),
            control=_workflow(None, None),
        ),
        Mutant(
            "runner_latest",
            "FLOATING_RUNNER",
            _workflow("runs-on: crown-runner", "runs-on: ubuntu-latest"),
            control=_workflow(None, None),
        ),
        Mutant(
            "receipt_standing_flipped",
            "RECEIPT_UNVERIFIED",
            _json_input("crown_receipt", lambda d: d.update(standing="BLOCKED")),
        ),
        Mutant(
            "chain_link_forged", "CHAIN_FORGED", _json_input("chain", lambda d: d.update(head="sha256:" + "1" * 64))
        ),
        Mutant("loop_cycle_without_repair", "MODEL_COUNTEREXAMPLE", _edge("E-RPL-01", lambda e: e.update(to="main"))),
        Mutant("gate_pass_without_evidence", "GATE_PASS_WITHOUT_EVIDENCE", verdict=_pass_without_evidence),
        Mutant("autonomic_without_alive", "AUTONOMY_WITHOUT_ALIVE", verdict=_autonomic_without_alive),
        Mutant("illegal_standing_value", "ILLEGAL_STANDING_COMBINATION", verdict=_illegal_triple),
    )


def emitted_codes(ev: Any) -> set[str]:
    """Finding codes, gate codes and gate-finding codes (e.g. U-13 violation kinds)."""
    out = set(ev.codes) | {g.code for g in ev.gates if g.code}
    for g in ev.gates:
        out |= {str(f).split(":", 1)[0] for f in g.findings}
    return out


def run(inputs: Any, mutants: tuple[Mutant, ...] | None = None) -> dict[str, Any]:
    from .court import evaluate

    base = evaluate(inputs, self_attack=False)
    control_codes = emitted_codes(base)
    out: dict[str, dict[str, Any]] = {}
    for m in mutants or catalog():
        try:
            if m.verdict is not None:
                emitted = m.verdict(base, True)
                control = m.verdict(base, False)
            else:
                ev = evaluate(m.build(inputs), self_attack=False)  # type: ignore[misc]
                emitted = emitted_codes(ev)
                control = (
                    control_codes
                    if m.control is None
                    else emitted_codes(evaluate(m.control(inputs), self_attack=False))
                )
            hit, leak = m.expected in emitted, m.expected in control
            out[m.name] = {"expected": m.expected, "killed": hit and not leak, "emitted": hit, "control_emitted": leak}
        except Exception as exc:  # noqa: BLE001 -- a crashing court is a typed survivor
            out[m.name] = {
                "expected": m.expected,
                "killed": False,
                "detail": f"SURVIVED: court raised {type(exc).__name__}: {exc}",
            }
    survivors = sorted(k for k, v in out.items() if not v["killed"])
    return {
        "mutants": dict(sorted(out.items())),
        "total": len(out),
        "killed": len(out) - len(survivors),
        "survivors": survivors,
    }


def dumps(report: dict[str, Any]) -> str:
    return json.dumps(report, indent=2, sort_keys=True)
