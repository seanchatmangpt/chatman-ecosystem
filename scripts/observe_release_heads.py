#!/usr/bin/env python3
"""Observe release heads for the root crown (read-only GitHub API; outside the court).

The root crown court (scripts/release_train/root_crown) never touches the network.
This observer produces its ``observations.json``:

  repos      per pinned repository: default_branch (never hardcoded: autofde-lab is
             ``master``), visibility, head_sha, pin_sha, compare_status of pin...head
  artifacts  per remote evidence locator ``owner/name:path``: sha256, parsed JSON,
             compare_status of the artifact's own subject_sha...head, and
             ``subject_delta_paths`` (compare API ``files[]`` of subject...head: the lineage
             proof the root crown's evidence binding classifies)
  tag        the release tag: peeled commit ``sha`` (null when absent), the ref's own
             ``object_sha``/``object_type`` (annotated tag object), and ``subject_delta``
             (paths changed from the tagged commit to the observed root head)
  local_worktrees (``--local-worktrees``) operator-local topology receipt m_term
  --post-tag-bindings  ``release/<v>/hardening/inputs/delta-observations.json``: the
             changed paths of every immutable (producer subject, container head) pair the
             tagged ``closure.json`` and the tag-named crown observations record, classified
             against ``root_crown/policy/<v>/delta-allowlist.json``
  private_repos  committed ``observations/private-repos.json`` (written by
             ``--private-local <repo...>`` on the operator's machine with the operator's
             ``gh`` auth, because the repo-scoped CI token cannot read private repos) plus
             ``public_compare`` of the recorded head against a publicly observed head,
             where one is observable. The court re-verifies digests and freshness.

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
import subprocess
import sys
import urllib.error
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

sys.path.insert(0, str(Path(__file__).resolve().parent))
_REPO_ROOT = str(Path(__file__).resolve().parents[1])
if _REPO_ROOT not in sys.path:
    sys.path.append(_REPO_ROOT)
import release_line  # noqa: E402
import verify_release  # noqa: E402

API = "https://api.github.com"
Fetch = Callable[[str], dict[str, Any]]
TOPOLOGY_GLOB = "~/.claude/migration/v26925-topology/TOPOLOGY-RECEIPT*.json"
PRIVATE_FILE = "observations/private-repos.json"
PRIVATE_SCHEMA = "https://chatman.dev/root-crown/private-observations/v1"
DELTA_FILE = "hardening/inputs/delta-observations.json"
DELTA_SCHEMA = "https://chatman.dev/root-crown/hardening/delta-observations/v1"
# The compare API lists at most 300 files; a full page cannot prove the delta is complete.
COMPARE_FILE_LIMIT = 300


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


def compare_delta(fetch: Fetch, repository: str, base: str, head: str) -> dict[str, Any]:
    """``{status, ahead_by, files, delta_paths}`` of base...head (compare API ``files[]``).

    ``delta_paths`` is every touched path: ``filename`` plus ``previous_filename`` of renames/copies.

    ``delta_paths`` is None when the listing may be truncated (``COMPARE_FILE_LIMIT``): an
    incomplete listing is not a lineage proof.
    """
    if base == head:
        return {"status": "identical", "ahead_by": 0, "files": [], "delta_paths": []}
    payload = fetch(f"{API}/repos/{repository}/compare/{base}...{urllib.parse.quote(head, safe='')}")
    status = payload.get("status")
    files = sorted(
        (_delta_file(f) for f in payload.get("files", []) if f.get("filename")),
        key=lambda f: str(f["filename"]),
    )
    complete = len(files) < COMPARE_FILE_LIMIT
    touched = {f["filename"] for f in files} | {f["previous_filename"] for f in files if "previous_filename" in f}
    return {
        "status": status if status in {"identical", "ahead", "behind", "diverged"} else None,
        "ahead_by": payload.get("ahead_by"),
        "files": files,
        "delta_paths": sorted(touched) if complete else None,
    }


def _delta_file(f: dict[str, Any]) -> dict[str, Any]:
    """One compare ``files[]`` entry. A rename/copy keeps ``previous_filename``: the source path is
    part of the delta (a code file renamed into ``receipts/`` removes code from the subject), so it
    lands in ``delta_paths`` and is classified like any other touched path."""
    out = {"filename": f.get("filename"), "status": f.get("status")}
    prev = f.get("previous_filename")
    if isinstance(prev, str) and prev and prev != f.get("filename"):
        out["previous_filename"] = prev
    return out


def gh_fetch(url: str) -> dict[str, Any]:
    """Operator-local transport: ``gh api`` with the operator's own auth (the token never leaves gh)."""
    path = url[len(API) + 1 :] if url.startswith(API) else url
    proc = subprocess.run(["gh", "api", path], capture_output=True, text=True, timeout=30, check=False)
    if proc.returncode != 0:
        code = 404 if "HTTP 404" in proc.stderr else 403 if "HTTP 403" in proc.stderr else 500
        raise urllib.error.HTTPError(url, code, proc.stderr.strip()[:200], {}, None)  # type: ignore[arg-type]
    payload = json.loads(proc.stdout or "{}")
    if isinstance(payload, list):
        return {"items": payload}
    return payload


