#!/usr/bin/env python3
"""Extract durable units from an exact-SHA external paradigm supplier.

The extractor observes immutable upstream content and emits candidate inventory.
It never admits a capability, grants authority, or performs consequential DO.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

from scripts.verify_external_paradigms import ParadigmRefusal, validate_registry


KINDS = {
    "skills": "skill",
    "agents": "agent",
    "commands": "command",
    "hooks": "hook",
    "workflows": "workflow",
}
SHA_RE = re.compile(r"^[0-9a-f]{40}$")


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


def _load_pattern_map(root: Path, supplier: dict) -> dict:
    rel = supplier.get("pattern_map")
    if not isinstance(rel, str) or not rel:
        raise ParadigmRefusal("REFUSED:PATTERN_MAP")
    return json.loads((root / rel).read_text(encoding="utf-8"))


def _classification_path(kind: str, item: dict) -> str:
    path = item["path"]
    if kind == "skill" and item.get("type") == "dir":
        return f"{path}/SKILL.md"
    return path


def _matches(path: str, source_path: str) -> bool:
    if source_path.endswith("/"):
        return path.startswith(source_path)
    return path == source_path


def _classification(path: str, pattern_map: dict) -> dict | None:
    candidates = []
    for entry in pattern_map.get("entries") or []:
        for source_path in entry.get("source_paths") or []:
            if _matches(path, source_path):
                candidates.append((len(source_path), source_path, entry))
    if not candidates:
        return None
    _, matched_source, entry = max(candidates, key=lambda row: row[0])
    return {
        "pattern_id": entry["id"],
        "matched_source": matched_source,
        "disposition": entry["disposition"],
        "chatman_target": entry.get("chatman_target"),
        "target_capabilities": entry.get("target_capabilities") or [],
        "authority": entry.get("authority"),
    }


def inventory_from_surfaces(
    supplier_id: str,
    repository: str,
    sha: str,
    surfaces: dict[str, list[dict]],
    pattern_map: dict,
) -> dict:
    if not SHA_RE.fullmatch(sha):
        raise ParadigmRefusal(f"REFUSED:INVALID_SUBJECT_SHA:{sha!r}")

    units = []
    counts: dict[str, int] = {}
    classified = 0

    for root_name, kind in KINDS.items():
        items = surfaces.get(root_name) or []
        counts[kind] = 0
        for item in sorted(items, key=lambda row: row.get("path", "")):
            path = item.get("path")
            item_type = item.get("type")
            blob_sha = item.get("sha")
            name = item.get("name")
            if not all(isinstance(v, str) and v for v in (path, item_type, blob_sha, name)):
                raise ParadigmRefusal(
                    f"REFUSED:MALFORMED_UPSTREAM_UNIT:{root_name}:{item!r}"
                )

            classification_path = _classification_path(kind, item)
            cls = _classification(classification_path, pattern_map)
            if cls is not None:
                classified += 1

            units.append(
                {
                    "id": f"{supplier_id}:{kind}:{name}",
                    "kind": kind,
                    "name": name,
                    "path": path,
                    "source_path": path,
                    "classification_path": classification_path,
                    "upstream_object_sha": blob_sha,
                    "upstream_object_type": item_type,
                    "state": "CANDIDATE",
                    "standing": "NONE",
                    "classification": cls,
                }
            )
            counts[kind] += 1

    units.sort(key=lambda row: (row["kind"], row["path"]))
    return {
        "schema": "chatman.external-paradigm-inventory.v1",
        "supplier": supplier_id,
        "repository": repository,
        "subject_sha": sha,
        "state": "OBSERVED",
        "standing": "NONE",
        "counts": counts,
        "unit_count": len(units),
        "classified_count": classified,
        "unmapped_count": len(units) - classified,
        "units": units,
    }


def fetch_surfaces(repository: str, sha: str, token: str | None = None) -> dict:
    quoted_ref = urllib.parse.quote(sha, safe="")
    result = {}
    for root_name in KINDS:
        url = (
            f"https://api.github.com/repos/{repository}/contents/"
            f"{root_name}?ref={quoted_ref}"
        )
        payload = _json_get(url, token)
        if not isinstance(payload, list):
            raise ParadigmRefusal(f"REFUSED:UPSTREAM_SURFACE:{root_name}")
        result[root_name] = payload
    return result


def extract(
    root: Path,
    supplier_id: str,
    token: str | None = None,
    fixture_surfaces: dict[str, list[dict]] | None = None,
) -> dict:
    registry_path = root / "upstream" / "paradigms.json"
    validate_registry(registry_path, root)
    registry = json.loads(registry_path.read_text(encoding="utf-8"))
    supplier = _supplier(registry, supplier_id)
    pattern_map = _load_pattern_map(root, supplier)

    repository = supplier["repository"]
    sha = supplier["pin"]["sha"]
    surfaces = (
        fixture_surfaces
        if fixture_surfaces is not None
        else fetch_surfaces(repository, sha, token)
    )

    return inventory_from_surfaces(
        supplier_id=supplier_id,
        repository=repository,
        sha=sha,
        surfaces=surfaces,
        pattern_map=pattern_map,
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--supplier", default="ecc")
    parser.add_argument("--json-out")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    try:
        result = extract(
            root,
            args.supplier,
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
