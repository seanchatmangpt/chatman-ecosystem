#!/usr/bin/env python3
"""Fail-closed DfCM admission and evidence law for the v26.9.1 crown-edge set.

This verifier owns mandatory-edge topology only. Broader release-candidate
readiness remains outside its claim ceiling and must be established by the
independent release graph, standing, runtime, receipt, replay, and exact-head
gates.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from datetime import datetime
from pathlib import Path
from typing import Any

SCHEMA = "chatman-ecosystem.release-crown-edges/1"
VERSION = "26.9.1"
CLAIM_CEILING = "MANDATORY_EDGE_ADMISSION_AND_EVIDENCE_TOPOLOGY_ONLY"

EDGE_AUTHORITY: dict[str, tuple[str, ...]] = {
    "semantic_o_star": ("SELECT",),
    "qlever_query_similarity": ("SELECT",),
    "planner_league_meta_selection_falsification": ("SELECT",),
    "bcinr_cmca_mfw_consumption": ("SELECT",),
    "gymact_domain_world_court": ("SELECT",),
    "brce_consequential_boundary": ("DO",),
    "independent_observation_verification": ("OBSERVE",),
    "canonical_receipt_ocel_replay": ("OBSERVE", "CONSTRUCT"),
    "affidavit_bcre_composition": ("SELECT",),
    "ggen_marketplace_deterministic_manufacture": ("CONSTRUCT",),
    "autofde_runtime_pinning": ("SELECT", "CONSTRUCT"),
}
MANDATORY_EDGES = tuple(EDGE_AUTHORITY)
ALLOWED_STANDINGS = {
    "UNKNOWN",
    "PARTIAL_ALIVE",
    "ALIVE",
    "BLOCKED",
    "BUILD_BROKEN",
    "UNSUPPORTED",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
TOKEN_RE = re.compile(r"^[A-Za-z0-9_.-]+:[^\s]+$")

ROOT_KEYS = {"release_crown", "policy", "edges"}
CROWN_KEYS = {
    "schema",
    "version",
    "observed_at",
    "standing",
    "claim_ceiling",
    "do_authority",
}
POLICY_KEYS = {
    "live_azure_mandatory",
    "live_azure_standing",
    "ww3gym_scope",
    "planner_policy_role_agent_authority_equivalent",
    "bcre_brce_equivalent",
    "zero_unreceipted_actuation",
    "brce_exclusive_do_path",
}
EDGE_REQUIRED_KEYS = {"id", "standing", "allowed_authority_classes", "do_authority"}
EDGE_ALLOWED_KEYS = EDGE_REQUIRED_KEYS | {"blocker", "evidence"}
EVIDENCE_KEYS = {
    "repository",
    "ref",
    "sha",
    "executed_sha",
    "receipt",
    "verifier",
    "replay",
    "authority_class",
}


class CrownEdgeRefusal(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _require_keys(
    value: dict[str, Any],
    *,
    required: set[str],
    allowed: set[str],
    label: str,
) -> None:
    missing = sorted(required - set(value))
    extra = sorted(set(value) - allowed)
    if missing:
        raise CrownEdgeRefusal(f"REFUSED:{label}_KEY_MISSING:" + ",".join(missing))
    if extra:
        raise CrownEdgeRefusal(f"REFUSED:{label}_KEY_UNADMITTED:" + ",".join(extra))


def _validate_observed_at(value: object) -> None:
    if not isinstance(value, str):
        raise CrownEdgeRefusal("REFUSED:CROWN_OBSERVED_AT")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise CrownEdgeRefusal("REFUSED:CROWN_OBSERVED_AT") from exc
    if parsed.utcoffset() is None:
        raise CrownEdgeRefusal("REFUSED:CROWN_OBSERVED_AT_TIMEZONE")


def _validate_evidence(
    edge_id: str,
    evidence: object,
    allowed_authorities: tuple[str, ...],
) -> list[dict[str, Any]]:
    if not isinstance(evidence, list):
        raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_INVALID:{edge_id}")

    receipts: set[str] = set()
    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(evidence):
        if not isinstance(item, dict):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_INVALID:{edge_id}:{index}")
        _require_keys(
            item,
            required=EVIDENCE_KEYS,
            allowed=EVIDENCE_KEYS,
            label=f"CROWN_EDGE_EVIDENCE:{edge_id}:{index}",
        )

        repository = item["repository"]
        ref = item["ref"]
        sha = item["sha"]
        executed_sha = item["executed_sha"]
        receipt = item["receipt"]
        verifier = item["verifier"]
        replay = item["replay"]
        authority_class = item["authority_class"]

        if not isinstance(repository, str) or not REPOSITORY_RE.fullmatch(repository):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_REPOSITORY:{edge_id}:{index}")
        if not isinstance(ref, str) or not ref.strip() or any(ch.isspace() for ch in ref):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_REF:{edge_id}:{index}")
        if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_SHA:{edge_id}:{index}")
        if not isinstance(executed_sha, str) or not SHA_RE.fullmatch(executed_sha):
            raise CrownEdgeRefusal(
                f"REFUSED:CROWN_EDGE_EVIDENCE_EXECUTED_SHA:{edge_id}:{index}"
            )
        if executed_sha != sha:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_IDENTITY:{edge_id}:{index}")
        if not isinstance(receipt, str) or not TOKEN_RE.fullmatch(receipt):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_RECEIPT:{edge_id}:{index}")
        if receipt in receipts:
            raise CrownEdgeRefusal(
                f"REFUSED:CROWN_EDGE_EVIDENCE_DUPLICATE_RECEIPT:{edge_id}:{index}"
            )
        receipts.add(receipt)
        if not isinstance(verifier, str) or not TOKEN_RE.fullmatch(verifier):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_VERIFIER:{edge_id}:{index}")
        if not isinstance(replay, str) or not TOKEN_RE.fullmatch(replay):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_REPLAY:{edge_id}:{index}")
        if authority_class not in allowed_authorities:
            raise CrownEdgeRefusal(
                f"REFUSED:CROWN_EDGE_EVIDENCE_AUTHORITY:{edge_id}:{index}:{authority_class}"
            )
        normalized.append(item)
    return normalized


def _edge_set_standing(standings: dict[str, str]) -> str:
    """Use the same aggregate standing law as the canonical release graph."""
    values = list(standings.values())
    if not values:
        return "UNKNOWN"
    if "BUILD_BROKEN" in values:
        return "BUILD_BROKEN"
    if "BLOCKED" in values:
        return "BLOCKED"
    if "UNKNOWN" in values:
        return "UNKNOWN"
    if "PARTIAL_ALIVE" in values:
        return "PARTIAL_ALIVE"
    if "UNSUPPORTED" in values:
        return "UNSUPPORTED"
    if all(value == "ALIVE" for value in values):
        return "ALIVE"
    return "UNKNOWN"


def _topology_digest(policy: dict[str, Any]) -> str:
    topology = {
        "schema": SCHEMA,
        "version": VERSION,
        "policy": policy,
        "edges": [
            {"id": edge_id, "allowed_authority_classes": EDGE_AUTHORITY[edge_id]}
            for edge_id in MANDATORY_EDGES
        ],
    }
    payload = json.dumps(topology, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def verify(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise CrownEdgeRefusal("REFUSED:CROWN_DOCUMENT_INVALID")
    _require_keys(data, required=ROOT_KEYS, allowed=ROOT_KEYS, label="CROWN_DOCUMENT")

    crown = data["release_crown"]
    policy = data["policy"]
    edges = data["edges"]
    if not isinstance(crown, dict):
        raise CrownEdgeRefusal("REFUSED:CROWN_RELEASE_IDENTITY")
    if not isinstance(policy, dict):
        raise CrownEdgeRefusal("REFUSED:CROWN_POLICY_MISSING")
    if not isinstance(edges, list):
        raise CrownEdgeRefusal("REFUSED:CROWN_EDGES_MISSING")

    _require_keys(crown, required=CROWN_KEYS, allowed=CROWN_KEYS, label="CROWN_RELEASE")
    _require_keys(policy, required=POLICY_KEYS, allowed=POLICY_KEYS, label="CROWN_POLICY")

    if crown["schema"] != SCHEMA or crown["version"] != VERSION:
        raise CrownEdgeRefusal("REFUSED:CROWN_RELEASE_IDENTITY")
    if crown["standing"] not in ALLOWED_STANDINGS:
        raise CrownEdgeRefusal("REFUSED:CROWN_RELEASE_STANDING")
    if crown["claim_ceiling"] != CLAIM_CEILING:
        raise CrownEdgeRefusal("REFUSED:CROWN_CLAIM_CEILING")
    if crown["do_authority"] is not False:
        raise CrownEdgeRefusal("REFUSED:CROWN_AMBIENT_DO_AUTHORITY")
    _validate_observed_at(crown["observed_at"])

    if (
        policy["live_azure_mandatory"] is not False
        or policy["live_azure_standing"] != "BLOCKED:LIVE_AZURE_AUTHORITY"
    ):
        raise CrownEdgeRefusal("REFUSED:LIVE_AZURE_AUTHORITY_POLICY")
    if policy["ww3gym_scope"] != "SIMULATION_EVALUATION_ONLY":
        raise CrownEdgeRefusal("REFUSED:WW3GYM_SCOPE")
    if policy["planner_policy_role_agent_authority_equivalent"] is not False:
        raise CrownEdgeRefusal("REFUSED:PLANNER_AUTHORITY_COLLAPSE")
    if policy["bcre_brce_equivalent"] is not False:
        raise CrownEdgeRefusal("REFUSED:BCRE_BRCE_EQUIVALENCE_WITHOUT_PROOF")
    if policy["zero_unreceipted_actuation"] is not True:
        raise CrownEdgeRefusal("REFUSED:ZERO_UNRECEIPTED_ACTUATION_DISABLED")
    if policy["brce_exclusive_do_path"] is not True:
        raise CrownEdgeRefusal("REFUSED:BRCE_EXCLUSIVE_DO_PATH_DISABLED")

    by_id: dict[str, dict[str, Any]] = {}
    for edge in edges:
        if not isinstance(edge, dict):
            raise CrownEdgeRefusal("REFUSED:CROWN_EDGE_INVALID")
        _require_keys(
            edge,
            required=EDGE_REQUIRED_KEYS,
            allowed=EDGE_ALLOWED_KEYS,
            label="CROWN_EDGE",
        )
        edge_id = edge["id"]
        if not isinstance(edge_id, str):
            raise CrownEdgeRefusal("REFUSED:CROWN_EDGE_INVALID")
        if edge_id in by_id:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_DUPLICATE:{edge_id}")
        by_id[edge_id] = edge

    missing = [edge for edge in MANDATORY_EDGES if edge not in by_id]
    extra = [edge for edge in by_id if edge not in MANDATORY_EDGES]
    if missing:
        raise CrownEdgeRefusal("REFUSED:CROWN_EDGE_MISSING:" + ",".join(missing))
    if extra:
        raise CrownEdgeRefusal("REFUSED:CROWN_EDGE_UNADMITTED:" + ",".join(extra))

    standings: dict[str, str] = {}
    for edge_id in MANDATORY_EDGES:
        edge = by_id[edge_id]
        standing = edge["standing"]
        if standing not in ALLOWED_STANDINGS:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_STANDING:{edge_id}:{standing}")
        standings[edge_id] = standing

        authorities = edge["allowed_authority_classes"]
        expected_authorities = EDGE_AUTHORITY[edge_id]
        if not isinstance(authorities, list) or tuple(authorities) != expected_authorities:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_AUTHORITY_TOPOLOGY:{edge_id}")
        if edge["do_authority"] is not False:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_AMBIENT_DO_AUTHORITY:{edge_id}")
        if "DO" in expected_authorities and edge_id != "brce_consequential_boundary":
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_DO_PATH:{edge_id}")

        blocker = edge.get("blocker")
        evidence = _validate_evidence(edge_id, edge.get("evidence", []), expected_authorities)

        if standing == "UNKNOWN":
            if evidence or blocker:
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_UNKNOWN_WITH_CLAIMS:{edge_id}")
        elif standing == "PARTIAL_ALIVE":
            if not evidence:
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_PARTIAL_WITHOUT_EVIDENCE:{edge_id}")
        elif standing == "ALIVE":
            if not evidence:
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_ALIVE_WITHOUT_EVIDENCE:{edge_id}")
            if blocker:
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_ALIVE_WITH_BLOCKER:{edge_id}")
        elif standing in {"BLOCKED", "UNSUPPORTED"}:
            if not isinstance(blocker, str) or not blocker.strip():
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_{standing}_WITHOUT_REASON:{edge_id}")
            if evidence:
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_{standing}_WITH_EXECUTION:{edge_id}")
        elif standing == "BUILD_BROKEN":
            if not isinstance(blocker, str) or not blocker.strip():
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_BUILD_BROKEN_WITHOUT_REASON:{edge_id}")
            if not evidence:
                raise CrownEdgeRefusal(
                    f"REFUSED:CROWN_EDGE_BUILD_BROKEN_WITHOUT_EXECUTION:{edge_id}"
                )

    derived_standing = _edge_set_standing(standings)
    if crown["standing"] == "ALIVE" and derived_standing != "ALIVE":
        raise CrownEdgeRefusal("REFUSED:CROWN_ALIVE_WITH_UNRESOLVED_EDGES")
    if derived_standing == "ALIVE" and crown["standing"] != "ALIVE":
        raise CrownEdgeRefusal("REFUSED:CROWN_STANDING_STALE")
    if crown["standing"] != derived_standing:
        raise CrownEdgeRefusal(
            f"REFUSED:CROWN_STANDING_DERIVATION:declared={crown['standing']}:derived={derived_standing}"
        )

    unresolved = [edge for edge in MANDATORY_EDGES if standings[edge] != "ALIVE"]
    all_alive = not unresolved
    return {
        "schema": SCHEMA,
        "version": VERSION,
        "mandatory_edge_count": len(MANDATORY_EDGES),
        "edge_set_standing": derived_standing,
        "unresolved_edges": unresolved,
        "mandatory_edges_ready": all_alive,
        "release_candidate_ready": False,
        "release_candidate_ready_reason": "OUTSIDE_EDGE_VERIFIER_CLAIM_CEILING",
        "topology_sha256": _topology_digest(policy),
        "claim_ceiling": CLAIM_CEILING,
        "do_authority": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--edges",
        type=Path,
        default=Path("release/v26.9.1/crown-edges.toml"),
    )
    args = parser.parse_args(argv)
    try:
        report = verify(load(args.edges))
    except (CrownEdgeRefusal, OSError, tomllib.TOMLDecodeError) as exc:
        print(str(exc))
        return 4
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
