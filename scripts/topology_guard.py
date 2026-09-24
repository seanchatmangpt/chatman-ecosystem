#!/usr/bin/env python3
"""Topology guard: repository topology is transport, never ontology.

A committed executable, source, template, config, court, query, ontology or test file of this
repository may not name a shadow checkout (an absolute, home-relative or $HOME path into the home
directory's retired shadow tree) and may not run git's worktree-add subcommand. Work happens in one
canonical checkout per repository on normal git branches; another repository's bytes at a SHA come
from `git show` / `git archive` into a scratch directory.

Scope: the real `git ls-files -s -z` of the checkout (the tracked tree; each regular file is read
from the working tree, or from its index blob when the working-tree file is absent).

  scanned   code, templates, config, build files, queries and ontologies, any executable-mode or
            shebang file, and agent-runtime config (AGENTS.md, CLAUDE.md, anything under .claude/)
  evidence  never scanned: the top-level receipts/ and migration/ directories, generated
            out/receipts/ projections, JSON other than named tool config (recorded evidence), logs,
            prose docs
  residue   a hit inside a file another owner pins (a vendored tree, a sha256-pinned import or
            design capital, a build-context snapshot) is legal only while its row in
            scripts/topology_guard.toml holds: the pin still matches and the row's hit-line count
            is exact. A row names its owner and the edge that removes it; rows only shrink.

Exit 0 ALIVE (no owned reference; every residue row live and exact), 1 REFUSED, 75 UNKNOWN
(not a git checkout, or the ledger is unreadable).
"""

from __future__ import annotations

import argparse
import fnmatch
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath

LEDGER_REL = "scripts/topology_guard.toml"
EXIT = {"ALIVE": 0, "REFUSED": 1, "UNKNOWN": 75}

# The shadow directory name and the subcommand word are split so this file never names them.
_SHADOW = b"w" + b"t"
_WORK = b"work" + b"tree"
_END = rb"(?=[/\s\"'`)\]}>,;:|]|$)"
PATTERNS: tuple[tuple[str, re.Pattern[bytes]], ...] = (
    ("SHADOW_ABSOLUTE_PATH", re.compile(rb"/(?:Users|home)/[A-Za-z0-9._-]+/" + _SHADOW + _END, re.M)),
    ("SHADOW_TILDE_PATH", re.compile(rb"~/" + _SHADOW + _END, re.M)),
    ("SHADOW_ENV_HOME_PATH", re.compile(rb"\$(?:HOME|\{HOME\})/" + _SHADOW + _END, re.M)),
    ("SHADOW_PATHLIB_JOIN", re.compile(rb"home\(\)\s*/\s*[\"']" + _SHADOW + rb"[\"']\s*/")),
    ("WORKTREE_ADD", re.compile(rb"\b" + _WORK + rb"\s+add\b")),
    ("WORKTREE_ADD_ARGV", re.compile(rb"[\"']" + _WORK + rb"[\"']\s*,\s*[\"']add[\"']")),
)

CODE = {".py", ".pyi", ".sh", ".bash", ".zsh", ".fish", ".ps1", ".rs", ".ex", ".exs", ".erl", ".hrl",
        ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".rb", ".go", ".java", ".kt", ".swift", ".c",
        ".h", ".cc", ".cpp", ".lua", ".pl", ".sql", ".pest", ".dl", ".pddl", ".hddl", ".wat"}
TEMPLATE = {".tmpl", ".tera", ".template", ".j2", ".jinja", ".hbs", ".mustache", ".in"}
CONFIG = {".toml", ".yml", ".yaml", ".ini", ".cfg", ".conf", ".lock", ".env", ".plist", ".service", ".mk"}
SEMANTIC = {".ttl", ".rq", ".sparql", ".ru", ".rdf", ".owl", ".n3", ".nt", ".nq", ".trig", ".shex", ".jsonld"}
SCANNED_SUFFIXES = CODE | TEMPLATE | CONFIG | SEMANTIC
SCANNED_NAMES = {"Makefile", "GNUmakefile", "Containerfile", "Justfile", "justfile", "Procfile", "AGENTS.md",
                 "CLAUDE.md", "package.json", "tsconfig.json", ".mcp.json", "devcontainer.json"}
# The repository's receipt store and migration record (top level), and generated receipt projections
# (an out/receipts/ pair anywhere). A source package that happens to be named receipts is scanned.
EVIDENCE_TOP = ("receipts", "migration")
EVIDENCE_PAIR = ("out", "receipts")
KINDS = ("sha256-pin", "vendored", "snapshot")


@dataclass
class Hit:
    path: str
    line: int
    codes: list[str]
    text: str

    def render(self) -> str:
        return f"{self.path}:{self.line} {','.join(self.codes)}: {self.text}"


