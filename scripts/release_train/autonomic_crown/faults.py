"""Crown self-attack (RFC-0005 §8): one injected fault per §39 class variant.

Each fault perturbs the court's own inputs (never a file on disk) and runs the real court.

* R (recoverable): the fault must produce its typed code; the machine repair must change
  the attempt input (``attempt_input_digest``: input bytes + recorded hypothesis) -- a
  retry with an unchanged attempt is ``REFUSED:UNCHANGED_RETRY`` (RFC-0004 §40); the
  re-verification must equal the unfaulted baseline exactly.
* U (unrecoverable): the fault must produce its typed code with the fixed §39 class, no
  repair is attempted, and every gate outside the fault's declared impact is unchanged
  (independent work continues). Authority faults must be REFUSED, never repaired.

Recoverability comes from ``model.RECOVERABILITY`` (the RFC table); a fault may not
reclassify its variant.
"""

from __future__ import annotations

import copy
import json
from dataclasses import dataclass, replace
from typing import Any, Callable

from . import gates
from .locate import FailingTransport, ResolverWithOverlay
from .model import CODES, RECOVERABILITY, digest, sha256_bytes

Inject = Callable[[Any], Any]


@dataclass(frozen=True)
class Fault:
    name: str
    failure_class: str
    variant: str
    code: str
    inject: Inject
    repair: Inject | None
    impacted: tuple[str, ...] = ()

    @property
    def recoverability(self) -> str:
        return RECOVERABILITY[(self.failure_class, self.variant)]


def attempt_input_digest(inputs: Any) -> str:
    return digest(
        {
            "gates": inputs.gates_doc,
            "edges": inputs.edges_doc,
            "locators": inputs.locators,
            "overrides": {k: sha256_bytes(v) for k, v in inputs.overrides.items()},
            "evaluated_heads": inputs.evaluated_heads,
            "source": inputs.source.name,
            "hypothesis": inputs.hypothesis,
        }
    )


def _resolved(inputs: Any, name: str) -> tuple[str, bytes]:
    from .court import _read

    receipt_data, _, _ = _read(inputs, "crown_receipt", None)
    crown_sha = json.loads(receipt_data)["crown_sha"] if receipt_data else None
    data, problem, locator = _read(inputs, name, crown_sha)
    if problem or data is None:
        raise RuntimeError(f"self-attack needs a resolvable {name}: {problem}")
    return locator, data


def _overlay(inputs: Any, name: str, fn: Callable[[bytes, int], bytes], label: str) -> Any:
    locator, data = _resolved(inputs, name)
    source = ResolverWithOverlay(inputs.source, {locator: lambda n: fn(data, n)}, label)
    return replace(inputs, source=source)


def _override(inputs: Any, name: str, fn: Callable[[Any], None]) -> Any:
    """A new input document (a fresh observation, a supplied receipt): the durable locator is
    immutable, so a changed document arrives as a file input, never as rewritten git bytes."""
    _, data = _resolved(inputs, name)
    return replace(inputs, overrides={**inputs.overrides, name: _json_edit(data, fn)})


def _edit_edge(inputs: Any, eid: str, fn: Callable[[dict[str, Any]], None]) -> Any:
    doc = copy.deepcopy(inputs.edges_doc)
    for edge in doc["edges"]:
        if edge["id"] == eid:
            fn(edge)
    return replace(inputs, edges_doc=doc)


def _json_edit(data: bytes, fn: Callable[[Any], None]) -> bytes:
    doc = json.loads(data)
    fn(doc)
    return json.dumps(doc).encode("utf-8")


def _set_head(repo: str, sha: str) -> Callable[[Any], None]:
    def edit(doc: Any) -> None:
        for block in (doc.get("repos") or {}, (doc.get("private_repos") or {}).get("repos") or {}):
            if repo in block:
                block[repo]["head_sha"] = sha

    return edit


def _forge_chain(doc: Any) -> None:
    doc["entries"][1]["previous_receipt_digest"] = "sha256:" + "0" * 64


