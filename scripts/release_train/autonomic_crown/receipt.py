"""Autonomic crown receipt (schema ``https://chatman.dev/autonomic-crown/receipt/v1``).

Deterministic: no wall clock (``evaluated_at`` is the observation time of the consumed
observations); ``receipt_digest`` is the canonical digest of every other field. The
receipt carries all three RFC-0005 §4 standings, one result per gate U-01..U-18, the §8
self-attack rows, the mutant summary and every typed finding.
"""

from __future__ import annotations

from typing import Any

from .court import Evaluation
from .model import SCHEMA_RECEIPT, digest

THEOREM = (
    "U = SelfStart AND SelfObserve AND SelfAdmit AND SelfDecompose AND SelfConstruct AND SelfActuate AND "
    "SelfVerify AND SelfRepair AND SelfReplay AND SelfContinue AND NoHiddenHuman AND NoRepeatedLLM"
)


def exit_code(ev: Evaluation) -> int:
    if ev.refused:
        return 2
    if ev.autonomy == "AUTONOMIC" and ev.execution["state"] == "ALIVE":
        return 0
    return 3


def build(
    ev: Evaluation, release: str, edges_digest: str, gates_digest: str, governance_digest: str | None
) -> dict[str, Any]:
    receipt = ev.crown_receipt or {}
    blocked = sorted(g.id for g in ev.gates if g.state != "PASS")
    body: dict[str, Any] = {
        "schema": SCHEMA_RECEIPT,
        "release": release,
        "scope": "POST_TAG (RFC-0005 §2: v26.9.25 is not evaluated against U; this is the first U measurement)",
        "authority": "NONE",
        "theorem": "RELEASE = C AND A AND R AND X AND F AND M AND U",
        "term_u": THEOREM,
        "crown_subject": receipt.get("crown_sha"),
        "crown_receipt_digest": receipt.get("receipt_digest"),
        "evaluated_at": None,
        "inputs": ev.input_digests,
        "input_documents": {"edges.json": edges_digest, "gates.json": gates_digest, "governance": governance_digest},
        "standings": {
            "execution": ev.execution,
            "autonomy": ev.autonomy,
            "authority": {"state": ev.authority, "detail": ev.authority_detail},
        },
        "gates": {g.id: g.as_dict() for g in ev.gates},
        "blocked_gates": blocked,
        "passed_gates": sorted(g.id for g in ev.gates if g.state == "PASS"),
        "findings": [f.as_dict() for f in ev.findings],
        "reports": ev.reports,
        "exit": exit_code(ev),
    }
    return body


def seal(body: dict[str, Any], evaluated_at: str | None) -> dict[str, Any]:
    out = dict(body)
    out["evaluated_at"] = evaluated_at
    out["receipt_digest"] = digest({k: v for k, v in out.items() if k != "receipt_digest"})
    return out


def verify(receipt: dict[str, Any]) -> bool:
    return (
        isinstance(receipt, dict)
        and receipt.get("schema") == SCHEMA_RECEIPT
        and receipt.get("receipt_digest") == digest({k: v for k, v in receipt.items() if k != "receipt_digest"})
    )