@dataclass
class Report:
    root: str
    head: str = ""
    scanned: int = 0
    owned: list[Hit] = field(default_factory=list)
    residue: dict[str, list[Hit]] = field(default_factory=dict)
    refused: list[tuple[str, str]] = field(default_factory=list)
    unknown: list[tuple[str, str]] = field(default_factory=list)

    @property
    def standing(self) -> str:
        if self.unknown:
            return "UNKNOWN"
        return "REFUSED" if self.owned or self.refused else "ALIVE"


class Unknown(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(detail)
        self.code, self.detail = code, detail


def git(root: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=text)


def classify(path: str, mode: str, head: bytes) -> str:
    """'evidence', 'scanned' or 'other' for one tracked path."""
    parts = PurePosixPath(path).parts
    dirs = parts[:-1]
    if parts[0] in EVIDENCE_TOP or any(dirs[i:i + 2] == EVIDENCE_PAIR for i in range(len(dirs) - 1)):
        return "evidence"
    name = parts[-1]
    suffix = PurePosixPath(name).suffix.lower()
    if ".claude" in parts[:-1] or name in SCANNED_NAMES or name.startswith("Dockerfile"):
        return "scanned"
    if suffix in SCANNED_SUFFIXES or mode == "100755" or head.startswith(b"#!"):
        return "scanned"
    return "other"


def find_hits(path: str, data: bytes) -> list[Hit]:
    lines: dict[int, list[str]] = {}
    for code, pattern in PATTERNS:
        for match in pattern.finditer(data):
            lines.setdefault(data.count(b"\n", 0, match.start()) + 1, []).append(code)
    if not lines:
        return []
    split = data.split(b"\n")
    return [Hit(path, n, sorted(set(codes)), split[n - 1].decode("utf-8", "replace").strip()[:160])
            for n, codes in sorted(lines.items())]


def tracked(root: Path) -> list[tuple[str, str, str]]:
    probe = git(root, "rev-parse", "--is-inside-work-tree")
    if probe.returncode != 0 or probe.stdout.strip() != "true":
        raise Unknown("NOT_A_CHECKOUT", f"{root} is not a git working tree: {probe.stderr.strip()[-200:]}")
    listing = git(root, "ls-files", "-s", "-z", text=False)
    if listing.returncode != 0:
        raise Unknown("GIT_FAILED", f"git ls-files: {listing.stderr.decode('utf-8', 'replace').strip()[-200:]}")
    entries = []
    for record in filter(None, listing.stdout.split(b"\0")):
        meta, _, path = record.partition(b"\t")
        mode, oid, _stage = meta.decode().split()
        entries.append((mode, oid, path.decode("utf-8", "surrogateescape")))
    return entries


def read_entry(root: Path, mode: str, oid: str, path: str) -> bytes | None:
    if mode not in ("100644", "100755"):
        return None  # symlink (its target is judged where it is tracked) or gitlink (another repository)
    p = root / path
    if p.is_file():
        return p.read_bytes()
    blob = git(root, "cat-file", "blob", oid, text=False)
    return blob.stdout if blob.returncode == 0 else b""


def load_ledger(root: Path, ledger: Path | None) -> list[dict]:
    path = ledger if ledger is not None else root / LEDGER_REL
    if not path.is_file():
        return []
    try:
        rows = tomllib.loads(path.read_text(encoding="utf-8")).get("residue", [])
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        raise Unknown("LEDGER_UNREADABLE", f"{path}: {exc}") from exc
    for row in rows:
        missing = [k for k in ("id", "kind", "paths", "hits", "owner", "edge") if not row.get(k)]
        if missing or row["kind"] not in KINDS:
            raise Unknown("LEDGER_UNREADABLE", f"residue row {row.get('id')!r}: missing {missing} or kind "
                                               f"{row.get('kind')!r} not in {KINDS}")
    return rows


def head_blob_equal(root: Path, path: str, data: bytes) -> bool:
    committed = git(root, "cat-file", "blob", f"HEAD:{path}", text=False)
    return committed.returncode == 0 and committed.stdout == data


def pin_holds(root: Path, row: dict, path: str, data: bytes) -> str | None:
    """None when the row's pin still covers `path` with bytes `data`, else the reason it does not."""
    kind = row["kind"]
    if kind == "sha256-pin":
        pin_file = root / row["pin_file"]
        digest = "sha256:" + hashlib.sha256(data).hexdigest()
        if not pin_file.is_file():
            return f"pin file {row['pin_file']} is absent"
        if digest.encode() not in pin_file.read_bytes():
            return f"{digest} is not pinned in {row['pin_file']} (the pinned bytes changed)"
        return None
    if not head_blob_equal(root, path, data):
        return "the file differs from its committed blob at HEAD (a hand edit of a foreign copy)"
    if kind == "vendored":
        vendor = root / row["vendor_file"]
        if not vendor.is_file():
            return f"vendor record {row['vendor_file']} is absent"
        base = PurePosixPath(row["vendor_file"]).parent
        for pack in tomllib.loads(vendor.read_text(encoding="utf-8")).get("pack", []):
            subdir = (base / pack.get("subdir", "")).as_posix()
            if path.startswith(subdir + "/"):
                tree = git(root, "rev-parse", f"HEAD:{subdir}").stdout.strip()
                if tree != pack.get("tree"):
                    return f"vendored tree {subdir} is {tree or 'absent'} at HEAD, VENDOR.toml records {pack.get('tree')}"
                return None
        return f"no [[pack]] row of {row['vendor_file']} covers {path}"
    writer = root / row["writer"]
    root_name = PurePosixPath(row["snapshot_root"]).name
    if not path.startswith(row["snapshot_root"] + "/"):
        return f"{path} is not under the snapshot root {row['snapshot_root']}"
    if not writer.is_file() or root_name.encode() not in writer.read_bytes():
        return f"snapshot writer {row['writer']} is absent or no longer writes {root_name}"
    return None


def scan(root: Path, ledger: Path | None = None) -> Report:
    root = root.resolve()
    report = Report(root=str(root))
    try:
        entries = tracked(root)
        rows = load_ledger(root, ledger)
    except Unknown as exc:
        report.unknown.append((exc.code, exc.detail))
        return report
    report.head = git(root, "rev-parse", "HEAD").stdout.strip()
    report.residue = {row["id"]: [] for row in rows}
    for mode, oid, path in entries:
        data = read_entry(root, mode, oid, path)
        if data is None or classify(path, mode, data[:2]) != "scanned":
            continue
        report.scanned += 1
        hits = find_hits(path, data)
        if not hits:
            continue
        row = next((r for r in rows if any(fnmatch.fnmatchcase(path, p) for p in r["paths"])), None)
        broken = pin_holds(root, row, path, data) if row else None
        if row and broken is None:
            report.residue[row["id"]].extend(hits)
            continue
        if row:
            report.refused.append(("RESIDUE_PIN_BROKEN", f"{row['id']} {path}: {broken}"))
        report.owned.extend(hits)
    for row in rows:
        got = len(report.residue[row["id"]])
        if got == 0:
            report.refused.append(("RESIDUE_STALE", f"{row['id']}: no hit remains under {row['paths']}; "
                                                    f"delete the row (the ledger only shrinks)"))
        elif got != row["hits"]:
            report.refused.append(("RESIDUE_COUNT_CHANGED", f"{row['id']}: {got} hit lines, the row records "
                                                            f"{row['hits']} (fewer: lower the row; more: a new "
                                                            f"reference entered a foreign copy)"))
    return report


def render(report: Report, rows: list[dict]) -> list[str]:
    owners = {row["id"]: row for row in rows}
    out = [f"{report.standing} topology_guard root={report.root} head={report.head or '-'} "
           f"scanned={report.scanned} owned={len(report.owned)} residue_rows={len(report.residue)}"]
    out += [f"UNKNOWN[{code}] {detail}" for code, detail in report.unknown]
    out += [f"REFUSED[SHADOW_REFERENCE] {hit.render()}" for hit in report.owned]
    out += [f"REFUSED[{code}] {detail}" for code, detail in report.refused]
    for rid, hits in report.residue.items():
        row = owners.get(rid, {})
        files = len({h.path for h in hits})
        out.append(f"RESIDUE[{rid}] {len(hits)} hit lines in {files} files ({row.get('kind')}; owner: "
                   f"{row.get('owner')}) edge: {row.get('edge')}")
    return out


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="topology guard: repository topology is transport, never ontology")
    ap.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--ledger", type=Path, default=None)
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args(argv)
    report = scan(args.root, args.ledger)
    if args.json:
        doc = {"standing": report.standing, "root": report.root, "head": report.head, "scanned": report.scanned,
               "owned": [h.__dict__ for h in report.owned], "refused": report.refused, "unknown": report.unknown,
               "residue": {k: [h.__dict__ for h in v] for k, v in report.residue.items()}}
        print(json.dumps(doc, indent=1, sort_keys=True))
    else:
        try:
            rows = load_ledger(args.root.resolve(), args.ledger)
        except Unknown:
            rows = []
        print("\n".join(render(report, rows)))
    return EXIT[report.standing]


if __name__ == "__main__":
    sys.exit(main())