def _tamper_receipt(doc: Any) -> None:
    doc["standing"] = "BLOCKED"  # digest not recomputed


def _stale_digest(edge: dict[str, Any]) -> None:
    edge["evidence"]["sha256"] = "0" * 64


def _unsupported_kind(edge: dict[str, Any]) -> None:
    edge["evidence"]["kind"] = "attestation"


def _self_grant(edge: dict[str, Any]) -> None:
    edge["authority_gate"] = {"grantor": "root-crown", "grant": "tag and publish the release"}


def _cycle(edge: dict[str, Any]) -> None:
    edge["to"] = "main"


def faults(original: Any) -> tuple[Fault, ...]:
    """The catalog, bound to the unfaulted inputs (the alternate transport is the original one)."""
    root = "seanchatmangpt/chatman-ecosystem"
    new_head = "9" * 40

    def repair_transport(i: Any) -> Any:
        return replace(
            i, source=original.source, hypothesis="transport down; re-observe through the git object database"
        )

    def inject_transport(i: Any) -> Any:
        return replace(i, source=FailingTransport())

    def repair_stale(i: Any) -> Any:
        doc = copy.deepcopy(i.edges_doc)
        for edge in doc["edges"]:
            if edge["id"] == "E-VER-01":
                edge["evidence"]["sha256"] = sha256_bytes(i.source.resolve(edge["evidence"]["locator"]))
        return replace(i, edges_doc=doc, hypothesis="stale digest; re-observe and recompute")

    def repair_subject(i: Any) -> Any:
        _, data = _resolved(i, "crown_receipt")
        doc = copy.deepcopy(i.edges_doc)
        doc["crown_subject"] = json.loads(data)["crown_sha"]
        return replace(i, edges_doc=doc, hypothesis="crown-sha split; re-bind to the current crown subject")

    def repair_new_head(i: Any) -> Any:
        return replace(
            i, evaluated_heads={root: new_head}, hypothesis="local NEW_HEAD; re-evaluate against the new head"
        )

    return (
        Fault("transport", "TRANSPORT_FAILURE", "any", "TRANSPORT_UNAVAILABLE", inject_transport, repair_transport),
        Fault(
            "build",
            "BUILD_FAILURE",
            "any",
            "GATE_COVERAGE_GAP",
            lambda i: replace(
                i,
                gates_doc={
                    **i.gates_doc,
                    "gates": [dict(g, threshold="2/3") if g["id"] == "U-18" else g for g in i.gates_doc["gates"]],
                },
            ),
            lambda i: replace(
                i, gates_doc=gates.project(i.rfc5_text), hypothesis="gates drifted; regenerate from RFC-0005 §7"
            ),
        ),
        Fault(
            "verification-transient",
            "VERIFICATION_FAILURE",
            "transient",
            "RECEIPT_UNVERIFIED",
            lambda i: _overlay(i, "crown_receipt", lambda d, n: d[: len(d) // 2] if n == 0 else d, "partial-read-once"),
            lambda i: replace(i, hypothesis="partial read; re-verify once"),
        ),
        Fault(
            "verification-deterministic",
            "VERIFICATION_FAILURE",
            "deterministic",
            "RECEIPT_UNVERIFIED",
            lambda i: _override(i, "crown_receipt", _tamper_receipt),
            None,
        ),
        Fault(
            "authority",
            "AUTHORITY_FAILURE",
            "any",
            "AUTHORITY_AMPLIFICATION",
            lambda i: _edit_edge(i, "E-DEC-01", _self_grant),
            None,
            ("U-08",),
        ),
        Fault(
            "evidence-stale",
            "EVIDENCE_FAILURE",
            "stale",
            "EVIDENCE_DIGEST_MISMATCH",
            lambda i: _edit_edge(i, "E-VER-01", _stale_digest),
            repair_stale,
        ),
        Fault(
            "evidence-forged-chain",
            "EVIDENCE_FAILURE",
            "forged chain",
            "CHAIN_FORGED",
            lambda i: _override(i, "chain", _forge_chain),
            None,
            ("U-18",),
        ),
        Fault(
            "dependency-local-new-head",
            "DEPENDENCY_FAILURE",
            "local NEW_HEAD",
            "NEW_HEAD",
            lambda i: _override(i, "observations", _set_head(root, new_head)),
            repair_new_head,
        ),
        Fault(
            "dependency-remote-producer",
            "DEPENDENCY_FAILURE",
            "remote producer",
            "WAITING_PRODUCER",
            lambda i: _override(i, "observations", _set_head("seanchatmangpt/xaas", new_head)),
            None,
        ),
        Fault(
            "capability-gap",
            "CAPABILITY_GAP",
            "any",
            "UNSUPPORTED_EVIDENCE_KIND",
            lambda i: _edit_edge(i, "E-CON-01", _unsupported_kind),
            None,
            ("U-04",),
        ),
        Fault(
            "model-counterexample",
            "MODEL_COUNTEREXAMPLE",
            "any",
            "MODEL_COUNTEREXAMPLE",
            lambda i: _edit_edge(i, "E-RPL-01", _cycle),
            None,
        ),
        Fault(
            "subject-crown-sha-split",
            "SUBJECT_FAILURE",
            "crown-sha split",
            "SUBJECT_SPLIT",
            lambda i: replace(i, edges_doc={**i.edges_doc, "crown_subject": "8" * 40}),
            repair_subject,
        ),
    )


def run(inputs: Any, catalog: tuple[Fault, ...] | None = None) -> dict[str, Any]:
    from .court import evaluate

    base = evaluate(inputs, self_attack=False)
    baseline = base.fingerprint()
    out: dict[str, dict[str, Any]] = {}
    for fault in catalog or faults(inputs):
        row: dict[str, Any] = {
            "class": fault.failure_class,
            "variant": fault.variant,
            "recoverability": fault.recoverability,
        }
        faulted_inputs = fault.inject(inputs)
        faulted = evaluate(faulted_inputs, self_attack=False)
        typed = [f for f in faulted.findings if f.code == fault.code]
        row["code"] = fault.code
        row["typed"] = bool(typed) and CODES[fault.code][0] == fault.failure_class
        row["attempt_input_digest"] = attempt_input_digest(faulted_inputs)
        if fault.recoverability == "R":
            if fault.repair is None:
                row.update(repaired=False, ok=False, detail="R fault without a machine repair")
            else:
                repaired_inputs = fault.repair(faulted_inputs)
                retry = attempt_input_digest(repaired_inputs)
                row["repair_input_digest"] = retry
                row["hypothesis"] = repaired_inputs.hypothesis
                if retry == row["attempt_input_digest"]:
                    row.update(repaired=False, ok=False, detail="REFUSED:UNCHANGED_RETRY")
                else:
                    after = evaluate(repaired_inputs, self_attack=False)
                    same = after.fingerprint() == baseline
                    row.update(
                        repaired=same,
                        ok=row["typed"] and same,
                        detail="re-verified equal to baseline" if same else "re-verification differs from baseline",
                    )
        else:
            exclude = ("U-05", "U-06", "U-07", "U-12") + fault.impacted
            unchanged = {k: v for k, v in faulted.fingerprint(exclude)["gates"].items()} == {
                k: v for k, v in base.fingerprint(exclude)["gates"].items()
            }
            refused_ok = fault.failure_class != "AUTHORITY_FAILURE" or (
                faulted.authority == "REFUSED" and all(f.severity == "REFUSED" for f in typed)
            )
            row.update(
                repaired=False,
                independent_unchanged=unchanged,
                ok=row["typed"] and unchanged and refused_ok,
                detail="typed; independent gates unchanged" if unchanged else "independent gates changed",
            )
        out[fault.name] = row
    return {"baseline_digest": digest(baseline), "faults": out}
