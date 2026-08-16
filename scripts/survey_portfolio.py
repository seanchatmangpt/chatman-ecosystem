#!/usr/bin/env python3
"""Generate a receipt-oriented Chatman Ecosystem portfolio survey.

This script observes GitHub and projects that observation against the admitted
v26.9.1 release manifest plus an explicit release-role -> constitutional-role
crosswalk. Observation never changes release standing and never actuates on
GitHub. Generated reports are projections only.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import sys
import tomllib
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping, Protocol, Sequence

DEFAULT_API = "https://api.github.com"
DEFAULT_MANIFEST = Path("release/v26.9.1/manifest.toml")
DEFAULT_FLEET = Path("release/v26.9.1/fleet-policy.toml")
DEFAULT_CROSSWALK = Path("release/v26.9.1/constitutional-role-crosswalk.toml")
DEFAULT_OUTPUT = Path(".artifacts/portfolio-survey")

ALLOWED_CONSTITUTIONAL_ROLES = {
    "Observe",
    "CandidateState",
    "SemanticState",
    "Construct",
    "Project",
    "ProduceEvidence",
    "Admit",
    "Actuate",
    "Receipt",
    "Replay",
    "ClassClose",
}


class SurveyError(RuntimeError):
    """Typed survey failure."""


class GitHubTransport(Protocol):
    def list_owned_repositories(self, owner: str) -> tuple[list[dict[str, Any]], dict[str, Any]]: ...

    def list_open_pull_requests(self, owner: str) -> list[dict[str, Any]]: ...

    def list_open_issues(self, owner: str) -> list[dict[str, Any]]: ...

    def resolve_ref(self, repository: str, ref: str) -> dict[str, Any]: ...


@dataclass(frozen=True)
class Finding:
    code: str
    severity: str
    subject: str
    detail: str

    def to_dict(self) -> dict[str, str]:
        return {
            "code": self.code,
            "severity": self.severity,
            "subject": self.subject,
            "detail": self.detail,
        }


class GitHubClient:
    """Minimal read-only GitHub REST client using only the Python stdlib."""

    def __init__(
        self,
        token: str | None = None,
        api_url: str = DEFAULT_API,
        inventory_mode: str = "public-owner",
        timeout_seconds: float = 30.0,
    ) -> None:
        if inventory_mode not in {"public-owner", "authenticated-owner"}:
            raise SurveyError(f"unsupported inventory mode: {inventory_mode}")
        if inventory_mode == "authenticated-owner" and not token:
            raise SurveyError("authenticated-owner inventory requires a token")
        self.token = token
        self.api_url = api_url.rstrip("/")
        self.inventory_mode = inventory_mode
        self.timeout_seconds = timeout_seconds

    def _request_json(self, path_or_url: str) -> Any:
        url = path_or_url if path_or_url.startswith("http") else f"{self.api_url}{path_or_url}"
        headers = {
            "Accept": "application/vnd.github+json",
            "User-Agent": "chatman-ecosystem-portfolio-survey/1",
            "X-GitHub-Api-Version": "2022-11-28",
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        request = urllib.request.Request(url, headers=headers, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=self.timeout_seconds) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            payload = exc.read().decode("utf-8", errors="replace")
            raise SurveyError(f"GitHub HTTP {exc.code} for {url}: {payload[:500]}") from exc
        except urllib.error.URLError as exc:
            raise SurveyError(f"GitHub transport failed for {url}: {exc.reason}") from exc

    def _paged(self, path_factory: Any, *, max_pages: int = 100) -> tuple[list[dict[str, Any]], int, bool]:
        items: list[dict[str, Any]] = []
        nonempty_pages = 0
        next_page_empty = False
        for page in range(1, max_pages + 1):
            payload = self._request_json(path_factory(page))
            if not isinstance(payload, list):
                raise SurveyError(f"expected GitHub list payload on page {page}")
            if not payload:
                next_page_empty = True
                break
            nonempty_pages += 1
            for item in payload:
                if isinstance(item, dict):
                    items.append(item)
        else:
            raise SurveyError(f"pagination exceeded {max_pages} pages without an empty terminator")
        return items, nonempty_pages, next_page_empty

    def list_owned_repositories(self, owner: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
        quoted_owner = urllib.parse.quote(owner, safe="")
        if self.inventory_mode == "authenticated-owner":
            def page_url(page: int) -> str:
                return f"/user/repos?affiliation=owner&per_page=100&page={page}&sort=full_name&direction=asc"
        else:
            def page_url(page: int) -> str:
                return f"/users/{quoted_owner}/repos?type=owner&per_page=100&page={page}&sort=full_name&direction=asc"

        repos, nonempty_pages, next_page_empty = self._paged(page_url)
        owned = [
            repo for repo in repos
            if isinstance(repo.get("owner"), dict) and repo["owner"].get("login") == owner
        ]
        owned.sort(key=lambda repo: str(repo.get("full_name", "")).lower())
        return owned, {
            "inventory_mode": self.inventory_mode,
            "page_size": 100,
            "nonempty_pages": nonempty_pages,
            "next_page_empty": next_page_empty,
            "observed_owned_repository_count": len(owned),
        }

    def _search_all(self, query: str) -> list[dict[str, Any]]:
        encoded = urllib.parse.urlencode({"q": query, "per_page": 100, "page": 1})
        first = self._request_json(f"/search/issues?{encoded}")
        if not isinstance(first, dict) or not isinstance(first.get("items"), list):
            raise SurveyError("invalid GitHub search response")
        items: list[dict[str, Any]] = list(first["items"])
        total_count = int(first.get("total_count", len(items)))
        capped = min(total_count, 1000)
        for page in range(2, (capped + 99) // 100 + 1):
            encoded = urllib.parse.urlencode({"q": query, "per_page": 100, "page": page})
            payload = self._request_json(f"/search/issues?{encoded}")
            if not isinstance(payload, dict) or not isinstance(payload.get("items"), list):
                raise SurveyError("invalid paged GitHub search response")
            items.extend(payload["items"])
        return items[:capped]

    def list_open_pull_requests(self, owner: str) -> list[dict[str, Any]]:
        return self._search_all(f"user:{owner} is:pr is:open")

    def list_open_issues(self, owner: str) -> list[dict[str, Any]]:
        return self._search_all(f"user:{owner} is:issue is:open")

    def resolve_ref(self, repository: str, ref: str) -> dict[str, Any]:
        owner_repo = "/".join(urllib.parse.quote(part, safe="") for part in repository.split("/", 1))
        encoded_ref = urllib.parse.quote(ref, safe="")
        payload = self._request_json(f"/repos/{owner_repo}/commits/{encoded_ref}")
        if not isinstance(payload, dict) or not isinstance(payload.get("sha"), str):
            raise SurveyError(f"could not resolve {repository}@{ref}")
        return {"sha": payload["sha"], "html_url": payload.get("html_url")}


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def required_components(manifest: Mapping[str, Any]) -> list[dict[str, Any]]:
    components = manifest.get("components", [])
    if not isinstance(components, list):
        raise SurveyError("manifest components must be an array")
    return [dict(component) for component in components if component.get("required") is True]


def release_repository_map(manifest: Mapping[str, Any]) -> dict[str, dict[str, Any]]:
    return {component["repository"]: component for component in required_components(manifest)}


def explicit_fleet_dispositions(fleet: Mapping[str, Any]) -> dict[str, str]:
    disposition_table = fleet.get("dispositions", {})
    if not isinstance(disposition_table, dict):
        raise SurveyError("fleet dispositions must be a table")
    names = {
        "crown": "CROWN",
        "required": "REQUIRED",
        "adapter": "ADAPTER",
        "bench_gym": "BENCH_GYM",
        "source_archaeology": "SOURCE_ARCHAEOLOGY",
        "explicit_out_of_release": "OUT_OF_RELEASE",
    }
    result: dict[str, str] = {}
    for key, disposition in names.items():
        values = disposition_table.get(key, [])
        if not isinstance(values, list):
            raise SurveyError(f"fleet disposition {key} must be an array")
        for repo in values:
            if not isinstance(repo, str):
                raise SurveyError(f"fleet disposition {key} contains a non-string repository")
            if repo in result:
                raise SurveyError(f"repository has multiple fleet dispositions: {repo}")
            result[repo] = disposition
    root = fleet.get("fleet", {}).get("composition_root")
    if isinstance(root, str):
        result[root] = "CROWN_ROOT"
    return result


def load_crosswalk(path: Path) -> tuple[dict[str, dict[str, Any]], list[Finding]]:
    data = load_toml(path)
    entries = data.get("crosswalk", [])
    findings: list[Finding] = []
    if not isinstance(entries, list):
        return {}, [Finding("CROSSWALK_SCHEMA_INVALID", "BLOCKING", str(path), "[[crosswalk]] entries required")]
    by_release_role: dict[str, dict[str, Any]] = {}
    for index, entry in enumerate(entries):
        if not isinstance(entry, dict):
            findings.append(Finding("CROSSWALK_ENTRY_INVALID", "BLOCKING", f"crosswalk[{index}]", "entry must be a table"))
            continue
        release_role = entry.get("release_role")
        primary = entry.get("primary")
        capabilities = entry.get("capabilities", [])
        if not isinstance(release_role, str) or not release_role:
            findings.append(Finding("CROSSWALK_ROLE_INVALID", "BLOCKING", f"crosswalk[{index}]", str(release_role)))
            continue
        if release_role in by_release_role:
            findings.append(Finding("CROSSWALK_ROLE_DUPLICATE", "BLOCKING", release_role, "exactly one crosswalk entry is allowed"))
            continue
        if primary not in ALLOWED_CONSTITUTIONAL_ROLES:
            findings.append(Finding("CROSSWALK_PRIMARY_INVALID", "BLOCKING", release_role, str(primary)))
        if not isinstance(capabilities, list) or any(cap not in ALLOWED_CONSTITUTIONAL_ROLES for cap in capabilities):
            findings.append(Finding("CROSSWALK_CAPABILITY_INVALID", "BLOCKING", release_role, str(capabilities)))
        if primary == "Actuate" and entry.get("brce_exclusive") is not True:
            findings.append(Finding("CROSSWALK_AMBIENT_ACTUATION", "BLOCKING", release_role, "Actuate requires brce_exclusive=true"))
        by_release_role[release_role] = dict(entry)
    return by_release_role, findings


def validate_crosswalk(manifest: Mapping[str, Any], crosswalk: Mapping[str, Mapping[str, Any]]) -> list[Finding]:
    findings: list[Finding] = []
    for component in required_components(manifest):
        role = component.get("role")
        component_id = str(component.get("id"))
        if not isinstance(role, str) or role not in crosswalk:
            findings.append(Finding("RELEASE_ROLE_UNMAPPED", "BLOCKING", component_id, str(role)))
    return findings


def _repository_from_search_item(item: Mapping[str, Any]) -> str | None:
    repository_url = item.get("repository_url")
    if not isinstance(repository_url, str):
        return None
    marker = "/repos/"
    if marker not in repository_url:
        return None
    return repository_url.split(marker, 1)[1]


def _csv_write(path: Path, rows: Sequence[Mapping[str, Any]], fields: Sequence[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(fields), extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({field: row.get(field, "") for field in fields})


def _iso_now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def build_survey(
    client: GitHubTransport,
    *,
    owner: str,
    manifest: Mapping[str, Any],
    fleet: Mapping[str, Any],
    crosswalk: Mapping[str, Mapping[str, Any]],
    crosswalk_findings: Iterable[Finding] = (),
    observed_at: str | None = None,
) -> dict[str, Any]:
    observed_at = observed_at or _iso_now()
    repos, pagination = client.list_owned_repositories(owner)
    repo_names = {str(repo.get("full_name")) for repo in repos}
    manifest_repos = release_repository_map(manifest)
    dispositions = explicit_fleet_dispositions(fleet)
    findings: list[Finding] = list(crosswalk_findings)
    findings.extend(validate_crosswalk(manifest, crosswalk))

    fleet_table = fleet.get("fleet", {})
    policy_count = fleet_table.get("observed_owned_repository_count")
    if isinstance(policy_count, int) and policy_count != len(repos):
        findings.append(Finding(
            "PORTFOLIO_COUNT_DRIFT",
            "WARN",
            owner,
            f"fleet-policy={policy_count} observed={len(repos)}",
        ))
    policy_pages = fleet_table.get("nonempty_pages")
    if isinstance(policy_pages, int) and policy_pages != pagination.get("nonempty_pages"):
        findings.append(Finding(
            "PORTFOLIO_PAGINATION_DRIFT",
            "WARN",
            owner,
            f"fleet-policy pages={policy_pages} observed pages={pagination.get('nonempty_pages')}",
        ))

    required = required_components(manifest)
    required_rows: list[dict[str, Any]] = []
    ref_observations: dict[str, dict[str, Any]] = {}
    for component in required:
        repo = str(component["repository"])
        ref = str(component["ref"])
        role = str(component["role"])
        mapping = crosswalk.get(role, {})
        observed_ref: dict[str, Any]
        try:
            observed_ref = client.resolve_ref(repo, ref)
        except SurveyError as exc:
            observed_ref = {"sha": "", "error": str(exc)}
            findings.append(Finding("REQUIRED_REF_UNOBSERVED", "WARN", f"{repo}@{ref}", str(exc)))
        ref_observations[repo] = observed_ref
        observed_sha = str(observed_ref.get("sha", ""))
        admitted_sha = str(component.get("sha", ""))
        drift = bool(observed_sha and observed_sha != admitted_sha)
        if drift:
            findings.append(Finding(
                "REQUIRED_REF_DRIFT",
                "WARN",
                repo,
                f"{ref}: admitted={admitted_sha} observed={observed_sha}",
            ))
        if repo not in repo_names:
            findings.append(Finding("REQUIRED_REPOSITORY_UNOBSERVED", "BLOCKING", repo, "required repository absent from owned inventory"))
        required_rows.append({
            "id": component.get("id"),
            "repository": repo,
            "ref": ref,
            "admitted_sha": admitted_sha,
            "observed_ref_sha": observed_sha,
            "ref_drift": str(drift).lower(),
            "release_role": role,
            "constitutional_primary": mapping.get("primary", "UNMAPPED"),
            "constitutional_capabilities": ";".join(mapping.get("capabilities", [])) if isinstance(mapping.get("capabilities", []), list) else "",
            "authority_ceiling": mapping.get("authority_ceiling", ""),
            "standing": component.get("standing", "UNKNOWN"),
            "blocker": component.get("blocker", ""),
            "execution_receipt": component.get("execution_receipt", ""),
            "disposition": component.get("disposition", ""),
            "depends_on": ";".join(component.get("depends_on", [])),
        })

    open_pr_items = client.list_open_pull_requests(owner)
    core_repos = set(dispositions)
    open_pr_rows: list[dict[str, Any]] = []
    for item in open_pr_items:
        repo = _repository_from_search_item(item)
        if repo not in core_repos:
            continue
        open_pr_rows.append({
            "repository": repo,
            "number": item.get("number", ""),
            "title": item.get("title", ""),
            "html_url": item.get("html_url", ""),
            "draft": item.get("draft", ""),
            "updated_at": item.get("updated_at", ""),
            "fleet_disposition": dispositions.get(repo, "OUT_OF_RELEASE"),
        })
    open_pr_rows.sort(key=lambda row: (str(row["repository"]), int(row["number"]) if str(row["number"]).isdigit() else 0))

    required_repo_set = set(manifest_repos)
    open_issue_items = client.list_open_issues(owner)
    required_issue_rows = []
    for item in open_issue_items:
        repo = _repository_from_search_item(item)
        if repo in required_repo_set:
            required_issue_rows.append({
                "repository": repo,
                "number": item.get("number", ""),
                "title": item.get("title", ""),
                "html_url": item.get("html_url", ""),
            })

    repo_rows: list[dict[str, Any]] = []
    for repo in repos:
        full_name = str(repo.get("full_name", ""))
        manifest_component = manifest_repos.get(full_name)
        release_role = str(manifest_component.get("role", "")) if manifest_component else ""
        mapping = crosswalk.get(release_role, {}) if release_role else {}
        disposition = dispositions.get(full_name, fleet_table.get("default_disposition", "OUT_OF_RELEASE"))
        scope = "UNMAPPED"
        if full_name == fleet_table.get("composition_root"):
            scope = "ROOT"
        elif manifest_component:
            scope = "REQUIRED_V26_9_1"
        elif disposition not in {"OUT_OF_RELEASE", ""}:
            scope = "CONSTITUTIONAL_SUPPORT"
        repo_rows.append({
            "repository": full_name,
            "visibility": repo.get("visibility", "public" if repo.get("private") is False else "private" if repo.get("private") is True else ""),
            "archived": str(bool(repo.get("archived", False))).lower(),
            "fork": str(bool(repo.get("fork", False))).lower(),
            "default_branch": repo.get("default_branch", ""),
            "updated_at": repo.get("updated_at", ""),
            "fleet_disposition": disposition,
            "constitutional_scope": scope,
            "release_component": manifest_component.get("id", "") if manifest_component else "",
            "release_role": release_role,
            "constitutional_primary": mapping.get("primary", ""),
            "standing": manifest_component.get("standing", "") if manifest_component else "",
        })

    standing_counts = Counter(row["standing"] for row in required_rows)
    pr_counts = Counter(row["repository"] for row in open_pr_rows)
    scope_counts = Counter(row["constitutional_scope"] for row in repo_rows)
    severity_counts = Counter(finding.severity for finding in findings)

    return {
        "observed_at": observed_at,
        "owner": owner,
        "pagination": pagination,
        "repositories": repo_rows,
        "required_components": required_rows,
        "open_core_prs": open_pr_rows,
        "open_required_issues": required_issue_rows,
        "findings": [finding.to_dict() for finding in findings],
        "summary": {
            "owned_repository_count": len(repo_rows),
            "required_component_count": len(required_rows),
            "open_core_pr_count": len(open_pr_rows),
            "open_required_issue_count": len(required_issue_rows),
            "scope_counts": dict(sorted(scope_counts.items())),
            "required_standing_counts": dict(sorted(standing_counts.items())),
            "open_pr_counts": dict(sorted(pr_counts.items())),
            "finding_severity_counts": dict(sorted(severity_counts.items())),
        },
    }


def render_report(survey: Mapping[str, Any]) -> str:
    summary = survey["summary"]
    standings = summary.get("required_standing_counts", {})
    pr_counts = summary.get("open_pr_counts", {})
    scopes = summary.get("scope_counts", {})
    findings = survey.get("findings", [])
    drift = [finding for finding in findings if finding.get("code") == "REQUIRED_REF_DRIFT"]
    blocking = [finding for finding in findings if finding.get("severity") == "BLOCKING"]
    lines = [
        "# Chatman Ecosystem portfolio survey",
        "",
        f"Observed: `{survey['observed_at']}`",
        f"Owner: `{survey['owner']}`",
        "",
        "## Boundary",
        "",
        f"- owned repositories observed: **{summary['owned_repository_count']}**",
        f"- v26.9.1 required components: **{summary['required_component_count']}**",
        f"- open core PRs: **{summary['open_core_pr_count']}**",
        f"- open issues in required repositories: **{summary['open_required_issue_count']}**",
        f"- exact required refs with drift: **{len(drift)}**",
        f"- blocking survey-contract findings: **{len(blocking)}**",
        "",
        "`Portfolio != ReleaseRequired`. Generated observation does not raise standing.",
        "",
        "## Required standing at admitted subjects",
        "",
        "| Standing | Count |",
        "|---|---:|",
    ]
    for standing, count in sorted(standings.items()):
        lines.append(f"| {standing} | {count} |")
    lines.extend(["", "## Portfolio scope", "", "| Scope | Count |", "|---|---:|"])
    for scope, count in sorted(scopes.items()):
        lines.append(f"| {scope} | {count} |")
    lines.extend(["", "## Open PR concentration", "", "| Repository | Open PRs |", "|---|---:|"])
    for repo, count in sorted(pr_counts.items(), key=lambda item: (-item[1], item[0])):
        lines.append(f"| `{repo}` | {count} |")
    lines.extend(["", "## Findings", ""])
    if findings:
        for finding in findings:
            lines.append(f"- **{finding['severity']} `{finding['code']}`** `{finding['subject']}` — {finding['detail']}")
    else:
        lines.append("No survey-contract findings.")
    lines.extend([
        "",
        "## Constitutional law",
        "",
        "- `Inspection != Execution`.",
        "- `Proof != Authority`.",
        "- release role and constitutional role are separate typed fields.",
        "- successful consequential DO remains BRCE-exclusive and receipt-bound.",
        "- a newer SHA never inherits standing from an older exact subject.",
        "",
    ])
    return "\n".join(lines)


def write_outputs(survey: Mapping[str, Any], output_dir: Path) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    repo_fields = [
        "repository", "visibility", "archived", "fork", "default_branch", "updated_at",
        "fleet_disposition", "constitutional_scope", "release_component", "release_role",
        "constitutional_primary", "standing",
    ]
    required_fields = [
        "id", "repository", "ref", "admitted_sha", "observed_ref_sha", "ref_drift",
        "release_role", "constitutional_primary", "constitutional_capabilities", "authority_ceiling",
        "standing", "blocker", "execution_receipt", "disposition", "depends_on",
    ]
    pr_fields = ["repository", "number", "title", "html_url", "draft", "updated_at", "fleet_disposition"]
    issue_fields = ["repository", "number", "title", "html_url"]
    _csv_write(output_dir / "REPO_CENSUS.csv", survey["repositories"], repo_fields)
    _csv_write(output_dir / "REQUIRED_COMPONENTS.csv", survey["required_components"], required_fields)
    _csv_write(output_dir / "OPEN_CORE_PRS.csv", survey["open_core_prs"], pr_fields)
    _csv_write(output_dir / "OPEN_REQUIRED_ISSUES.csv", survey["open_required_issues"], issue_fields)
    (output_dir / "FINDINGS.json").write_text(json.dumps(survey, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (output_dir / "REPORT.md").write_text(render_report(survey), encoding="utf-8")

    checksum_rows = []
    for path in sorted(output_dir.iterdir()):
        if path.is_file() and path.name != "SHA256SUMS":
            checksum_rows.append(f"{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}")
    (output_dir / "SHA256SUMS").write_text("\n".join(checksum_rows) + "\n", encoding="utf-8")


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--owner", default="seanchatmangpt")
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--fleet", type=Path, default=DEFAULT_FLEET)
    parser.add_argument("--crosswalk", type=Path, default=DEFAULT_CROSSWALK)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--api-url", default=os.environ.get("GITHUB_API_URL", DEFAULT_API))
    parser.add_argument("--token-env", default="GITHUB_TOKEN")
    parser.add_argument("--inventory-mode", choices=["public-owner", "authenticated-owner"], default="public-owner")
    parser.add_argument("--observed-at", default=None, help="Override timestamp for deterministic fixture/replay")
    parser.add_argument("--fail-on-blocking", action="store_true", help="Exit 2 when survey-contract BLOCKING findings exist")
    parser.add_argument("--require-policy-current", action="store_true", help="Exit 2 when observed portfolio count/pagination drifts from fleet-policy")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    token = os.environ.get(args.token_env) or None
    try:
        manifest = load_toml(args.manifest)
        fleet = load_toml(args.fleet)
        crosswalk, crosswalk_findings = load_crosswalk(args.crosswalk)
        client = GitHubClient(token=token, api_url=args.api_url, inventory_mode=args.inventory_mode)
        survey = build_survey(
            client,
            owner=args.owner,
            manifest=manifest,
            fleet=fleet,
            crosswalk=crosswalk,
            crosswalk_findings=crosswalk_findings,
            observed_at=args.observed_at,
        )
        write_outputs(survey, args.output_dir)
    except (OSError, tomllib.TOMLDecodeError, SurveyError) as exc:
        print(json.dumps({"standing": "BLOCKED", "error": str(exc)}, indent=2), file=sys.stderr)
        return 2

    severities = Counter(finding["severity"] for finding in survey["findings"])
    codes = {finding["code"] for finding in survey["findings"]}
    result = {
        "standing": "ALIVE" if severities.get("BLOCKING", 0) == 0 else "BLOCKED",
        "output_dir": str(args.output_dir),
        "summary": survey["summary"],
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if args.fail_on_blocking and severities.get("BLOCKING", 0):
        return 2
    if args.require_policy_current and ({"PORTFOLIO_COUNT_DRIFT", "PORTFOLIO_PAGINATION_DRIFT"} & codes):
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
