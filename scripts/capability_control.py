#!/usr/bin/env python3
"""Read-only capability control kernel for Chatman Ecosystem v26.9.1.

The canonical source is catalog/capabilities.toml. This executable projects the
same admitted capability semantics into CLI/API/MCP/A2A discovery views and
computes a reversible DfCM frontier. It manufactures intents and descriptions;
it never performs consequential DO.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import pathlib
import sys
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
VERIFY_SPEC = importlib.util.spec_from_file_location(
    "verify_capabilities", ROOT / "scripts" / "verify_capabilities.py"
)
if VERIFY_SPEC is None or VERIFY_SPEC.loader is None:
    raise RuntimeError("REFUSED:CAPABILITY_VERIFIER_UNAVAILABLE")
verify_capabilities = importlib.util.module_from_spec(VERIFY_SPEC)
VERIFY_SPEC.loader.exec_module(verify_capabilities)

SURFACES = ("cli", "api", "mcp", "a2a")
NON_CONSEQUENTIAL = {"OBSERVE", "SELECT", "CONSTRUCT"}


class ControlError(RuntimeError):
    pass


def catalog_items(path: pathlib.Path | None = None) -> list[dict[str, Any]]:
    source = path or ROOT / "catalog" / "capabilities.toml"
    return verify_capabilities.verify(verify_capabilities.load(source))


def by_id(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def public_contract(item: dict[str, Any]) -> dict[str, Any]:
    """Return protocol-independent semantics without creating execution authority."""
    return {
        "id": item["id"],
        "title": item["title"],
        "class": item["class"],
        "owner": item["owner"],
        "required_authority": item["required_authority"],
        "broker_required": item["broker_required"],
        "receipt_required": item["receipt_required"],
        "reversible": item["reversible"],
        "standing": item["standing"],
        "inputs": item["inputs"],
        "outputs": item["outputs"],
        "depends_on": item.get("depends_on", []),
        "refusals": item["refusals"],
        "interfaces": item["interfaces"],
        "authority_from_surface": False,
    }


def surface_projection(surface: str, items: list[dict[str, Any]]) -> dict[str, Any]:
    if surface not in SURFACES:
        raise ControlError(f"REFUSED:UNKNOWN_CAPABILITY_SURFACE:{surface}")
    contracts = []
    for item in items:
        contract = public_contract(item)
        if surface == "cli":
            binding = {
                "discovery": f"ecosystem-capability show {item['id']}",
                "execution": "intent-only",
            }
        elif surface == "api":
            binding = {
                "method": "GET",
                "path": f"/v1/capabilities/{item['id']}",
                "execution": "contract-only",
            }
        elif surface == "mcp":
            binding = {
                "resource": f"capability://{item['id']}",
                "tool": "ecosystem.capability.describe",
                "execution": "read-only",
            }
        else:
            binding = {
                "skill_id": item["id"],
                "task_mode": "intent-only",
                "execution": "contract-only",
            }
        contract["surface"] = surface
        contract["binding"] = binding
        contracts.append(contract)
    return {
        "schema": "chatman.capability-surface.v1",
        "surface": surface,
        "subject": "catalog/capabilities.toml",
        "transport_execution_claimed": surface in {"cli", "mcp"},
        "consequential_do_claimed": False,
        "capabilities": contracts,
    }


def dependency_graph(items: list[dict[str, Any]]) -> dict[str, list[str]]:
    return {item["id"]: list(item.get("depends_on", [])) for item in items}


def dfcm_frontier(
    items: list[dict[str, Any]],
    observed_standing: dict[str, str],
    allowed_authorities: set[str],
    include_do: bool,
) -> dict[str, Any]:
    """Preserve every dependency-closed reversible option before selection.

    A dependency is admitted for construction only when explicitly ALIVE in the
    supplied observation. Missing observations remain UNKNOWN and therefore keep
    dependent edges outside the executable frontier rather than deleting them.
    DO is excluded by default. If requested, it still requires its exact authority
    plus the catalog's broker and receipt fences.
    """
    index = by_id(items)
    frontier: list[dict[str, Any]] = []
    blocked: list[dict[str, Any]] = []

    for item in items:
        cid = item["id"]
        deps = item.get("depends_on", [])
        missing = [dep for dep in deps if observed_standing.get(dep, "UNKNOWN") != "ALIVE"]
        authority_ok = item["required_authority"] in allowed_authorities
        do_ok = item["class"] != "DO" or (
            include_do
            and item["broker_required"] is True
            and item["receipt_required"] is True
            and authority_ok
        )
        non_do_ok = item["class"] in NON_CONSEQUENTIAL and authority_ok
        admitted = not missing and (do_ok if item["class"] == "DO" else non_do_ok)
        record = {
            "id": cid,
            "class": item["class"],
            "reversible": item["reversible"],
            "required_authority": item["required_authority"],
            "missing_alive_dependencies": missing,
        }
        if admitted:
            frontier.append(record)
        else:
            reasons = []
            if missing:
                reasons.append("BLOCKED:DEPENDENCY_NOT_ALIVE")
            if not authority_ok:
                reasons.append("REFUSED:EXACT_AUTHORITY_MISSING")
            if item["class"] == "DO" and not include_do:
                reasons.append("REFUSED:DO_NOT_ADMITTED_BY_DFCM")
            record["reasons"] = reasons
            blocked.append(record)

    return {
        "schema": "chatman.dfcm-frontier.v1",
        "policy": "preserve-maximal-reversible-dependency-closed-options",
        "frontier": frontier,
        "blocked": blocked,
        "selection_performed": False,
        "consequential_do_performed": False,
    }


def emit(value: Any) -> None:
    print(json.dumps(value, indent=2, sort_keys=True))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Chatman Ecosystem capability control kernel")
    parser.add_argument("--catalog", type=pathlib.Path, default=ROOT / "catalog" / "capabilities.toml")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("list")
    show = sub.add_parser("show")
    show.add_argument("capability_id")
    sub.add_parser("graph")
    surface = sub.add_parser("surface")
    surface.add_argument("surface", choices=SURFACES)
    plan = sub.add_parser("dfcm")
    plan.add_argument("--state", type=pathlib.Path, required=True)
    plan.add_argument("--authority", action="append", default=[])
    plan.add_argument("--include-do", action="store_true")

    args = parser.parse_args(argv)
    items = catalog_items(args.catalog)
    index = by_id(items)

    if args.command == "list":
        emit([public_contract(item) for item in items])
    elif args.command == "show":
        item = index.get(args.capability_id)
        if item is None:
            raise ControlError(f"REFUSED:UNKNOWN_CAPABILITY:{args.capability_id}")
        emit(public_contract(item))
    elif args.command == "graph":
        emit(dependency_graph(items))
    elif args.command == "surface":
        emit(surface_projection(args.surface, items))
    elif args.command == "dfcm":
        payload = json.loads(args.state.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ControlError("REFUSED:DFCM_STATE_SHAPE")
        observed = payload.get("standing", {})
        if not isinstance(observed, dict) or any(not isinstance(k, str) or not isinstance(v, str) for k, v in observed.items()):
            raise ControlError("REFUSED:DFCM_STANDING_SHAPE")
        emit(dfcm_frontier(items, observed, set(args.authority), args.include_do))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ControlError, verify_capabilities.CapabilityError, OSError, json.JSONDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
