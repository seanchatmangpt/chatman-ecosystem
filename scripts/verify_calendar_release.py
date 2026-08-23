#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import re
import sys
import tomllib
from pathlib import Path
from typing import Any

VERSION_RE = re.compile(r"^v?(\d{2})\.(\d{1,2})\.(\d{1,2})$")
SHA_RE = re.compile(r"^[0-9a-f]{40}$")
STANDINGS = {"UNKNOWN","PARTIAL_ALIVE","ALIVE","BLOCKED","BUILD_BROKEN","UNSUPPORTED"}
AUTHORITY = {"OBSERVE","SELECT","CONSTRUCT","VERIFY"}
REQUIRED_GATES = {
    "exact_subject",
    "process_intelligence_methodology",
    "deterministic_manufacture",
    "independent_verification",
    "receipt_replay",
    "brce_only_do",
    "failure_dominance",
}

def canonical_release(version: str) -> tuple[str, dt.date]:
    match = VERSION_RE.fullmatch(version)
    if not match:
        raise ValueError(f"invalid calendar version: {version}")
    yy, month, day = map(int, match.groups())
    date = dt.date(2000 + yy, month, day)
    return f"v{yy:02d}.{month}.{day}", date

def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()

def load(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        data = tomllib.load(handle)
    if not isinstance(data, dict):
        raise ValueError("release document must be a TOML object")
    return data

def _cycles(by_id: dict[str, dict[str, Any]]) -> list[str]:
    errors: list[str] = []
    visiting: set[str] = set()
    visited: set[str] = set()
    def visit(node: str, trail: list[str]) -> None:
        if node in visited:
            return
        if node in visiting:
            errors.append("DEPENDENCY_CYCLE:" + "->".join(trail + [node]))
            return
        visiting.add(node)
        for dep in by_id[node].get("depends_on", []):
            if dep in by_id:
                visit(dep, trail + [node])
        visiting.remove(node)
        visited.add(node)
    for node in by_id:
        visit(node, [])
    return errors

def verify(release_dir: Path) -> dict[str, Any]:
    manifest_path = release_dir / "manifest.toml"
    requirements_path = release_dir / "requirements.toml"
    manifest = load(manifest_path)
    requirements = load(requirements_path)
    errors: list[str] = []
    release = manifest.get("release", {})
    raw_version = str(release.get("version", ""))
    try:
        canonical, release_date = canonical_release(raw_version)
    except (ValueError, TypeError) as exc:
        canonical, release_date = "", None
        errors.append(f"VERSION_INVALID:{exc}")
    if canonical and release_dir.name != canonical:
        errors.append(f"VERSION_PATH_MISMATCH:{release_dir.name}!={canonical}")
    if release_date and str(release.get("target_date")) != release_date.isoformat():
        errors.append("TARGET_DATE_MISMATCH")
    if release.get("standing") not in STANDINGS:
        errors.append("RELEASE_STANDING_INVALID")
    declared_gates = set(requirements.get("release_requirements", {}).get("required_gates", []))
    for gate in sorted(REQUIRED_GATES - declared_gates):
        errors.append(f"REQUIRED_GATE_MISSING:{gate}")
    reqs = requirements.get("requirements", [])
    if not isinstance(reqs, list) or not reqs:
        errors.append("REQUIREMENTS_MISSING")
        reqs = []
    ids: set[str] = set()
    for req in reqs:
        rid = str(req.get("id", ""))
        if not rid or rid in ids:
            errors.append(f"REQUIREMENT_ID_INVALID:{rid}")
        ids.add(rid)
        if req.get("standing") not in STANDINGS:
            errors.append(f"REQUIREMENT_STANDING_INVALID:{rid}")
        subject = req.get("subject")
        if not isinstance(subject, str) or "@" not in subject or not SHA_RE.fullmatch(subject.rsplit("@",1)[-1]):
            errors.append(f"REQUIREMENT_SUBJECT_INVALID:{rid}")
        authority = set(req.get("authority", []))
        if not authority <= AUTHORITY:
            errors.append(f"REQUIREMENT_AUTHORITY_INVALID:{rid}")
        if "DO" in authority:
            errors.append(f"AMBIENT_DO_FORBIDDEN:{rid}")
        if not req.get("falsifier"):
            errors.append(f"REQUIREMENT_FALSIFIER_MISSING:{rid}")
    components = manifest.get("components", [])
    if not isinstance(components, list) or not components:
        errors.append("COMPONENTS_MISSING")
        components = []
    by_id: dict[str, dict[str, Any]] = {}
    for component in components:
        cid = str(component.get("id", ""))
        if not cid or cid in by_id:
            errors.append(f"COMPONENT_ID_INVALID:{cid}")
            continue
        by_id[cid] = component
        if not SHA_RE.fullmatch(str(component.get("sha", ""))):
            errors.append(f"COMPONENT_SHA_INVALID:{cid}")
        if component.get("standing") not in STANDINGS:
            errors.append(f"COMPONENT_STANDING_INVALID:{cid}")
        for dep in component.get("depends_on", []):
            if dep == cid:
                errors.append(f"SELF_DEPENDENCY:{cid}")
    for cid, component in by_id.items():
        for dep in component.get("depends_on", []):
            if dep not in by_id:
                errors.append(f"DEPENDENCY_NOT_ADMITTED:{cid}->{dep}")
    errors.extend(_cycles(by_id))
    return {
        "release": raw_version,
        "release_dir": release_dir.as_posix(),
        "manifest_sha256": digest(manifest_path),
        "requirements_sha256": digest(requirements_path),
        "requirement_count": len(reqs),
        "component_count": len(components),
        "standing": "BLOCKED" if errors else str(release.get("standing")),
        "errors": errors,
    }

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--release", default="v26.8.23")
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--report", type=Path)
    args = parser.parse_args(argv)
    canonical, _ = canonical_release(args.release)
    report = verify(args.root / "release" / canonical)
    rendered = json.dumps(report, sort_keys=True, indent=2)
    print(rendered)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(rendered + "\n", encoding="utf-8")
    return 0 if not report["errors"] else 2

if __name__ == "__main__":
    sys.exit(main())
