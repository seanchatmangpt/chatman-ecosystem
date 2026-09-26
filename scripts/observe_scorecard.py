"""Scorecard observer: stream ``git archive`` of every pinned SHA out of the local object DBs.

Inputs (committed): ``release/<v>/pins.json`` (the release's repository heads; the root
repository's subject is the tag commit from ``hardening/TAG-SUBJECT.json``, never its pin),
the predecessor's ``release/<p>/closure.json`` subject SHAs (per repository the descendant-most
of its rows), and ``hardening/inputs/final-lanes.json`` ``mutation_harnesses`` (durable
locators of the harness outputs).

Transport: ``git -C <repos-root>/<name> archive --format=tar <sha>`` read as a tar stream
(nothing is extracted to disk), ``git merge-base --is-ancestor`` for the predecessor choice,
and ``scripts/durable_locator`` for the harness bytes (owner-checked local object DB).
No network. It lives outside ``scripts/release_train`` because it spawns ``git``
(release-train.yml greps that whole tree for ``subprocess.``); the measures it applies are the
pure ``scripts.release_train.scorecard.measure``. The output carries no clock and no machine path, so a re-run on the same pins
is byte-identical: ``--check`` re-observes and refuses ``REFUSED:OBSERVATION_DRIFT``.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path
from typing import Any, Iterator

from scripts.release_train.scorecard import measure

SCHEMA = "https://chatman.dev/release-scorecard/observations/v1"
OUT = "hardening/inputs/scorecard-observations.json"
OBSERVED = "scripts/observe_scorecard.py -- observation, do not edit; re-observe"
MARKETPLACE = "seanchatmangpt/ggen-marketplace"


class ObserveError(RuntimeError):
    pass


def _git(repo_dir: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
    return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, check=False)


def archive_members(repo_dir: Path, sha: str) -> Iterator[tuple[str, bytes]]:
    """(path, bytes) of every regular file of ``git archive <sha>``, in archive order."""
    proc = subprocess.Popen(
        ["git", "-C", str(repo_dir), "archive", "--format=tar", sha],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert proc.stdout is not None
    try:
        with tarfile.open(fileobj=proc.stdout, mode="r|") as tar:
            for member in tar:
                if not member.isreg():
                    continue
                handle = tar.extractfile(member)
                yield member.name, handle.read() if handle is not None else b""
    finally:
        proc.stdout.close()
        err = b""
        if proc.stderr is not None:
            err = proc.stderr.read()
            proc.stderr.close()
        if proc.wait() != 0:
            raise ObserveError(f"ARCHIVE_FAILED:{repo_dir.name}@{sha}:{err.decode(errors='replace').strip()}")


def repo_dir(repos_root: Path, repository: str) -> Path:
    return repos_root / repository.split("/", 1)[1]


def release_subjects(root: Path, release: str) -> dict[str, dict[str, Any]]:
    """repository -> {sha, source} for the release under measure."""
    release_dir = root / "release" / release
    pins = json.loads((release_dir / "pins.json").read_text(encoding="utf-8"))
    out: dict[str, dict[str, Any]] = {}
    for name, pin in sorted(pins["repos"].items()):
        out[pin["repository"]] = {"sha": pin["sha"], "source": f"release/{release}/pins.json#/repos/{name}/sha"}
    record_path = release_dir / "hardening" / "TAG-SUBJECT.json"
    if record_path.is_file():
        record = json.loads(record_path.read_text(encoding="utf-8"))
        out[pins["root_repository"]] = {
            "sha": record["subject"]["commit_sha"],
            "source": f"release/{release}/hardening/TAG-SUBJECT.json#/subject/commit_sha (root subject = tag commit)",
        }
    return out


def predecessor_subjects(root: Path, predecessor: str, repos_root: Path) -> dict[str, dict[str, Any]]:
    closure = json.loads((root / "release" / predecessor / "closure.json").read_text(encoding="utf-8"))
    by_repo: dict[str, list[str]] = {}
    for row in closure.get("subjects", []):
        shas = by_repo.setdefault(row["repository"], [])
        if row.get("sha") and row["sha"] not in shas:
            shas.append(row["sha"])
    out: dict[str, dict[str, Any]] = {}
    for repository, shas in sorted(by_repo.items()):
        shas = sorted(shas)
        directory = repo_dir(repos_root, repository)
        heads = [
            s
            for s in shas
            if all(o == s or _git(directory, "merge-base", "--is-ancestor", o, s).returncode == 0 for o in shas)
        ]
        choice = heads[0] if heads else None
        out[repository] = {
            "sha": choice,
            "candidates": shas,
            "source": f"release/{predecessor}/closure.json subjects (descendant-most)",
            "error": None if choice else "PREDECESSOR_AMBIGUOUS:no candidate descends from all others",
        }
    return out


def measure_repo(
    repos_root: Path, repository: str, sha: str, keep_lines: bool
) -> measure.TreeMeasure:
    tree = measure.TreeMeasure()
    for path, data in archive_members(repo_dir(repos_root, repository), sha):
        tree.add(path, data, keep_lines=keep_lines)
    return tree


def _harness_counts(parser: str, doc: Any) -> tuple[int, int]:
    if parser == "root_crown_report":
        return int(doc["killed"]), int(doc["total"])
    if parser == "xprod":
        mutants = doc["mutants"]
        return sum(1 for m in mutants.values() if m.get("killed") is True), len(mutants)
    if parser == "affidavit_brce":
        killed, total = str(doc["courts"]["brce_court"]["mutants_killed"]).split("/")
        return int(killed), int(total)
    if parser == "zoela_witness":
        return int(doc["summary"]["killed"]), int(doc["summary"]["mutants"])
    if parser == "ggen_igniter_origin":
        mutants = doc["replay"]["mutation_court"]["mutants"]
        return sum(1 for m in mutants if m.get("verdict") == "KILLED"), len(mutants)
    raise ObserveError(f"HARNESS_PARSER_UNKNOWN:{parser}")


def observe_harnesses(root: Path, release: str, repos_root: Path) -> list[dict[str, Any]]:
    from scripts.durable_locator import durable_locator

    lanes_path = root / "release" / release / "hardening" / "inputs" / "final-lanes.json"
    if not lanes_path.is_file():
        return []
    lanes = json.loads(lanes_path.read_text(encoding="utf-8"))
    resolver = durable_locator.Resolver(repos_root, allow_network=False)
    out = []
    for harness in lanes.get("mutation_harnesses", []):
        row: dict[str, Any] = {"name": harness["name"], "parser": harness["parser"], "locator": harness["locator"]}
        try:
            data = resolver.resolve(durable_locator.parse(harness["locator"]))
            killed, total = _harness_counts(harness["parser"], json.loads(data))
            row.update({"sha256": hashlib.sha256(data).hexdigest(), "killed": killed, "total": total, "error": None})
        except (durable_locator.Refused, ObserveError, KeyError, ValueError) as exc:
            row.update({"sha256": None, "killed": None, "total": None, "error": str(exc)})
        out.append(row)
    return out


def observe(root: Path, release: str, predecessor: str, repos_root: Path) -> dict[str, Any]:
    current = release_subjects(root, release)
    previous = predecessor_subjects(root, predecessor, repos_root)
    marketplace_blobs: dict[str, set[str]] = {}
    measures: dict[str, dict[str, measure.TreeMeasure]] = {release: {}, predecessor: {}}
    errors: dict[str, dict[str, str]] = {release: {}, predecessor: {}}
    for label, subjects in ((release, current), (predecessor, previous)):
        order = sorted(subjects, key=lambda r: (r != MARKETPLACE, r))
        for repository in order:
            sha = subjects[repository].get("sha")
            if not sha:
                errors[label][repository] = subjects[repository].get("error") or "NO_SHA"
                continue
            keep = label == release and repository in previous and previous[repository].get("sha") is not None
            try:
                measures[label][repository] = measure_repo(repos_root, repository, sha, keep_lines=keep)
            except ObserveError as exc:
                errors[label][repository] = str(exc)
                continue
            if repository == MARKETPLACE:
                marketplace_blobs[label] = {
                    f.blob for f in measures[label][repository].files.values() if f.loc is not None
                }
    releases: dict[str, Any] = {}
    for label, subjects in ((release, current), (predecessor, previous)):
        repos: dict[str, Any] = {}
        blobs = marketplace_blobs.get(label)
        for repository in sorted(subjects):
            entry = dict(subjects[repository])
            if repository in measures[label]:
                entry.update(
                    measures[label][repository].summary(None if repository == MARKETPLACE else blobs)
                )
            entry["error"] = errors[label].get(repository, entry.get("error"))
            repos[repository] = entry
        releases[label] = {"repos": repos, "marketplace_pinned": blobs is not None}
    surfaces: dict[str, list[str]] = {}
    per_repo: dict[str, Any] = {}
    no_predecessor = []
    for repository in sorted(current):
        base = measures[predecessor].get(repository)
        head = measures[release].get(repository)
        if base is None or head is None:
            no_predecessor.append(repository)
            continue
        changed = sorted(
            p for p in head.derivable if p not in base.files or base.files[p].blob != head.files[p].blob
        )
        for path in changed:
            surfaces[f"{repository}:{path}"] = head.derivable[path]
        per_repo[repository] = {
            "base": previous[repository]["sha"],
            "head": current[repository]["sha"],
            "files": len(changed),
            "loc": sum(head.files[p].loc or 0 for p in changed),
        }
    duplication = measure.duplicated_lines(surfaces)
    duplication["repos"] = per_repo
    duplication["no_predecessor"] = no_predecessor
    return {
        "OBSERVED": OBSERVED,
        "schema": SCHEMA,
        "release": release,
        "predecessor": predecessor,
        "authority": "NONE",
        "transport": "git archive --format=tar <sha> (local object DBs, streamed, no extraction, no network)",
        "parameters": measure.parameters(),
        "releases": releases,
        "new_surfaces": duplication,
        "mutation_harnesses": observe_harnesses(root, release, repos_root),
    }


def dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m scripts.observe_scorecard")
    parser.add_argument("--release", required=True)
    parser.add_argument("--predecessor", required=True)
    parser.add_argument("--root", type=Path, default=Path("."))
    parser.add_argument("--repos-root", type=Path, required=True, help="directory holding one checkout per repo name")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args(argv)
    target = args.root / "release" / args.release / OUT
    data = dump(observe(args.root, args.release, args.predecessor, args.repos_root))
    if args.write:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        print(f"WROTE:{target.as_posix()}")
        return 0
    if not target.is_file() or target.read_bytes() != data:
        print(f"REFUSED:OBSERVATION_DRIFT:{target.as_posix()}")
        return 2
    print(f"OBSERVATION_CURRENT:{target.as_posix()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
