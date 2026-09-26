#!/usr/bin/env python3
"""Fail-closed CS2 canonical producer/consumer contract verifier."""
from __future__ import annotations
import argparse, hashlib, json, re
from pathlib import Path

REQUIRED = {
    "RFC-CS2-001", "CS2-CHICAGO", "seanchatmangpt/chatman-ecosystem",
    "CS2-WRK-002", "CS2-WRK-003", "CS2-WRK-012",
    "requiresExactSubject true", "requiresProvenance true",
    "requiresReceiptReplay true",
}
CONSUMERS = {
    "ggen-marketplace": "CS2-WRK-003",
    "ash-a2a": "CS2-WRK-012",
}

def verify(ttl: Path, subject_sha: str) -> dict:
    text = ttl.read_text(encoding="utf-8")
    missing = sorted(x for x in REQUIRED if x not in text)
    sha_ok = bool(re.fullmatch(r"[0-9a-f]{40}", subject_sha))
    digest = hashlib.sha256(text.encode()).hexdigest()
    standing = "CANDIDATE" if not missing and sha_ok else "REFUSED"
    return {
        "schema": "CS2_CANONICAL_CONTRACT_V1",
        "subject": "RFC-CS2-001",
        "producer": "seanchatmangpt/chatman-ecosystem",
        "producer_sha": subject_sha,
        "contract_sha256": digest,
        "authority_ceiling": "CONSTRUCT",
        "consumers": CONSUMERS,
        "missing": missing,
        "standing": standing,
        "note": "CANDIDATE is construction evidence, not ALIVE standing.",
    }

def main() -> int:
    p=argparse.ArgumentParser()
    p.add_argument("--ttl", default="cs2/canonical.ttl")
    p.add_argument("--subject-sha", required=True)
    p.add_argument("--out")
    a=p.parse_args()
    result=verify(Path(a.ttl), a.subject_sha)
    encoded=json.dumps(result, sort_keys=True, indent=2)+"\n"
    if a.out: Path(a.out).write_text(encoded, encoding="utf-8")
    print(encoded, end="")
    return 0 if result["standing"] == "CANDIDATE" else 2

if __name__ == "__main__":
    raise SystemExit(main())