def git_blob_sha(raw: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(raw) + raw).hexdigest()


def observe_private_repo(
    fetch: Fetch, repository: str, pin_sha: str | None, paths: list[str], observed_at: str
) -> dict[str, Any]:
    """One private repository observed with operator authority; receipts carry their bytes."""
    out: dict[str, Any] = {"repository": repository, "observer": "operator-local", "observed_at": observed_at}
    if pin_sha:
        out["pin_sha"] = pin_sha
    try:
        meta = fetch(f"{API}/repos/{repository}")
        branch = meta["default_branch"]
        out["default_branch"] = branch
        out["visibility"] = meta.get("visibility")
        head = fetch(f"{API}/repos/{repository}/commits/{urllib.parse.quote(branch, safe='')}")["sha"]
        out["head_sha"] = head
        if pin_sha:
            out["compare_status"] = "identical" if head == pin_sha else _compare(fetch, repository, pin_sha, head)
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        out["error"] = _err(exc)
        return out
    receipts = []
    for path in sorted(set(paths)):
        entry: dict[str, Any] = {"path": path}
        try:
            payload = fetch(f"{API}/repos/{repository}/contents/{urllib.parse.quote(path)}?ref={head}")
            raw = base64.b64decode(payload.get("content", ""))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            entry["error"] = _err(exc)
            receipts.append(entry)
            continue
        entry.update(
            {
                "blob_sha": payload.get("sha"),
                "sha256": hashlib.sha256(raw).hexdigest(),
                "content": raw.decode("utf-8", errors="replace"),
            }
        )
        try:
            data = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            data = None
        subject = data.get("subject_sha") if isinstance(data, dict) else None
        if isinstance(subject, str) and len(subject) == 40:
            try:
                entry["subject_compare"] = (
                    "identical" if subject == head else _compare(fetch, repository, subject, head)
                )
            except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
                entry["subject_compare_error"] = _err(exc)
        receipts.append(entry)
    out["receipts"] = receipts
    try:
        runs = fetch(f"{API}/repos/{repository}/commits/{head}/check-runs?per_page=100").get("check_runs", [])
        out["check_runs"] = sorted(
            (
                {
                    "name": r.get("name"),
                    "status": r.get("status"),
                    "conclusion": r.get("conclusion"),
                    "head_sha": r.get("head_sha"),
                }
                for r in runs
            ),
            key=lambda r: (str(r["name"]), str(r["conclusion"])),
        )
    except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
        out["check_runs_error"] = _err(exc)
    return out


