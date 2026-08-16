#!/usr/bin/env python3
"""Construct deterministic, powerless completion intents for Chatman Ecosystem v26.9.1."""

from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
ACTIVE_FLEET_KEYS = {
    "adapter": ("ADAPTER", "ORIENT_PIN_ADAPT_VERIFY", 4),
    "bench_gym": ("BENCH_GYM", "QUALIFY_BOUNDED_EPISODE", 5),
    "source_archaeology": ("SOURCE_ARCHAEOLOGY", "HARVEST_AND_FREEZE", 6),
}


def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def release_action(component: dict[str, Any]) -> tuple[str, int]:
    standing = component["standing"]
    if standing == "BUILD_BROKEN":
        return "REPAIR_EXACT_FAILURE", 0
    if standing == "BLOCKED":
        return "UNBLOCK_OR_RECLASSIFY_WITH_EVIDENCE", 2
    if standing in {"UNKNOWN", "PARTIAL_ALIVE"}:
        priority = 3 if component["disposition"] == "CROWN" else (1 if not component["depends_on"] else 2)
        return "EXECUTE_CANONICAL_VERIFIER_OR_REPAIR", priority
    if standing == "ALIVE":
        return "HOLD_EXACT_IDENTITY", 9
    if standing == "UNSUPPORTED":
        return "RESOLVE_UNSUPPORTED_OR_REMOVE_FROM_CROWN", 2
    raise ValueError(f"unsupported standing: {standing}")


