#!/usr/bin/env python3
"""Validate capability contracts against the canonical DfCM profile.

This court is structural and fail-closed. It validates that capability
contracts preserve DfCM's reversible frontier, authority separation,
falsifier requirement, extension order, public-ontology boundary, and
broker-only consequential DO law. It does not grant runtime standing.
"""
from __future__ import annotations

import argparse
import importlib.util
import pathlib
import sys
import tomllib
from typing import Any

ROOT = pathlib.Path(__file__).resolve().parents[1]
DFCM = ROOT / "catalog" / "dfcm.toml"
CAPABILITY_VERIFIER = ROOT / "scripts" / "verify_capabilities.py"
FLEET_CATALOG = ROOT / "catalog" / "capabilities-fleet.toml"

SPEC = importlib.util.spec_from_file_location("verify_capabilities", CAPABILITY_VERIFIER)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("REFUSED:CAPABILITY_VERIFIER_UNAVAILABLE")
verify_capabilities = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_capabilities)

EPR_IDS = {
    "capability:observe-external-paradigm-subject",
    "capability:extract-external-paradigm-units",
    "capability:classify-external-paradigm",
    "capability:project-external-paradigm-cross-product",
    "capability:detect-external-paradigm-delta",
}

EXPECTED_EXTENSION_ORDER = ["reuse", "compose", "extend", "invent"]
EXPECTED_BOUND_DIMENSIONS = {
    "ontology",
    "capability",
    "authority",
    "cost",
    "evidence",
    "consequence",
}
REQUIRED_PUBLIC_ONTOLOGIES = {"prov", "skos", "dcterms", "odrl", "sh"}


class DfcmCapabilityError(RuntimeError):
    """Typed DfCM capability refusal."""


