#!/usr/bin/env python3
"""Read-only governance observation for the autonomic crown (RFC-0005 §12, §13).

GET-only. Two requests, both through the GitHub REST API with a read token taken from
``GITHUB_TOKEN`` (the environment only; never written anywhere):

* ``GET /repos/{repo}/branches/main`` -> ``.protected``
* ``GET /repos/{repo}/environments/release-crown`` -> ``.protection_rules`` (required
  reviewers) and ``.deployment_branch_policy.protected_branches``

A 404 environment is recorded as absent (no reviewers). A transport failure is recorded
as ``UNOBSERVED`` with its HTTP status; the crown then keeps authority at
WAITING_EXTERNAL_AUTHORITY rather than guessing. The parsing functions are pure.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

SCHEMA = "https://chatman.dev/autonomic-crown/governance/v1"
API = "https://api.github.com"


def parse_branch(doc: dict[str, Any]) -> dict[str, Any]:
    return {"protected": doc.get("protected") is True}


def parse_environment(doc: dict[str, Any] | None) -> dict[str, Any]:
    if doc is None:
        return {"present": False, "reviewers": 0, "protected_branches": False}
    reviewers = 0
    for rule in doc.get("protection_rules") or []:
        if rule.get("type") == "required_reviewers":
            reviewers += len(rule.get("reviewers") or [])
    policy = doc.get("deployment_branch_policy") or {}
    return {"present": True, "reviewers": reviewers, "protected_branches": policy.get("protected_branches") is True}


def _get(path: str, token: str | None) -> tuple[int, dict[str, Any] | None]:
    request = urllib.request.Request(f"{API}{path}", method="GET")
    request.add_header("Accept", "application/vnd.github+json")
    request.add_header("X-GitHub-Api-Version", "2022-11-28")
    if token:
        request.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(request, timeout=30) as response:  # noqa: S310 -- fixed https host
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return exc.code, None
    except (urllib.error.URLError, TimeoutError):
        return 0, None


def observe(repo: str, token: str | None) -> dict[str, Any]:
    out: dict[str, Any] = {
        "schema": SCHEMA,
        "repository": repo,
        "observed_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": "github-api:read",
        "requests": [],
    }
    status, branch = _get(f"/repos/{repo}/branches/main", token)
    out["requests"].append({"method": "GET", "path": f"/repos/{repo}/branches/main", "status": status})
    out["main"] = parse_branch(branch) if branch is not None else {"protected": None, "unobserved": status}
    status, env = _get(f"/repos/{repo}/environments/release-crown", token)
    out["requests"].append({"method": "GET", "path": f"/repos/{repo}/environments/release-crown", "status": status})
    if env is not None or status == 404:
        out["environments"] = {"release-crown": parse_environment(env)}
    else:
        out["environments"] = {"release-crown": {"unobserved": status}}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="observe_governance")
    parser.add_argument("--repo", default="seanchatmangpt/chatman-ecosystem")
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)
    doc = observe(args.repo, os.environ.get("GITHUB_TOKEN"))
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"main": doc["main"], "environments": doc["environments"]}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