def branch_slug(component_id: str, action: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", component_id.lower()).strip("-")
    suffix = {
        "REPAIR_EXACT_FAILURE": "repair",
        "UNBLOCK_OR_RECLASSIFY_WITH_EVIDENCE": "unblock",
        "EXECUTE_CANONICAL_VERIFIER_OR_REPAIR": "closure",
        "HOLD_EXACT_IDENTITY": "hold",
        "RESOLVE_UNSUPPORTED_OR_REMOVE_FROM_CROWN": "support",
        "BOOTSTRAP_REPOSITORY": "bootstrap",
        "ORIENT_PIN_ADAPT_VERIFY": "adapter",
        "QUALIFY_BOUNDED_EPISODE": "gym",
        "HARVEST_AND_FREEZE": "harvest",
    }[action]
    return f"agent/v26.9.1-{slug}-{suffix}"


def acceptance(action: str, exact_subject: bool) -> list[str]:
    steps = [
        "Resolve and freeze the exact base identity before editing.",
        "Read root and nested AGENTS.md plus repository Definition of Done and generated-artifact policy.",
        "Implement the smallest dependency-closed change that closes the admitted gap; do not duplicate canonical semantics.",
        "Run the owning canonical verifier locally when possible; preserve typed failures instead of rerunning unchanged failures.",
        "Publish only a purpose branch and draft pull request; do not merge, tag, release, or grant DO authority.",
        "Observe exact-head execution and bind owning receipt/replay evidence before any ALIVE promotion.",
        "Refuse standing transfer by adjacency: workflow metadata, nearby green commits, or another repository's receipt are insufficient.",
    ]
    if not exact_subject:
        steps.insert(1, "Orient the repository and pin a concrete ref/SHA before claiming implementation or execution standing.")
    if action == "BOOTSTRAP_REPOSITORY":
        steps.insert(0, "Create the named repository only through an authorized repository-creation boundary; do not substitute ggen-mcp or another adjacent repository.")
    return steps


def release_packets(manifest: dict[str, Any]) -> list[dict[str, Any]]:
    by_id = {component["id"]: component for component in manifest["components"]}
    packets: list[dict[str, Any]] = []
    for component in manifest["components"]:
        action, priority = release_action(component)
        blocked_by = [
            dependency
            for dependency in component["depends_on"]
            if by_id[dependency]["standing"] != "ALIVE"
        ]
        packet = {
            "id": component["id"],
            "repository": component["repository"],
            "role": component["role"],
            "disposition": component["disposition"],
            "release_blocking": True,
            "standing": component["standing"],
            "ref": component["ref"],
            "sha": component["sha"],
            "depends_on": component["depends_on"],
            "blocked_by": blocked_by,
            "construct_ready": action != "HOLD_EXACT_IDENTITY",
            "promotion_ready": not blocked_by and component["standing"] == "ALIVE",
            "action": action,
            "priority": priority,
            "branch": None if action == "HOLD_EXACT_IDENTITY" else branch_slug(component["id"], action),
            "do_authority": False,
            "acceptance": acceptance(action, exact_subject=True),
        }
        for key in ("blocker", "execution_receipt", "executed_sha"):
            if key in component:
                packet[key] = component[key]
        packets.append(packet)
    return packets


def bootstrap_packets(bootstrap: dict[str, Any], release_components: set[str]) -> list[dict[str, Any]]:
    if bootstrap.get("bootstrap", {}).get("do_authority") is not False:
        raise ValueError("bootstrap must be powerless: do_authority=false")
    packets: list[dict[str, Any]] = []
    for requirement in bootstrap.get("requirements", []):
        if requirement["id"] in release_components:
            raise ValueError(f"bootstrap requirement already admitted: {requirement['id']}")
        substitute = requirement.get("substitute", "")
        if substitute:
            raise ValueError(f"bootstrap requirement cannot silently substitute: {requirement['id']} -> {substitute}")
        packet = {
            "id": requirement["id"],
            "repository": requirement["repository"],
            "role": requirement["role"],
            "disposition": requirement["disposition"],
            "release_blocking": True,
            "standing": requirement["standing"],
            "blocker": requirement["blocker"],
            "ref": None,
            "sha": None,
            "depends_on": requirement.get("depends_on", []),
            "blocked_by": [requirement["blocker"]],
            "construct_ready": True,
            "promotion_ready": False,
            "action": "BOOTSTRAP_REPOSITORY",
            "priority": 0,
            "branch": branch_slug(requirement["id"], "BOOTSTRAP_REPOSITORY"),
            "do_authority": False,
            "acceptance": acceptance("BOOTSTRAP_REPOSITORY", exact_subject=False),
        }
        packets.append(packet)
    return packets


def portfolio_packets(policy: dict[str, Any], release_repositories: set[str]) -> list[dict[str, Any]]:
    packets: list[dict[str, Any]] = []
    dispositions = policy["dispositions"]
    for key, (disposition, action, priority) in ACTIVE_FLEET_KEYS.items():
        for repository in dispositions.get(key, []):
            if repository in release_repositories:
                raise ValueError(f"release repository duplicated in portfolio fanout: {repository}")
            component_id = repository.split("/", 1)[1]
            packets.append(
                {
                    "id": component_id,
                    "repository": repository,
                    "role": key.replace("_", "-"),
                    "disposition": disposition,
                    "release_blocking": False,
                    "standing": "UNKNOWN",
                    "ref": None,
                    "sha": None,
                    "depends_on": [],
                    "blocked_by": ["EXACT_SUBJECT_NOT_ADMITTED"],
                    "construct_ready": True,
                    "promotion_ready": False,
                    "action": action,
                    "priority": priority,
                    "branch": branch_slug(component_id, action),
                    "do_authority": False,
                    "acceptance": acceptance(action, exact_subject=False),
                }
            )
    return packets


def construct_plan(
    manifest: dict[str, Any],
    policy: dict[str, Any],
    bootstrap: dict[str, Any],
    include_portfolio: bool = True,
) -> dict[str, Any]:
    release = manifest["release"]
    release_rows = release_packets(manifest)
    release_ids = {row["id"] for row in release_rows}
    release_repositories = {row["repository"] for row in release_rows}
    bootstrap_rows = bootstrap_packets(bootstrap, release_ids)
    rows = release_rows + bootstrap_rows
    if include_portfolio:
        rows.extend(portfolio_packets(policy, release_repositories))

    rows.sort(key=lambda row: (row["priority"], row["release_blocking"] is False, row["repository"], row["id"]))

    explicit_dispositions = sum(len(values) for values in policy["dispositions"].values())
    observed = policy["fleet"]["observed_owned_repository_count"]
    root = policy["fleet"]["composition_root"]
    root_in_dispositions = any(root in values for values in policy["dispositions"].values())
    classified_existing = explicit_dispositions + (0 if root_in_dispositions else 1)
    frozen_default = observed - classified_existing
    if frozen_default < 0:
        raise ValueError("fleet policy classifies more repositories than were observed")

    return {
        "schema": "urn:chatman:ecosystem:completion-plan:v1",
        "release": release["version"],
        "target_date": release["target_date"],
        "authority": {
            "select": True,
            "construct": True,
            "do": False,
            "rule": "Planner manufactures intents only; GymAct/BRCE owns consequential DO.",
        },
        "counts": {
            "release_components": len(release_rows),
            "bootstrap_requirements": len(bootstrap_rows),
            "portfolio_active": len(rows) - len(release_rows) - len(bootstrap_rows),
            "active_packets": len(rows),
            "observed_owned_repositories": observed,
            "explicit_frozen": len(policy["dispositions"].get("explicit_out_of_release", [])),
            "default_frozen": frozen_default,
        },
        "crown": {
            "current": release["standing"],
            "strict_done_when": "Every admitted required component is ALIVE at its exact subject, gdmcp is admitted rather than bootstrapped, and the FDEGym capstone has owning execution/receipt/replay evidence.",
        },
        "packets": rows,
    }


def validate_plan(plan: dict[str, Any]) -> list[str]:
    findings: list[str] = []
    packets = plan.get("packets", [])
    coordinates: set[tuple[str, str]] = set()
    for packet in packets:
        coordinate = (packet["repository"], packet["id"])
        if coordinate in coordinates:
            findings.append(f"DUPLICATE_PACKET:{packet['repository']}:{packet['id']}")
        coordinates.add(coordinate)
        if packet.get("do_authority") is not False:
            findings.append(f"AMBIENT_DO_AUTHORITY:{packet['repository']}")
        sha = packet.get("sha")
        if sha is not None and not SHA_RE.fullmatch(sha):
            findings.append(f"INVALID_SHA:{packet['repository']}:{sha}")
        if packet["standing"] == "ALIVE" and not packet.get("execution_receipt"):
            findings.append(f"ALIVE_WITHOUT_RECEIPT:{packet['repository']}")
        if packet["standing"] == "BUILD_BROKEN":
            if not packet.get("blocker") or not packet.get("execution_receipt"):
                findings.append(f"BUILD_BROKEN_WITHOUT_EVIDENCE:{packet['repository']}")
            if packet.get("executed_sha") != packet.get("sha"):
                findings.append(f"BUILD_BROKEN_SUBJECT_DRIFT:{packet['repository']}")
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml"))
    parser.add_argument("--fleet", type=Path, default=Path("release/v26.9.1/fleet-policy.toml"))
    parser.add_argument("--bootstrap", type=Path, default=Path("release/v26.9.1/fanout-bootstrap.toml"))
    parser.add_argument("--release-only", action="store_true")
    args = parser.parse_args(argv)

    manifest = load(args.manifest)
    policy = load(args.fleet)
    bootstrap = load(args.bootstrap)
    plan = construct_plan(manifest, policy, bootstrap, include_portfolio=not args.release_only)
    findings = validate_plan(plan)
    plan["standing"] = "ALIVE" if not findings else "BLOCKED"
    plan["findings"] = findings
    print(json.dumps(plan, indent=2, sort_keys=True))
    return 0 if not findings else 2


if __name__ == "__main__":
    sys.exit(main())
