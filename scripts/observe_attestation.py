#!/usr/bin/env python3
"""Observe the post-tag hardening lanes for the H4 attestation (read-only; outside the court).

Reads the hand-written lane record ``release/<v>/hardening/inputs/attestation-lanes.json``
and the operator-action rows ``release/<v>/hardening/operator-actions.json``, and writes
``release/<v>/hardening/inputs/attestation-observations.json``:

  lanes       per lane: the PR as GitHub reports it (state, head, merge commit), the
              repository default branch and its head, ``merge_on_default`` (compare API
              status of merge_sha...default_head; ``identical``/``ahead`` = the merge commit
              is an ancestor of the default branch), and the receipt locator's bytes
              (sha256 through ``scripts/durable_locator`` for ``git:`` locators)
  weaver      the Weaver Exact-Subject Capability Crown runs on the chatman default head
  governance  GET-only observations named by operator-action rows (main protection,
              release-crown reviewers, zoela name and latest main run, refs/notes/receipts
              on origin, blocked bundle count)

Authority: ``gh-cli:operator:read`` (GET only; the operator's ``gh`` auth). It never
writes to GitHub. Every failed call is recorded as a typed ``error`` string.
The court (``scripts/release_train/root_crown/attestation.py``) never touches the network;
it projects ATTESTATION.json from these committed observations.
"""

from __future__ import annotations

import argparse
import collections
import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
from scripts.durable_locator import durable_locator as dl  # noqa: E402

SCHEMA = "https://chatman.dev/root-crown/hardening/attestation-observations/v1"
LANES = "hardening/inputs/attestation-lanes.json"
ACTIONS = "hardening/operator-actions.json"
OUT = "hardening/inputs/attestation-observations.json"
ROOT_REPOSITORY = "seanchatmangpt/chatman-ecosystem"
WEAVER = "Weaver Exact-Subject Capability Crown"
Api = Callable[[str], Any]


def gh_api(path: str) -> Any:
    out = subprocess.run(["gh", "api", path], capture_output=True, check=False)
    if out.returncode != 0:
        raise RuntimeError(
            f"gh api {path}: exit {out.returncode}: {out.stderr.decode('utf-8', 'replace').strip()[:200]}"
        )
    return json.loads(out.stdout)


def _err(exc: Exception) -> str:
    return f"{type(exc).__name__}:{exc}"


def classify_merge(status: str | None) -> str:
    """Compare-API status of ``merge...default_head`` -> ancestry verdict."""
    if status in ("identical", "ahead"):
        return "ON_DEFAULT"
    if status in ("behind", "diverged"):
        return "NOT_ON_DEFAULT"
    return "UNKNOWN"


def observe_lane(
    api: Api, resolver: dl.Resolver, lane: dict[str, Any]
) -> dict[str, Any]:
    repo = lane["repository"]
    out: dict[str, Any] = {"id": lane["id"], "repository": repo, "pr": lane["pr"]}
    try:
        info = api(f"repos/{repo}")
        out["default_branch"] = info["default_branch"]
        out["default_head"] = api(f"repos/{repo}/commits/{info['default_branch']}")[
            "sha"
        ]
    except Exception as exc:  # noqa: BLE001 - recorded, never raised
        out["error"] = _err(exc)
        return out
    try:
        pr = api(f"repos/{repo}/pulls/{lane['pr']}")
        out["pr_state"] = "MERGED" if pr.get("merged") else pr["state"].upper()
        out["pr_head"] = pr["head"]["sha"]
        out["pr_merge_commit"] = (
            pr.get("merge_commit_sha") if pr.get("merged") else None
        )
    except Exception as exc:  # noqa: BLE001
        out["pr_error"] = _err(exc)
    if lane.get("merge_sha"):
        try:
            cmp = api(
                f"repos/{repo}/compare/{lane['merge_sha']}...{out['default_head']}"
            )
            out["compare_status"] = cmp["status"]
        except Exception as exc:  # noqa: BLE001
            out["compare_status"] = None
            out["compare_error"] = _err(exc)
        out["merge_on_default"] = classify_merge(out.get("compare_status"))
    receipt: dict[str, Any] = {"locator": lane["receipt_locator"]}
    try:
        loc = dl.parse(lane["receipt_locator"])
        receipt["kind"] = loc.kind
        if loc.kind == "git":
            receipt["sha256"] = dl.sha256_hex(resolver.resolve(loc))
    except dl.Refused as exc:
        receipt["error"] = f"REFUSED[{exc.code}]"
    out["receipt"] = receipt
    return out


