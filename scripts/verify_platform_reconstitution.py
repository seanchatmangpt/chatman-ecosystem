#!/usr/bin/env python3
"""Fail-closed structural and standing verifier for the platform reconstitution benchmark."""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

try:
    import tomllib
except ModuleNotFoundError as exc:  # pragma: no cover
    raise SystemExit("REFUSED:PYTHON_3_11_REQUIRED") from exc

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_BENCHMARK = ROOT / "benchmarks" / "platform-reconstitution" / "v1" / "benchmark.toml"

SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ALLOWED_STANDING = {
    "UNKNOWN",
    "PARTIAL_ALIVE",
    "ALIVE",
    "BLOCKED",
    "BUILD_BROKEN",
    "UNSUPPORTED",
}

REQUIRED_PACKS = {
    "dfcm-full-deployment-pack",
    "domain-capability-pack",
    "fortune5-deployment-blocks-pack",
    "ggen-combinatorial-maximalism-pack",
    "mfact-pack",
    "mfw-pack",
    "praxis-core-pack",
    "shacl-projection-pack",
    "standing-ladder-pack",
}
REQUIRED_PROJECTIONS = {
    "application-source",
    "api",
    "cli",
    "mcp",
    "a2a",
    "ui",
    "data-schema",
    "database",
    "infrastructure",
    "policy",
    "tests",
    "documentation",
    "sbom",
    "receipt",
    "replay",
}
REQUIRED_SUBSTRATES = {
    "local",
    "kubernetes",
    "aws",
    "azure",
    "gcp",
    "wasm-edge",
    "airgap",
}
REQUIRED_NEGATIVE_CONTROLS = {
    "ambient-do-refused",
    "direct-mcp-mutation-refused",
    "unauthorized-actuation-refused",
    "projection-loss-recoverable",
    "stale-subject-refused",
}
REQUIRED_INTERFACES = {"cli", "api", "mcp", "a2a"}
REQUIRED_ONTOLOGY_SOURCES = {"public", "custom"}
REQUIRED_TOOLCHAIN_ROLES = {
    "public-ontology",
    "config-admission",
    "manufacture",
    "formal-proof",
    "orchestration",
    "actuation",
    "process-execution",
    "provenance",
}
REQUIRED_RECONSTITUTION_PRESERVE = {
    "admitted-graph",
    "manufacturing-rules",
    "toolchain-identities",
    "policies",
    "proof-obligations",
    "historical-receipts",
}


@dataclass(frozen=True)
class Finding:
    code: str
    detail: str

    def render(self) -> str:
        return f"REFUSED:{self.code}:{self.detail}"


def load_toml(path: Path) -> dict[str, Any]:
    try:
        payload = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise SystemExit(f"REFUSED:BENCHMARK_INPUT_MISSING:{path}") from exc
    except (OSError, UnicodeError, tomllib.TOMLDecodeError) as exc:
        raise SystemExit(f"REFUSED:BENCHMARK_INPUT_INVALID:{path}:{exc}") from exc
    if not isinstance(payload, dict):
        raise SystemExit(f"REFUSED:BENCHMARK_INPUT_NOT_TABLE:{path}")
    return payload


def _table(data: dict[str, Any], name: str, findings: list[Finding]) -> dict[str, Any]:
    value = data.get(name)
    if not isinstance(value, dict):
        findings.append(Finding("BENCHMARK_TABLE_MISSING", name))
        return {}
    return value


def _string_set(table: dict[str, Any], key: str, findings: list[Finding]) -> set[str]:
    value = table.get(key)
    if not isinstance(value, list) or any(not isinstance(item, str) or not item for item in value):
        findings.append(Finding("BENCHMARK_STRING_LIST_INVALID", key))
        return set()
    if len(value) != len(set(value)):
        findings.append(Finding("BENCHMARK_DUPLICATE_VALUE", key))
    return set(value)


