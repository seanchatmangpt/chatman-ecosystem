#!/usr/bin/env python3
"""Observe release heads for the root crown (read-only GitHub API; outside the court).

The root crown court (scripts/release_train/root_crown) never touches the network.
This observer produces its ``observations.json``:

  repos      per pinned repository: default_branch (never hardcoded: autofde-lab is
             ``master``), visibility, head_sha, pin_sha, compare_status of pin...head
  artifacts  per remote evidence locator ``owner/name:path``: sha256, parsed JSON,
             and compare_status of the artifact's own subject_sha...head
  tag        the release tag's commit SHA or null
  local_worktrees (``--local-worktrees``) operator-local topology receipt m_term

Authority: ``github-api:<token-env>:read``. It never writes to GitHub. Every failed
call is recorded as a typed ``error`` string, never raised past the repository.
"""

from __future__ import annotations

import argparse
import base64
import glob
import hashlib
import json
import os
import sys
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
import release_line  # noqa: E402
import verify_release  # noqa: E402

API = "https://api.github.com"
Fetch = Callable[[str], dict[str, Any]]
TOPOLOGY_GLOB = "~/.claude/migration/v26925-topology/TOPOLOGY-RECEIPT*.json"


def github_fetch(url: str) -> dict[str, Any]:
    return verify_release._github_json(url, 15.0)


def _err(exc: Exception) -> str:
    if isinstance(exc, urllib.error.HTTPError):
        return f"HTTP{exc.code}"
    return f"{type(exc).__name__}:{exc}"


def _compare(fetch: Fetch, repository: str, base: str, head: str) -> str | None:
    payload = fetch(f"{API}/repos/{repository}/compare/{base}...{urllib.parse.quote(head, safe='')}")
    status = payload.get("status")
    return status if status in {"identical", "ahead", "behind", "diverged"} else None


def observe_repo(fetch: Fetch, repository: str, pin_sha: str) -> dict[str, Any]:
    out: dict[str, Any] = {"pin_sha": pin_sha}
    try:
        meta = fetch(f"{API}/repos/{repository}")
        branch = meta["default_branch"]
        out["default_branch"] = branch
        out["visibility"] = meta.get("visibility")
        head = fetch(f"{API}/repos/{repository}/commits/{urllib.parse.quote(branch, safe='')}")
        out["head_sha"] = head["sha"]
        out["compare_status"] = (
            "identical" if head["sha"] == pin_sha else _compare(fetch, repository, pin_sha, head["sha"])
        )
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        out["error"] = _err(exc)
    return out


def observe_artifact(fetch: Fetch, locator: str, repo_obs: dict[str, Any]) -> dict[str, Any]:
    repository, _, path = locator.partition(":")
    head = repo_obs.get("head_sha")
    if not head:
        return {"error": f"repo-unobserved:{repo_obs.get('error', 'no-head')}"}
    try:
        payload = fetch(f"{API}/repos/{repository}/contents/{urllib.parse.quote(path)}?ref={head}")
        raw = base64.b64decode(payload.get("content", ""))
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        return {"error": _err(exc), "head_sha": head}
    out: dict[str, Any] = {"sha256": hashlib.sha256(raw).hexdigest(), "head_sha": head, "blob_sha": payload.get("sha")}
    try:
        data = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return out
    out["json"] = data
    subject = data.get("subject_sha") if isinstance(data, dict) else None
    if isinstance(subject, str) and len(subject) == 40:
        try:
            out["subject_compare"] = "identical" if subject == head else _compare(fetch, repository, subject, head)
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            out["subject_compare_error"] = _err(exc)
    return out


def observe_tag(fetch: Fetch, repository: str, tag: str) -> dict[str, Any]:
    try:
        ref = fetch(f"{API}/repos/{repository}/git/ref/tags/{urllib.parse.quote(tag, safe='')}")
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return {"name": tag, "sha": None}
        return {"name": tag, "error": _err(exc)}
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"name": tag, "error": _err(exc)}
    obj = ref.get("object", {})
    sha = obj.get("sha")
    if obj.get("type") == "tag":
        try:
            sha = fetch(f"{API}/repos/{repository}/git/tags/{sha}")["object"]["sha"]
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            return {"name": tag, "error": _err(exc)}
    return {"name": tag, "sha": sha}


