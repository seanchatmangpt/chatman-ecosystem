#!/usr/bin/env python3
"""Render the canonical capability catalogs as a deterministic RDF/Turtle projection."""
from __future__ import annotations

import importlib.util
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "verify_capabilities", ROOT / "scripts" / "verify_capabilities.py"
)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError("REFUSED:CAPABILITY_VERIFIER_UNAVAILABLE")
verify_capabilities = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(verify_capabilities)

CLASS_TERM = {
    "OBSERVE": "ce:Observe",
    "SELECT": "ce:Select",
    "CONSTRUCT": "ce:Construct",
    "DO": "ce:Do",
}
INTERFACE_TERM = {
    "cli": "ce:CLI",
    "api": "ce:API",
    "mcp": "ce:MCP",
    "a2a": "ce:A2A",
}


def literal(value: str) -> str:
    return '"' + value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n") + '"'


def term(capability_id: str) -> str:
    suffix = capability_id.removeprefix("capability:")
    if not re.fullmatch(r"[a-z0-9_-]+", suffix):
        raise ValueError(f"REFUSED:RDF_CAPABILITY_ID:{capability_id}")
    return f"ce:capability-{suffix}"


def render(items: list[dict]) -> str:
    lines = [
        "@prefix ce: <https://seanchatmangpt.github.io/chatman-ecosystem/ontology/capabilities#> .",
        "@prefix dcterms: <http://purl.org/dc/terms/> .",
        "@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .",
        "",
        "# Generated from catalog/capabilities*.toml. Do not edit as source authority.",
        "",
    ]
    for item in items:
        subject = term(item["id"])
        interfaces = ", ".join(INTERFACE_TERM[value] for value in sorted(item["interfaces"]))
        lines.extend([
            f"{subject} a ce:Capability ;",
            f"    dcterms:identifier {literal(item['id'])} ;",
            f"    dcterms:title {literal(item['title'])} ;",
            f"    ce:capabilityClass {CLASS_TERM[item['class']]} ;",
            f"    ce:executionOwner {literal(item['owner'])} ;",
            f"    ce:requiredAuthority {literal(item['required_authority'])} ;",
            f"    ce:brokerRequired {str(item['broker_required']).lower()} ;",
            f"    ce:receiptRequired {str(item['receipt_required']).lower()} ;",
            f"    ce:reversible {str(item['reversible']).lower()} ;",
            f"    ce:standing {literal(item['standing'])} ;",
            f"    ce:interface {interfaces}" + (" ;" if item.get("depends_on") or item.get("source_repositories") or item.get("refusals") else " ."),
        ])
        if item.get("depends_on"):
            deps = ", ".join(term(dep) for dep in sorted(item["depends_on"]))
            lines.append(f"    ce:dependsOn {deps}" + (" ;" if item.get("source_repositories") or item.get("refusals") else " ."))
        if item.get("source_repositories"):
            values = ", ".join(literal(value) for value in sorted(item["source_repositories"]))
            lines.append(f"    ce:sourceRepository {values}" + (" ;" if item.get("refusals") else " ."))
        refusals = item.get("refusals", [])
        if refusals:
            values = ", ".join(literal(value) for value in sorted(refusals))
            lines.append(f"    ce:refusal {values} .")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    items = verify_capabilities.verify(verify_capabilities.load_default(ROOT))
    repositories = verify_capabilities.load(ROOT / "catalog" / "repositories.toml")
    verify_capabilities.verify_repository_owners(items, repositories)
    output = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else None
    text = render(items)
    if output is None:
        sys.stdout.write(text)
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8")
        print(f"CAPABILITY_RDF_RENDERED count={len(items)} path={output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
