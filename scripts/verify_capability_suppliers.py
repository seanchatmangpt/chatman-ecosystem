#!/usr/bin/env python3
"""Verify fleet capability-owner closure against exact pinned repository subjects."""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
SUPPLIERS = ROOT / "catalog" / "capability-suppliers.toml"
REPOSITORIES = ROOT / "catalog" / "repositories.toml"
VERIFY = ROOT / "scripts" / "verify_capabilities.py"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
SCHEMA = "chatman.capability-supplier-registry.v1"
SELF = "repository:chatman-ecosystem"

spec = importlib.util.spec_from_file_location("verify_capabilities", VERIFY)
if spec is None or spec.loader is None:
    raise RuntimeError("REFUSED:CAPABILITY_VERIFIER_UNAVAILABLE")
verify_capabilities = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify_capabilities)


class SupplierError(RuntimeError):
    pass


def load(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def validate() -> dict:
    registry = load(SUPPLIERS)
    if registry.get("schema") != SCHEMA:
        raise SupplierError("REFUSED:CAPABILITY_SUPPLIER_SCHEMA")
    if registry.get("control_plane") != SELF:
        raise SupplierError("REFUSED:CAPABILITY_SUPPLIER_CONTROL_PLANE")

    repositories = load(REPOSITORIES).get("repository", [])
    internal = {
        item["id"]: item
        for item in repositories
        if item.get("url", "").startswith("https://github.com/seanchatmangpt/")
    }
    if SELF not in internal:
        raise SupplierError("REFUSED:CAPABILITY_CONTROL_PLANE_UNREGISTERED")

    items = verify_capabilities.verify(verify_capabilities.load_default(ROOT))
    by_owner: dict[str, set[str]] = {}
    for item in items:
        by_owner.setdefault(item["owner"], set()).add(item["id"])

    rows = registry.get("supplier", [])
    if not isinstance(rows, list) or not rows:
        raise SupplierError("REFUSED:CAPABILITY_SUPPLIER_EMPTY")

    seen: set[str] = set()
    claimed: set[str] = set()
    for row in rows:
        sid = row.get("id")
        if sid in seen:
            raise SupplierError(f"REFUSED:DUPLICATE_CAPABILITY_SUPPLIER:{sid}")
        seen.add(sid)
        if sid not in internal or sid == SELF:
            raise SupplierError(f"REFUSED:UNREGISTERED_CAPABILITY_SUPPLIER:{sid}")
        expected_repo = internal[sid]["url"].removeprefix("https://github.com/")
        if row.get("repository") != expected_repo:
            raise SupplierError(f"REFUSED:CAPABILITY_SUPPLIER_REPOSITORY:{sid}")
        if row.get("mode") != "owner":
            raise SupplierError(f"REFUSED:CAPABILITY_SUPPLIER_MODE:{sid}")
        sha = row.get("subject_sha")
        if not isinstance(sha, str) or not HEX40.fullmatch(sha):
            raise SupplierError(f"REFUSED:CAPABILITY_SUPPLIER_SUBJECT:{sid}")
        discovery = row.get("discovery_ref")
        if not isinstance(discovery, str) or not discovery:
            raise SupplierError(f"REFUSED:CAPABILITY_SUPPLIER_DISCOVERY_REF:{sid}")
        if row.get("standing") != "CANDIDATE":
            raise SupplierError(f"REFUSED:CAPABILITY_SUPPLIER_SELF_STANDING:{sid}")

        declared = row.get("capabilities")
        if not isinstance(declared, list) or not declared:
            raise SupplierError(f"REFUSED:CAPABILITY_OWNER_WITHOUT_CAPABILITIES:{sid}")
        if len(declared) != len(set(declared)):
            raise SupplierError(f"REFUSED:DUPLICATE_SUPPLIER_CAPABILITY:{sid}")

        canonical = by_owner.get(sid, set())
        if set(declared) != canonical:
            missing = sorted(canonical - set(declared))
            extra = sorted(set(declared) - canonical)
            raise SupplierError(
                f"REFUSED:CAPABILITY_SUPPLIER_CLOSURE:{sid}:"
                f"missing={','.join(missing)}:extra={','.join(extra)}"
            )
        for cid in declared:
            if cid in claimed:
                raise SupplierError(f"REFUSED:CAPABILITY_MULTI_OWNER:{cid}")
            claimed.add(cid)

    expected_suppliers = set(internal) - {SELF}
    if seen != expected_suppliers:
        missing = sorted(expected_suppliers - seen)
        extra = sorted(seen - expected_suppliers)
        raise SupplierError(
            f"REFUSED:OWNED_REPOSITORY_CAPABILITY_COVERAGE:"
            f"missing={','.join(missing)}:extra={','.join(extra)}"
        )

    expected_claimed = {item["id"] for item in items if item["owner"] != SELF}
    if claimed != expected_claimed:
        raise SupplierError("REFUSED:FLEET_CAPABILITY_COVERAGE")

    return {
        "schema": SCHEMA,
        "repository_count": len(internal),
        "supplier_count": len(rows),
        "capability_count": len(items),
        "fleet_owned_capability_count": len(claimed),
        "state": "ADMITTED_STRUCTURE",
        "standing": "NONE",
    }


if __name__ == "__main__":
    try:
        result = validate()
        print(
            "CAPABILITY_SUPPLIERS_ALIVE "
            f"repositories={result['repository_count']} "
            f"suppliers={result['supplier_count']} "
            f"capabilities={result['capability_count']} "
            f"fleet_owned={result['fleet_owned_capability_count']} "
            "standing=NONE"
        )
    except (SupplierError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
