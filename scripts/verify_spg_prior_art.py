#!/usr/bin/env python3
"""Structural court for prior-art routing and Semantic Procedural Graphs.

This court establishes repository-local structural admission only. It does not
grant runtime authority, execution standing, or semantic equivalence to any
projection.
"""
from __future__ import annotations

import argparse
import copy
import json
import pathlib
import sys
import tomllib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
PRIOR_ART = ROOT / "catalog" / "prior-art.toml"
EXAMPLE = ROOT / "examples" / "spg" / "sa2a-brce.json"

ALLOWED_NODE_CLASSES = {"OBSERVE", "SELECT", "CONSTRUCT", "DO"}
ALLOWED_RELATIONS = {"LEADS_TO", "TRIGGERS", "PROVIDES_INPUT_FOR", "CONVERGES_TO"}
ALLOWED_STATES = {"CANDIDATE", "ADMITTED", "REFUSED"}
ALLOWED_STANDING = {"NONE", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "UNSUPPORTED"}
ALLOWED_DISPOSITIONS = {"REUSE", "COMPOSE", "EXTEND", "NOVEL_GAP"}
REQUIRED_PROJECTIONS = {"hddl", "tla_plus", "ocel2", "sa2a", "brce"}


class SpgRefusal(ValueError):
    """Typed structural refusal."""


def _require(condition: bool, refusal: str) -> None:
    if not condition:
        raise SpgRefusal(refusal)


def load_prior_art(path: pathlib.Path = PRIOR_ART) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def load_graph(path: pathlib.Path = EXAMPLE) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_prior_art_catalog(catalog: dict[str, Any]) -> set[str]:
    _require(
        catalog.get("schema") == "chatman.prior-art-catalog.v1",
        "REFUSED:PRIOR_ART_SCHEMA",
    )
    _require(
        catalog.get("standing") == "CANDIDATE_REFERENCE",
        "REFUSED:PRIOR_ART_SELF_STANDING",
    )
    entries = catalog.get("entry")
    _require(isinstance(entries, list) and entries, "REFUSED:PRIOR_ART_EMPTY")

    ids: set[str] = set()
    semantics_seen: set[str] = set()
    for entry in entries:
        eid = entry.get("id")
        _require(
            isinstance(eid, str) and eid.startswith("prior:"),
            f"REFUSED:PRIOR_ART_ID:{eid!r}",
        )
        _require(eid not in ids, f"REFUSED:PRIOR_ART_DUPLICATE:{eid}")
        ids.add(eid)

        _require(bool(entry.get("name")), f"REFUSED:PRIOR_ART_NAME:{eid}")
        _require(bool(entry.get("kind")), f"REFUSED:PRIOR_ART_KIND:{eid}")
        uri = entry.get("retrieval_uri")
        _require(
            isinstance(uri, str) and uri.startswith("https://"),
            f"REFUSED:PRIOR_ART_URI:{eid}",
        )
        semantics = entry.get("semantics")
        _require(
            isinstance(semantics, list) and semantics,
            f"REFUSED:PRIOR_ART_SEMANTICS:{eid}",
        )
        semantics_seen.update(semantics)
        _require(
            isinstance(entry.get("exact_version_required_before_projection"), bool),
            f"REFUSED:PRIOR_ART_PIN_POLICY:{eid}",
        )

    required_families = {
        "ontology",
        "graph-constraints",
        "hierarchical-planning",
        "nondeterministic-planning",
        "transition-system",
        "object-centric-events",
        "constraints",
        "proof",
        "optimization",
    }
    _require(
        required_families.issubset(semantics_seen),
        "REFUSED:PRIOR_ART_ROUTING_GAP",
    )
    return ids