def observe_private_local(
    release_dir: Path, repositories: list[str], fetch: Fetch = gh_fetch, *, now: str | None = None
) -> dict[str, Any]:
    """``--private-local``: the lawful local-observation path (same shape of authority as AC-09)."""
    observed_at = now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    pins = json.loads((release_dir / "pins.json").read_text(encoding="utf-8"))
    requirements = json.loads((release_dir / "requirements.json").read_text(encoding="utf-8"))["requirements"]
    pin_of = {p["repository"]: p["sha"] for p in pins["repos"].values()}
    repos: dict[str, Any] = {}
    for repository in sorted(set(repositories)):
        paths = [
            r["evidence_locator"].partition(":")[2]
            for r in requirements
            if r["evidence_locator"].partition(":")[0] == repository
        ]
        repos[repository] = observe_private_repo(fetch, repository, pin_of.get(repository), paths, observed_at)
    return {
        "schema": PRIVATE_SCHEMA,
        "release": release_dir.name,
        "observed_at": observed_at,
        "observer": "operator-local",
        "authority": "gh-cli:operator:read",
        "repos": repos,
    }


def public_compare(fetch: Fetch, private: dict[str, Any], repos: dict[str, Any]) -> dict[str, str | None]:
    """Recorded private head vs the publicly observed head, where the public side is observable."""
    out: dict[str, str | None] = {}
    for repository, record in sorted(private.get("repos", {}).items()):
        public_head = repos.get(repository, {}).get("head_sha")
        recorded = record.get("head_sha") if isinstance(record, dict) else None
        if not public_head or not recorded:
            continue
        try:
            out[repository] = (
                "identical" if recorded == public_head else _compare(fetch, repository, recorded, public_head)
            )
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError):
            out[repository] = None
    return out


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
            delta = compare_delta(fetch, repository, subject, head)
            out["subject_compare"] = delta["status"]
            out["subject_delta_paths"] = delta["delta_paths"]
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            out["subject_compare_error"] = _err(exc)
    return out


def _closure_claim(text: Any) -> str | None:
    """The delta class a closure court's prose claims (``receipt-only paths`` -> RECEIPT_ONLY)."""
    return "RECEIPT_ONLY" if isinstance(text, str) and "receipt-only" in text else None


def immutable_pairs(release_dir: Path) -> list[dict[str, Any]]:
    """(repository, producer subject, container head) pairs recorded by tag-immutable inputs.

    Sources: ``closure.json`` courts whose ``evidence_subject_sha`` differs from the court
    ``sha``; the tag-named crown observations (``hardening/TAG-SUBJECT.json`` ->
    ``tag_receipt.observations_path``) artifacts whose receipt ``subject_sha`` differs from
    the observed ``head_sha``.
    """
    pairs: dict[tuple[str, str, str], dict[str, Any]] = {}

    def add(repository: str, base: str, head: str, source: str, claimed: str | None) -> None:
        entry = pairs.setdefault(
            (repository, base, head), {"repository": repository, "base": base, "head": head, "claims": []}
        )
        entry["claims"].append({"source": source, "claimed_class": claimed})

    closure = json.loads((release_dir / "closure.json").read_text(encoding="utf-8"))
    for i, row in enumerate(closure.get("subjects", [])):
        for j, court in enumerate(row.get("courts", [])):
            base, head = court.get("evidence_subject_sha"), court.get("sha")
            if isinstance(base, str) and isinstance(head, str) and base != head:
                add(row["repository"], base, head, f"closure.json#/subjects/{i}/courts/{j}", _closure_claim(court.get("detail")))
    record_path = release_dir / "hardening" / "TAG-SUBJECT.json"
    if record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        rel = record["tag_receipt"]["observations_path"]
        observations = json.loads((release_dir / "hardening" / rel).read_text(encoding="utf-8"))
        for locator, art in sorted(observations.get("artifacts", {}).items()):
            data = art.get("json") if isinstance(art, dict) else None
            base = data.get("subject_sha") if isinstance(data, dict) else None
            head = art.get("head_sha") if isinstance(art, dict) else None
            if "@" in locator or not (isinstance(base, str) and isinstance(head, str)) or base == head:
                continue
            add(locator.partition(":")[0], base, head, f"hardening/{rel}#/artifacts/{locator}", None)
    for entry in pairs.values():
        entry["claims"].sort(key=lambda c: c["source"])
    return [pairs[k] for k in sorted(pairs)]


