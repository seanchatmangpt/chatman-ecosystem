#!/usr/bin/env python3
"""Verify closed admission of the mandatory v26.9.1 release-crown edge set."""
from __future__ import annotations

import argparse
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

MANDATORY_EDGES = (
    "semantic_o_star",
    "qlever_query_similarity",
    "planner_league_meta_selection_falsification",
    "bcinr_cmca_mfw_consumption",
    "gymact_domain_world_court",
    "brce_consequential_boundary",
    "independent_observation_verification",
    "canonical_receipt_ocel_replay",
    "affidavit_bcre_composition",
    "ggen_marketplace_deterministic_manufacture",
    "autofde_runtime_pinning",
)
ALLOWED = {"UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED"}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


class CrownEdgeRefusal(ValueError):
    pass


def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def verify(data: dict[str, Any]) -> dict[str, Any]:
    crown = data.get("release_crown")
    policy = data.get("policy")
    edges = data.get("edges")
    if not isinstance(crown, dict) or crown.get("version") != "26.9.1":
        raise CrownEdgeRefusal("REFUSED:CROWN_RELEASE_IDENTITY")
    if not isinstance(policy, dict):
        raise CrownEdgeRefusal("REFUSED:CROWN_POLICY_MISSING")
    if policy.get("live_azure_mandatory") is not False or policy.get("live_azure_standing") != "BLOCKED:LIVE_AZURE_AUTHORITY":
        raise CrownEdgeRefusal("REFUSED:LIVE_AZURE_AUTHORITY_POLICY")
    if policy.get("ww3gym_scope") != "SIMULATION_EVALUATION_ONLY":
        raise CrownEdgeRefusal("REFUSED:WW3GYM_SCOPE")
    if policy.get("planner_policy_role_agent_authority_equivalent") is not False:
        raise CrownEdgeRefusal("REFUSED:PLANNER_AUTHORITY_COLLAPSE")
    if policy.get("bcre_brce_equivalent") is not False:
        raise CrownEdgeRefusal("REFUSED:BCRE_BRCE_EQUIVALENCE_WITHOUT_PROOF")
    if not isinstance(edges, list):
        raise CrownEdgeRefusal("REFUSED:CROWN_EDGES_MISSING")

    by_id: dict[str, dict[str, Any]] = {}
    for edge in edges:
        if not isinstance(edge, dict) or not isinstance(edge.get("id"), str):
            raise CrownEdgeRefusal("REFUSED:CROWN_EDGE_INVALID")
        edge_id = edge["id"]
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
        standing = edge.get("standing")
        if standing not in ALLOWED:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_STANDING:{edge_id}:{standing}")
        standings[edge_id] = standing
        evidence = edge.get("evidence", [])
        if not isinstance(evidence, list):
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_INVALID:{edge_id}")
        if standing == "ALIVE" and not evidence:
            raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_ALIVE_WITHOUT_EVIDENCE:{edge_id}")
        for index, item in enumerate(evidence):
            if not isinstance(item, dict):
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_INVALID:{edge_id}:{index}")
            sha = item.get("sha")
            executed_sha = item.get("executed_sha")
            receipt = item.get("receipt")
            if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_SHA:{edge_id}:{index}")
            if executed_sha is not None and executed_sha != sha:
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_IDENTITY:{edge_id}:{index}")
            if executed_sha is not None and (not isinstance(receipt, str) or not receipt.strip()):
                raise CrownEdgeRefusal(f"REFUSED:CROWN_EDGE_EVIDENCE_RECEIPT:{edge_id}:{index}")

    unresolved = [edge for edge in MANDATORY_EDGES if standings[edge] != "ALIVE"]
    return {
        "schema": crown.get("schema"),
        "version": crown["version"],
        "mandatory_edge_count": len(MANDATORY_EDGES),
        "unresolved_edges": unresolved,
        "release_candidate_ready": not unresolved,
        "do_authority": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--edges", type=Path, default=Path("release/v26.9.1/crown-edges.toml"))
    args = parser.parse_args(argv)
    try:
        report = verify(load(args.edges))
    except CrownEdgeRefusal as exc:
        print(str(exc))
        return 4
    print(json.dumps(report, sort_keys=True, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
