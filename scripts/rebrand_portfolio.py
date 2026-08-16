#!/usr/bin/env python3
"""Open provenance-safe Forward Deployment OS draft PRs across owned repositories.

Uses only the Python standard library. The script is idempotent with respect to
an existing open PR from the configured campaign branch.
"""

from __future__ import annotations

import argparse
import base64
import dataclasses
import datetime as dt
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any, Iterable

API_ROOT = "https://api.github.com"
DEFAULT_BRANCH_NAME = "brand/forward-deployment-os-2026-08"
DEFAULT_FILE_PATH = "FORWARD_DEPLOYMENT.md"


@dataclasses.dataclass(frozen=True)
class Result:
    repository: str
    state: str
    reason: str | None = None
    base: str | None = None
    base_sha: str | None = None
    head_sha: str | None = None
    pull_request: str | None = None


class GitHubAPI:
    def __init__(self, token: str) -> None:
        self.token = token

    def request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None = None,
    ) -> tuple[Any, dict[str, str]]:
        url = path if path.startswith("https://") else f"{API_ROOT}{path}"
        data = None
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self.token}",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "chatman-forward-deployment-rebrand",
        }
        if payload is not None:
            data = json.dumps(payload).encode("utf-8")
            headers["Content-Type"] = "application/json"
        request = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                raw = response.read()
                parsed = json.loads(raw) if raw else None
                return parsed, {k.lower(): v for k, v in response.headers.items()}
        except urllib.error.HTTPError as error:
            raw = error.read().decode("utf-8", errors="replace")
            try:
                body: Any = json.loads(raw)
            except json.JSONDecodeError:
                body = raw
            raise RuntimeError(
                json.dumps(
                    {
                        "method": method,
                        "url": url,
                        "status": error.code,
                        "body": body,
                    },
                    sort_keys=True,
                )
            ) from error

    def paginate(self, path: str) -> Iterable[dict[str, Any]]:
        page = 1
        while True:
            separator = "&" if "?" in path else "?"
            payload, _ = self.request("GET", f"{path}{separator}per_page=100&page={page}")
            if not isinstance(payload, list):
                raise RuntimeError(f"Expected list response for {path}")
            yield from payload
            if len(payload) < 100:
                break
            page += 1


def portfolio_context(repository: str) -> str:
    return f"""# Forward Deployment Portfolio Context

`{repository}` is included in Sean Chatman’s public engineering portfolio around **The 2,001st Forward-Deployed Agentic Architect** and the **Chatman Ecosystem: the operating system for forward deployment**.

The portfolio models forward deployment as an evidence-bearing lifecycle:

```text
observe → admit → model → plan → construct → authorize
→ actuate → verify → receipt → replay → standing
```

```text
A = μ(O*)
R = receipt(A)
```

## Repository boundary

This note adds portfolio context only. The repository’s existing README, upstream provenance, authorship, license, governance, purpose, and project-specific maturity statements remain authoritative within their declared scopes.

Inclusion does **not** assert that:

- this repository was authored from scratch by Sean Chatman;
- every capability is integrated into the Chatman Ecosystem;
- a build, workflow, generated artifact, or protocol surface has achieved production standing;
- models, agents, hooks, or generated outputs possess ambient execution authority.

Exact observed execution against the admitted subject, with bounded verification and receipts, determines operational standing.

The canonical portfolio narrative is maintained in `seanchatmangpt/chatman-ecosystem`.
"""


def parse_error(error: Exception) -> dict[str, Any]:
    try:
        value = json.loads(str(error))
        return value if isinstance(value, dict) else {"error": str(error)}
    except json.JSONDecodeError:
        return {"error": str(error)}


def get_ref(api: GitHubAPI, owner: str, repo: str, branch: str) -> str:
    encoded = urllib.parse.quote(branch, safe="")
    payload, _ = api.request("GET", f"/repos/{owner}/{repo}/git/ref/heads/{encoded}")
    return str(payload["object"]["sha"])


def existing_pr(
    api: GitHubAPI,
    owner: str,
    repo: str,
    base: str,
    head_branch: str,
) -> dict[str, Any] | None:
    query = urllib.parse.urlencode(
        {"state": "open", "base": base, "head": f"{owner}:{head_branch}"}
    )
    payload, _ = api.request("GET", f"/repos/{owner}/{repo}/pulls?{query}")
    return payload[0] if payload else None


def ensure_branch(
    api: GitHubAPI,
    owner: str,
    repo: str,
    base: str,
    campaign_branch: str,
) -> tuple[str, str]:
    base_sha = get_ref(api, owner, repo, base)
    try:
        head_sha = get_ref(api, owner, repo, campaign_branch)
        return base_sha, head_sha
    except RuntimeError as error:
        if parse_error(error).get("status") != 404:
            raise
    payload, _ = api.request(
        "POST",
        f"/repos/{owner}/{repo}/git/refs",
        {"ref": f"refs/heads/{campaign_branch}", "sha": base_sha},
    )
    return base_sha, str(payload["object"]["sha"])