def load_profile(path: pathlib.Path = DFCM) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def _index(items: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    return {item["id"]: item for item in items}


def _require(condition: bool, refusal: str) -> None:
    if not condition:
        raise DfcmCapabilityError(refusal)


def _contains_all(values: list[str], required: set[str]) -> bool:
    joined = " | ".join(values)
    return all(value in joined for value in required)


def validate_profile(profile: dict[str, Any]) -> None:
    _require(
        profile.get("schema") == "chatman.dfcm-profile.v1",
        "REFUSED:DFCM_PROFILE_SCHEMA",
    )
    _require(profile.get("canonical") is True, "REFUSED:DFCM_NOT_CANONICAL")

    objective = profile.get("objective") or {}
    _require(
        objective.get("expression")
        == "maximize lawful reversible possibilities before irreversible selection",
        "REFUSED:DFCM_OBJECTIVE_DRIFT",
    )

    bound = profile.get("bound") or {}
    _require(bound.get("operator") == "intersection", "REFUSED:DFCM_BOUND_OPERATOR")
    _require(
        set(bound.get("dimensions") or []) == EXPECTED_BOUND_DIMENSIONS,
        "REFUSED:DFCM_BOUND_DIMENSIONS",
    )

    authority = profile.get("authority") or {}
    _require(
        authority.get("exclusive_do_path") == "BRCE",
        "REFUSED:DFCM_DO_PATH",
    )
    for key in ("hooks_grant_authority", "plan_grants_authority", "proof_grants_authority"):
        _require(authority.get(key) is False, f"REFUSED:DFCM_AUTHORITY_DRIFT:{key}")

    selection = profile.get("selection") or {}
    for key in (
        "requires_preserved_frontier",
        "requires_bound",
        "requires_falsifier",
        "irreversible_requires_authority",
    ):
        _require(selection.get(key) is True, f"REFUSED:DFCM_SELECTION_DRIFT:{key}")
    _require(
        selection.get("failed_edge_invalidates_graph") is False,
        "REFUSED:DFCM_FAILED_EDGE_COLLAPSE",
    )

    extension = profile.get("extension") or {}
    _require(
        extension.get("order") == EXPECTED_EXTENSION_ORDER,
        "REFUSED:DFCM_EXTENSION_ORDER",
    )
    _require(
        extension.get("invent_only_after_public_falsifier") is True,
        "REFUSED:DFCM_INVENTION_WITHOUT_FALSIFIER",
    )

    public = profile.get("public_ontologies") or {}
    _require(
        REQUIRED_PUBLIC_ONTOLOGIES.issubset(public),
        "REFUSED:DFCM_PUBLIC_ONTOLOGY_BOUNDARY",
    )


def validate_all_capabilities(
    items: list[dict[str, Any]], profile: dict[str, Any]
) -> dict[str, Any]:
    validate_profile(profile)
    index = _index(items)

    # Global DfCM authority/reversibility laws.
    for item in items:
        cid = item["id"]
        if item["class"] == "DO":
            _require(item["broker_required"] is True, f"REFUSED:DFCM_DO_BROKER:{cid}")
            _require(item["receipt_required"] is True, f"REFUSED:DFCM_DO_RECEIPT:{cid}")
            if item["reversible"] is False:
                _require(
                    item["required_authority"]
                    in verify_capabilities.MUTATING_AUTHORITIES,
                    f"REFUSED:DFCM_IRREVERSIBLE_AUTHORITY:{cid}",
                )
        else:
            _require(
                item["reversible"] is True,
                f"REFUSED:DFCM_NON_DO_IRREVERSIBLE:{cid}",
            )

    fleet_payload = verify_capabilities.load(FLEET_CATALOG)
    fleet_ids = {
        item.get("id")
        for item in fleet_payload.get("capability", [])
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    _require(
        len(fleet_ids) == len(fleet_payload.get("capability", [])),
        "REFUSED:FLEET_CAPABILITY_IDENTITY",
    )
    missing_fleet = sorted(fleet_ids - set(index))
    _require(
        not missing_fleet,
        f"REFUSED:FLEET_CAPABILITY_MISSING:{','.join(missing_fleet)}",
    )
    fleet = {cid: index[cid] for cid in sorted(fleet_ids)}

    _require(
        all(item["standing"] == "CANDIDATE" for item in fleet.values()),
        "REFUSED:FLEET_CAPABILITY_SELF_STANDING",
    )

    fleet_select = [item for item in fleet.values() if item["class"] == "SELECT"]
    for item in fleet_select:
        cid = item["id"]
        _require(
            item["required_authority"] == "classify",
            f"REFUSED:DFCM_SELECT_AUTHORITY:{cid}",
        )
        _require(
            _contains_all(item["inputs"], {"preserved", "bounded", "falsifier"}),
            f"REFUSED:DFCM_SELECT_INPUTS:{cid}",
        )
        _require(
            {
                "REFUSED:PREMATURE_SELECTION",
                "REFUSED:FALSIFIER_MISSING",
                "REFUSED:UNBOUNDED_OPTION_GRAPH",
            }.issubset(set(item["refusals"])),
            f"REFUSED:DFCM_SELECT_REFUSALS:{cid}",
        )

    fleet_do = [item for item in fleet.values() if item["class"] == "DO"]
    for item in fleet_do:
        cid = item["id"]
        _require(
            "capability:broker-consequential-do" in item.get("depends_on", []),
            f"REFUSED:DFCM_FLEET_DO_BYPASSES_BRCE:{cid}",
        )
        _require(
            item["required_authority"] in verify_capabilities.MUTATING_AUTHORITIES,
            f"REFUSED:DFCM_FLEET_DO_AUTHORITY:{cid}",
        )

    missing = sorted(EPR_IDS - set(index))
    _require(not missing, f"REFUSED:EPR_CAPABILITY_MISSING:{','.join(missing)}")

    epr = {cid: index[cid] for cid in sorted(EPR_IDS)}

    # External supplier intake is observation/selection/construction only.
    _require(
        all(item["class"] != "DO" for item in epr.values()),
        "REFUSED:EPR_CONSEQUENTIAL_DO",
    )
    _require(
        all(item["standing"] == "CANDIDATE" for item in epr.values()),
        "REFUSED:EPR_SELF_STANDING",
    )
    _require(
        all(item["broker_required"] is False for item in epr.values()),
        "REFUSED:EPR_SPURIOUS_BROKER",
    )
    _require(
        all(item["reversible"] is True for item in epr.values()),
        "REFUSED:EPR_IRREVERSIBLE_INTAKE",
    )

    observe = epr["capability:observe-external-paradigm-subject"]
    _require(observe["class"] == "OBSERVE", "REFUSED:EPR_OBSERVE_CLASS")
    _require(observe["required_authority"] == "observe", "REFUSED:EPR_OBSERVE_AUTHORITY")
    _require(
        _contains_all(observe["inputs"], {"exact upstream SHA"}),
        "REFUSED:EPR_EXACT_SUBJECT_INPUT",
    )
    _require(
        {"REFUSED:MUTABLE_OR_INVALID_SHA", "REFUSED:SUPPLIER_SELF_STANDING"}
        .issubset(set(observe["refusals"])),
        "REFUSED:EPR_SUBJECT_FENCE",
    )

    extract = epr["capability:extract-external-paradigm-units"]
    _require(extract["class"] == "OBSERVE", "REFUSED:EPR_EXTRACT_CLASS")
    _require(
        observe["id"] in extract.get("depends_on", []),
        "REFUSED:EPR_EXTRACT_WITHOUT_EXACT_SUBJECT",
    )
    _require(
        _contains_all(extract["outputs"], {"exact upstream object identities"}),
        "REFUSED:EPR_OBJECT_IDENTITY_MISSING",
    )

    classify = epr["capability:classify-external-paradigm"]
    _require(classify["class"] == "SELECT", "REFUSED:EPR_CLASSIFY_CLASS")
    _require(
        classify["required_authority"] == "classify",
        "REFUSED:EPR_CLASSIFY_AUTHORITY",
    )
    _require(
        _contains_all(
            classify["inputs"],
            {
                "preserved candidate frontier",
                "bounded comparison dimensions",
                "explicit falsifier",
                "reuse -> compose -> extend -> invent",
            },
        ),
        "REFUSED:EPR_DFCM_SELECTION_INPUTS",
    )
    _require(
        {
            "REFUSED:PREMATURE_SELECTION",
            "REFUSED:UNBOUNDED_OPTION_GRAPH",
            "REFUSED:FALSIFIER_MISSING",
            "REFUSED:EXTENSION_ORDER_VIOLATION",
            "REFUSED:NOVELTY_WITHOUT_FALSIFIER",
            "REFUSED:CAPABILITY_AS_AUTHORITY",
        }.issubset(set(classify["refusals"])),
        "REFUSED:EPR_DFCM_SELECTION_REFUSALS",
    )

    project = epr["capability:project-external-paradigm-cross-product"]
    _require(project["class"] == "CONSTRUCT", "REFUSED:EPR_PROJECT_CLASS")
    _require(
        classify["id"] in project.get("depends_on", []),
        "REFUSED:EPR_PROJECT_WITHOUT_CLASSIFICATION",
    )
    _require(
        _contains_all(project["outputs"], {"PROV", "DCTERMS", "SKOS"}),
        "REFUSED:EPR_PUBLIC_ONTOLOGY_PROJECTION",
    )
    _require(
        {
            "REFUSED:INVENTORY_SELF_STANDING",
            "REFUSED:UNIT_STANDING",
        }.issubset(set(project["refusals"])),
        "REFUSED:EPR_PROJECTION_STANDING_FENCE",
    )

    delta = epr["capability:detect-external-paradigm-delta"]
    _require(delta["class"] == "OBSERVE", "REFUSED:EPR_DELTA_CLASS")
    _require(
        _contains_all(delta["inputs"], {"mutable discovery ref"}),
        "REFUSED:EPR_DELTA_DISCOVERY_REF",
    )
    _require(
        _contains_all(delta["outputs"], {"new exact candidate SHA"}),
        "REFUSED:EPR_DELTA_EXACT_SUBJECT",
    )

    return {
        "schema": "chatman.dfcm-capability-validation.v1",
        "capability_count": len(items),
        "epr_capability_count": len(epr),
        "epr_do_count": sum(1 for item in epr.values() if item["class"] == "DO"),
        "fleet_capability_count": len(fleet),
        "fleet_select_count": len(fleet_select),
        "fleet_do_count": len(fleet_do),
        "extension_order": EXPECTED_EXTENSION_ORDER,
        "standing": "NONE",
        "state": "ADMITTED_STRUCTURE",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--profile", type=pathlib.Path, default=DFCM)
    args = parser.parse_args()

    items = verify_capabilities.verify(verify_capabilities.load_default(ROOT))
    try:
        result = validate_all_capabilities(items, load_profile(args.profile))
    except (DfcmCapabilityError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        return 2

    print(
        "DFCM_CAPABILITIES_ALIVE "
        f"count={result['capability_count']} "
        f"epr={result['epr_capability_count']} "
        f"epr_do={result['epr_do_count']} "
        f"fleet={result['fleet_capability_count']} "
        f"fleet_select={result['fleet_select_count']} "
        f"fleet_do={result['fleet_do_count']} "
        "standing=NONE"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
