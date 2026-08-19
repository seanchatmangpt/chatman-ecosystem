#!/usr/bin/env python3
"""Verify the public/custom capability ontology boundary without claiming SHACL execution."""
from __future__ import annotations

import pathlib
import re
import sys

EXPECTED_PREFIXES = {
    "ce": "https://seanchatmangpt.github.io/chatman-ecosystem/ontology/capabilities#",
    "prov": "http://www.w3.org/ns/prov#",
    "dcterms": "http://purl.org/dc/terms/",
    "skos": "http://www.w3.org/2004/02/skos/core#",
    "odrl": "http://www.w3.org/ns/odrl/2/",
    "sh": "http://www.w3.org/ns/shacl#",
    "xsd": "http://www.w3.org/2001/XMLSchema#",
    "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
    "owl": "http://www.w3.org/2002/07/owl#",
}
REQUIRED_CUSTOM_TERMS = {
    "ce:Capability",
    "ce:CapabilityClass",
    "ce:Planner",
    "ce:Policy",
    "ce:Role",
    "ce:Agent",
    "ce:AuthorityGrant",
    "ce:BrokeredConsequentialExecution",
    "ce:CapabilityOwnership",
    "ce:LiveAzureAuthorityFence",
    "ce:CLI",
    "ce:API",
    "ce:MCP",
    "ce:A2A",
    "ce:requiredAuthority",
    "ce:brokerRequired",
    "ce:receiptRequired",
    "ce:executionOwner",
    "ce:sourceRepository",
    "ce:CapabilityShape",
    "ce:DoShape",
}


class OntologyError(RuntimeError):
    pass


def verify_text(text: str) -> None:
    prefixes = dict(
        re.findall(r"^@prefix\s+([A-Za-z][\w-]*):\s+<([^>]+)>\s*\.\s*$", text, re.MULTILINE)
    )
    for prefix, iri in EXPECTED_PREFIXES.items():
        if prefixes.get(prefix) != iri:
            raise OntologyError(f"REFUSED:ONTOLOGY_PREFIX_DRIFT:{prefix}")

    for term in sorted(REQUIRED_CUSTOM_TERMS):
        if term not in text:
            raise OntologyError(f"REFUSED:ONTOLOGY_TERM_MISSING:{term}")

    if "ce:Capability a owl:Class" not in text or "rdfs:subClassOf prov:Plan" not in text:
        raise OntologyError("REFUSED:CAPABILITY_PROV_ALIGNMENT")
    if "ce:Policy a owl:Class ; rdfs:subClassOf odrl:Policy" not in text:
        raise OntologyError("REFUSED:POLICY_ODRL_ALIGNMENT")
    if "ce:Agent a owl:Class ; rdfs:subClassOf prov:Agent" not in text:
        raise OntologyError("REFUSED:AGENT_PROV_ALIGNMENT")
    if "ce:AuthorityPolicy a odrl:Policy" not in text:
        raise OntologyError("REFUSED:AUTHORITY_ODRL_ALIGNMENT")
    if "ce:CapabilityShape a sh:NodeShape" not in text:
        raise OntologyError("REFUSED:SHACL_SHAPE_DECLARATION_MISSING")
    if "sh:path ce:interface ; sh:minCount 4" not in text:
        raise OntologyError("REFUSED:ONTOLOGY_SURFACE_CLOSURE")

    # Public vocabularies are imports/alignment authorities. The local namespace
    # may reference them but must not define their terms as subjects.
    for prefix in ("prov", "dcterms", "skos", "odrl", "sh"):
        if re.search(rf"^(?:{prefix}):[^\s]+\s+a\s+", text, re.MULTILINE):
            raise OntologyError(f"REFUSED:PUBLIC_ONTOLOGY_REDEFINED:{prefix}")

    required_phrases = (
        "Capability does not imply authority",
        "Planner != Policy != Role != Agent != Authority",
        "exclusive consequential DO transition",
        "BLOCKED until a named allowlisted live-Azure authority",
    )
    for phrase in required_phrases:
        if phrase not in text:
            raise OntologyError(f"REFUSED:ONTOLOGY_LAW_MISSING:{phrase}")


def main() -> int:
    path = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path("ontology/capabilities.ttl")
    verify_text(path.read_text(encoding="utf-8"))
    print("CAPABILITY_ONTOLOGY_BOUNDARY_ALIVE public=5 custom=remainder shacl_execution=false")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OntologyError, OSError) as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(1)