def create_context_file(
    api: GitHubAPI,
    owner: str,
    repo: str,
    branch: str,
    file_path: str,
) -> str:
    encoded_path = urllib.parse.quote(file_path, safe="/")
    try:
        existing, _ = api.request(
            "GET", f"/repos/{owner}/{repo}/contents/{encoded_path}?ref={urllib.parse.quote(branch)}"
        )
        return str(existing.get("sha", "existing"))
    except RuntimeError as error:
        if parse_error(error).get("status") != 404:
            raise
    content = portfolio_context(repo)
    payload, _ = api.request(
        "PUT",
        f"/repos/{owner}/{repo}/contents/{encoded_path}",
        {
            "message": "docs: add Forward Deployment OS portfolio context",
            "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
            "branch": branch,
        },
    )
    return str(payload["commit"]["sha"])


def open_draft_pr(
    api: GitHubAPI,
    owner: str,
    repo: str,
    base: str,
    head: str,
) -> dict[str, Any]:
    current = existing_pr(api, owner, repo, base, head)
    if current is not None:
        return current
    body = """## Purpose

Add provenance-safe portfolio context for Sean Chatman’s Forward Deployment OS rebranding campaign.

## Change

- adds `FORWARD_DEPLOYMENT.md`
- identifies **The 2,001st Forward-Deployed Agentic Architect** category and the Chatman Ecosystem thesis
- preserves the repository’s existing purpose, authorship, upstream provenance, license, governance, and maturity boundaries
- introduces no runtime, dependency, build, test, or release behavior changes

## Verification

- docs-only change
- no existing file replaced
- operational standing remains bounded by exact observed execution and receipts
"""
    payload, _ = api.request(
        "POST",
        f"/repos/{owner}/{repo}/pulls",
        {
            "title": "docs: add Forward Deployment OS portfolio context",
            "body": body,
            "head": head,
            "base": base,
            "draft": True,
            "maintainer_can_modify": True,
        },
    )
    return payload


def process_repository(
    api: GitHubAPI,
    owner: str,
    metadata: dict[str, Any],
    campaign_branch: str,
    file_path: str,
    dry_run: bool,
) -> Result:
    name = str(metadata["name"])
    full_name = str(metadata["full_name"])
    base = str(metadata["default_branch"])
    if metadata.get("archived"):
        return Result(full_name, "REFUSED", "ARCHIVED", base=base)
    if int(metadata.get("size", 0)) == 0:
        return Result(full_name, "UNSUPPORTED", "NO_BASE_COMMIT", base=base)
    permissions = metadata.get("permissions") or {}
    if not permissions.get("push", False):
        return Result(full_name, "REFUSED", "NO_PUSH_AUTHORITY", base=base)
    if dry_run:
        return Result(full_name, "CANDIDATE", "DRY_RUN", base=base)

    prior = existing_pr(api, owner, name, base, campaign_branch)
    if prior is not None:
        return Result(
            full_name,
            "ALIVE",
            "EXISTING_OPEN_PR",
            base=base,
            head_sha=prior.get("head", {}).get("sha"),
            pull_request=prior.get("html_url"),
        )

    base_sha, _ = ensure_branch(api, owner, name, base, campaign_branch)
    head_sha = create_context_file(api, owner, name, campaign_branch, file_path)
    pr = open_draft_pr(api, owner, name, base, campaign_branch)
    return Result(
        full_name,
        "ALIVE",
        base=base,
        base_sha=base_sha,
        head_sha=head_sha,
        pull_request=pr.get("html_url"),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--owner", default="seanchatmangpt")
    parser.add_argument("--branch", default=DEFAULT_BRANCH_NAME)
    parser.add_argument("--file-path", default=DEFAULT_FILE_PATH)
    parser.add_argument("--repo", action="append", default=[])
    parser.add_argument("--max-repos", type=int)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--receipt", type=Path, default=Path("rebrand-receipt.json"))
    parser.add_argument("--sleep", type=float, default=0.35)
    args = parser.parse_args()

    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print("REFUSED:MISSING_GITHUB_TOKEN", file=sys.stderr)
        return 2

    api = GitHubAPI(token)
    repositories = list(
        api.paginate("/user/repos?affiliation=owner&sort=full_name&direction=asc")
    )
    selected = set(args.repo)
    if selected:
        repositories = [repo for repo in repositories if repo["name"] in selected]
    if args.max_repos is not None:
        repositories = repositories[: args.max_repos]

    results: list[Result] = []
    for metadata in repositories:
        try:
            result = process_repository(
                api,
                args.owner,
                metadata,
                args.branch,
                args.file_path,
                args.dry_run,
            )
        except Exception as error:  # preserve a per-repository typed failure
            details = parse_error(error)
            status = details.get("status")
            state = "BLOCKED" if status in {403, 429} else "BUILD_BROKEN"
            result = Result(
                str(metadata.get("full_name", metadata.get("name"))),
                state,
                json.dumps(details, sort_keys=True),
                base=metadata.get("default_branch"),
            )
            results.append(result)
            if status in {403, 429}:
                break
        else:
            results.append(result)
        print(json.dumps(dataclasses.asdict(result), sort_keys=True), flush=True)
        if args.sleep:
            time.sleep(args.sleep)

    receipt = {
        "schema": "chatman.forward-deployment.rebrand-receipt.v1",
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "owner": args.owner,
        "branch": args.branch,
        "file_path": args.file_path,
        "dry_run": args.dry_run,
        "observed_repository_count": len(repositories),
        "results": [dataclasses.asdict(result) for result in results],
    }
    args.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")

    failed = [result for result in results if result.state in {"BLOCKED", "BUILD_BROKEN"}]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