def validate_prior_art_claim(claim: dict[str, Any], known_ids: set[str]) -> None:
    required = claim.get("required_semantics")
    searched = claim.get("searched")
    selected = claim.get("selected")
    disposition = claim.get("disposition")
    falsifier = claim.get("falsifier")

    _require(
        isinstance(required, list) and required,
        "REFUSED:REQUIRED_SEMANTICS_MISSING",
    )
    _require(
        isinstance(searched, list) and searched,
        "REFUSED:PRIOR_ART_SEARCH_MISSING",
    )
    unknown = sorted(set(searched) - known_ids)
    _require(not unknown, f"REFUSED:UNKNOWN_PRIOR_ART:{','.join(unknown)}")
    _require(
        disposition in ALLOWED_DISPOSITIONS,
        f"REFUSED:PRIOR_ART_DISPOSITION:{disposition!r}",
    )
    _require(
        isinstance(falsifier, str) and falsifier.strip(),
        "REFUSED:FALSIFIER_MISSING",
    )

    if disposition == "NOVEL_GAP":
        _require(
            selected in (None, []),
            "REFUSED:NOVELTY_WITH_SELECTED_PRIOR_ART",
        )
        failures = claim.get("candidate_failures")
        _require(
            isinstance(failures, list) and failures,
            "REFUSED:NOVELTY_WITHOUT_PRIOR_ART_FAILURES",
        )
        failed_ids = {item.get("id") for item in failures if isinstance(item, dict)}
        _require(
            set(searched).issubset(failed_ids),
            "REFUSED:NOVELTY_SEARCH_NOT_DISCHARGED",
        )
        for failure in failures:
            _require(
                isinstance(failure.get("missing_semantics"), list)
                and failure["missing_semantics"],
                "REFUSED:NOVELTY_FAILURE_UNTYPED",
            )
    else:
        _require(
            isinstance(selected, list) and selected,
            "REFUSED:PRIOR_ART_SELECTION_MISSING",
        )
        _require(
            set(selected).issubset(set(searched)),
            "REFUSED:SELECTED_OUTSIDE_SEARCH",
        )


def validate_graph(graph: dict[str, Any], known_prior_art: set[str]) -> dict[str, Any]:
    _require(graph.get("schema") == "chatman.spg.v1", "REFUSED:SPG_SCHEMA")
    _require(bool(graph.get("id")), "REFUSED:SPG_ID")
    _require(bool(graph.get("version")), "REFUSED:SPG_VERSION")
    _require(graph.get("state") in ALLOWED_STATES, "REFUSED:SPG_STATE")
    _require(graph.get("standing") in ALLOWED_STANDING, "REFUSED:SPG_STANDING")

    nodes = graph.get("nodes")
    edges = graph.get("edges")
    _require(isinstance(nodes, list) and nodes, "REFUSED:SPG_NODES")
    _require(isinstance(edges, list) and edges, "REFUSED:SPG_EDGES")

    node_ids: set[str] = set()
    for node in nodes:
        nid = node.get("id")
        _require(isinstance(nid, str) and nid, "REFUSED:SPG_NODE_ID")
        _require(nid not in node_ids, f"REFUSED:SPG_DUPLICATE_NODE:{nid}")
        node_ids.add(nid)
        _require(
            node.get("class") in ALLOWED_NODE_CLASSES,
            f"REFUSED:SPG_NODE_CLASS:{nid}",
        )
        _require(bool(node.get("capability")), f"REFUSED:SPG_NODE_CAPABILITY:{nid}")

    edge_ids: set[str] = set()
    consequential = 0
    for edge in edges:
        eid = edge.get("id")
        _require(isinstance(eid, str) and eid, "REFUSED:SPG_EDGE_ID")
        _require(eid not in edge_ids, f"REFUSED:SPG_DUPLICATE_EDGE:{eid}")
        edge_ids.add(eid)
        _require(edge.get("from") in node_ids, f"REFUSED:SPG_EDGE_FROM:{eid}")
        _require(edge.get("to") in node_ids, f"REFUSED:SPG_EDGE_TO:{eid}")
        _require(
            edge.get("relation") in ALLOWED_RELATIONS,
            f"REFUSED:SPG_RELATION:{eid}",
        )
        _require(bool(edge.get("guard")), f"REFUSED:SPG_GUARD:{eid}")
        evidence = edge.get("evidence_required")
        _require(
            isinstance(evidence, list) and evidence,
            f"REFUSED:SPG_EVIDENCE:{eid}",
        )
        _require(
            isinstance(edge.get("authority_required"), str)
            and edge["authority_required"],
            f"REFUSED:SPG_AUTHORITY:{eid}",
        )
        consequence = edge.get("consequence")
        _require(
            consequence in {"observational", "constructive", "consequential"},
            f"REFUSED:SPG_CONSEQUENCE:{eid}",
        )
        if consequence == "consequential":
            consequential += 1
            _require(
                edge.get("authority_required") != "NONE",
                f"REFUSED:CONSEQUENCE_WITHOUT_AUTHORITY:{eid}",
            )
            _require(
                edge.get("receipt_required") is True,
                f"REFUSED:CONSEQUENCE_WITHOUT_RECEIPT:{eid}",
            )
            _require(
                isinstance(edge.get("falsifier"), str) and edge["falsifier"].strip(),
                f"REFUSED:CONSEQUENCE_WITHOUT_FALSIFIER:{eid}",
            )

    projections = graph.get("projections")
    _require(isinstance(projections, dict), "REFUSED:SPG_PROJECTIONS")
    _require(
        REQUIRED_PROJECTIONS.issubset(projections),
        "REFUSED:SPG_PROJECTION_FAMILY_MISSING",
    )
    for family, bindings in projections.items():
        _require(
            isinstance(bindings, dict) and bindings,
            f"REFUSED:SPG_PROJECTION_EMPTY:{family}",
        )
        dangling = sorted(set(bindings) - node_ids)
        _require(
            not dangling,
            f"REFUSED:SPG_PROJECTION_DANGLING:{family}:{','.join(dangling)}",
        )

    claims = graph.get("prior_art")
    _require(
        isinstance(claims, list) and claims,
        "REFUSED:SPG_PRIOR_ART_MISSING",
    )
    for claim in claims:
        validate_prior_art_claim(claim, known_prior_art)

    # A structural SPG cannot self-authorize execution or external standing.
    _require(
        graph.get("standing") != "ALIVE",
        "REFUSED:SPG_SELF_STANDING",
    )

    return {
        "schema": "chatman.spg-validation.v1",
        "graph": graph["id"],
        "nodes": len(nodes),
        "edges": len(edges),
        "consequential_edges": consequential,
        "projection_families": sorted(projections),
        "prior_art_claims": len(claims),
        "state": "ADMITTED_STRUCTURE",
        "standing": "NONE",
    }


