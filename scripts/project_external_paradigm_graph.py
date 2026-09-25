#!/usr/bin/env python3
"""Project external paradigm inventory into a bounded RDF candidate graph.

Projection establishes provenance and declared target edges only. It does not
assert semantic equivalence, admission, execution, authority, or standing.
"""

from __future__ import annotations

import argparse
import json
import tomllib
import urllib.parse
from pathlib import Path


PROV = "http://www.w3.org/ns/prov#"
DCTERMS = "http://purl.org/dc/terms/"
SKOS = "http://www.w3.org/2004/02/skos/core#"


class ProjectionRefusal(ValueError):
    """Typed refusal for malformed inventory or dangling target capabilities."""


def _literal(value: str) -> str:
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
        .replace("\r", "\\r")
    )
    return f'"{escaped}"'


def _iri(value: str) -> str:
    return f"<{value}>"


def _unit_iri(supplier: str, subject_sha: str, kind: str, name: str) -> str:
    encoded = urllib.parse.quote(name, safe="")
    return f"urn:chatman:external:{supplier}:{subject_sha}:{kind}:{encoded}"


def load_capability_ids(catalog_root: Path) -> set[str]:
    ids: set[str] = set()
    for path in sorted(catalog_root.glob("*.toml")):
        try:
            payload = tomllib.loads(path.read_text(encoding="utf-8"))
        except (tomllib.TOMLDecodeError, UnicodeDecodeError):
            continue
        capabilities = payload.get("capability")
        if not isinstance(capabilities, list):
            continue
        for capability in capabilities:
            if isinstance(capability, dict):
                cid = capability.get("id")
                if isinstance(cid, str) and cid:
                    ids.add(cid)
    return ids