def _require_superset(actual: set[str], required: set[str], code: str, label: str, findings: list[Finding]) -> None:
    missing = sorted(required - actual)
    if missing:
        findings.append(Finding(code, f"{label}={','.join(missing)}"))


def validate_benchmark(data: dict[str, Any], scenario: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    benchmark = _table(data, "benchmark", findings)
    marketplace = _table(data, "marketplace", findings)
    toolchain = _table(data, "toolchain", findings)
    calculus = _table(data, "calculus", findings)
    coverage = _table(data, "coverage", findings)
    scenario_table = _table(scenario, "scenario", findings)
    reconstitution = _table(scenario, "reconstitution", findings)

    benchmark_id = benchmark.get("id")
    if benchmark_id != "platform-reconstitution-v1":
        findings.append(Finding("BENCHMARK_IDENTITY_INVALID", str(benchmark_id)))
    if benchmark.get("version") != "1.0.0":
        findings.append(Finding("BENCHMARK_VERSION_INVALID", str(benchmark.get("version"))))

    standing = benchmark.get("standing")
    if standing not in ALLOWED_STANDING:
        findings.append(Finding("BENCHMARK_STANDING_INVALID", str(standing)))

    repository = marketplace.get("repository")
    if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
        findings.append(Finding("BENCHMARK_REPOSITORY_INVALID", str(repository)))
    sha = marketplace.get("sha")
    if not isinstance(sha, str) or not SHA40.fullmatch(sha):
        findings.append(Finding("BENCHMARK_SHA_INVALID", str(sha)))
    if marketplace.get("ref") != "main":
        findings.append(Finding("BENCHMARK_MARKETPLACE_REF_INVALID", str(marketplace.get("ref"))))

    packs = _string_set(marketplace, "required_packs", findings)
    _require_superset(packs, REQUIRED_PACKS, "BENCHMARK_PACK_CLOSURE_MISSING", "packs", findings)

    if toolchain.get("release_manifest") != "release/v26.9.1/manifest.toml":
        findings.append(Finding("BENCHMARK_TOOLCHAIN_MANIFEST_INVALID", str(toolchain.get("release_manifest"))))
    components = toolchain.get("components")
    toolchain_by_role: dict[str, dict[str, Any]] = {}
    if not isinstance(components, list):
        findings.append(Finding("BENCHMARK_TOOLCHAIN_COMPONENTS_INVALID", "toolchain.components"))
        components = []
    seen_ids: set[str] = set()
    for component in components:
        if not isinstance(component, dict):
            findings.append(Finding("BENCHMARK_TOOLCHAIN_COMPONENT_INVALID", str(component)))
            continue
        component_id = component.get("id")
        role = component.get("role")
        repository = component.get("repository")
        component_sha = component.get("sha")
        ref = component.get("ref")
        if not isinstance(component_id, str) or not component_id:
            findings.append(Finding("BENCHMARK_TOOLCHAIN_ID_INVALID", str(component_id)))
        elif component_id in seen_ids:
            findings.append(Finding("BENCHMARK_TOOLCHAIN_DUPLICATE_ID", component_id))
        else:
            seen_ids.add(component_id)
        if not isinstance(role, str) or not role:
            findings.append(Finding("BENCHMARK_TOOLCHAIN_ROLE_INVALID", str(role)))
        elif role in toolchain_by_role:
            findings.append(Finding("BENCHMARK_TOOLCHAIN_DUPLICATE_ROLE", role))
        else:
            toolchain_by_role[role] = component
        if not isinstance(repository, str) or not REPOSITORY.fullmatch(repository):
            findings.append(Finding("BENCHMARK_TOOLCHAIN_REPOSITORY_INVALID", f"{component_id}:{repository}"))
        if not isinstance(component_sha, str) or not SHA40.fullmatch(component_sha):
            findings.append(Finding("BENCHMARK_TOOLCHAIN_SHA_INVALID", f"{component_id}:{component_sha}"))
        if not isinstance(ref, str) or not ref:
            findings.append(Finding("BENCHMARK_TOOLCHAIN_REF_INVALID", f"{component_id}:{ref}"))
    missing_roles = sorted(REQUIRED_TOOLCHAIN_ROLES - set(toolchain_by_role))
    if missing_roles:
        findings.append(Finding("BENCHMARK_TOOLCHAIN_ROLE_MISSING", ",".join(missing_roles)))

    required_calculus = {
        "canonical_semantics": "admitted_graph",
        "select_path": "candidate_graph",
        "construct_path": "ggen",
        "do_path": "BRCE",
        "ambient_do": False,
        "hooks_actuate": False,
        "planner_actuate": False,
        "receipt_required": True,
        "replay_required": True,
        "exact_subject_required": True,
    }
    for key, expected in required_calculus.items():
        if calculus.get(key) != expected:
            findings.append(Finding("BENCHMARK_CALCULUS_VIOLATION", f"{key}={calculus.get(key)!r},expected={expected!r}"))

    ontology_sources = _string_set(coverage, "ontology_sources", findings)
    projections = _string_set(coverage, "projection_classes", findings)
    substrates = _string_set(coverage, "substrates", findings)
    negative_controls = _string_set(coverage, "negative_controls", findings)
    _require_superset(ontology_sources, REQUIRED_ONTOLOGY_SOURCES, "BENCHMARK_ONTOLOGY_SOURCE_MISSING", "ontology_sources", findings)
    _require_superset(projections, REQUIRED_PROJECTIONS, "BENCHMARK_PROJECTION_CLOSURE_MISSING", "projections", findings)
    _require_superset(substrates, REQUIRED_SUBSTRATES, "BENCHMARK_SUBSTRATE_CLOSURE_MISSING", "substrates", findings)
    _require_superset(
        negative_controls,
        REQUIRED_NEGATIVE_CONTROLS,
        "BENCHMARK_NEGATIVE_CONTROL_MISSING",
        "controls",
        findings,
    )

    if scenario_table.get("id") != "regulated-claims":
        findings.append(Finding("BENCHMARK_SCENARIO_IDENTITY_INVALID", str(scenario_table.get("id"))))
    if scenario_table.get("canonical_semantics") != "admitted_graph":
        findings.append(Finding("BENCHMARK_SCENARIO_SEMANTIC_SOURCE_INVALID", str(scenario_table.get("canonical_semantics"))))
    if scenario_table.get("projection_is_source") is not False:
        findings.append(Finding("BENCHMARK_PROJECTION_OWNS_MEANING", str(scenario_table.get("projection_is_source"))))
    if scenario_table.get("pii_region_bound") is not True:
        findings.append(Finding("BENCHMARK_PII_REGION_BOUNDARY_MISSING", "pii_region_bound"))
    if scenario_table.get("consequential_do_requires_authority") is not True:
        findings.append(Finding("BENCHMARK_AUTHORITY_BOUNDARY_MISSING", "consequential_do_requires_authority"))

    interfaces = _string_set(scenario_table, "interfaces", findings)
    _require_superset(interfaces, REQUIRED_INTERFACES, "BENCHMARK_INTERFACE_CLOSURE_MISSING", "interfaces", findings)

    delete_classes = _string_set(reconstitution, "delete_projection_classes", findings)
    required_delete = REQUIRED_PROJECTIONS - {"receipt", "replay"}
    _require_superset(
        delete_classes,
        required_delete,
        "BENCHMARK_RECONSTITUTION_DELETE_SET_INCOMPLETE",
        "delete_projection_classes",
        findings,
    )
    preserve = _string_set(reconstitution, "preserve", findings)
    _require_superset(
        preserve,
        REQUIRED_RECONSTITUTION_PRESERVE,
        "BENCHMARK_RECONSTITUTION_SOURCE_INCOMPLETE",
        "preserve",
        findings,
    )
    if reconstitution.get("require_semantic_equivalence") is not True:
        findings.append(Finding("BENCHMARK_SEMANTIC_EQUIVALENCE_NOT_REQUIRED", "require_semantic_equivalence"))
    if reconstitution.get("require_new_subject_standing") is not True:
        findings.append(Finding("BENCHMARK_NEW_SUBJECT_STANDING_NOT_REQUIRED", "require_new_subject_standing"))

    evidence = data.get("evidence")
    if standing == "ALIVE":
        if not isinstance(evidence, dict):
            findings.append(Finding("BENCHMARK_ALIVE_EVIDENCE_MISSING", "evidence"))
        else:
            if evidence.get("executed_marketplace_sha") != sha:
                findings.append(
                    Finding(
                        "BENCHMARK_EXACT_SUBJECT_MISMATCH",
                        f"executed={evidence.get('executed_marketplace_sha')},admitted={sha}",
                    )
                )
            executed_toolchain = evidence.get("executed_toolchain")
            if not isinstance(executed_toolchain, dict):
                findings.append(Finding("BENCHMARK_EXECUTED_TOOLCHAIN_MISSING", "evidence.executed_toolchain"))
            else:
                for role in sorted(REQUIRED_TOOLCHAIN_ROLES):
                    component = toolchain_by_role.get(role)
                    admitted_sha = component.get("sha") if isinstance(component, dict) else None
                    executed_sha = executed_toolchain.get(role)
                    if executed_sha != admitted_sha:
                        findings.append(
                            Finding(
                                "BENCHMARK_TOOLCHAIN_SUBJECT_MISMATCH",
                                f"role={role},executed={executed_sha},admitted={admitted_sha}",
                            )
                        )
            original_subject = evidence.get("original_subject_id")
            reconstituted_subject = evidence.get("reconstituted_subject_id")
            if not isinstance(original_subject, str) or not original_subject.strip():
                findings.append(Finding("BENCHMARK_ORIGINAL_SUBJECT_MISSING", "original_subject_id"))
            if not isinstance(reconstituted_subject, str) or not reconstituted_subject.strip():
                findings.append(Finding("BENCHMARK_RECONSTITUTED_SUBJECT_MISSING", "reconstituted_subject_id"))
            if isinstance(original_subject, str) and isinstance(reconstituted_subject, str) and original_subject == reconstituted_subject:
                findings.append(Finding("BENCHMARK_RECONSTITUTED_SUBJECT_NOT_NEW", original_subject))
            for key in ("execution_receipt", "reconstitution_receipt", "replay_receipt"):
                value = evidence.get(key)
                if not isinstance(value, str) or not value.strip():
                    findings.append(Finding("BENCHMARK_ALIVE_RECEIPT_MISSING", key))
            for key in ("projection_set_digest_before", "projection_set_digest_after", "semantic_digest_before", "semantic_digest_after"):
                value = evidence.get(key)
                if not isinstance(value, str) or not DIGEST.fullmatch(value):
                    findings.append(Finding("BENCHMARK_ALIVE_DIGEST_INVALID", f"{key}={value}"))
            projection_before = evidence.get("projection_set_digest_before")
            projection_after = evidence.get("projection_set_digest_after")
            if isinstance(projection_before, str) and isinstance(projection_after, str) and DIGEST.fullmatch(projection_before) and DIGEST.fullmatch(projection_after) and projection_before != projection_after:
                findings.append(Finding("BENCHMARK_RECONSTITUTION_DIGEST_MISMATCH", f"before={projection_before},after={projection_after}"))
            semantic_before = evidence.get("semantic_digest_before")
            semantic_after = evidence.get("semantic_digest_after")
            if isinstance(semantic_before, str) and isinstance(semantic_after, str) and DIGEST.fullmatch(semantic_before) and DIGEST.fullmatch(semantic_after) and semantic_before != semantic_after:
                findings.append(Finding("BENCHMARK_SEMANTIC_DIGEST_MISMATCH", f"before={semantic_before},after={semantic_after}"))
            verified_ontology_sources = _string_set(evidence, "verified_ontology_sources", findings)
            verified_projections = _string_set(evidence, "verified_projections", findings)
            verified_substrates = _string_set(evidence, "verified_substrates", findings)
            verified_negative_controls = _string_set(evidence, "verified_negative_controls", findings)
            _require_superset(
                verified_ontology_sources,
                REQUIRED_ONTOLOGY_SOURCES,
                "BENCHMARK_ALIVE_ONTOLOGY_EVIDENCE_INCOMPLETE",
                "verified_ontology_sources",
                findings,
            )
            _require_superset(
                verified_projections,
                REQUIRED_PROJECTIONS,
                "BENCHMARK_ALIVE_PROJECTION_EVIDENCE_INCOMPLETE",
                "verified_projections",
                findings,
            )
            _require_superset(
                verified_substrates,
                REQUIRED_SUBSTRATES,
                "BENCHMARK_ALIVE_SUBSTRATE_EVIDENCE_INCOMPLETE",
                "verified_substrates",
                findings,
            )
            _require_superset(
                verified_negative_controls,
                REQUIRED_NEGATIVE_CONTROLS,
                "BENCHMARK_ALIVE_NEGATIVE_CONTROL_EVIDENCE_INCOMPLETE",
                "verified_negative_controls",
                findings,
            )
    elif isinstance(evidence, dict) and evidence.get("executed_marketplace_sha") not in (None, "", sha):
        findings.append(
            Finding(
                "BENCHMARK_EXACT_SUBJECT_MISMATCH",
                f"executed={evidence.get('executed_marketplace_sha')},admitted={sha}",
            )
        )

    return findings


def resolve_scenario(benchmark_path: Path, data: dict[str, Any]) -> Path:
    benchmark = data.get("benchmark")
    raw = benchmark.get("scenario") if isinstance(benchmark, dict) else None
    if not isinstance(raw, str) or not raw:
        raise SystemExit("REFUSED:BENCHMARK_SCENARIO_PATH_MISSING:benchmark.scenario")
    candidate = (ROOT / raw).resolve()
    root = ROOT.resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise SystemExit(f"REFUSED:BENCHMARK_SCENARIO_PATH_ESCAPE:{raw}") from exc
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--benchmark", type=Path, default=DEFAULT_BENCHMARK)
    parser.add_argument("--require-alive", action="store_true")
    args = parser.parse_args(argv)

    benchmark_path = args.benchmark
    if not benchmark_path.is_absolute():
        benchmark_path = (ROOT / benchmark_path).resolve()
    data = load_toml(benchmark_path)
    scenario_path = resolve_scenario(benchmark_path, data)
    scenario = load_toml(scenario_path)
    findings = validate_benchmark(data, scenario)

    standing = data.get("benchmark", {}).get("standing", "UNKNOWN") if isinstance(data.get("benchmark"), dict) else "UNKNOWN"
    if args.require_alive and standing != "ALIVE":
        findings.append(Finding("BENCHMARK_NOT_ALIVE", str(standing)))

    if findings:
        for finding in findings:
            print(finding.render())
        return 2

    marketplace = data["marketplace"]
    print(f"PLATFORM_RECONSTITUTION={standing}")
    print(f"BENCHMARK={data['benchmark']['id']}@{data['benchmark']['version']}")
    print(f"MARKETPLACE_SUBJECT={marketplace['repository']}@{marketplace['sha']}")
    print(f"ONTOLOGY_SOURCES={len(set(data['coverage']['ontology_sources']))}/{len(REQUIRED_ONTOLOGY_SOURCES)}")
    print(f"TOOLCHAIN_ROLES={len(set(component['role'] for component in data['toolchain']['components']))}/{len(REQUIRED_TOOLCHAIN_ROLES)}")
    print(f"PROJECTIONS={len(set(data['coverage']['projection_classes']))}/{len(REQUIRED_PROJECTIONS)}")
    print(f"SUBSTRATES={len(set(data['coverage']['substrates']))}/{len(REQUIRED_SUBSTRATES)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
