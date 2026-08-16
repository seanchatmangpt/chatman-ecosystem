#!/usr/bin/env python3
"""Verify an exact Chatman Ecosystem release composition manifest.

The exact admitted release subject is the component SHA. A declared branch ref
identifies its lineage, not a mutable alias that must remain equal to the SHA
forever. Normal branch advancement is therefore observed but does not
invalidate an already-admitted immutable subject. A required GitHub-backed
component is valid when its admitted SHA is identical to, or an ancestor of,
the declared ref head. Rewinds/divergence, missing refs/commits, and inaccessible
lineage remain fail-closed.
"""

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
ALLOWED_REF_CHECKS = {"github", "external"}
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
        "ref_check",
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
        if component["ref_check"] not in ALLOWED_REF_CHECKS:
            findings.append(Finding("ECOSYSTEM_REF_CHECK_MODE_INVALID", component_id, str(component["ref_check"])))
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

    observations = data.get("external_ref_observations", [])
    if not isinstance(observations, list):
        findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_OBSERVATIONS_INVALID", "external_ref_observations", "must be an array of tables"))
        observations = []
    observation_by_component: dict[str, dict[str, Any]] = {}
    for observation in observations:
        if not isinstance(observation, dict):
            findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_OBSERVATION_INVALID", "external_ref_observations", "observation must be a table"))
            continue
        component_id = observation.get("component")
        if not isinstance(component_id, str) or component_id not in by_id:
            findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_COMPONENT_INVALID", str(component_id), "observation must name an admitted component"))
            continue
        if component_id in observation_by_component:
            findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_DUPLICATE", component_id, "only one external observation is admitted per component"))
            continue
        observation_by_component[component_id] = observation

    for component_id, component in by_id.items():
        if component.get("ref_check") != "external":
            continue
        observation = observation_by_component.get(component_id)
        if observation is None:
            findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_EVIDENCE_MISSING", component_id, "external ref check requires an exact observation"))
            continue
        for field in ("repository", "ref", "sha"):
            if observation.get(field) != component.get(field):
                findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_EVIDENCE_MISMATCH", component_id, f"{field}: admitted={component.get(field)} observed={observation.get(field)}"))
        if not isinstance(observation.get("authority"), str) or not observation.get("authority", "").strip():
            findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_AUTHORITY_MISSING", component_id, "external observation requires authority"))
        if not isinstance(observation.get("observed_at"), str) or not observation.get("observed_at", "").strip():
            findings.append(Finding("ECOSYSTEM_EXTERNAL_REF_TIME_MISSING", component_id, "external observation requires observed_at"))

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


def _github_json(url: str, timeout: float) -> dict[str, Any]:
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
    if not isinstance(payload, dict):
        raise ValueError(f"GitHub returned a non-object payload for {url}")
    return payload


def resolve_ref(repository: str, ref: str, timeout: float = 10.0) -> str:
    owner, name = repository.split("/", 1)
    encoded_ref = urllib.parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{owner}/{name}/git/ref/heads/{encoded_ref}"
    payload = _github_json(url, timeout)
    sha = payload.get("object", {}).get("sha")
    if not isinstance(sha, str) or not SHA_RE.fullmatch(sha):
        raise ValueError(f"GitHub returned no commit SHA for {repository}@{ref}")
    return sha


def compare_ref_lineage(
    repository: str,
    ref: str,
    admitted_sha: str,
    timeout: float = 10.0,
) -> str:
    """Return GitHub compare status for admitted_sha...ref.

    With the admitted SHA as the compare base and the branch ref as the compare
    head, only ``identical`` and ``ahead`` establish that the admitted immutable
    subject remains on the declared branch lineage.
    """

    owner, name = repository.split("/", 1)
    encoded_ref = urllib.parse.quote(ref, safe="")
    url = f"https://api.github.com/repos/{owner}/{name}/compare/{admitted_sha}...{encoded_ref}"
    payload = _github_json(url, timeout)
    base_sha = payload.get("base_commit", {}).get("sha")
    status = payload.get("status")
    if base_sha != admitted_sha:
        raise ValueError(
            f"GitHub compare base mismatch for {repository}@{ref}: "
            f"admitted={admitted_sha} compare_base={base_sha}"
        )
    if status not in {"identical", "ahead", "behind", "diverged"}:
        raise ValueError(f"GitHub returned invalid compare status for {repository}@{ref}: {status}")
    return status


def check_ref_drift(data: dict[str, Any]) -> tuple[list[Finding], dict[str, int]]:
    """Verify admitted SHA lineage without conflating it with the current head.

    A branch advancing beyond an admitted SHA is normal candidate-state motion.
    It is counted as ``github_advanced`` but is not a release finding. A rewind
    or divergence means the admitted SHA is no longer on the declared lineage
    and remains fail-closed.
    """

    findings: list[Finding] = []
    coverage = {
        "github_live": 0,
        "github_exact": 0,
        "github_advanced": 0,
        "external_exact": 0,
    }
    for component in data.get("components", []):
        if not component.get("required", False):
            continue
        component_id = component["id"]
        if component.get("ref_check") == "external":
            # validate_manifest already requires an exact, authority-named observation
            # matching repository/ref/SHA. CI admits that bounded observation rather
            # than pretending its repository-scoped token can see a private sibling.
            coverage["external_exact"] += 1
            continue

        repository = component["repository"]
        ref = component["ref"]
        admitted_sha = component["sha"]
        try:
            observed_head = resolve_ref(repository, ref)
            coverage["github_live"] += 1
            if observed_head == admitted_sha:
                coverage["github_exact"] += 1
                continue
            lineage_status = compare_ref_lineage(repository, ref, admitted_sha)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, ValueError) as exc:
            findings.append(Finding("ECOSYSTEM_REF_CHECK_BLOCKED", component_id, str(exc)))
            continue

        if lineage_status == "ahead":
            coverage["github_advanced"] += 1
            continue

        findings.append(
            Finding(
                "ECOSYSTEM_REF_LINEAGE_VIOLATION",
                component_id,
                (
                    f"admitted={admitted_sha} observed_head={observed_head} "
                    f"ref={ref} compare_status={lineage_status}"
                ),
            )
        )
    return findings, coverage


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


def build_report(path: Path, data: dict[str, Any], findings: list[Finding], checked_refs: bool, ref_coverage: dict[str, int] | None = None) -> dict[str, Any]:
    standing = crown_standing(data, findings)
    return {
        "release": data.get("release", {}).get("version"),
        "manifest_sha256": manifest_digest(path),
        "component_count": len(data.get("components", [])),
        "required_component_count": sum(1 for c in data.get("components", []) if c.get("required", False)),
        "refs_checked": checked_refs,
        "ref_coverage": ref_coverage
        or {
            "github_live": 0,
            "github_exact": 0,
            "github_advanced": 0,
            "external_exact": 0,
        },
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
    ref_coverage = {
        "github_live": 0,
        "github_exact": 0,
        "github_advanced": 0,
        "external_exact": 0,
    }
    if args.check_refs and not findings:
        ref_findings, ref_coverage = check_ref_drift(data)
        findings.extend(ref_findings)

    report = build_report(args.manifest, data, findings, args.check_refs, ref_coverage)
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
