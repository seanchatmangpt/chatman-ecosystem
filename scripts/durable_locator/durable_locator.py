"""Durable evidence locators (CE23-9 grammar): parse, resolve, rehash, index, verify.

Grammar (anything else is refused):

    git:<owner>/<repo>@<40hex>:<path>        a blob at an exact commit
    git-notes:refs/notes/<ref>@<40hex>       a git note on an exact commit
    https://...                               an external URL (no local resolution)

Refused locators (typed REFUSED[<code>], broken_term R_missing_replay, EVIDENCE_FAILURE):
    SCRATCH_LOCATOR   session scratch, /tmp, /private/tmp, ~/.claude, .claude/migration
    ABSOLUTE_PATH     any other absolute or home-relative filesystem path
    MISSING_SHA       owner/repo:path or git:owner/repo:path without @<40hex>
    MALFORMED         everything else

Resolution reads the canonical object database of ``<repos-root>/<repo>`` with
``git cat-file`` (read-only; never touches a working tree) only when that checkout's
``origin`` remote names the locator's full ``<owner>/<repo>``; otherwise (no checkout,
or OWNER_MISMATCH) it falls back to ``gh api`` on the full ``owner/repo``, and without
network it refuses REFUSED[OWNER_MISMATCH] / REFUSED[REPOSITORY_UNAVAILABLE]. This module is deliberately
outside ``scripts/release_train`` (not only root_crown) because it spawns
``git``/``gh``: release-train.yml's static no-DO boundary greps the whole
``scripts/release_train`` tree for ``subprocess.``, and root_crown stays
subprocess-free.

Subcommands:
    parse <locator>                        print the parsed locator or the refusal
    index --rules R --out O --write|--check
                                           generate INDEX.json from a hand-written rules file
    verify <INDEX.json>                    resolve + rehash every durable row
    completeness <INDEX.json>              rescan the sources; 0 unindexed scratch locators
    requirements-locators --release V --write|--check
                                           generate release/V/hardening/requirements-locators.json

Exit codes: 0 ok, 1 refusal/drift/mismatch, 2 usage.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator

SCHEMA_INDEX = "https://chatman.dev/root-crown/hardening/evidence-index/v1"
SCHEMA_REQ = "https://chatman.dev/root-crown/hardening/requirements-locators/v1"
GENERATED_INDEX = "scripts/durable_locator/durable_locator.py index -- do not edit; run --write"
GENERATED_REQ = (
    "scripts/durable_locator/durable_locator.py requirements-locators -- do not edit; run --write"
)

HEX40 = r"[0-9a-f]{40}"
_REPO = r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+"
GIT_RX = re.compile(rf"^git:(?P<repo>{_REPO})@(?P<sha>{HEX40}):(?P<path>[^\s]+)$")
NOTES_RX = re.compile(rf"^git-notes:(?P<ref>refs/notes/[A-Za-z0-9_./-]+)@(?P<sha>{HEX40})$")
HTTPS_RX = re.compile(r"^https://[^\s]+$")
SHALESS_RX = re.compile(rf"^(?:git:)?(?P<repo>{_REPO})(?:@(?P<badsha>[^:]*))?:(?P<path>[^\s]+)$")
# Scratch / tmp / agent-home evidence: never durable. Also used by the completeness scan.
SCRATCH_RX = re.compile(
    r"(scratchpad/|/private/tmp/|(?<![\w.])/tmp/|~/\.claude|/Users/[^/\s]+/\.claude/|\.claude/migration)"
)


class Refused(Exception):
    """A typed refusal: ``code`` is the REFUSED[...] discriminator."""

    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"REFUSED[{code}] {detail}")
        self.code = code
        self.detail = detail


@dataclass(frozen=True)
class Locator:
    kind: str  # git | git-notes | https
    repository: str | None
    sha: str | None
    path: str | None
    ref: str | None
    text: str

    def as_dict(self) -> dict[str, Any]:
        return {k: v for k, v in self.__dict__.items() if v is not None}


def parse(text: str) -> Locator:
    """Parse one locator or raise :class:`Refused`. Scratch checks run first."""
    if not isinstance(text, str) or not text or text != text.strip():
        raise Refused("MALFORMED", repr(text))
    if SCRATCH_RX.search(text):
        raise Refused("SCRATCH_LOCATOR", text)
    if text.startswith("/") or text.startswith("~"):
        raise Refused("ABSOLUTE_PATH", text)
    m = GIT_RX.match(text)
    if m:
        path = m["path"]
        if path.startswith("/") or ".." in path.split("/"):
            raise Refused("MALFORMED", f"path must be repo-relative: {text}")
        return Locator("git", m["repo"], m["sha"], path, None, text)
    m = NOTES_RX.match(text)
    if m:
        return Locator("git-notes", None, m["sha"], None, m["ref"], text)
    if HTTPS_RX.match(text):
        return Locator("https", None, None, None, None, text)
    m = SHALESS_RX.match(text)
    if m and not text.startswith(("http:", "https:")):
        raise Refused("MISSING_SHA", text)
    raise Refused("MALFORMED", text)


_REMOTE_RX = re.compile(
    r"^(?:(?:https?|ssh|git)://(?:[^@/\s]+@)?[^/\s]+/|[^@/\s]+@[^:/\s]+:)"
    r"(?P<owner>[A-Za-z0-9_.-]+)/(?P<repo>[A-Za-z0-9_.-]+?)(?:\.git)?/?$"
)


def remote_slug(url: str) -> str | None:
    """Normalize an https/ssh/scp-style remote URL to ``owner/repo``; None if unrecognized."""
    m = _REMOTE_RX.match(url.strip())
    return f"{m['owner']}/{m['repo']}" if m else None


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


class Resolver:
    """Reads blobs at exact commits: local object DB first, ``gh api`` second."""

    def __init__(self, repos_root: Path, allow_network: bool = True) -> None:
        self.repos_root = Path(repos_root)
        self.allow_network = allow_network

    def _candidate_dir(self, repository: str) -> Path | None:
        d = self.repos_root / repository.split("/", 1)[1]
        return d if (d / ".git").exists() or (d / "HEAD").is_file() else None

    def origin_slug(self, repo_dir: Path) -> str | None:
        """``owner/repo`` of the checkout's ``origin`` remote (normalized), or None."""
        out = self._git(repo_dir, "remote", "get-url", "origin")
        if out.returncode != 0:
            return None
        return remote_slug(out.stdout.decode("utf-8", "replace").strip())

    def owner_mismatch(self, repository: str) -> str | None:
        """Why the local checkout named like ``repository`` is NOT that repository, else None.

        The directory is keyed by the repo name only, so ``git:attacker/<repo>@...`` would
        otherwise resolve against the canonical ``<owner>/<repo>`` object database. The
        checkout's ``origin`` remote must name the full ``owner/repo`` (case-insensitive).
        """
        d = self._candidate_dir(repository)
        if d is None:
            return None
        slug = self.origin_slug(d)
        if slug is None:
            return f"{repository}: local checkout {d.name} has no recognizable origin remote"
        if slug.lower() != repository.lower():
            return f"{repository}: local checkout {d.name} origin is {slug}"
        return None

    def local_dir(self, repository: str) -> Path | None:
        """The local checkout for ``repository`` only if its origin remote names ``owner/repo``."""
        d = self._candidate_dir(repository)
        if d is None or self.owner_mismatch(repository) is not None:
            return None
        return d

    def _git(self, repo_dir: Path, *args: str) -> subprocess.CompletedProcess[bytes]:
        return subprocess.run(["git", "-C", str(repo_dir), *args], capture_output=True, check=False)

    def blob(self, repository: str, sha: str, path: str) -> bytes:
        d = self.local_dir(repository)
        mismatch = self.owner_mismatch(repository) if d is None else None
        if d is not None:
            if self._git(d, "cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
                raise Refused("SHA_NOT_FOUND", f"{repository}@{sha}")
            if self._git(d, "cat-file", "-e", f"{sha}:{path}").returncode != 0:
                raise Refused("PATH_NOT_FOUND", f"{repository}@{sha}:{path}")
            out = self._git(d, "cat-file", "blob", f"{sha}:{path}")
            if out.returncode != 0:
                raise Refused("NOT_A_BLOB", f"{repository}@{sha}:{path}")
            return out.stdout
        if not self.allow_network:
            if mismatch is not None:
                raise Refused("OWNER_MISMATCH", mismatch)
            raise Refused("REPOSITORY_UNAVAILABLE", repository)
        # Owner mismatch with network: the gh api path addresses the full owner/repo.
        out = subprocess.run(
            ["gh", "api", "-H", "Accept: application/vnd.github.raw", f"repos/{repository}/contents/{path}?ref={sha}"],
            capture_output=True,
            check=False,
        )
        if out.returncode != 0:
            raise Refused("REMOTE_UNRESOLVED", f"{repository}@{sha}:{path}")
        return out.stdout

    def tree_paths(self, repository: str, sha: str, prefix: str) -> list[str]:
        d = self.local_dir(repository)
        if d is None:
            mismatch = self.owner_mismatch(repository)
            if mismatch is not None:
                raise Refused("OWNER_MISMATCH", mismatch)
            raise Refused("REPOSITORY_UNAVAILABLE", repository)
        out = self._git(d, "ls-tree", "-r", "-z", "--name-only", sha, "--", prefix)
        if out.returncode != 0:
            raise Refused("SHA_NOT_FOUND", f"{repository}@{sha}")
        return sorted(p for p in out.stdout.decode("utf-8").split("\0") if p)

    def resolve(self, loc: Locator) -> bytes:
        if loc.kind == "git":
            assert loc.repository and loc.sha and loc.path
            return self.blob(loc.repository, loc.sha, loc.path)
        if loc.kind == "git-notes":
            raise Refused("UNSUPPORTED_RESOLUTION", f"git-notes resolution needs a repository: {loc.text}")
        raise Refused("UNSUPPORTED_RESOLUTION", f"https locators are not fetched: {loc.text}")


def git_locator(repository: str, sha: str, path: str) -> str:
    return f"git:{repository}@{sha}:{path}"


# ---------------------------------------------------------------- scanning


def _escape(key: str) -> str:
    return key.replace("~", "~0").replace("/", "~1")


def walk_strings(value: Any, pointer: str = "") -> Iterator[tuple[str, str]]:
    if isinstance(value, dict):
        for k, v in value.items():
            yield from walk_strings(v, f"{pointer}/{_escape(k)}")
    elif isinstance(value, list):
        for i, v in enumerate(value):
            yield from walk_strings(v, f"{pointer}/{i}")
    elif isinstance(value, str):
        yield pointer, value


def scan_bytes(data: bytes) -> list[tuple[str, str]]:
    """Every (pointer, string) holding a scratch locator. JSON: RFC 6901 pointer; text: #L<n>."""
    try:
        doc = json.loads(data)
    except (ValueError, UnicodeDecodeError):
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            return []
        return [(f"#L{i}", line) for i, line in enumerate(text.splitlines(), 1) if SCRATCH_RX.search(line)]
    return [(p, s) for p, s in walk_strings(doc) if SCRATCH_RX.search(s)]


def pointer_get(doc: Any, pointer: str) -> Any:
    cur = doc
    for raw in pointer.split("/")[1:]:
        key = raw.replace("~1", "/").replace("~0", "~")
        cur = cur[int(key)] if isinstance(cur, list) else cur[key]
    return cur


def scan_sources(resolver: Resolver, sources: list[dict[str, Any]]) -> list[dict[str, Any]]:
    hits: list[dict[str, Any]] = []
    for src in sources:
        repo, sha, prefix = src["repository"], src["sha"], src["prefix"]
        match = re.compile(src.get("match", ".*"))
        for path in resolver.tree_paths(repo, sha, prefix):
            if not match.search(path):
                continue
            data = resolver.blob(repo, sha, path)
            for pointer, text in scan_bytes(data):
                hits.append({"repository": repo, "sha": sha, "path": path, "pointer": pointer, "text": text})
    return hits


# ---------------------------------------------------------------- index


def _recorded(doc: Any, pointer: str, field: str | None, up: int) -> str | None:
    if not field or doc is None or pointer.startswith("#"):
        return None
    parent = "/".join(pointer.split("/")[: -up]) if up else pointer
    try:
        v = pointer_get(doc, parent).get(field)
    except (KeyError, IndexError, ValueError, AttributeError, TypeError):
        return None
    if not isinstance(v, str):
        return None
    return v.removeprefix("sha256:")


def _match_rule(rules: list[dict[str, Any]], hit: dict[str, Any]) -> dict[str, Any] | None:
    for rule in rules:
        if rule.get("repository", hit["repository"]) != hit["repository"]:
            continue
        if not re.search(rule.get("path", ".*"), hit["path"]):
            continue
        if not re.search(rule.get("pointer", ".*"), hit["pointer"]):
            continue
        if not re.search(rule.get("locator", ".*"), hit["text"]):
            continue
        return rule
    return None


def _companion(
    resolver: "Resolver", e1: dict[str, Any], doc: Any, pointer: str, comp: dict[str, Any], up: int
) -> dict[str, Any]:
    """A durable file bound to a digest recorded either in the scanned source or in another E1 file."""
    e1_repo, e1_sha, e1_root = e1["repository"], e1["commit"], e1["root"]
    path = f"{e1_root}/{comp['durable']}"
    digest = sha256_hex(resolver.blob(e1_repo, e1_sha, path))
    out: dict[str, Any] = {"durable_locator": git_locator(e1_repo, e1_sha, path), "sha256": digest}
    if "recorded_by" in comp:
        by = comp["recorded_by"]
        by_path = f"{e1_root}/{by['durable']}"
        try:
            rec = pointer_get(json.loads(resolver.blob(e1_repo, e1_sha, by_path)), by["pointer"])
        except (KeyError, IndexError, ValueError):
            rec = None
        rec = rec.removeprefix("sha256:") if isinstance(rec, str) else None
        out["recorded_by"] = f"{git_locator(e1_repo, e1_sha, by_path)}#{by['pointer']}"
    else:
        rec = _recorded(doc, pointer, comp.get("recorded_field"), int(comp.get("recorded_up", up)))
        out["recorded_field"] = comp.get("recorded_field")
    out["recorded_sha256"] = rec
    out["recorded_in_closure"] = "UNRECORDED" if rec is None else ("match" if rec == digest else "MISMATCH")
    if out["recorded_in_closure"] == "MISMATCH" and "divergence" in comp:
        out["divergence"] = comp["divergence"]
    return out


def build_index(resolver: Resolver, rules_doc: dict[str, Any]) -> dict[str, Any]:
    e1 = rules_doc["e1"]
    e1_repo, e1_sha, e1_root = e1["repository"], e1["commit"], e1["root"]
    hits = scan_sources(resolver, rules_doc["sources"])
    docs: dict[tuple[str, str, str], Any] = {}
    rows: list[dict[str, Any]] = []
    unmatched: list[dict[str, Any]] = []

    def e1_file(rel: str) -> tuple[str, str]:
        path = f"{e1_root}/{rel}"
        return git_locator(e1_repo, e1_sha, path), sha256_hex(resolver.blob(e1_repo, e1_sha, path))

    for hit in hits:
        key = (hit["repository"], hit["sha"], hit["path"])
        if key not in docs:
            try:
                docs[key] = json.loads(resolver.blob(*key))
            except ValueError:
                docs[key] = None
        rule = _match_rule(rules_doc["rules"], hit)
        if rule is None:
            unmatched.append(hit)
            continue
        doc = docs[key]
        up = int(rule.get("recorded_up", 1))
        recorded = _recorded(doc, hit["pointer"], rule.get("recorded_field"), up)
        row: dict[str, Any] = {
            "source": git_locator(hit["repository"], hit["sha"], hit["path"]),
            "json_pointer": hit["pointer"],
            "tagged_locator": hit["text"],
            "rule": rule["id"],
            "recorded_sha256": recorded,
        }
        if hit["path"].endswith("/closure.json"):
            row["closure_pointer"] = hit["pointer"]
        if "durable" in rule:
            loc, digest = e1_file(rule["durable"])
            row["durable_locator"] = loc
            row["sha256"] = digest
            row["recorded_in_closure"] = (
                "UNRECORDED" if recorded is None else ("match" if recorded == digest else "MISMATCH")
            )
            row["standing"] = "ALIVE" if row["recorded_in_closure"] != "MISMATCH" else "REFUSED(HASH_MISMATCH)"
        else:
            row["durable_locator"] = f"RESIDUE:{rule['residue']}"
            row["sha256"] = None
            row["recorded_in_closure"] = "UNRECORDED" if recorded is None else "RESIDUE_RECORDED"
            row["standing"] = rule["standing"]
            for k in ("broken_term", "rfc_class", "edge"):
                if k in rule:
                    row[k] = rule[k]
        companions = [_companion(resolver, e1, doc, hit["pointer"], comp, up) for comp in rule.get("companions", [])]
        if companions:
            row["companions"] = companions
        rows.append(row)

    supplemental = []
    for sup in rules_doc.get("supplemental", []):
        src = sup["source"]
        loc = parse(src)
        doc = json.loads(resolver.resolve(loc))
        dl, digest = e1_file(sup["durable"])
        rec = _recorded(doc, sup["json_pointer"], sup["recorded_field"], 0)
        supplemental.append(
            {
                "source": src,
                "json_pointer": sup["json_pointer"],
                "tagged_locator": None,
                "reason": sup["reason"],
                "durable_locator": dl,
                "sha256": digest,
                "recorded_field": sup["recorded_field"],
                "recorded_sha256": rec,
                "recorded_in_closure": "UNRECORDED" if rec is None else ("match" if rec == digest else "MISMATCH"),
            }
        )

    counts: dict[str, int] = {}
    for r in rows:
        dl = r["durable_locator"]
        kind = dl.split("(")[0] if dl.startswith("RESIDUE:") else "durable"
        counts[kind] = counts.get(kind, 0) + 1
    return {
        "GENERATED": GENERATED_INDEX,
        "schema": SCHEMA_INDEX,
        "release": rules_doc["release"],
        "e1": e1,
        "sources": rules_doc["sources"],
        "rows": rows,
        "supplemental": supplemental,
        "replays": rules_doc.get("replays", []),
        "unmatched": [
            {**h, "standing": "REFUSED(UNINDEXED_SCRATCH_LOCATOR)", "broken_term": "R_missing_replay"}
            for h in unmatched
        ],
        "summary": {"rows": len(rows), "by_disposition": dict(sorted(counts.items())), "unmatched": len(unmatched)},
    }


def dump(value: Any) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def verify_index(resolver: Resolver, index: dict[str, Any], resolve_only: bool = False) -> list[str]:
    """Resolve + rehash every durable locator in rows, companions and supplemental rows.

    ``resolve_only`` (requirements-locators.json: no digests are pinned there) checks that
    every durable locator parses and resolves to a blob; a null locator is refused.
    """
    findings: list[str] = []
    entries: list[tuple[str, dict[str, Any]]] = []
    for i, r in enumerate(index.get("rows", [])):
        entries.append((f"rows/{i}", r))
        entries += [(f"rows/{i}/companions/{j}", c) for j, c in enumerate(r.get("companions", []))]
    entries += [(f"supplemental/{i}", s) for i, s in enumerate(index.get("supplemental", []))]
    for where, e in entries:
        dl = e.get("durable_locator")
        if dl is None:
            findings.append(f"REFUSED[UNBOUND_LOCATOR] {where} {e.get('standing')}")
            continue
        if isinstance(dl, str) and dl.startswith("RESIDUE:"):
            if not e.get("standing") or e.get("sha256") is not None:
                findings.append(f"REFUSED[UNTYPED_RESIDUE] {where}")
            continue
        try:
            loc = parse(dl)
            data = resolver.resolve(loc)
        except Refused as exc:
            findings.append(f"{exc} at {where}")
            continue
        if resolve_only:
            continue
        if sha256_hex(data) != e.get("sha256"):
            findings.append(f"REFUSED[HASH_MISMATCH] {where} {dl} recorded={e.get('sha256')} observed={sha256_hex(data)}")
        elif e.get("recorded_in_closure") == "MISMATCH" and not e.get("divergence"):
            findings.append(f"REFUSED[RECORDED_DIGEST_MISMATCH] {where} {dl}")
    for i, u in enumerate(index.get("unmatched", [])):
        findings.append(f"REFUSED[UNINDEXED_SCRATCH_LOCATOR] unmatched/{i} {u.get('path')}{u.get('pointer')}")
    return findings


def completeness(resolver: Resolver, index: dict[str, Any]) -> list[str]:
    """Rescan the index's sources; every scratch locator must have exactly one row."""
    indexed = {(r["source"], r["json_pointer"]): r["tagged_locator"] for r in index.get("rows", [])}
    findings = []
    seen = set()
    for hit in scan_sources(resolver, index["sources"]):
        key = (git_locator(hit["repository"], hit["sha"], hit["path"]), hit["pointer"])
        seen.add(key)
        if key not in indexed:
            findings.append(f"REFUSED[UNINDEXED_SCRATCH_LOCATOR] {key[0]}#{key[1]}")
        elif indexed[key] != hit["text"]:
            findings.append(f"REFUSED[LOCATOR_TEXT_DRIFT] {key[0]}#{key[1]}")
    for key in sorted(set(indexed) - seen):
        findings.append(f"REFUSED[STALE_ROW] {key[0]}#{key[1]}")
    return findings


# ---------------------------------------------------------------- requirements


def requirements_locators(repo_root: Path, release: str) -> dict[str, Any]:
    rel = repo_root / "release" / release
    reqs = json.loads((rel / "requirements.json").read_text(encoding="utf-8"))
    pins = json.loads((rel / "pins.json").read_text(encoding="utf-8"))
    subject = json.loads((rel / "hardening" / "TAG-SUBJECT.json").read_text(encoding="utf-8"))
    by_repo = {v["repository"]: v["sha"] for v in pins["repos"].values()}
    root_repo = subject["repository"]
    crown = subject["subject"]["commit_sha"]
    rows = []
    for i, req in enumerate(reqs["requirements"]):
        for pointer, text in walk_strings(req, f"/requirements/{i}"):
            if not pointer.endswith("/evidence_locator"):
                continue
            row: dict[str, Any] = {"id": req["id"], "json_pointer": pointer, "tagged_locator": text}
            if text.startswith("local:"):
                row.update(
                    {
                        "binding": "tag-commit (v26.9.25^{commit}, TAG-SUBJECT.json subject.commit_sha)",
                        "durable_locator": git_locator(root_repo, crown, text[len("local:"):]),
                    }
                )
            else:
                m = SHALESS_RX.match(text)
                repo = m["repo"] if m else None
                if repo is None or m["badsha"] is not None:
                    row.update({"durable_locator": None, "standing": "REFUSED(MALFORMED)"})
                elif repo not in by_repo:
                    row.update({"durable_locator": None, "standing": "REFUSED(UNPINNED_REPOSITORY)"})
                else:
                    row.update(
                        {
                            "binding": "pins.json repos[*].sha (tag-time default-branch head)",
                            "durable_locator": git_locator(repo, by_repo[repo], m["path"]),
                        }
                    )
            rows.append(row)
    return {
        "GENERATED": GENERATED_REQ,
        "schema": SCHEMA_REQ,
        "release": release,
        "inputs": [f"release/{release}/requirements.json", f"release/{release}/pins.json",
                   f"release/{release}/hardening/TAG-SUBJECT.json"],
        "rows": rows,
    }


# ---------------------------------------------------------------- cli


def _write_or_check(path: Path, data: bytes, write: bool) -> int:
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        print(f"WROTE {path}")
        return 0
    if not path.is_file() or path.read_bytes() != data:
        print(f"REFUSED:PROJECTION_DRIFT:{path}")
        return 1
    print(f"OK {path}")
    return 0


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="durable_locator")
    ap.add_argument("--repos-root", default=os.environ.get("DURABLE_LOCATOR_REPOS_ROOT", str(Path.home())))
    ap.add_argument("--no-network", action="store_true")
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("parse")
    p.add_argument("locator")
    p = sub.add_parser("index")
    p.add_argument("--rules", required=True)
    p.add_argument("--out", required=True)
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    p = sub.add_parser("verify")
    p.add_argument("index")
    p.add_argument("--resolve-only", action="store_true")
    p = sub.add_parser("completeness")
    p.add_argument("index")
    p = sub.add_parser("requirements-locators")
    p.add_argument("--release", required=True)
    p.add_argument("--repo-root", default=".")
    g = p.add_mutually_exclusive_group(required=True)
    g.add_argument("--write", action="store_true")
    g.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)
    resolver = Resolver(Path(args.repos_root), allow_network=not args.no_network)
    try:
        if args.cmd == "parse":
            print(json.dumps(parse(args.locator).as_dict(), sort_keys=True))
            return 0
        if args.cmd == "index":
            rules = json.loads(Path(args.rules).read_text(encoding="utf-8"))
            return _write_or_check(Path(args.out), dump(build_index(resolver, rules)), args.write)
        if args.cmd == "requirements-locators":
            root = Path(args.repo_root)
            out = root / "release" / args.release / "hardening" / "requirements-locators.json"
            return _write_or_check(out, dump(requirements_locators(root, args.release)), args.write)
        index = json.loads(Path(getattr(args, "index")).read_text(encoding="utf-8"))
        findings = (
            verify_index(resolver, index, args.resolve_only) if args.cmd == "verify" else completeness(resolver, index)
        )
    except Refused as exc:
        print(str(exc))
        return 1
    for f in findings:
        print(f)
    n = len(index.get("rows", []))
    status = "ALIVE" if not findings else "REFUSED"
    print(f"{args.cmd.upper()} {status} rows={n} findings={len(findings)}")
    return 0 if not findings else 1


if __name__ == "__main__":
    sys.exit(main())
