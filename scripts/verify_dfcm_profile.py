#!/usr/bin/env python3
"""Verify the canonical DfCM public-ontology application profile.

This verifier proves profile identity and declared invariants only. It does not
execute SHACL, grant authority, perform BRCE DO, or promote ALIVE standing.
"""
from __future__ import annotations

import pathlib
import re
import sys
import tomllib

ROOT = pathlib.Path(__file__).resolve().parents[1]
CATALOG = ROOT / "catalog" / "dfcm.toml"
ONTOLOGY = ROOT / "ontology" / "dfcm.ttl"
SHAPES = ROOT / "ontology" / "dfcm.shacl.ttl"

EXPECTED_PUBLIC = {
    "prov": "http://www.w3.org/ns/prov#",
    "pplan": "http://purl.org/net/p-plan#",
    "sh": "http://www.w3.org/ns/shacl#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "org": "http://www.w3.org/ns/org#",
    "sosa": "http://www.w3.org/ns/sosa/",
    "earl": "http://www.w3.org/ns/earl#",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "time": "http://www.w3.org/2006/time#",
    "dcat": "http://www.w3.org/ns/dcat#",
    "dcterms": "http://purl.org/dc/terms/",
    "dqv": "http://www.w3.org/ns/dqv#",
    "qudt": "http://qudt.org/schema/qudt/",
    "spdx": "http://spdx.org/rdf/terms#",
}
BOUND_DIMENSIONS = ["ontology", "capability", "authority", "cost", "evidence", "consequence"]
STANDINGS = ["UNKNOWN", "PARTIAL_ALIVE", "ALIVE", "BLOCKED", "BUILD_BROKEN", "UNSUPPORTED", "REFUSED"]
STAGES = ["PRESERVE", "FENCE", "CALCULUS", "EXCLUSIONS", "FALSIFIER", "EXTENSION", "OPERATIONALIZE"]


class DfCMProfileError(RuntimeError):
    pass


def _prefixes(text: str) -> dict[str, str]:
    return dict(re.findall(r"^@prefix\s+([A-Za-z][\w-]*):\s+<([^>]+)>\s*\.\s*$", text, re.MULTILINE))


def verify(catalog: dict, ontology: str, shapes: str) -> None:
    if catalog.get("schema") != "chatman.dfcm-profile.v1" or catalog.get("canonical") is not True:
        raise DfCMProfileError("REFUSED:DFCM_CANONICAL_IDENTITY")

    if catalog.get("objective", {}).get("stages") != STAGES:
        raise DfCMProfileError("REFUSED:DFCM_SOLVE_ORDER")
    if catalog.get("bound", {}).get("operator") != "intersection":
        raise DfCMProfileError("REFUSED:DFCM_BOUND_OPERATOR")
    if catalog.get("bound", {}).get("dimensions") != BOUND_DIMENSIONS:
        raise DfCMProfileError("REFUSED:DFCM_BOUND_DIMENSIONS")
    if catalog.get("standing", {}).get("values") != STANDINGS:
        raise DfCMProfileError("REFUSED:DFCM_STANDING_VOCABULARY")

    selection = catalog.get("selection", {})
    required_selection = {
        "requires_preserved_frontier": True,
        "requires_bound": True,
        "requires_falsifier": True,
        "irreversible_requires_authority": True,
        "failed_edge_invalidates_graph": False,
    }
    for key, expected in required_selection.items():
        if selection.get(key) is not expected:
            raise DfCMProfileError(f"REFUSED:DFCM_SELECTION_LAW:{key}")

    authority = catalog.get("authority", {})
    if authority.get("exclusive_do_path") != "BRCE":
        raise DfCMProfileError("REFUSED:DFCM_DO_PATH")
    for key in ("hooks_grant_authority", "plan_grants_authority", "proof_grants_authority"):
        if authority.get(key) is not False:
            raise DfCMProfileError(f"REFUSED:DFCM_AUTHORITY_CONFLATION:{key}")

    public = catalog.get("public_ontologies", {})
    if public != EXPECTED_PUBLIC:
        raise DfCMProfileError("REFUSED:DFCM_PUBLIC_ONTOLOGY_DRIFT")

    ontology_prefixes = _prefixes(ontology)
    for prefix, iri in EXPECTED_PUBLIC.items():
        if ontology_prefixes.get(prefix) != iri:
            raise DfCMProfileError(f"REFUSED:DFCM_PREFIX_DRIFT:{prefix}")

    custom = catalog.get("custom_remainder", {})
    for term in custom.get("classes", []) + custom.get("properties", []):
        if f"dfcm:{term}" not in ontology:
            raise DfCMProfileError(f"REFUSED:DFCM_TERM_MISSING:{term}")

    # Public vocabularies may be referenced but never defined by this profile.
    for prefix in EXPECTED_PUBLIC:
        if re.search(rf"^(?:{prefix}):[^\s]+\s+a\s+", ontology, re.MULTILINE):
            raise DfCMProfileError(f"REFUSED:PUBLIC_ONTOLOGY_REDEFINED:{prefix}")

    required_phrases = (
        "Plan != execution and capability != authority",
        "One failed edge is topology, not graph failure",
        "BRCE is the exclusive consequential DO path",
        "SHACL conformance is admission evidence, never ALIVE by itself",
    )
    for phrase in required_phrases:
        if phrase not in ontology:
            raise DfCMProfileError(f"REFUSED:DFCM_LAW_MISSING:{phrase}")

    shape_prefixes = _prefixes(shapes)
    for prefix in ("dfcm", "sh", "odrl", "prov"):
        expected = ontology_prefixes.get(prefix)
        if shape_prefixes.get(prefix) != expected:
            raise DfCMProfileError(f"REFUSED:DFCM_SHAPE_PREFIX_DRIFT:{prefix}")
    for shape in ("DecisionPointShape", "OptionShape", "SelectionShape", "StandingAssessmentShape"):
        if f"dfcm:{shape} a sh:NodeShape" not in shapes:
            raise DfCMProfileError(f"REFUSED:DFCM_SHAPE_MISSING:{shape}")
    if "sh:path dfcm:authorityPolicy" not in shapes or "sh:class odrl:Policy" not in shapes:
        raise DfCMProfileError("REFUSED:DFCM_IRREVERSIBLE_AUTHORITY_SHAPE")
    if "sh:path dfcm:hasFalsifier ; sh:minCount 1" not in shapes:
        raise DfCMProfileError("REFUSED:DFCM_FALSIFIER_SHAPE")
    if "this shape cannot promote standing" not in shapes:
        raise DfCMProfileError("REFUSED:DFCM_ADMISSION_STANDING_CONFLATION")


def main() -> int:
    with CATALOG.open("rb") as handle:
        catalog = tomllib.load(handle)
    verify(
        catalog,
        ONTOLOGY.read_text(encoding="utf-8"),
        SHAPES.read_text(encoding="utf-8"),
    )
    print("DFCM_PROFILE_ALIVE identity=canonical public=14 custom=thin shacl_execution=false do=false standing_promotion=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (DfCMProfileError, OSError, tomllib.TOMLDecodeError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