def observe_post_tag_bindings(release_dir: Path, fetch: Fetch = github_fetch, *, now: str | None = None) -> dict[str, Any]:
    """``--post-tag-bindings``: observe and classify every immutable subject->container delta."""
    from scripts.release_train.root_crown import binding

    release = release_dir.name
    allowlist_path = binding.POLICY_ROOT / release / binding.ALLOWLIST_FILE
    allowlist = binding.load_allowlist(release)
    out_pairs = []
    for pair in immutable_pairs(release_dir):
        entry = dict(pair)
        try:
            entry.update(compare_delta(fetch, pair["repository"], pair["base"], pair["head"]))
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            entry.update({"error": _err(exc), "status": None, "delta_paths": None})
        computed, offending = binding.classify_delta(entry.get("delta_paths"), allowlist)
        entry["delta_class"] = computed
        entry["offending_paths"] = offending
        claims = [c["claimed_class"] for c in entry["claims"] if c["claimed_class"]]
        entry["claim_holds"] = None if not claims else all(c == computed for c in claims)
        if entry.get("status") in {"behind", "diverged"}:
            entry["binding"] = "REFUSED(EVIDENCE_SUBJECT_SPLIT)"
        elif computed is None or entry.get("status") not in {"identical", "ahead"}:
            entry["binding"] = "REFUSED(EVIDENCE_LINEAGE_MISSING)"
        elif computed == "UNBOUNDED":
            entry["binding"] = "BLOCKED(EVIDENCE_DELTA_UNBOUNDED)"
        else:
            entry["binding"] = "ADMITTED"
        out_pairs.append(entry)
    return {
        "OBSERVED": "scripts/observe_release_heads.py --post-tag-bindings -- observation, do not edit; re-observe",
        "schema": DELTA_SCHEMA,
        "release": release,
        "observed_at": now or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "allowlist": {
            "path": allowlist_path.relative_to(Path(_REPO_ROOT)).as_posix()
            if allowlist_path.is_relative_to(Path(_REPO_ROOT))
            else allowlist_path.name,
            "sha256": hashlib.sha256(allowlist_path.read_bytes()).hexdigest(),
        },
        "pairs": out_pairs,
        "authority": "NONE",
    }


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
    object_sha = obj.get("sha")
    object_type = obj.get("type")
    sha = object_sha
    if object_type == "tag":
        try:
            sha = fetch(f"{API}/repos/{repository}/git/tags/{object_sha}")["object"]["sha"]
        except (urllib.error.URLError, TimeoutError, ValueError, KeyError) as exc:
            return {"name": tag, "object_sha": object_sha, "object_type": object_type, "error": _err(exc)}
    # ``sha`` is the peeled commit; ``object_sha``/``object_type`` identify the ref's own
    # object (the annotated tag object), which the post-tag crown binds to its record.
    return {"name": tag, "sha": sha, "object_sha": object_sha, "object_type": object_type}


def observe_subject_delta(fetch: Fetch, repository: str, tag: dict[str, Any], head: str | None) -> dict[str, Any]:
    """Paths changed from the tagged commit to the observed head (post-tag drift, data only)."""
    base = tag.get("sha")
    if not base or not head:
        return {"base": base, "head": head, "paths": None}
    if base == head:
        return {"base": base, "head": head, "paths": []}
    try:
        cmp = fetch(f"{API}/repos/{repository}/compare/{base}...{head}")
    except (urllib.error.URLError, TimeoutError, ValueError) as exc:
        return {"base": base, "head": head, "error": _err(exc)}
    return {
        "base": base,
        "head": head,
        "status": cmp.get("status"),
        "paths": sorted({f.get("filename") for f in cmp.get("files", []) if f.get("filename")}),
    }