def observe_weaver(api: Api, head: str) -> dict[str, Any]:
    try:
        runs = api(
            f"repos/{ROOT_REPOSITORY}/actions/runs?head_sha={head}&per_page=100"
        )["workflow_runs"]
    except Exception as exc:  # noqa: BLE001
        return {"head_sha": head, "error": _err(exc)}
    rows = sorted(
        (
            {
                "id": r["id"],
                "event": r["event"],
                "status": r["status"],
                "conclusion": r["conclusion"],
            }
            for r in runs
            if r["name"] == WEAVER
        ),
        key=lambda r: r["id"],
    )
    return {"head_sha": head, "workflow": WEAVER, "runs": rows}


def observe_governance(
    api: Api, release_dir: Path, root_checkout: Path | None
) -> dict[str, Any]:
    gov: dict[str, Any] = {}
    try:
        gov["main_protected"] = bool(
            api(f"repos/{ROOT_REPOSITORY}/branches/main")["protected"]
        )
    except Exception as exc:  # noqa: BLE001
        gov["main_protected_error"] = _err(exc)
    try:
        env = api(f"repos/{ROOT_REPOSITORY}/environments/release-crown")
        gov["release_crown_required_reviewers"] = sum(
            len(r.get("reviewers") or [])
            for r in env.get("protection_rules") or []
            if r.get("type") == "required_reviewers"
        )
        gov["release_crown_protected_branches"] = bool(
            (env.get("deployment_branch_policy") or {}).get("protected_branches")
        )
    except Exception as exc:  # noqa: BLE001
        gov["release_crown_error"] = _err(exc)
    try:
        gov["zoela_name"] = api("repos/seanchatmangpt/zoela")["name"]
        runs = api("repos/seanchatmangpt/zoela/actions/runs?branch=main&per_page=1")[
            "workflow_runs"
        ]
        gov["zoela_latest_main_run_conclusion"] = (
            runs[0]["conclusion"] if runs else None
        )
    except Exception as exc:  # noqa: BLE001
        gov["zoela_error"] = _err(exc)
    if root_checkout is not None:
        out = subprocess.run(
            ["git", "-C", str(root_checkout), "ls-remote", "origin", "refs/notes/*"],
            capture_output=True,
            check=False,
        )
        refs = sorted(
            line.split("\t", 1)[1]
            for line in out.stdout.decode().splitlines()
            if "\t" in line
        )
        gov["notes_remote_refs"] = refs
        gov["notes_receipts_remote"] = "refs/notes/receipts" in refs
    bundles = json.loads(
        (release_dir / "hardening/bundles.json").read_text(encoding="utf-8")
    )["bundles"]
    counts = collections.Counter(b["standing"] for b in bundles)
    gov["bundles_blocked"] = sum(
        n for s, n in counts.items() if s.startswith("BLOCKED")
    )
    gov["bundles_by_standing"] = dict(sorted(counts.items()))
    return gov


def observe(
    release_dir: Path,
    api: Api,
    resolver: dl.Resolver,
    root_checkout: Path | None,
    now: str,
) -> dict[str, Any]:
    lanes_doc = json.loads((release_dir / LANES).read_text(encoding="utf-8"))
    lanes = [observe_lane(api, resolver, lane) for lane in lanes_doc["lanes"]]
    root_head = next(
        (ln.get("default_head") for ln in lanes if ln["repository"] == ROOT_REPOSITORY),
        None,
    )
    lanes_bytes = (release_dir / LANES).read_bytes()
    return {
        "OBSERVED": "scripts/observe_attestation.py -- observation, do not edit; re-observe",
        "schema": SCHEMA,
        "release": release_dir.name,
        "observed_at": now,
        "observer": "operator-local",
        "authority": "gh-cli:operator:read",
        "lanes_sha256": hashlib.sha256(lanes_bytes).hexdigest(),
        "lanes": lanes,
        "weaver": observe_weaver(api, root_head)
        if root_head
        else {"error": "ROOT_HEAD_UNOBSERVED"},
        "governance": observe_governance(api, release_dir, root_checkout),
    }


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python3 scripts/observe_attestation.py")
    ap.add_argument("--release", required=True)
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument(
        "--repos-root",
        default=os.environ.get("DURABLE_LOCATOR_REPOS_ROOT", str(Path.home())),
    )
    ap.add_argument(
        "--root-checkout",
        type=Path,
        help="canonical checkout for git ls-remote (read-only)",
    )
    ap.add_argument("--out", type=Path)
    args = ap.parse_args(argv)
    release_dir = args.root / "release" / args.release
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    doc = observe(
        release_dir, gh_api, dl.Resolver(Path(args.repos_root)), args.root_checkout, now
    )
    target = args.out or release_dir / OUT
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    errors = [
        ln["id"]
        for ln in doc["lanes"]
        if ln.get("error") or (ln.get("receipt") or {}).get("error")
    ]
    print(
        json.dumps(
            {"observed_at": now, "lanes": len(doc["lanes"]), "errors": errors},
            sort_keys=True,
        )
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
