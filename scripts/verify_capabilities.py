#!/usr/bin/env python3
"""Fail-closed verifier and deterministic projections for capability catalogs."""
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
DEFAULT_BASE = pathlib.Path("catalog/capabilities.toml")
DEFAULT_EXTENSION = pathlib.Path("catalog/capabilities-decision-graph.toml")
DEFAULT_BASE_PROJECTION = pathlib.Path("views/generated/capabilities.md")
DEFAULT_EXTENSION_PROJECTION = pathlib.Path("views/generated/capabilities-decision-graph.md")


class CapabilityError(RuntimeError):
    pass


def load(path: pathlib.Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def combine(catalogs: list[dict]) -> dict:
    if not catalogs:
        raise CapabilityError("REFUSED:CAPABILITY_CATALOG_EMPTY")
    first = catalogs[0]
    for catalog in catalogs[1:]:
        for field in ("schema", "version", "subject"):
            if catalog.get(field) != first.get(field):
                raise CapabilityError(f"REFUSED:CAPABILITY_CATALOG_ALIGNMENT:{field}")
    return {
        "schema": first.get("schema"),
        "version": first.get("version"),
        "subject": first.get("subject"),
        "capability": [
            item
            for catalog in catalogs
            for item in catalog.get("capability", [])
        ],
    }


def load_default(root: pathlib.Path, base: pathlib.Path | None = None) -> dict:
    base_path = base or root / DEFAULT_BASE
    catalogs = [load(base_path)]
    extension = root / DEFAULT_EXTENSION
    if extension.exists() and extension.resolve() != base_path.resolve():
        catalogs.append(load(extension))
    return combine(catalogs)


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

        owner = item.get("owner", "")
        if not owner.startswith("repository:") or len(owner) <= len("repository:"):
            raise CapabilityError(f"REFUSED:CAPABILITY_OWNER:{cid}")
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
        if not item.get("source_repositories"):
            raise CapabilityError(f"REFUSED:CAPABILITY_SOURCE_OWNERSHIP_EMPTY:{cid}")

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


def render(items: list[dict], source: str = "catalog/capabilities.toml") -> str:
    out = [
        "# Chatman Ecosystem Capabilities",
        "",
        f"> Generated from `{source}`. Do not edit manually.",
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
    parser.add_argument("--catalog", type=pathlib.Path, default=DEFAULT_BASE)
    parser.add_argument("--extension", type=pathlib.Path, default=DEFAULT_EXTENSION)
    parser.add_argument("--projection", type=pathlib.Path, default=DEFAULT_BASE_PROJECTION)
    parser.add_argument(
        "--extension-projection",
        type=pathlib.Path,
        default=DEFAULT_EXTENSION_PROJECTION,
    )
    parser.add_argument("--write", action="store_true")
    args = parser.parse_args()

    base = load(args.catalog)
    catalogs = [base]
    extension = None
    if args.extension.exists() and args.extension.resolve() != args.catalog.resolve():
        extension = load(args.extension)
        catalogs.append(extension)

    items = verify(combine(catalogs))
    base_items = verify(base)
    base_expected = render(base_items, args.catalog.as_posix())

    extension_expected = None
    extension_items: list[dict] = []
    if extension is not None:
        extension_ids = {item["id"] for item in extension.get("capability", [])}
        extension_items = [item for item in items if item["id"] in extension_ids]
        extension_expected = render(extension_items, args.extension.as_posix())

    if args.write:
        args.projection.parent.mkdir(parents=True, exist_ok=True)
        args.projection.write_text(base_expected, encoding="utf-8")
        if extension_expected is not None:
            args.extension_projection.parent.mkdir(parents=True, exist_ok=True)
            args.extension_projection.write_text(extension_expected, encoding="utf-8")
        print(
            f"CAPABILITIES_RENDERED count={len(items)} "
            f"base={len(base_items)} extension={len(extension_items)}"
        )
        return 0

    if args.projection.read_text(encoding="utf-8") != base_expected:
        raise CapabilityError("REFUSED:CAPABILITY_PROJECTION_DRIFT")
    if extension_expected is not None:
        if not args.extension_projection.exists():
            raise CapabilityError("REFUSED:CAPABILITY_EXTENSION_PROJECTION_MISSING")
        if args.extension_projection.read_text(encoding="utf-8") != extension_expected:
            raise CapabilityError("REFUSED:CAPABILITY_EXTENSION_PROJECTION_DRIFT")
    print(
        f"CAPABILITIES_ALIVE count={len(items)} "
        f"base={len(base_items)} extension={len(extension_items)}"
    )
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (CapabilityError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