def observe_local_worktrees(pattern: str = TOPOLOGY_GLOB) -> dict[str, Any] | None:
    paths = sorted(glob.glob(os.path.expanduser(pattern)))
    if not paths:
        return None
    # Newest observation wins, never the lexically last name: ``TOPOLOGY-RECEIPT.stage1.json``
    # sorts after ``TOPOLOGY-RECEIPT.json`` but is an older stage.
    candidates = []
    for name in paths:
        raw_candidate = Path(name).read_bytes()
        parsed = json.loads(raw_candidate)
        m = parsed.get("m_term") if isinstance(parsed.get("m_term"), dict) else {}
        stamp = str(m.get("observed_at") or parsed.get("observed_at") or parsed.get("generated_at") or "")
        candidates.append((stamp, name, raw_candidate, parsed))
    _, chosen, raw, receipt = max(candidates, key=lambda c: (c[0], c[1]))
    path = Path(chosen)
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
    observations["tag"]["subject_delta"] = observe_subject_delta(
        fetch, pins["root_repository"], observations["tag"], repos.get(pins["root_repository"], {}).get("head_sha")
    )
    committed = release_dir / "observations/local-worktrees.json"
    if committed.is_file():
        observations["local_worktrees"] = json.loads(committed.read_text(encoding="utf-8"))
    private_path = release_dir / PRIVATE_FILE
    if private_path.is_file():
        private = json.loads(private_path.read_text(encoding="utf-8"))
        observations["private_repos"] = private
        observations["private_public_compare"] = public_compare(fetch, private, repos)
    return observations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", required=True)
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--private-local",
        nargs="+",
        metavar="REPO",
        help="operator-local: observe these private repos with gh auth into observations/private-repos.json",
    )
    parser.add_argument(
        "--local-worktrees", action="store_true", help="ingest the operator-local topology receipt m_term"
    )
    parser.add_argument("--cold", action="store_true", help="declare a clean runner (CI) for AC-12")
    parser.add_argument(
        "--post-tag-bindings",
        action="store_true",
        help=f"observe the immutable subject->container deltas into release/<v>/{DELTA_FILE}",
    )
    parser.add_argument("--transport", choices=("api", "gh"), default="api", help="gh = operator-local gh auth")
    parser.add_argument("--run-id")
    args = parser.parse_args(argv)
    release_dir = release_line.release_dir(args.release)
    if args.post_tag_bindings:
        doc = observe_post_tag_bindings(release_dir, gh_fetch if args.transport == "gh" else github_fetch)
        target = args.out or release_dir / DELTA_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        print(
            json.dumps(
                {
                    "out": str(target),
                    "pairs": [
                        f"{p['repository']}@{p['base'][:8]}..{p['head'][:8]}:{p['delta_class']}:{p['binding']}"
                        for p in doc["pairs"]
                    ],
                },
                sort_keys=True,
            )
        )
        return 1 if any(p.get("error") for p in doc["pairs"]) else 0
    if args.private_local:
        private = observe_private_local(release_dir, args.private_local)
        target = args.out or release_dir / PRIVATE_FILE
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(json.dumps(private, indent=2, sort_keys=True) + "\n", encoding="utf-8")
        summary = {
            repo: {
                "head_sha": rec.get("head_sha"),
                "error": rec.get("error"),
                "receipts": [(r["path"], r.get("sha256") or r.get("error")) for r in rec.get("receipts", [])],
            }
            for repo, rec in private["repos"].items()
        }
        print(json.dumps({"observed_at": private["observed_at"], "out": str(target), "repos": summary}, sort_keys=True))
        return 1 if any(rec.get("error") for rec in private["repos"].values()) else 0
    if args.out is None:
        parser.error("--out is required unless --private-local")
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
