#!/usr/bin/env python3
"""Fail-closed evidence law for v26.9.1 component standing."""

from __future__ import annotations

import argparse
import json
import re
import tomllib
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
RECEIPT_RE = re.compile(r"^[A-Za-z0-9_.-]+:[^\s]+$")


class EvidenceRefusal(ValueError):
    pass


def verify(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)

    checked = 0
    alive = 0
    blocked = 0
    for component in data.get("components", []):
        component_id = component.get("id", "<unknown>")
        standing = component.get("standing")
        sha = component.get("sha")
        receipt = component.get("execution_receipt")
        executed_sha = component.get("executed_sha")
        blocker = component.get("blocker")

        checked += 1
        if standing == "ALIVE":
            alive += 1
            if not isinstance(receipt, str) or not RECEIPT_RE.fullmatch(receipt):
                raise EvidenceRefusal(f"REFUSED:ALIVE_WITHOUT_EXECUTION_RECEIPT:{component_id}")
            if not isinstance(executed_sha, str) or not SHA_RE.fullmatch(executed_sha):
                raise EvidenceRefusal(f"REFUSED:ALIVE_WITHOUT_EXECUTED_SHA:{component_id}")
            if executed_sha != sha:
                raise EvidenceRefusal(
                    f"REFUSED:ALIVE_SUBJECT_IDENTITY_MISMATCH:{component_id}:admitted={sha}:executed={executed_sha}"
                )
            if blocker:
                raise EvidenceRefusal(f"REFUSED:ALIVE_WITH_BLOCKER:{component_id}")
        elif standing == "BLOCKED":
            blocked += 1
            if not isinstance(blocker, str) or not blocker.strip():
                raise EvidenceRefusal(f"REFUSED:BLOCKED_WITHOUT_REASON:{component_id}")
            if receipt or executed_sha:
                raise EvidenceRefusal(f"REFUSED:BLOCKED_WITH_EXECUTION_STANDING:{component_id}")
        elif receipt or executed_sha:
            if not (isinstance(receipt, str) and RECEIPT_RE.fullmatch(receipt)):
                raise EvidenceRefusal(f"REFUSED:MALFORMED_EXECUTION_RECEIPT:{component_id}")
            if not isinstance(executed_sha, str) or executed_sha != sha:
                raise EvidenceRefusal(f"REFUSED:EXECUTION_SUBJECT_IDENTITY_MISMATCH:{component_id}")

    return {
        "schema": "chatman-ecosystem.standing-evidence/1",
        "components_checked": checked,
        "alive_components": alive,
        "blocked_components": blocked,
        "claim_ceiling": "EXACT_SUBJECT_STANDING_EVIDENCE_ONLY_NO_TRANSITIVE_AUTHORITY",
        "do_authority": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--manifest",
        type=Path,
        default=Path("release/v26.9.1/manifest.toml"),
    )
    args = parser.parse_args()
    try:
        receipt = verify(args.manifest)
    except EvidenceRefusal as exc:
        print(str(exc))
        return 4
    print(json.dumps(receipt, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
