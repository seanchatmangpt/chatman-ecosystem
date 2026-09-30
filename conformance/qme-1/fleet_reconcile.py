#!/usr/bin/env python3
"""Fail-closed validator for the v26.9.30 fleet evidence snapshot."""
from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

HEX40 = re.compile(r"^[0-9a-f]{40}$")
SCHEMA = "chatman.fleet-reconcile/1"
ROOT = "seanchatmangpt/chatman-ecosystem"
REQUIRED_SETS = {
    "qme_reference_core",
    "economic_effect_chain",
    "semantic_diataxis",
    "planning_runtime",
    "semantic_manufacture",
    "evidence_observation",
}


class Refusal(Exception):
    def __init__(self, code: str, detail: str):
        super().__init__(detail)
        self.code = code
        self.detail = detail


def refuse(code: str, detail: str):
    raise Refusal(code, detail)


def _canonical(value) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    ).encode()


def check(doc: dict) -> dict:
    if doc.get("schema") != SCHEMA:
        refuse("SCHEMA_INVALID", "unexpected schema")
    if doc.get("authority") != "NONE" or doc.get("consequence") != "EVIDENCE_ONLY":
        refuse("FLEET_AUTHORITY_PROMOTION", "fleet census is evidence-only")

    scan = doc.get("scan") or {}
    repos = doc.get("repositories")
    if not isinstance(repos, list) or not repos:
        refuse("REPOSITORIES_MISSING", "repositories must be non-empty")
    if scan.get("unique_repositories") != len(repos):
        refuse("REPOSITORY_COUNT_DRIFT", "declared unique count differs from snapshot")

    subject = doc.get("canonical_subject") or {}
    if (
        subject.get("repository") != ROOT
        or not HEX40.fullmatch(str(subject.get("base_sha", "")))
    ):
        refuse(
            "ROOT_OWNERSHIP_INVALID",
            "canonical subject must be exact chatman-ecosystem base",
        )

    names = set()
    by_name = {}
    for row in repos:
        name = row.get("repository")
        if not isinstance(name, str) or "/" not in name:
            refuse("REPOSITORY_INVALID", str(name))
        if name in names:
            refuse("DUPLICATE_REPOSITORY", name)
        names.add(name)
        by_name[name] = row
        if not HEX40.fullmatch(str(row.get("head_sha", ""))):
            refuse("INVALID_SUBJECT", name)
        if not row.get("branch"):
            refuse("BRANCH_MISSING", name)
        if row.get("evidence_kind") != "OBSERVED":
            refuse("OBSERVATION_PROMOTION", name)
        if row.get("projection_authority_effect") != "NONE":
            refuse("FLEET_AUTHORITY_PROMOTION", name)

    if ROOT not in names:
        refuse("ROOT_OWNERSHIP_INVALID", "canonical repository absent from fleet snapshot")
    if by_name[ROOT]["head_sha"] != subject["base_sha"]:
        refuse("ROOT_SUBJECT_DRIFT", "snapshot root differs from canonical base")

    sets = doc.get("capability_sets")
    if not isinstance(sets, list):
        refuse("CAPABILITY_SETS_MISSING", "capability_sets must be a list")
    ids = [item.get("id") for item in sets]
    if len(ids) != len(set(ids)):
        refuse("DUPLICATE_CAPABILITY_SET", "capability set ids must be unique")
    missing_sets = REQUIRED_SETS - set(ids)
    if missing_sets:
        refuse("CAPABILITY_SET_INCOMPLETE", ",".join(sorted(missing_sets)))

    for cap in sets:
        if cap.get("authority_effect") != "NONE":
            refuse("FLEET_AUTHORITY_PROMOTION", str(cap.get("id")))
        members = cap.get("members")
        if (
            not isinstance(members, list)
            or not members
            or len(members) != len(set(members))
        ):
            refuse("CAPABILITY_SET_INCOMPLETE", str(cap.get("id")))
        missing = sorted(set(members) - names)
        if missing:
            refuse(
                "CAPABILITY_SET_INCOMPLETE",
                f"{cap.get('id')}:{','.join(missing)}",
            )

    digest = hashlib.sha256(_canonical(doc)).hexdigest()
    return {
        "schema": "chatman.fleet-reconcile.receipt/1",
        "subject": f"{ROOT}@{subject['base_sha']}",
        "snapshot_digest": f"sha256:{digest}",
        "repository_count": len(repos),
        "capability_set_count": len(sets),
        "authority": "NONE",
        "consequence": "EVIDENCE_ONLY",
        "standing": "PARTIAL_ALIVE",
    }


def main(argv=None) -> int:
    argv = argv or sys.argv
    if len(argv) != 2:
        print("usage: fleet_reconcile.py SNAPSHOT.json", file=sys.stderr)
        return 2
    try:
        doc = json.loads(Path(argv[1]).read_text())
        print(json.dumps(check(doc), sort_keys=True, separators=(",", ":")))
        return 0
    except Refusal as exc:
        print(f"REFUSED:{exc.code}:{exc.detail}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
