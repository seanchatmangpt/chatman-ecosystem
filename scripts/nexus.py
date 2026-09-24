#!/usr/bin/env python3
"""Repository Nexus: one canonical join over every repository the owner holds.

`catalog/nexus.toml` is the single index of the owner's public repositories. The
Nexus joins that index against every other registry in this composition root
(catalog/repositories.toml, the West manifests, the release manifests) and
against a live inventory observation, and reports where the registries diverge.

The Nexus is OBSERVE/CONSTRUCT only. It grants no standing, never promotes a
repository to ALIVE, never actuates GitHub, and never publishes the name of a
private repository learned by observation (private repositories are counted only).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
import tomllib
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Mapping, Sequence

import yaml

ROOT = Path(__file__).resolve().parents[1]
NEXUS = Path("catalog/nexus.toml")
VIEW = Path("views/generated/nexus.md")
SCHEMA = "chatman.nexus/1"
REPORT_SCHEMA = "chatman.nexus-report/1"
ALLOWED_AUTHORITY = {"OBSERVE_ONLY"}
INVENTORY_KEYS = {"full_name", "visibility", "fork", "pushed_at"}
COORDINATE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9-]{0,38})/[A-Za-z0-9._-]{1,100}$")
RELEASE_REPOSITORY = re.compile(r'repository\s*=\s*"([A-Za-z0-9-]+/[A-Za-z0-9._-]+)"')
GITHUB_URL = re.compile(r"https://github\.com/([A-Za-z0-9-]+/[A-Za-z0-9._-]+?)(?:\.git)?/?$")


class NexusRefusal(ValueError):
    """Typed refusal: the Nexus or an observation is malformed or unlawful."""


@dataclass(frozen=True)
class Finding:
    code: str
    subject: str
    detail: str
    blocking: bool = True

    def as_dict(self) -> dict[str, Any]:
        return {"code": self.code, "subject": self.subject, "detail": self.detail, "blocking": self.blocking}


@dataclass
class Registries:
    """Every repository coordinate named elsewhere in the composition root."""

    references: dict[str, set[str]] = field(default_factory=dict)

    def add(self, coordinate: str, registry: str) -> None:
        self.references.setdefault(coordinate.lower(), set()).add(registry)


def load_toml(path: Path) -> dict[str, Any]:
    with path.open("rb") as handle:
        return tomllib.load(handle)


def canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


def names_digest(names: Iterable[str]) -> str:
    """Digest of the sorted, lower-cased coordinate set: identity of the membership."""
    return canonical_digest(sorted({name.lower() for name in names}))


# --------------------------------------------------------------------------- observation


def admit_inventory(rows: Any, owners: Sequence[str]) -> list[dict[str, Any]]:
    """Admit a raw inventory observation or refuse it with a typed reason."""
    if not isinstance(rows, list) or not rows:
        raise NexusRefusal("REFUSED[INVENTORY_EMPTY_OR_NOT_A_LIST]")
    owner_set = {owner.lower() for owner in owners}
    admitted: dict[str, dict[str, Any]] = {}
    for index, row in enumerate(rows):
        if not isinstance(row, dict) or not INVENTORY_KEYS <= set(row):
            raise NexusRefusal(f"REFUSED[INVENTORY_ROW_MALFORMED] index={index}")
        name = row["full_name"]
        if not isinstance(name, str) or not COORDINATE.match(name):
            raise NexusRefusal(f"REFUSED[INVENTORY_COORDINATE_INVALID] {name!r}")
        if row["visibility"] not in {"public", "private"}:
            raise NexusRefusal(f"REFUSED[INVENTORY_VISIBILITY_INVALID] {name} {row['visibility']!r}")
        if not isinstance(row["fork"], bool):
            raise NexusRefusal(f"REFUSED[INVENTORY_FORK_NOT_BOOLEAN] {name}")
        if name.split("/", 1)[0].lower() not in owner_set:
            continue  # access to another owner's repository is not ownership
        key = name.lower()
        if key in admitted:
            raise NexusRefusal(f"REFUSED[INVENTORY_DUPLICATE] {name}")
        admitted[key] = {
            "full_name": name,
            "visibility": row["visibility"],
            "fork": row["fork"],
            "pushed_at": str(row["pushed_at"]),
        }
    return sorted(admitted.values(), key=lambda item: item["full_name"].lower())


# --------------------------------------------------------------------------- registries


def _west_coordinates(document: Mapping[str, Any], inherited_remotes: Mapping[str, str]) -> Iterable[str]:
    manifest = document.get("manifest", {}) or {}
    remotes = dict(inherited_remotes)
    for remote in manifest.get("remotes", []) or []:
        remotes[remote["name"]] = remote["url-base"].rstrip("/")
    default_remote = (manifest.get("defaults", {}) or {}).get("remote")
    for project in manifest.get("projects", []) or []:
        if "url" in project:
            match = GITHUB_URL.match(project["url"])
            if match:
                yield match.group(1)
            continue
        base = remotes.get(project.get("remote", default_remote) or "")
        if not base or not base.startswith("https://github.com"):
            continue
        tail = project.get("repo-path", project["name"])
        match = GITHUB_URL.match(f"{base}/{tail}")
        if match:
            yield match.group(1)


def collect_registries(root: Path) -> Registries:
    """Collect every repository coordinate the composition root already names."""
    registries = Registries()

    catalog = load_toml(root / "catalog/repositories.toml")
    for repository in catalog.get("repository", []):
        match = GITHUB_URL.match(repository.get("url", ""))
        if match:
            registries.add(match.group(1), "catalog")

    west_root = yaml.safe_load((root / "west.yml").read_text(encoding="utf-8"))
    root_remotes = {
        remote["name"]: remote["url-base"].rstrip("/")
        for remote in west_root["manifest"].get("remotes", []) or []
    }
    for coordinate in _west_coordinates(west_root, {}):
        registries.add(coordinate, "west")
    for path in sorted((root / "west").glob("*.yml")):
        document = yaml.safe_load(path.read_text(encoding="utf-8"))
        for coordinate in _west_coordinates(document, root_remotes):
            registries.add(coordinate, "west-portfolio" if "portfolio" in path.name else "west-corpus")

    for path in sorted((root / "release").glob("*/manifest.toml")):
        release = path.parent.name
        for coordinate in RELEASE_REPOSITORY.findall(path.read_text(encoding="utf-8")):
            registries.add(coordinate, f"release-{release}")
    return registries


# --------------------------------------------------------------------------- classification


def compile_constellations(nexus: Mapping[str, Any]) -> list[tuple[str, list[re.Pattern[str]]]]:
    compiled = []
    for constellation in nexus.get("constellation", []):
        patterns = [re.compile(pattern, re.IGNORECASE) for pattern in constellation["match"]]
        compiled.append((constellation["id"], patterns))
    return compiled


def classify(member: Mapping[str, Any], constellations: Sequence[tuple[str, list[re.Pattern[str]]]]) -> str | None:
    if member.get("constellation"):
        return str(member["constellation"])
    name = member["full_name"].split("/", 1)[1]
    for constellation_id, patterns in constellations:
        if any(pattern.search(name) for pattern in patterns):
            return constellation_id
    return None


# --------------------------------------------------------------------------- verification


def verify(nexus: Mapping[str, Any], registries: Registries, inventory: list[dict[str, Any]] | None = None) -> list[Finding]:
    """Verify the Nexus as an index. Returns findings; blocking findings refuse."""
    findings: list[Finding] = []

    def add(code: str, subject: str, detail: str, blocking: bool = True) -> None:
        findings.append(Finding(code, subject, detail, blocking))

    header = nexus.get("nexus", {})
    if header.get("schema") != SCHEMA:
        add("NEXUS_SCHEMA_INVALID", "nexus.schema", repr(header.get("schema")))
    if header.get("authority") not in ALLOWED_AUTHORITY:
        add("NEXUS_AUTHORITY_ESCALATION", "nexus.authority", repr(header.get("authority")))
    owners = [owner.lower() for owner in header.get("owners", [])]
    if not owners:
        add("NEXUS_OWNERS_MISSING", "nexus.owners", "at least one owner is required")

    members = nexus.get("member", [])
    seen: set[str] = set()
    for member in members:
        name = member.get("full_name", "")
        key = name.lower()
        if not COORDINATE.match(name):
            add("NEXUS_COORDINATE_INVALID", name or "<missing>", "owner/repo required")
            continue
        if key in seen:
            add("NEXUS_DUPLICATE_MEMBER", name, "a repository is indexed exactly once")
        seen.add(key)
        if name.split("/", 1)[0].lower() not in owners:
            add("NEXUS_FOREIGN_MEMBER", name, "member owner is not a declared Nexus owner")
        if member.get("visibility") != "public":
            add("NEXUS_PRIVATE_NAME_PUBLISHED", name, "private repositories are counted, never named here")
        if "standing" in member:
            add("NEXUS_STANDING_ASSIGNED", name, "the Nexus indexes identity; standing belongs to owning verifiers")

    observation = nexus.get("observation", {})
    public_members = [member["full_name"] for member in members if member.get("visibility") == "public"]
    if observation.get("public") != len(public_members):
        add("NEXUS_PUBLIC_COUNT_MISMATCH", "observation.public", f"declared={observation.get('public')} indexed={len(public_members)}")
    if observation.get("public_names_sha256") != names_digest(public_members):
        add("NEXUS_MEMBERSHIP_DIGEST_MISMATCH", "observation.public_names_sha256", "membership changed without re-observation")
    forks = sum(1 for member in members if member.get("fork"))
    if observation.get("forks") != forks:
        add("NEXUS_FORK_COUNT_MISMATCH", "observation.forks", f"declared={observation.get('forks')} indexed={forks}")
    total = observation.get("public", 0) + observation.get("private", 0)
    if observation.get("total") != total:
        add("NEXUS_TOTAL_MISMATCH", "observation.total", f"declared={observation.get('total')} public+private={total}")

    constellations = compile_constellations(nexus)
    known_constellations = {constellation_id for constellation_id, _ in constellations}
    for member in members:
        constellation = classify(member, constellations)
        if constellation is None:
            add("NEXUS_UNCLASSIFIED", member["full_name"], "no constellation rule matches")
        elif constellation not in known_constellations:
            add("NEXUS_CONSTELLATION_UNKNOWN", member["full_name"], constellation)

    excluded = {item["full_name"].lower(): item for item in nexus.get("exclusion", [])}
    for key, item in excluded.items():
        if not item.get("reason"):
            add("NEXUS_EXCLUSION_UNREASONED", item["full_name"], "every exclusion names its reason")
        if key in seen:
            add("NEXUS_EXCLUSION_SHADOWS_MEMBER", item["full_name"], "an indexed member cannot also be excluded")
    for coordinate, sources in sorted(registries.references.items()):
        if coordinate.split("/", 1)[0] not in owners or coordinate in seen or coordinate in excluded:
            continue
        add("NEXUS_ORPHAN_REFERENCE", coordinate, "named by " + ", ".join(sorted(sources)) + " but not indexed or excluded")
    for key, item in excluded.items():
        if key not in registries.references:
            add("NEXUS_EXCLUSION_STALE", item["full_name"], "no registry names it any more", blocking=False)

    if inventory is not None:
        findings.extend(drift(nexus, inventory))
    return findings


def drift(nexus: Mapping[str, Any], inventory: list[dict[str, Any]]) -> list[Finding]:
    """Compare the Nexus with a fresh admitted inventory. Drift is never silent."""
    findings: list[Finding] = []
    indexed = {member["full_name"].lower(): member for member in nexus.get("member", [])}
    live_public = {row["full_name"].lower(): row for row in inventory if row["visibility"] == "public"}
    live_private = [row for row in inventory if row["visibility"] == "private"]
    for key in sorted(set(live_public) - set(indexed)):
        findings.append(Finding("NEXUS_DRIFT_UNINDEXED", live_public[key]["full_name"], "public repository not in the Nexus"))
    for key in sorted(set(indexed) - set(live_public)):
        findings.append(Finding("NEXUS_DRIFT_VANISHED", indexed[key]["full_name"], "indexed but not publicly observable (deleted, renamed, or made private)"))
    for key in sorted(set(indexed) & set(live_public)):
        if bool(indexed[key].get("fork")) != live_public[key]["fork"]:
            findings.append(Finding("NEXUS_DRIFT_FORK_FLAG", indexed[key]["full_name"], "fork flag changed"))
    declared_private = nexus.get("observation", {}).get("private")
    if declared_private != len(live_private):
        findings.append(Finding("NEXUS_DRIFT_PRIVATE_COUNT", "observation.private", f"declared={declared_private} observed={len(live_private)}", blocking=False))
    return findings


# --------------------------------------------------------------------------- construction


def refresh(nexus: dict[str, Any], inventory: list[dict[str, Any]], observed_at: str, source: str) -> dict[str, Any]:
    """CONSTRUCT a new Nexus membership from an admitted inventory, keeping curation."""
    curated = {member["full_name"].lower(): member for member in nexus.get("member", [])}
    members = []
    for row in inventory:
        if row["visibility"] != "public":
            continue
        member = {"full_name": row["full_name"], "visibility": "public", "fork": row["fork"], "pushed_at": row["pushed_at"]}
        previous = curated.get(row["full_name"].lower(), {})
        for key in ("constellation", "note"):
            if key in previous:
                member[key] = previous[key]
        members.append(member)
    public = len(members)
    private = sum(1 for row in inventory if row["visibility"] == "private")
    updated = dict(nexus)
    updated["observation"] = {
        "observed_at": observed_at,
        "source": source,
        "total": public + private,
        "public": public,
        "private": private,
        "forks": sum(1 for member in members if member["fork"]),
        "public_names_sha256": names_digest(member["full_name"] for member in members),
    }
    updated["member"] = members
    return updated


def _toml_value(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, list):
        return "[" + ", ".join(_toml_value(item) for item in value) + "]"
    return json.dumps(str(value), ensure_ascii=False)


def dump_nexus(nexus: Mapping[str, Any]) -> str:
    """Deterministic TOML serialization of the Nexus (header, rules, members)."""
    lines = [
        "# Repository Nexus: the single index of every repository the owner holds.",
        "# Canonical source. Membership is re-observed with `scripts/nexus.py refresh`;",
        "# constellation rules, notes, and exclusions are curated by hand.",
        "# views/generated/nexus.md is a projection of this file and must not be edited.",
        "",
    ]
    for table in ("nexus", "observation"):
        lines.append(f"[{table}]")
        for key, value in nexus.get(table, {}).items():
            lines.append(f"{key} = {_toml_value(value)}")
        lines.append("")
    for array in ("constellation", "exclusion", "member"):
        for item in nexus.get(array, []):
            lines.append(f"[[{array}]]")
            for key, value in item.items():
                lines.append(f"{key} = {_toml_value(value)}")
            lines.append("")
    return "\n".join(lines).rstrip("\n") + "\n"


# --------------------------------------------------------------------------- projection


def build_report(nexus: Mapping[str, Any], registries: Registries, findings: Sequence[Finding]) -> dict[str, Any]:
    constellations = compile_constellations(nexus)
    titles = {item["id"]: item.get("title", item["id"]) for item in nexus.get("constellation", [])}
    rows = []
    for member in nexus.get("member", []):
        coordinate = member["full_name"].lower()
        rows.append({
            "full_name": member["full_name"],
            "constellation": classify(member, constellations),
            "fork": bool(member.get("fork")),
            "pushed_at": member.get("pushed_at", ""),
            "registries": sorted(registries.references.get(coordinate, set())),
            "note": member.get("note", ""),
        })
    by_constellation = Counter(row["constellation"] for row in rows)
    return {
        "schema": REPORT_SCHEMA,
        "hub": nexus.get("nexus", {}).get("hub"),
        "authority": nexus.get("nexus", {}).get("authority"),
        "observation": dict(nexus.get("observation", {})),
        "nexus_sha256": canonical_digest(nexus),
        "constellations": [
            {"id": cid, "title": titles.get(cid, cid), "members": by_constellation.get(cid, 0)}
            for cid, _ in constellations
        ],
        "registered_elsewhere": sum(1 for row in rows if row["registries"]),
        "unregistered": sum(1 for row in rows if not row["registries"]),
        "members": rows,
        "exclusions": list(nexus.get("exclusion", [])),
        "findings": [finding.as_dict() for finding in findings],
        "verdict": "REFUSED" if any(f.blocking for f in findings) else "ADMITTED",
    }


def render(report: Mapping[str, Any]) -> str:
    observation = report["observation"]
    lines = [
        "# Repository Nexus",
        "",
        "> Generated from `catalog/nexus.toml` by `scripts/nexus.py render`. Do not edit manually.",
        "> The Nexus indexes identity only: it grants no standing and no actuation authority.",
        "",
        f"Hub: `{report['hub']}` · Authority: `{report['authority']}` · Observed: `{observation.get('observed_at')}`",
        "",
        "| Measure | Count |",
        "|---|---:|",
        f"| Repositories owned (public + private) | {observation.get('total')} |",
        f"| Public, indexed here | {observation.get('public')} |",
        f"| Private, counted only (names never published) | {observation.get('private')} |",
        f"| Forks among indexed | {observation.get('forks')} |",
        f"| Indexed and already named by another registry | {report['registered_elsewhere']} |",
        f"| Indexed and named by no other registry | {report['unregistered']} |",
        "",
        "## Constellations",
        "",
        "| Constellation | Members |",
        "|---|---:|",
    ]
    for constellation in report["constellations"]:
        lines.append(f"| {constellation['title']} (`{constellation['id']}`) | {constellation['members']} |")
    by_constellation: dict[str, list[Mapping[str, Any]]] = {}
    for row in report["members"]:
        by_constellation.setdefault(row["constellation"] or "unclassified", []).append(row)
    for constellation in report["constellations"]:
        rows = by_constellation.get(constellation["id"], [])
        if not rows:
            continue
        lines += ["", f"## {constellation['title']}", "", "| Repository | Fork | Last push | Registries |", "|---|---|---|---|"]
        for row in sorted(rows, key=lambda item: item["full_name"].lower()):
            registries = ", ".join(f"`{name}`" for name in row["registries"]) or "—"
            name = row["full_name"]
            lines.append(f"| [{name}](https://github.com/{name}) | {'fork' if row['fork'] else ''} | {row['pushed_at'][:10]} | {registries} |")
    if report["exclusions"]:
        lines += ["", "## Excluded references", "", "| Coordinate | Reason |", "|---|---|"]
        for item in report["exclusions"]:
            lines.append(f"| `{item['full_name']}` | {item['reason']} |")
    lines += ["", "## Verdict", "", f"`{report['verdict']}` with {len(report['findings'])} finding(s)."]
    for finding in report["findings"]:
        lines.append(f"- `{finding['code']}` {finding['subject']}: {finding['detail']}")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- CLI


def _load_inventory(path: Path, nexus: Mapping[str, Any]) -> list[dict[str, Any]]:
    return admit_inventory(json.loads(path.read_text(encoding="utf-8")), nexus.get("nexus", {}).get("owners", []))


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--root", type=Path, default=ROOT)
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("verify", help="verify the Nexus against every registry (and optionally a live inventory)")
    check.add_argument("--inventory", type=Path)
    check.add_argument("--json", action="store_true")
    renew = sub.add_parser("refresh", help="CONSTRUCT membership from an admitted inventory observation")
    renew.add_argument("--inventory", type=Path, required=True)
    renew.add_argument("--observed-at", required=True)
    renew.add_argument("--source", required=True)
    view = sub.add_parser("render", help="write or check the generated projection")
    view.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)

    root = args.root
    nexus = load_toml(root / NEXUS)
    registries = collect_registries(root)

    try:
        if args.command == "refresh":
            inventory = _load_inventory(args.inventory, nexus)
            (root / NEXUS).write_text(dump_nexus(refresh(nexus, inventory, args.observed_at, args.source)), encoding="utf-8")
            print(f"NEXUS_REFRESHED members={sum(1 for row in inventory if row['visibility'] == 'public')}")
            return 0
        inventory = _load_inventory(args.inventory, nexus) if getattr(args, "inventory", None) else None
    except NexusRefusal as refusal:
        print(str(refusal), file=sys.stderr)
        return 2

    findings = verify(nexus, registries, inventory)
    report = build_report(nexus, registries, findings)
    if args.command == "render":
        # The projection is a function of the canonical index, never of a live observation.
        text = render(build_report(nexus, registries, verify(nexus, registries)))
        target = root / VIEW
        if args.check:
            current = target.read_text(encoding="utf-8") if target.exists() else ""
            if current != text:
                print(f"REFUSED[NEXUS_PROJECTION_STALE] {VIEW}", file=sys.stderr)
                return 1
            print(f"NEXUS_PROJECTION_CURRENT {VIEW}")
            return 0
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text, encoding="utf-8")
        print(f"NEXUS_PROJECTION_WRITTEN {VIEW}")
        return 0

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for finding in findings:
            print(f"{'REFUSED' if finding.blocking else 'NOTICE'}[{finding.code}] {finding.subject}: {finding.detail}")
        observation = report["observation"]
        print(f"NEXUS_{report['verdict']} public={observation.get('public')} private={observation.get('private')} constellations={len(report['constellations'])}")
    return 1 if report["verdict"] == "REFUSED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
