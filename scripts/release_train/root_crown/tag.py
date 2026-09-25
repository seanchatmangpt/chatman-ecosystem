"""Tag legality (RFC-0004 §45): tagSHA = crownSHA, tag is the final operation.

LEGAL only when the receipt digest recomputes, the crown standing is ALIVE, the
checked-out head equals the receipt's crown_sha, and the tag is absent or already
at crown_sha (idempotent). The decision is data; the court never tags.
"""

from __future__ import annotations

from typing import Any

from .crown import verify_receipt


def tag_decision(receipt: dict[str, Any], head_sha: str, existing_tag_sha: str | None, tag: str) -> dict[str, Any]:
    reasons: list[str] = []
    crown_sha = receipt.get("crown_sha") if isinstance(receipt, dict) else None
    if not verify_receipt(receipt):
        reasons.append("TAG_ILLEGAL:RECEIPT_UNVERIFIED")
    if receipt.get("standing") != "ALIVE":
        open_terms = sorted(t for t, v in receipt.get("terms", {}).items() if v.get("state") != "PASS")
        reasons.append(f"TAG_ILLEGAL:CROWN_NOT_ALIVE:{receipt.get('standing')}:terms={','.join(open_terms)}")
    if head_sha != crown_sha:
        reasons.append(f"TAG_ILLEGAL:SHA_MISMATCH:head={head_sha}:crown={crown_sha}")
    if existing_tag_sha is not None and existing_tag_sha != crown_sha:
        reasons.append(f"TAG_ILLEGAL:TAG_EXISTS_ELSEWHERE:{tag}={existing_tag_sha}")
    return {
        "tag": tag,
        "decision": "ILLEGAL" if reasons else "LEGAL",
        "crown_sha": crown_sha,
        "head_sha": head_sha,
        "existing_tag_sha": existing_tag_sha,
        "receipt_digest": receipt.get("receipt_digest") if isinstance(receipt, dict) else None,
        "reasons": reasons,
        "remaining": [
            {k: item.get(k) for k in ("id", "term", "state", "code", "failure_class", "broken_term", "detail")}
            for item in receipt.get("remaining", [])
        ],
        "authority": "NONE (decision only; tagging requires the release-crown environment approval)",
    }
