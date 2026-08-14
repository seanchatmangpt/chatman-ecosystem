#!/usr/bin/env python3
"""Verify an exact Chatman Ecosystem release composition manifest."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

SHA_RE = re.compile(r"^[0-9a-f]{40}$")
REPO_RE = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
ALLOWED_STANDINGS = {
    "UNKNOWN",
    "PARTIAL_ALIVE",
    "ALIVE",
    "BLOCKED",
    "BUILD_BROKEN",
    "UNSUPPORTED",
}
ALLOWED_DISPOSITIONS = {
    "CROWN",
    "REQUIRED",
    "ADAPTER",
    "BENCH_GYM",
    "SOURCE_ARCHAEOLOGY",
    "OUT_OF_RELEASE",
}


@dataclass(frozen=True)
class Finding:
    code: str
    subject: str
    detail: str

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "subject": self.subject, "detail": self.detail}


def load_manifest(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def manifest_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def validate_manifest(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    release = data.get("release")
    components = data.get("components")

    if not isinstance(release, dict):
        return [Finding("ECOSYSTEM_RELEASE_SECTION_MISSING", "release", "[release] is required")]
    if not isinstance(components, list) or not components:
        return [Finding("ECOSYSTEM_COMPONENTS_MISSING", "components", "at least one [[components]] entry is required")]

    if release.get("version") != "26.9.1":
        findings.append(Finding("ECOSYSTEM_VERSION_MISMATCH", "release.version", "expected 26.9.1"))
    if release.get("standing") not in ALLOWED_STANDINGS:
        findings.append(Finding("ECOSYSTEM_RELEASE_STANDING_INVALID", "release.standing", str(release.get("standing"))))

    ids: set[str] = set()
    repositories: set[str] = set()
    roles: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}

    required_fields = {
        "id",
        "repository",
        "ref",
        "sha",
        "role",
        "disposition",
        "standing",
        "required",
        "depends_on",
    }

    for index, component in enumerate(components):
        subject = component.get("id", f"components[{index}]") if isinstance(component, dict) else f"components[{index}]"
        if not isinstance(component, dict):
            findings.append(Finding("ECOSYSTEM_COMPONENT_INVALID", subject, "component must be a table"))
            continue

        missing = sorted(required_fields - component.keys())
        if missing:
            findings.append(Finding("ECOSYSTEM_COMPONENT_FIELDS_MISSING", subject, ",".join(missing)))
            continue

        component_id = component["id"]
        repository = component["repository"]
        role = component["role"]
        by_id[component_id] = component
        roles.add(role)

        if component_id in ids:
            findings.append(Finding("ECOSYSTEM_DUPLICATE_COMPONENT_ID", component_id, "component id must be unique"))
        ids.add(component_id)

        if repository in repositories:
            findings.append(Finding("ECOSYSTEM_DUPLICATE_REPOSITORY", repository, "repository may appear only once"))
        repositories.add(repository)

        if not REPO_RE.fullmatch(repository):
            findings.append(Finding("ECOSYSTEM_REPOSITORY_INVALID", component_id, repository))
        if not isinstance(component["ref"], str) or not component["ref"].strip():
            findings.append(Finding("ECOSYSTEM_REF_INVALID", component_id, str(component["ref"])))
        if not SHA_RE.fullmatch(component["sha"]):
            findings.append(Finding("ECOSYSTEM_SHA_INVALID", component_id, str(component["sha"])))
        if component["disposition"] not in ALLOWED_DISPOSITIONS:
            findings.append(Finding("ECOSYSTEM_DISPOSITION_INVALID", component_id, str(component["disposition"])))
        if component["standing"] not in ALLOWED_STANDINGS:
            findings.append(Finding("ECOSYSTEM_STANDING_INVALID", component_id, str(component["standing"])))
        if not isinstance(component["required"], bool):
            findings.append(Finding("ECOSYSTEM_REQUIRED_INVALID", component_id, "required must be boolean"))
        if not isinstance(component["depends_on"], list) or not all(isinstance(dep, str) for dep in component["depends_on"]):
            findings.append(Finding("ECOSYSTEM_DEPENDENCIES_INVALID", component_id, "depends_on must be an array of component ids"))
        if component["required"] and component["disposition"] == "OUT_OF_RELEASE":
            findings.append(Finding("ECOSYSTEM_REQUIRED_OUT_OF_RELEASE", component_id, "required component cannot be OUT_OF_RELEASE"))
        if component["required"] and component["standing"] == "UNSUPPORTED":
            findings.append(Finding("ECOSYSTEM_REQUIRED_UNSUPPORTED", component_id, "required component cannot be UNSUPPORTED"))

    for component_id, component in by_id.items():
        for dependency in component.get("depends_on", []):
            if dependency not in by_id:
                findings.append(Finding("ECOSYSTEM_DEPENDENCY_NOT_ADMITTED", component_id, dependency))
            if dependency == component_id:
                findings.append(Finding("ECOSYSTEM_SELF_DEPENDENCY", component_id, dependency))

    expected_roles = release.get("required_roles", [])
    if not isinstance(expected_roles, list) or not all(isinstance(role, str) for role in expected_roles):
        findings.append(Finding("ECOSYSTEM_REQUIRED_ROLES_INVALID", "release.required_roles", "must be an array of strings"))
    else:
        for role in expected_roles:
            if role not in roles:
                findings.append(Finding("ECOSYSTEM_REQUIRED_ROLE_MISSING", role, "no component provides required role"))

    findings.extend(_detect_cycles(by_id))
    return findings


def _detect_cycles(by_id: dict[str, dict[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(node: str, trail: list[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            cycle_start = trail.index(node) if node in trail else 0
            cycle = trail[cycle_start:] + [node]
            findings.append(Finding("ECOSYSTEM_DEPENDENCY_CYCLE", node, " -> ".join(cycle)))
            return

        visiting.add(node)
        trail.append(node)
        for dependency in by_id[node].get("depends_on", []):
            if dependency in by_id:
                visit(dependency, trail)
        trail.pop()
        visiting.remove(node)
        visited.add(node)

    for component_id in by_id:
        visit(component_id, [])
    return findings


def resolve_ref(repository: str, ref: str, timeout: float = 10.0) -> str:
    owner, name = repository.split("/", 1)
    encoded_ref = urllib.parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{owner}/{name}/git/ref/heads/{encoded_ref}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "chatman-ecosystem-release-verifier/26.9.1",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.load(response)
    sha = payload.get("object", {}).get("sha")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ValueError(f"GitHub returned no commit SHA for {repository}@{ref}")
    return sha


def check_ref_drift(data: dict[str, Any]) -> list[Finding]:
    findings: list[Finding] = []
    for component in data.get("components", []):
        if not component.get("required", False):
            continue
        component_id = component["id"]
        try:
            observed = resolve_ref(component["repository"], component["ref"])
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            findings.append(Finding("ECOSYSTEM_REF_CHECK_BLOCKED", component_id, str(exc)))
            continue
        if observed != component["sha"]:
            findings.append(
                Finding(
                    "ECOSYSTEM_HEAD_DRIFT",
                    component_id,
                    f"admitted={component['sha']} observed={observed} ref={component['ref']}",
                )
            )
    return findings


def crown_standing(data: dict[str, Any], findings: list[Finding]) -> str:
    if findings:
        return "BLOCKED"
    standings = [component["standing"] for component in data.get("components", []) if component.get("required", False)]
    if not standings:
        return "UNKNOWN"
    if "BUILD_BROKEN" in standings:
        return "BUILD_BROKEN"
    if "BLOCKED" in standings:
        return "BLOCKED"
    if "UNKNOWN" in standings:
        return "UNKNOWN"
    if "PARTIAL_ALIVE" in standings:
        return "PARTIAL_ALIVE"
    if "UNSUPPORTED" in standings:
        return "UNSUPPORTED"
    if all(standing == "ALIVE" for standing in standings):
        return "ALIVE"
    return "UNKNOWN"


def build_report(path: Path, data: dict[str, Any], findings: list[Finding], checked_refs: bool) -> dict[str, Any]:
    standing = crown_standing(data, findings)
    return {
        "release": data.get("release", {}).get("version"),
        "manifest_sha256": manifest_digest(path),
        "component_count": len(data.get("components", [])),
        "required_component_count": sum(1 for c in data.get("components", []) if c.get("required", False)),
        "refs_checked": checked_refs,
        "standing": standing,
        "findings": [finding.as_dict() for finding in findings],
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, default=Path("release/v26.9.1/manifest.toml"))
    parser.add_argument("--check-refs", action="store_true")
    parser.add_argument("--require-alive", action="store_true")
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)

    data = load_manifest(args.manifest)
    findings = validate_manifest(data)
    if args.check_refs and not findings:
        findings.extend(check_ref_drift(data))

    report = build_report(args.manifest, data, findings, args.check_refs)
    rendered = json.dumps(report, indent=2, sort_keys=True)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")

    if findings:
        return 2
    if args.require_alive and report["standing"] != "ALIVE":
        return 3
    return 0


if __name__ == "__main__":
    sys.exit(main())
