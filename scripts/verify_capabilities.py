#!/usr/bin/env python3
"""Fail-closed verifier and deterministic projection for capability catalog."""
from __future__ import annotations

import argparse
import pathlib
import sys
import tomllib

ALLOWED_CLASSES = {"OBSERVE", "SELECT", "CONSTRUCT", "DO"}
ALLOWED_STANDING = {
    "UNKNOWN", "OBSERVED", "CANDIDATE", "PARTIAL_ALIVE", "ALIVE",
    "BLOCKED", "UNSUPPORTED", "REJECTED", "SUPERSEDED",
}
ALLOWED_AUTHORITY = {
    "observe", "classify", "draft", "persist_control_plane",
    "open_draft_pull_request", "modify_external_object", "communicate",
    "merge", "delete", "spend", "approve", "release",
}
ALLOWED_INTERFACES = {"cli", "api", "mcp", "a2a"}
MUTATING_AUTHORITIES = {
    "modify_external_object", "communicate", "merge", "delete",
    "spend", "approve", "release",
}


class CapabilityError(RuntimeError):
    pass


def load(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def verify(catalog: dict) -> list[dict]:
    if catalog.get("schema") != "chatman.capability-catalog.v1":
        raise CapabilityError("REFUSED:CAPABILITY_SCHEMA")
    if catalog.get("subject") != "SELF":
        raise CapabilityError("REFUSED:CAPABILITY_SUBJECT")
    items = catalog.get("capability", [])
    if not items:
        raise CapabilityError("REFUSED:CAPABILITY_CATALOG_EMPTY")

    ids: set[str] = set()
    by_id: dict[str, dict] = {}
    for item in items:
        cid = item.get("id", "")
        if not cid.startswith("capability:") or len(cid) <= len("capability:"):
            raise CapabilityError(f"REFUSED:CAPABILITY_ID:{cid}")
        suffix = cid.split(":", 1)[1]
        if any(not (c.islower() or c.isdigit() or c in "-_") for c in suffix):
            raise CapabilityError(f"REFUSED:CAPABILITY_ID:{cid}")
        if cid in ids:
            raise CapabilityError(f"REFUSED:DUPLICATE_CAPABILITY:{cid}")
        ids.add(cid)
        by_id[cid] = item

        if item.get("class") not in ALLOWED_CLASSES:
            raise CapabilityError(f"REFUSED:CAPABILITY_CLASS:{cid}")
        if item.get("standing") not in ALLOWED_STANDING:
            raise CapabilityError(f"REFUSED:CAPABILITY_STANDING:{cid}")
        authority = item.get("required_authority")
        if authority not in ALLOWED_AUTHORITY:
            raise CapabilityError(f"REFUSED:CAPABILITY_AUTHORITY:{cid}")

        interfaces = set(item.get("interfaces", []))
        if interfaces != ALLOWED_INTERFACES:
            raise CapabilityError(f"REFUSED:SURFACE_CLOSURE:{cid}")
        if not item.get("inputs") or not item.get("outputs") or not item.get("refusals"):
            raise CapabilityError(f"REFUSED:CAPABILITY_CONTRACT_INCOMPLETE:{cid}")

        if item.get("class") == "DO":
            if authority not in MUTATING_AUTHORITIES:
                raise CapabilityError(f"REFUSED:DO_WITHOUT_MUTATING_AUTHORITY:{cid}")
            if item.get("broker_required") is not True:
                raise CapabilityError(f"REFUSED:DO_WITHOUT_BROKER:{cid}")
            if item.get("receipt_required") is not True:
                raise CapabilityError(f"REFUSED:DO_WITHOUT_RECEIPT:{cid}")
        elif item.get("broker_required") and authority not in MUTATING_AUTHORITIES:
            raise CapabilityError(f"REFUSED:SPURIOUS_BROKER:{cid}")

    for cid, item in by_id.items():
        for dep in item.get("depends_on", []):
            if dep not in by_id:
                raise CapabilityError(f"REFUSED:MISSING_CAPABILITY_DEPENDENCY:{cid}:{dep}")

    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(cid: str) -> None:
        if cid in visiting:
            raise CapabilityError(f"REFUSED:CAPABILITY_CYCLE:{cid}")
        if cid in visited:
            return
        visiting.add(cid)
        for dep in by_id[cid].get("depends_on", []):
            visit(dep)
        visiting.remove(cid)
        visited.add(cid)

    for cid in sorted(by_id):
        visit(cid)

    return [by_id[cid] for cid in sorted(by_id)]


def render(items: list[dict]) -> str:
    out = [
        "# Chatman Ecosystem Capabilities",
        "",
        "> Generated from `catalog/capabilities.toml`. Do not edit manually.",
        "",
        "| Capability | Class | Authority | Broker | Receipt | Standing | Interfaces |",
        "|---|---|---|---|---|---|---|",
    ]
    for item in items:
        out.append(
            f"| `{item['id']}` | `{item['class']}` | `{item['required_authority']}` | "
            f"{str(item['broker_required']).lower()} | {str(item['receipt_required']).lower()} | "
            f"`{item['standing']}` | {', '.join(item['interfaces'])} |"
        )
    out.extend(["", "## Dependency graph", ""])
    for item in items:
        deps = ", ".join(f"`{dep}`" for dep in item.get("depends_on", [])) or "—"
        out.append(f"- `{item['id']}` ← {deps}")
    out.append("")
    return "\n".join(out)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--catalog", default="catalog/capabilities.toml")
    parser.add_argument("--projection", default="views/generated/capabilities.md")
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    catalog_path = pathlib.Path(args.catalog)
    projection_path = pathlib.Path(args.projection)
    items = verify(load(catalog_path))
    expected = render(items)

    if args.write:
        projection_path.parent.mkdir(parents=True, exist_ok=True)
        projection_path.write_text(expected, encoding="utf-8")
        print(f"CAPABILITIES_RENDERED count={len(items)}")
        return 0

    actual = projection_path.read_text(encoding="utf-8")
    if actual != expected:
        raise CapabilityError("REFUSED:CAPABILITY_PROJECTION_DRIFT")
    print(f"CAPABILITIES_ALIVE count={len(items)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CapabilityError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
