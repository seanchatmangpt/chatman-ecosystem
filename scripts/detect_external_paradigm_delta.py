#!/usr/bin/env python3
"""Detect exact-SHA upstream paradigm deltas without admitting them.

A mutable ref may be observed only to discover a new immutable candidate SHA.
The discovered SHA remains CANDIDATE and confers no authority or standing.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

try:
    from scripts.verify_external_paradigms import ParadigmRefusal, validate_registry
except ModuleNotFoundError:
    from verify_external_paradigms import ParadigmRefusal, validate_registry


WATCH_ROOTS = ("skills/", "agents/", "commands/", "hooks/", "docs/architecture/")


class TransportBlocked(RuntimeError):
    """External observation could not be completed."""


def _json_get(url: str, token: str | None = None) -> Any:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "chatman-ecosystem-epr/1",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.load(response)
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as exc:
        raise TransportBlocked(f"BLOCKED:TRANSPORT:{url}:{exc}") from exc


def _supplier(registry: dict, supplier_id: str) -> dict:
    for supplier in registry.get("suppliers") or []:
        if supplier.get("id") == supplier_id:
            return supplier
    raise ParadigmRefusal(f"REFUSED:UNKNOWN_SUPPLIER:{supplier_id}")


def _pattern_map(root: Path, supplier: dict) -> dict:
    path = supplier.get("pattern_map")
    if not isinstance(path, str) or not path:
        raise ParadigmRefusal("REFUSED:PATTERN_MAP")
    return json.loads((root / path).read_text(encoding="utf-8"))


def _matches(path: str, source_path: str) -> bool:
    if source_path.endswith("/"):
        return path.startswith(source_path)
    return path == source_path


def _unit_for(path: str) -> str | None:
    parts = path.split("/")
    if path.startswith("skills/") and len(parts) >= 2:
        return "/".join(parts[:2]) + "/"
    if path.startswith("agents/") and len(parts) >= 2:
        return "/".join(parts[:2])
    if path.startswith("commands/") and len(parts) >= 2:
        return "/".join(parts[:2])
    if path.startswith("hooks/") and len(parts) >= 2:
        return "/".join(parts[:2])
    if path.startswith("docs/architecture/") and len(parts) >= 3:
        return path
    return None


def classify_compare(files: list[dict], pattern_map: dict) -> dict:
    entries = pattern_map.get("entries") or []
    matched: dict[str, set[str]] = {}
    new_units: set[str] = set()
    unmapped: list[str] = []
    changed: list[dict] = []

    for item in files:
        path = item.get("filename")
        if not isinstance(path, str):
            continue
        status = item.get("status") or "unknown"
        changed.append({"path": path, "status": status})

        pattern_ids = []
        for entry in entries:
            if any(_matches(path, src) for src in entry.get("source_paths") or []):
                eid = entry.get("id")
                if isinstance(eid, str):
                    pattern_ids.append(eid)
                    matched.setdefault(eid, set()).add(path)

        if not pattern_ids and path.startswith(WATCH_ROOTS):
            unmapped.append(path)

        if status == "added":
            unit = _unit_for(path)
            if unit is not None:
                new_units.add(unit)

    return {
        "changed_files": changed,
        "matched_patterns": {
            key: sorted(paths) for key, paths in sorted(matched.items())
        },
        "new_units": sorted(new_units),
        "unmapped_files": sorted(unmapped),
    }


def detect(
    root: Path,
    supplier_id: str,
    discovery_ref: str,
    token: str | None = None,
    compare_payload: dict | None = None,
    discovered_sha: str | None = None,
) -> dict:
    registry_path = root / "upstream" / "paradigms.json"
    validate_registry(registry_path, root)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    supplier = _supplier(registry, supplier_id)
    pmap = _pattern_map(root, supplier)

    repository = supplier["repository"]
    base_sha = supplier["pin"]["sha"]

    if discovered_sha is None:
        commit = _json_get(
            f"https://api.github.com/repos/{repository}/commits/{discovery_ref}",
            token,
        )
        discovered_sha = commit.get("sha")

    if not isinstance(discovered_sha, str) or len(discovered_sha) != 40:
        raise ParadigmRefusal(
            f"REFUSED:DISCOVERED_SUBJECT:{supplier_id}:{discovered_sha!r}"
        )

    if discovered_sha == base_sha:
        return {
            "schema": "chatman.external-paradigm-delta.v1",
            "supplier": supplier_id,
            "repository": repository,
            "discovery_ref": discovery_ref,
            "base_sha": base_sha,
            "candidate_sha": discovered_sha,
            "state": "CURRENT",
            "standing": "NONE",
            "changed_files": [],
            "matched_patterns": {},
            "new_units": [],
            "unmapped_files": [],
        }

    if compare_payload is None:
        compare_payload = _json_get(
            f"https://api.github.com/repos/{repository}/compare/{base_sha}...{discovered_sha}",
            token,
        )

    classified = classify_compare(compare_payload.get("files") or [], pmap)
    return {
        "schema": "chatman.external-paradigm-delta.v1",
        "supplier": supplier_id,
        "repository": repository,
        "discovery_ref": discovery_ref,
        "base_sha": base_sha,
        "candidate_sha": discovered_sha,
        "compare_status": compare_payload.get("status"),
        "ahead_by": compare_payload.get("ahead_by"),
        "behind_by": compare_payload.get("behind_by"),
        "state": "CANDIDATE_DELTA",
        "standing": "NONE",
        **classified,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--supplier", default="ecc")
    parser.add_argument(
        "--discovery-ref",
        default="main",
        help="mutable ref used only to discover a new immutable candidate SHA",
    )
    parser.add_argument("--json-out")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        result = detect(
            root,
            args.supplier,
            args.discovery_ref,
            token=os.environ.get("GITHUB_TOKEN"),
        )
    except ParadigmRefusal as exc:
        print(json.dumps({"state": "REFUSED", "reason": str(exc)}, sort_keys=True))
        return 2
    except TransportBlocked as exc:
        print(json.dumps({"state": "BLOCKED", "reason": str(exc)}, sort_keys=True))
        return 3

    rendered = json.dumps(result, indent=2, sort_keys=True)
    print(rendered)
    if args.json_out:
        Path(args.json_out).write_text(rendered + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