def observe_local_worktrees(pattern: str = TOPOLOGY_GLOB) -> dict[str, Any] | None:
    paths = sorted(glob.glob(os.path.expanduser(pattern)))
    if not paths:
        return None
    path = Path(paths[-1])
    raw = path.read_bytes()
    receipt = json.loads(raw)
    m_term = receipt.get("m_term")
    worktrees = None
    observed_at = receipt.get("observed_at") or receipt.get("generated_at")
    if isinstance(m_term, dict):
        observed_at = m_term.get("observed_at") or observed_at
        violations = m_term.get("violations")
        if isinstance(violations, list):
            worktrees = [
                {"repo": v.get("repo_id"), "path": v.get("path"), "class": v.get("class"), "blocked": v.get("blocked")}
                for v in violations
                if isinstance(v, dict)
            ]
    return {
        "authority": "operator-local:TOPOLOGY-RECEIPT",
        "source": path.name,
        "sha256": hashlib.sha256(raw).hexdigest(),
        "observed_at": observed_at,
        "holds": m_term.get("holds") if isinstance(m_term, dict) else None,
        "unauthorized_worktrees": m_term.get("unauthorized_worktrees") if isinstance(m_term, dict) else None,
        "worktrees": worktrees,
    }


def observe(
    release_dir: Path,
    fetch: Fetch = github_fetch,
    *,
    now: str | None = None,
    token_env: str = "GITHUB_TOKEN",
    cold: bool = False,
    run_id: str | None = None,
) -> dict[str, Any]:
    pins = json.loads((release_dir / "pins.json").read_text(encoding="utf-8"))
    requirements = json.loads((release_dir / "requirements.json").read_text(encoding="utf-8"))["requirements"]
    imports = json.loads((release_dir / "imports/IMPORTS.json").read_text(encoding="utf-8"))["imports"]
    repos: dict[str, Any] = {}
    for pin in pins["repos"].values():
        repos[pin["repository"]] = observe_repo(fetch, pin["repository"], pin["sha"])
    artifacts: dict[str, Any] = {}
    for locator in sorted(
        {r["evidence_locator"] for r in requirements if not r["evidence_locator"].startswith("local:")}
    ):
        repository = locator.partition(":")[0]
        artifacts[locator] = observe_artifact(fetch, locator, repos.get(repository, {"error": "not-pinned"}))
    for entry in imports:
        key = f"{entry['source_repo']}:{entry['source_path']}@{entry['source_sha']}"
        try:
            payload = fetch(
                f"{API}/repos/{entry['source_repo']}/contents/{urllib.parse.quote(entry['source_path'])}?ref={entry['source_sha']}"
            )
            artifacts[key] = {"sha256": hashlib.sha256(base64.b64decode(payload.get("content", ""))).hexdigest()}
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            artifacts[key] = {"error": _err(exc)}
    subjects: dict[str, str | None] = {}
    root = release_dir.parent.parent
    for req in requirements:
        if req["evidence_kind"] != "xprod_case" or not req["evidence_locator"].startswith("local:"):
            continue
        case_path = root / req["evidence_locator"][len("local:") :]
        if not case_path.is_file():
            continue
        for subject in json.loads(case_path.read_text(encoding="utf-8")).get("subjects", []):
            identity = f"{subject['repository']}@{subject['subject_sha']}"
            head = repos.get(subject["repository"], {}).get("head_sha")
            try:
                subjects[identity] = (
                    (
                        "identical"
                        if subject["subject_sha"] == head
                        else _compare(fetch, subject["repository"], subject["subject_sha"], head)
                    )
                    if head
                    else None
                )
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
                subjects[identity] = None
    observations: dict[str, Any] = {
        "schema": "https://chatman.dev/root-crown/observations/v1",
        "release": release_dir.name,
        "observed_at": now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "authority": f"github-api:{token_env}:read",
        "environment": {"cold": cold, "run_id": run_id},
        "repos": repos,
        "artifacts": artifacts,
        "subjects": subjects,
        "tag": observe_tag(fetch, pins["root_repository"], release_dir.name),
    }
    committed = release_dir / "observations/local-worktrees.json"
    if committed.is_file():
        observations["local_worktrees"] = json.loads(committed.read_text(encoding="utf-8"))
    return observations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument(
        "--local-worktrees", action="store_true", help="ingest the operator-local topology receipt m_term"
    )
    parser.add_argument("--cold", action="store_true", help="declare a clean runner (CI) for AC-12")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    release_dir = release_line.release_dir(args.release)
    token_env = "GITHUB_TOKEN" if os.environ.get("GITHUB_TOKEN") else "GH_TOKEN"
    observations = observe(release_dir, cold=args.cold, run_id=args.run_id, token_env=token_env)
    if args.local_worktrees:
        local = observe_local_worktrees()
        if local is not None:
            observations["local_worktrees"] = local
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(observations, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    errors = sorted(k for k, v in observations["repos"].items() if v.get("error"))
    print(
        json.dumps(
            {
                "observed_at": observations["observed_at"],
                "repos": len(observations["repos"]),
                "repo_errors": errors,
                "tag": observations["tag"],
            },
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
