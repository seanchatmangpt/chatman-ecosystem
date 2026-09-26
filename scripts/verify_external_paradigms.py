#!/usr/bin/env python3
"""Fail-closed validation for external paradigm suppliers.

This court validates repository-local supplier metadata only. It does not fetch
upstream repositories and does not grant standing to any imported pattern.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SCHEMA = "chatman.external-paradigms.v1"
MAP_SCHEMA = "chatman.external-pattern-map.v1"
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ALLOWED = {"VENDOR", "WRAP", "REPLACE", "NOVEL_GAP"}
ALLOWED_AUTH = {
    "NONE",
    "OBSERVE",
    "SELECT",
    "CONSTRUCT",
    "OBSERVE_SELECT",
    "SELECT_CONSTRUCT_ONLY",
}


class ParadigmRefusal(ValueError):
    """Typed local refusal for malformed supplier metadata."""


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ParadigmRefusal(f"REFUSED:MISSING:{path}") from exc
    except json.JSONDecodeError as exc:
        raise ParadigmRefusal(f"REFUSED:INVALID_JSON:{path}:{exc}") from exc


def validate_registry(registry_path: Path, root: Path) -> dict:
    registry = _load(registry_path)
    if registry.get("schema") != SCHEMA:
        raise ParadigmRefusal("REFUSED:REGISTRY_SCHEMA")

    policy = registry.get("policy") or {}
    if policy.get("mutable_refs_forbidden") is not True:
        raise ParadigmRefusal("REFUSED:MUTABLE_REF_POLICY_DISABLED")
    if set(policy.get("allowed_dispositions") or []) != ALLOWED:
        raise ParadigmRefusal("REFUSED:DISPOSITION_POLICY_DRIFT")

    suppliers = registry.get("suppliers")
    if not isinstance(suppliers, list) or not suppliers:
        raise ParadigmRefusal("REFUSED:NO_SUPPLIERS")

    seen: set[str] = set()
    counts = {key: 0 for key in ALLOWED}

    for supplier in suppliers:
        sid = supplier.get("id")
        if not isinstance(sid, str) or not sid or sid in seen:
            raise ParadigmRefusal(f"REFUSED:SUPPLIER_ID:{sid!r}")
        seen.add(sid)

        pin = supplier.get("pin") or {}
        sha = pin.get("sha")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise ParadigmRefusal(f"REFUSED:MUTABLE_OR_INVALID_SHA:{sid}:{sha!r}")

        source_url = supplier.get("source_url")
        if not isinstance(source_url, str) or not source_url.startswith("https://github.com/"):
            raise ParadigmRefusal(f"REFUSED:SOURCE_URL:{sid}")

        if supplier.get("standing") != "CANDIDATE":
            raise ParadigmRefusal(f"REFUSED:SUPPLIER_SELF_STANDING:{sid}")

        map_rel = supplier.get("pattern_map")
        if not isinstance(map_rel, str) or not map_rel:
            raise ParadigmRefusal(f"REFUSED:PATTERN_MAP:{sid}")

        pattern_map = _load(root / map_rel)
        if pattern_map.get("schema") != MAP_SCHEMA:
            raise ParadigmRefusal(f"REFUSED:PATTERN_MAP_SCHEMA:{sid}")
        if pattern_map.get("supplier") != sid:
            raise ParadigmRefusal(f"REFUSED:PATTERN_MAP_SUPPLIER:{sid}")
        if pattern_map.get("supplier_sha") != sha:
            raise ParadigmRefusal(f"REFUSED:PATTERN_MAP_SHA_DRIFT:{sid}")

        entries = pattern_map.get("entries")
        if not isinstance(entries, list) or not entries:
            raise ParadigmRefusal(f"REFUSED:NO_PATTERN_ENTRIES:{sid}")

        entry_ids: set[str] = set()
        for entry in entries:
            eid = entry.get("id")
            if not isinstance(eid, str) or not eid or eid in entry_ids:
                raise ParadigmRefusal(f"REFUSED:PATTERN_ID:{sid}:{eid!r}")
            entry_ids.add(eid)

            disposition = entry.get("disposition")
            if disposition not in ALLOWED:
                raise ParadigmRefusal(
                    f"REFUSED:UNKNOWN_DISPOSITION:{sid}:{eid}:{disposition!r}"
                )
            counts[disposition] += 1

            source_paths = entry.get("source_paths")
            if not isinstance(source_paths, list) or not source_paths:
                raise ParadigmRefusal(f"REFUSED:NO_SOURCE_PATHS:{sid}:{eid}")

            if entry.get("authority") not in ALLOWED_AUTH:
                raise ParadigmRefusal(f"REFUSED:AUTHORITY_CLASS:{sid}:{eid}")

            if disposition != "NOVEL_GAP" and not entry.get("chatman_target"):
                raise ParadigmRefusal(f"REFUSED:NO_TARGET:{sid}:{eid}")

            if disposition == "NOVEL_GAP":
                required = entry.get("required_semantics")
                searched = entry.get("searched_prior_art")
                failures = entry.get("candidate_failures")
                falsifier = entry.get("falsifier")
                if not isinstance(required, list) or not required:
                    raise ParadigmRefusal(
                        f"REFUSED:NOVELTY_REQUIRED_SEMANTICS_MISSING:{sid}:{eid}"
                    )
                if not isinstance(searched, list) or not searched:
                    raise ParadigmRefusal(
                        f"REFUSED:NOVELTY_PRIOR_ART_SEARCH_MISSING:{sid}:{eid}"
                    )
                if not isinstance(failures, list) or not failures:
                    raise ParadigmRefusal(
                        f"REFUSED:NOVELTY_WITHOUT_PRIOR_ART_FAILURES:{sid}:{eid}"
                    )
                failed_ids = {
                    item.get("id")
                    for item in failures
                    if isinstance(item, dict)
                }
                if not set(searched).issubset(failed_ids):
                    raise ParadigmRefusal(
                        f"REFUSED:NOVELTY_SEARCH_NOT_DISCHARGED:{sid}:{eid}"
                    )
                for failure in failures:
                    if (
                        not isinstance(failure, dict)
                        or not isinstance(failure.get("missing_semantics"), list)
                        or not failure.get("missing_semantics")
                    ):
                        raise ParadigmRefusal(
                            f"REFUSED:NOVELTY_FAILURE_UNTYPED:{sid}:{eid}"
                        )
                if not isinstance(falsifier, str) or not falsifier.strip():
                    raise ParadigmRefusal(
                        f"REFUSED:NOVELTY_WITHOUT_FALSIFIER:{sid}:{eid}"
                    )

    return {
        "schema": SCHEMA,
        "supplier_count": len(suppliers),
        "pattern_count": sum(counts.values()),
        "dispositions": counts,
        "state": "OBSERVED",
        "standing": "NONE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--registry",
        default="upstream/paradigms.json",
        help="registry path relative to repository root",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        result = validate_registry(root / args.registry, root)
    except ParadigmRefusal as exc:
        if args.json:
            print(json.dumps({"state": "REFUSED", "reason": str(exc)}, sort_keys=True))
        else:
            print(str(exc))
        return 2

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "external-paradigms: OK "
            f"suppliers={result['supplier_count']} patterns={result['pattern_count']} "
            "standing=NONE"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