def project_inventory(inventory: dict, capability_ids: set[str]) -> tuple[dict, str]:
    if inventory.get("schema") != "chatman.external-paradigm-inventory.v1":
        raise ProjectionRefusal("REFUSED:INVENTORY_SCHEMA")
    supplier = inventory.get("supplier")
    repository = inventory.get("repository")
    subject_sha = inventory.get("subject_sha")
    if not all(isinstance(v, str) and v for v in (supplier, repository, subject_sha)):
        raise ProjectionRefusal("REFUSED:INVENTORY_IDENTITY")
    if inventory.get("standing") != "NONE":
        raise ProjectionRefusal("REFUSED:INVENTORY_SELF_STANDING")

    subject_iri = f"urn:chatman:external-subject:{supplier}:{subject_sha}"
    edges = []
    unresolved = []
    lines = [
        f"@prefix prov: <{PROV}> .",
        f"@prefix dcterms: <{DCTERMS}> .",
        f"@prefix skos: <{SKOS}> .",
        "",
        f"{_iri(subject_iri)} a prov:Entity ;",
        f"  dcterms:identifier {_literal(subject_sha)} ;",
        f"  dcterms:source {_literal('https://github.com/' + repository)} .",
        "",
    ]

    dispositions: set[str] = set()

    for unit in inventory.get("units") or []:
        uid = unit.get("id")
        kind = unit.get("kind")
        name = unit.get("name")
        source_path = unit.get("source_path")
        state = unit.get("state")
        standing = unit.get("standing")
        if not all(isinstance(v, str) and v for v in (uid, kind, name, source_path)):
            raise ProjectionRefusal(f"REFUSED:MALFORMED_UNIT:{unit!r}")
        if state != "CANDIDATE" or standing != "NONE":
            raise ProjectionRefusal(f"REFUSED:UNIT_STANDING:{uid}")

        cls = unit.get("classification")
        target_capabilities = []
        disposition = None
        pattern_id = None
        if isinstance(cls, dict):
            disposition = cls.get("disposition")
            pattern_id = cls.get("pattern_id")
            target_capabilities = cls.get("target_capabilities") or []
            if not isinstance(target_capabilities, list):
                raise ProjectionRefusal(f"REFUSED:TARGET_CAPABILITIES:{uid}")

        unit_iri = _unit_iri(supplier, subject_sha, kind, name)
        source_url = (
            f"https://github.com/{repository}/blob/{subject_sha}/{source_path}"
        )

        lines.extend(
            [
                f"{_iri(unit_iri)} a prov:Entity ;",
                f"  dcterms:identifier {_literal(uid)} ;",
                f"  dcterms:type {_literal(kind)} ;",
                f"  dcterms:title {_literal(name)} ;",
                f"  dcterms:source {_literal(source_url)} ;",
                f"  prov:wasDerivedFrom {_iri(subject_iri)}",
            ]
        )

        if disposition:
            dispositions.add(disposition)
            lines[-1] += " ;"
            lines.append(
                f"  dcterms:subject {_iri('urn:chatman:disposition:' + disposition)}"
            )

        if pattern_id:
            lines[-1] += " ;"
            lines.append(f"  dcterms:relation {_literal(pattern_id)}")

        valid_targets = []
        for target in target_capabilities:
            if not isinstance(target, str) or not target:
                raise ProjectionRefusal(f"REFUSED:TARGET_CAPABILITY:{uid}")
            if target not in capability_ids:
                raise ProjectionRefusal(
                    f"REFUSED:DANGLING_TARGET_CAPABILITY:{uid}:{target}"
                )
            valid_targets.append(target)
            edges.append(
                {
                    "external_unit": uid,
                    "pattern_id": pattern_id,
                    "disposition": disposition,
                    "target_capability": target,
                    "relation": "DECLARED_TARGET",
                    "semantic_equivalence": "UNCLAIMED",
                }
            )

        for target in valid_targets:
            lines[-1] += " ;"
            lines.append(
                f"  dcterms:relation {_iri('urn:chatman:capability:' + urllib.parse.quote(target, safe=''))}"
            )

        lines[-1] += " ."
        lines.append("")

        if not valid_targets:
            unresolved.append(
                {
                    "external_unit": uid,
                    "pattern_id": pattern_id,
                    "disposition": disposition,
                    "reason": "NO_DECLARED_INTERNAL_CAPABILITY_TARGET",
                }
            )

    for disposition in sorted(dispositions):
        concept_iri = f"urn:chatman:disposition:{disposition}"
        lines.extend(
            [
                f"{_iri(concept_iri)} a skos:Concept ;",
                f"  skos:prefLabel {_literal(disposition)} .",
                "",
            ]
        )

    result = {
        "schema": "chatman.external-paradigm-cross-product.v1",
        "supplier": supplier,
        "subject_sha": subject_sha,
        "state": "CANDIDATE",
        "standing": "NONE",
        "relation_semantics": {
            "DECLARED_TARGET": "integration target only; semantic equivalence is unclaimed"
        },
        "edge_count": len(edges),
        "unresolved_count": len(unresolved),
        "edges": sorted(
            edges,
            key=lambda row: (
                row["external_unit"],
                row["target_capability"],
            ),
        ),
        "unresolved": sorted(
            unresolved,
            key=lambda row: row["external_unit"],
        ),
    }
    return result, "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--inventory", required=True)
    parser.add_argument("--cross-product-out", required=True)
    parser.add_argument("--ttl-out", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    inventory = json.loads(Path(args.inventory).read_text(encoding="utf-8"))
    capability_ids = load_capability_ids(root / "catalog")
    try:
        cross_product, ttl = project_inventory(inventory, capability_ids)
    except ProjectionRefusal as exc:
        print(json.dumps({"state": "REFUSED", "reason": str(exc)}, sort_keys=True))
        return 2

    Path(args.cross_product_out).write_text(
        json.dumps(cross_product, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    Path(args.ttl_out).write_text(ttl + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "state": "CANDIDATE",
                "standing": "NONE",
                "edges": cross_product["edge_count"],
                "unresolved": cross_product["unresolved_count"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