def semantic_diff(old: dict[str, Any], new: dict[str, Any]) -> dict[str, Any]:
    """Return behaviorally relevant graph changes by stable semantic identity."""

    old_nodes = {item["id"]: item for item in old.get("nodes", [])}
    new_nodes = {item["id"]: item for item in new.get("nodes", [])}
    old_edges = {item["id"]: item for item in old.get("edges", [])}
    new_edges = {item["id"]: item for item in new.get("edges", [])}

    result: dict[str, Any] = {
        "added_nodes": sorted(set(new_nodes) - set(old_nodes)),
        "removed_nodes": sorted(set(old_nodes) - set(new_nodes)),
        "added_edges": sorted(set(new_edges) - set(old_edges)),
        "removed_edges": sorted(set(old_edges) - set(new_edges)),
        "changed_nodes": [],
        "changed_edges": [],
    }

    node_fields = ("class", "capability")
    for nid in sorted(set(old_nodes) & set(new_nodes)):
        changes = {
            field: {"old": old_nodes[nid].get(field), "new": new_nodes[nid].get(field)}
            for field in node_fields
            if old_nodes[nid].get(field) != new_nodes[nid].get(field)
        }
        if changes:
            result["changed_nodes"].append({"id": nid, "changes": changes})

    edge_fields = (
        "from",
        "to",
        "relation",
        "guard",
        "evidence_required",
        "authority_required",
        "consequence",
        "receipt_required",
        "falsifier",
    )
    for eid in sorted(set(old_edges) & set(new_edges)):
        changes = {
            field: {"old": old_edges[eid].get(field), "new": new_edges[eid].get(field)}
            for field in edge_fields
            if old_edges[eid].get(field) != new_edges[eid].get(field)
        }
        if changes:
            result["changed_edges"].append({"id": eid, "changes": changes})
    return result


def self_test() -> dict[str, Any]:
    prior_art = validate_prior_art_catalog(load_prior_art())
    result = validate_graph(load_graph(), prior_art)

    mutated = copy.deepcopy(load_graph())
    edge = next(item for item in mutated["edges"] if item["id"] == "e4")
    edge["authority_required"] = "NONE"
    try:
        validate_graph(mutated, prior_art)
    except SpgRefusal as exc:
        _require(
            "CONSEQUENCE_WITHOUT_AUTHORITY" in str(exc),
            "REFUSED:SPG_NEGATIVE_CONTROL_WRONG_FAILURE",
        )
    else:
        raise SpgRefusal("REFUSED:SPG_NEGATIVE_CONTROL_VACUOUS")

    return result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--prior-art", type=pathlib.Path, default=PRIOR_ART)
    parser.add_argument("--graph", type=pathlib.Path, default=EXAMPLE)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()

    try:
        if args.self_test:
            result = self_test()
        else:
            known = validate_prior_art_catalog(load_prior_art(args.prior_art))
            result = validate_graph(load_graph(args.graph), known)
    except (SpgRefusal, OSError, json.JSONDecodeError, tomllib.TOMLDecodeError) as exc:
        if args.json:
            print(json.dumps({"state": "REFUSED", "reason": str(exc)}, sort_keys=True))
        else:
            print(str(exc), file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "SPG_PRIOR_ART_ALIVE "
            f"graph={result['graph']} nodes={result['nodes']} edges={result['edges']} "
            f"prior_art={result['prior_art_claims']} standing=NONE"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
