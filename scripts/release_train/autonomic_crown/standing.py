"""The three orthogonal standings (RFC-0005 §4) and their legality.

execution  -- from the verified crown receipt (never from the gates).
autonomy   -- AUTONOMIC only when every gate U-01..U-18 is PASS *and* execution is
              ALIVE; all gates PASS without ALIVE is ``REFUSED:AUTONOMY_WITHOUT_ALIVE``.
authority  -- AUTHORIZED only when observed governance shows the operator-only gates
              configured (RFC-0005 §13); otherwise WAITING_EXTERNAL_AUTHORITY; an
              accepted amplification is REFUSED(AUTHORITY_FAILURE).
"""

from __future__ import annotations

from typing import Any, Iterable

from .model import AUTHORITY, AUTONOMY, EXECUTION, GATE_IDS, Finding, GateResult


def execution_of(receipt: dict[str, Any] | None, findings: Iterable[Finding]) -> dict[str, str]:
    codes = {f.code for f in findings}
    if "RECEIPT_UNVERIFIED" in codes:
        return {"state": "REFUSED", "type": "VERIFICATION_FAILURE"}
    if "CHAIN_FORGED" in codes:
        return {"state": "REFUSED", "type": "EVIDENCE_FAILURE"}
    if receipt is None:
        if "TRANSPORT_UNAVAILABLE" in codes:
            return {"state": "BLOCKED", "type": "TRANSPORT_FAILURE"}
        return {"state": "UNKNOWN", "type": "EVIDENCE_FAILURE"}
    state = receipt.get("standing")
    if state == "ALIVE":
        return {"state": "ALIVE"}
    if state in EXECUTION:
        return {"state": state, "type": "SUBJECT_FAILURE"}
    return {"state": "UNKNOWN", "type": "EVIDENCE_FAILURE"}


def autonomy_of(gates: Iterable[GateResult], execution: str) -> tuple[str, list[Finding]]:
    by_id = {g.id: g for g in gates}
    all_pass = all(by_id.get(gid) is not None and by_id[gid].state == "PASS" for gid in GATE_IDS)
    if all_pass and execution != "ALIVE":
        return "NOT_AUTONOMIC", [
            Finding("AUTONOMY_WITHOUT_ALIVE", "autonomy", f"all gates PASS, execution={execution}")
        ]
    return ("AUTONOMIC" if all_pass else "NOT_AUTONOMIC"), []


def authority_of(governance: dict[str, Any] | None, findings: Iterable[Finding]) -> tuple[str, str]:
    if any(f.code == "AUTHORITY_AMPLIFICATION" for f in findings):
        return "REFUSED", "authority amplification accepted into the inventory"
    if not governance:
        return "WAITING_EXTERNAL_AUTHORITY", "governance unobserved; operator-only gates (RFC-0005 §13) not witnessed"
    gaps = governance_gaps(governance)
    if gaps:
        return "WAITING_EXTERNAL_AUTHORITY", "; ".join(gaps)
    return "AUTHORIZED", "main protected; release-crown has required reviewers on protected branches"


def governance_gaps(governance: dict[str, Any]) -> list[str]:
    gaps = []
    main = governance.get("main") or {}
    env = (governance.get("environments") or {}).get("release-crown") or {}
    if main.get("protected") is not True:
        gaps.append("main unprotected")
    if not isinstance(env.get("reviewers"), int) or env["reviewers"] < 1:
        gaps.append("release-crown has no required reviewer")
    if env.get("protected_branches") is not True:
        gaps.append("release-crown deployment_branch_policy.protected_branches is not true")
    return gaps


def legality(execution: str, autonomy: str, authority: str, do_receipts_without_authority: int = 0) -> list[Finding]:
    """RFC-0005 §4 legal-combination table; an illegal triple is REFUSED(VERIFICATION_FAILURE)."""
    out = []
    if execution not in EXECUTION or autonomy not in AUTONOMY or authority not in AUTHORITY:
        out.append(Finding("ILLEGAL_STANDING_COMBINATION", "standings", f"{execution}/{autonomy}/{authority}"))
    if autonomy == "AUTONOMIC" and execution != "ALIVE":
        out.append(Finding("AUTONOMY_WITHOUT_ALIVE", "standings", f"AUTONOMIC with execution={execution}"))
    if authority == "REFUSED" and do_receipts_without_authority:
        out.append(Finding("ILLEGAL_STANDING_COMBINATION", "standings", "DO receipt under REFUSED authority"))
    return out
