"""Premise imports (RFC-0005 edge E-ADM-02): the machine producer and offline court.

An admitted premise (an RFC merged by the operator into its owner repository) becomes
release input only as an *import*: a byte copy under ``release/<v>/[<lane>/]imports/``
plus one row of ``IMPORTS.json`` binding the copy to its exact source::

    {"path": "imports/RFC-0005.md", "source_repo": "owner/repo", "source_sha": "<40hex>",
     "source_path": "docs/...md", "source_blob_sha1": "<git blob id>", "sha256": "<hex>",
     "standing": "NOT_A_SPEC", ["scope": "..."], "owner": "..."}

Through v26.9.25 the copy and the row were made by a person or an LLM lane (edges.json
E-ADM-02, owner_kinds [human, llm]). This module makes that edge a machine edge:

``import``  reads the blob at the exact ``git:<owner>/<repo>@<sha>:<path>`` locator through
            ``durable_locator.Resolver`` (owner-checked local object DB, then ``gh api`` unless
            ``--no-network``), writes the copy, and upserts the row with digests *computed from
            the bytes read* -- never from supplied text. Re-importing the same subject is a
            byte-identical no-op; a different subject on an existing path is refused unless
            ``--replace``.
``plan``    derives, from ``catalog/premise-imports.toml`` and an owner checkout, every
            premise a release line admits: the FINAL_SPEC RFC files on the source ``ref``
            and, for each, the admitting commit (the first first-parent commit of ``ref``
            that adds it). Each planned row is IMPORTED, MISSING or SUBJECT_DIFFERS against
            the committed imports; ``--release`` with no admitted premise is PREMISE_ABSENT
            (typed BLOCKED on the operator's admission gate E-ADM-01, exit 3).
``sync``    imports every MISSING planned row (never rebinds SUBJECT_DIFFERS).
``check``   recomputes every IMPORTS.json under ``release/`` offline: row shape, path
            confinement, copy presence, sha256 and git blob id, and unlisted copies. With
            ``--repos-root`` it also re-reads each source and compares bytes; a source that
            cannot be reached is TRANSPORT_UNAVAILABLE (reported, never a subject failure).

Typed refusals (finding codes):

  IMPORT_ROW_MALFORMED     a required field is missing or has the wrong shape
  IMPORT_PATH_ESCAPE       ``path`` is not ``imports/<file>`` (absolute, ``..``, nested)
  IMPORT_COPY_MISSING      the row names a copy that does not exist
  IMPORT_DIGEST_MISMATCH   the copy's sha256 or git blob id does not recompute
  IMPORT_UNLISTED_COPY     a file in ``imports/`` has no row (hand-supplied bytes)
  IMPORT_DUPLICATE_PATH    two rows name the same copy
  IMPORT_PATH_CONFLICT     import onto a path already bound to a different subject
  IMPORT_SOURCE_DRIFT      the source blob no longer equals the copy
  IMPORT_SOURCE_UNRESOLVED the source locator is refused by the resolver (SHA/path absent)
  TRANSPORT_UNAVAILABLE    the source repository cannot be reached (not a subject failure)

  PREMISE_ABSENT           --release names a line no admitted premise targets (BLOCKED)
  IMPORTED_NOT_FINAL       a committed import's source is not FINAL_SPEC at its admitting commit

Exit codes: 0 ok, 1 refusal, 2 usage, 3 typed BLOCKED (plan/sync: PREMISE_ABSENT).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from scripts.durable_locator.durable_locator import Refused, Resolver, parse

SCHEMA_CHECK = "https://chatman.dev/premise-import/check/v1"
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
STANDING = re.compile(r"^[A-Z][A-Z_]*$")
COPY_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]*$")
ROW_ORDER = (
    "path",
    "source_repo",
    "source_sha",
    "source_path",
    "source_blob_sha1",
    "sha256",
    "standing",
    "scope",
    "owner",
)
REQUIRED = ("path", "source_repo", "source_sha", "source_path", "source_blob_sha1", "sha256", "standing", "owner")
TRANSPORT_CODES = ("REPOSITORY_UNAVAILABLE", "OWNER_MISMATCH", "REMOTE_UNRESOLVED")
INDEX = "IMPORTS.json"


def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_blob_id(data: bytes) -> str:
    return hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()


@dataclass(frozen=True)
class Finding:
    code: str
    where: str
    detail: str

    @property
    def is_transport(self) -> bool:
        return self.code == "TRANSPORT_UNAVAILABLE"

    def as_dict(self) -> dict[str, str]:
        return {"code": self.code, "where": self.where, "detail": self.detail}


class ImportRefused(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"{code}:{detail}")
        self.code = code
        self.detail = detail


def ordered(row: dict[str, Any]) -> dict[str, Any]:
    known = {k: row[k] for k in ROW_ORDER if k in row}
    return {**known, **{k: v for k, v in sorted(row.items()) if k not in known}}


def render(doc: dict[str, Any]) -> bytes:
    return (json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")


def load_index(imports_dir: Path) -> dict[str, Any]:
    path = imports_dir / INDEX
    if not path.is_file():
        return {"imports": []}
    return json.loads(path.read_text(encoding="utf-8"))


# ---------------------------------------------------------------- produce


def import_premise(
    resolver: Resolver,
    locator: str,
    imports_dir: Path,
    copy_name: str,
    owner: str,
    standing: str,
    scope: str | None = None,
    replace: bool = False,
) -> tuple[dict[str, Any], bool]:
    """Copy the blob at ``locator`` into ``imports_dir/copy_name`` and upsert its row.

    Returns ``(row, changed)``. Digests are computed from the bytes the resolver returned.
    """
    try:
        loc = parse(locator)
    except Refused as exc:
        raise ImportRefused("IMPORT_ROW_MALFORMED", f"{exc.code}:{locator}") from None
    if loc.kind != "git":
        raise ImportRefused("IMPORT_ROW_MALFORMED", f"only git: locators are importable: {locator}")
    if not COPY_NAME.fullmatch(copy_name) or copy_name == INDEX:
        raise ImportRefused("IMPORT_PATH_ESCAPE", copy_name)
    if not STANDING.fullmatch(standing):
        raise ImportRefused("IMPORT_ROW_MALFORMED", f"standing {standing!r}")
    if not owner.strip():
        raise ImportRefused("IMPORT_ROW_MALFORMED", "owner is empty")
    assert loc.repository and loc.sha and loc.path
    try:
        data = resolver.blob(loc.repository, loc.sha, loc.path)
    except Refused as exc:
        code = "TRANSPORT_UNAVAILABLE" if exc.code in TRANSPORT_CODES else "IMPORT_SOURCE_UNRESOLVED"
        raise ImportRefused(code, f"{exc.code}:{locator}") from None

    row: dict[str, Any] = {
        "path": f"imports/{copy_name}",
        "source_repo": loc.repository,
        "source_sha": loc.sha,
        "source_path": loc.path,
        "source_blob_sha1": git_blob_id(data),
        "sha256": sha256_hex(data),
        "standing": standing,
        "owner": owner,
    }
    if scope:
        row["scope"] = scope
    row = ordered(row)

    doc = load_index(imports_dir)
    rows: list[dict[str, Any]] = list(doc.get("imports", []))
    existing = [i for i, r in enumerate(rows) if r.get("path") == row["path"]]
    if len(existing) > 1:
        raise ImportRefused("IMPORT_DUPLICATE_PATH", row["path"])
    if existing:
        old = rows[existing[0]]
        same_subject = all(old.get(k) == row[k] for k in ("source_repo", "source_sha", "source_path", "sha256"))
        if not same_subject and not replace:
            raise ImportRefused(
                "IMPORT_PATH_CONFLICT",
                f"{row['path']} is bound to {old.get('source_repo')}@{old.get('source_sha')}:{old.get('source_path')}",
            )
        rows[existing[0]] = row
    else:
        rows.append(row)
    rows.sort(key=lambda r: str(r.get("path")))
    new_doc = {**doc, "imports": rows}

    imports_dir.mkdir(parents=True, exist_ok=True)
    copy = imports_dir / copy_name
    index = imports_dir / INDEX
    new_index = render(new_doc)
    changed = False
    if not copy.is_file() or copy.read_bytes() != data:
        copy.write_bytes(data)
        changed = True
    if not index.is_file() or index.read_bytes() != new_index:
        index.write_bytes(new_index)
        changed = True
    return row, changed


# ---------------------------------------------------------------- check


def discover(root: Path) -> list[Path]:
    """Every ``imports/`` directory under ``root/release`` that holds an IMPORTS.json."""
    return sorted(p.parent for p in (root / "release").rglob(f"imports/{INDEX}"))


def _row_shape(row: Any, where: str) -> list[Finding]:
    if not isinstance(row, dict):
        return [Finding("IMPORT_ROW_MALFORMED", where, "row is not an object")]
    out = [Finding("IMPORT_ROW_MALFORMED", where, f"missing {k}") for k in REQUIRED if not isinstance(row.get(k), str) or not row.get(k)]
    if out:
        return out
    if not HEX40.fullmatch(row["source_sha"]):
        out.append(Finding("IMPORT_ROW_MALFORMED", where, "source_sha is not 40 hex"))
    if not HEX40.fullmatch(row["source_blob_sha1"]):
        out.append(Finding("IMPORT_ROW_MALFORMED", where, "source_blob_sha1 is not 40 hex"))
    if not HEX64.fullmatch(row["sha256"]):
        out.append(Finding("IMPORT_ROW_MALFORMED", where, "sha256 is not 64 hex"))
    if not STANDING.fullmatch(row["standing"]):
        out.append(Finding("IMPORT_ROW_MALFORMED", where, f"standing {row['standing']!r}"))
    try:
        parse(f"git:{row['source_repo']}@{row['source_sha']}:{row['source_path']}")
    except Refused as exc:
        out.append(Finding("IMPORT_ROW_MALFORMED", where, f"source locator {exc.code}"))
    parts = row["path"].split("/")
    if len(parts) != 2 or parts[0] != "imports" or not COPY_NAME.fullmatch(parts[1]) or parts[1] == INDEX:
        out.append(Finding("IMPORT_PATH_ESCAPE", where, row["path"]))
    return out


def check_dir(imports_dir: Path, root: Path, resolver: Resolver | None) -> tuple[list[Finding], int]:
    """Findings for one imports directory and the number of rows it admits."""
    rel = imports_dir.relative_to(root).as_posix()
    try:
        doc = json.loads((imports_dir / INDEX).read_text(encoding="utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        return [Finding("IMPORT_ROW_MALFORMED", f"{rel}/{INDEX}", f"not JSON: {exc}")], 0
    rows = doc.get("imports") if isinstance(doc, dict) else None
    if not isinstance(rows, list):
        return [Finding("IMPORT_ROW_MALFORMED", f"{rel}/{INDEX}", "imports is not a list")], 0
    findings: list[Finding] = []
    listed: set[str] = set()
    for n, row in enumerate(rows):
        where = f"{rel}/{INDEX}#/imports/{n}"
        shape = _row_shape(row, where)
        if shape:
            findings.extend(shape)
            continue
        name = row["path"].split("/", 1)[1]
        if name in listed:
            findings.append(Finding("IMPORT_DUPLICATE_PATH", where, row["path"]))
            continue
        listed.add(name)
        copy = imports_dir / name
        if not copy.is_file():
            findings.append(Finding("IMPORT_COPY_MISSING", where, f"{rel}/{name}"))
            continue
        data = copy.read_bytes()
        if sha256_hex(data) != row["sha256"] or git_blob_id(data) != row["source_blob_sha1"]:
            findings.append(Finding("IMPORT_DIGEST_MISMATCH", where, f"{rel}/{name} does not recompute"))
            continue
        if resolver is None:
            continue
        try:
            source = resolver.blob(row["source_repo"], row["source_sha"], row["source_path"])
        except Refused as exc:
            code = "TRANSPORT_UNAVAILABLE" if exc.code in TRANSPORT_CODES else "IMPORT_SOURCE_UNRESOLVED"
            findings.append(Finding(code, where, f"{exc.code}:{row['source_repo']}@{row['source_sha']}"))
            continue
        if source != data:
            findings.append(Finding("IMPORT_SOURCE_DRIFT", where, f"{rel}/{name} != source blob"))
    for f in sorted(imports_dir.iterdir()):
        if f.is_file() and f.name != INDEX and f.name not in listed:
            findings.append(Finding("IMPORT_UNLISTED_COPY", f"{rel}/{f.name}", "no IMPORTS.json row"))
    return findings, len(listed)


def check(root: Path, resolver: Resolver | None) -> dict[str, Any]:
    dirs = discover(root)
    report_dirs = []
    all_findings: list[Finding] = []
    for d in dirs:
        findings, admitted = check_dir(d, root, resolver)
        all_findings.extend(findings)
        report_dirs.append(
            {
                "imports_dir": d.relative_to(root).as_posix(),
                "rows_admitted": admitted,
                "findings": [f.as_dict() for f in findings],
            }
        )
    refusals = [f for f in all_findings if not f.is_transport]
    return {
        "schema": SCHEMA_CHECK,
        "source_verification": "offline" if resolver is None else "resolved",
        "directories": report_dirs,
        "refusals": len(refusals),
        "transport_unavailable": len(all_findings) - len(refusals),
        "verdict": "REFUSED" if refusals else "ADMITTED",
    }


# ---------------------------------------------------------------- plan


CATALOG = Path("catalog/premise-imports.toml")
SCHEMA_CATALOG = "premise-imports.v1"
SCHEMA_PLAN = "https://chatman.dev/premise-import/plan/v1"
RELEASE_RX = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")
MERGE_RX = re.compile(r"^Merge (?:pull request|PR) #(\d+)\b")


def release_key(release: str) -> tuple[int, int, int]:
    m = RELEASE_RX.fullmatch(release)
    if not m:
        raise ImportRefused("IMPORT_ROW_MALFORMED", f"release {release!r}")
    return int(m[1]), int(m[2]), int(m[3])


def load_catalog(root: Path) -> dict[str, Any]:
    doc = tomllib.loads((root / CATALOG).read_text(encoding="utf-8"))
    if doc.get("schema") != SCHEMA_CATALOG or not isinstance(doc.get("source"), list):
        raise ImportRefused("IMPORT_ROW_MALFORMED", f"{CATALOG.as_posix()}: schema {SCHEMA_CATALOG} with [[source]]")
    return doc


class SourceRepo:
    """Read-only git over an owner-checked local checkout (``Resolver.local_dir``)."""

    def __init__(self, resolver: Resolver, repository: str) -> None:
        self.repository = repository
        self.dir = resolver.local_dir(repository)
        if self.dir is None:
            mismatch = resolver.owner_mismatch(repository)
            raise ImportRefused("TRANSPORT_UNAVAILABLE", mismatch or f"no local checkout of {repository}")

    def git(self, *args: str) -> str:
        out = subprocess.run(["git", "-C", str(self.dir), *args], capture_output=True, check=False)
        if out.returncode != 0:
            raise ImportRefused("IMPORT_SOURCE_UNRESOLVED", f"{self.repository}: git {' '.join(args)}")
        return out.stdout.decode("utf-8")

    def commit_of(self, ref: str) -> str:
        for cand in (ref, f"origin/{ref}", f"refs/remotes/origin/{ref}"):
            out = subprocess.run(
                ["git", "-C", str(self.dir), "rev-parse", "-q", "--verify", f"{cand}^{{commit}}"],
                capture_output=True,
                check=False,
            )
            if out.returncode == 0:
                return out.stdout.decode().strip()
        raise ImportRefused("IMPORT_SOURCE_UNRESOLVED", f"{self.repository}: ref {ref} not found")


def _status_line(text: str) -> str:
    return next((ln.strip() for ln in text.splitlines() if ln.strip().startswith("**Status:**")), "")


def plan(root: Path, resolver: Resolver, release: str | None = None) -> dict[str, Any]:
    """Every premise the catalog admits, with its standing against the committed imports."""
    catalog = load_catalog(root)
    rows: list[dict[str, Any]] = []
    sources: list[dict[str, Any]] = []
    for src in catalog["source"]:
        repo_name = src["repository"]
        try:
            repo = SourceRepo(resolver, repo_name)
            head = repo.commit_of(src["ref"])
        except ImportRefused as exc:
            sources.append({"repository": repo_name, "ref": src["ref"], "status": exc.code, "detail": exc.detail})
            continue
        sources.append({"repository": repo_name, "ref": src["ref"], "commit": head, "status": "OBSERVED"})
        pattern = re.compile(src["pattern"])
        since = release_key(src["since"])
        overrides = {o["number"]: o for o in src.get("override", [])}
        for path in sorted(p for p in repo.git("ls-tree", "-r", "--name-only", head).splitlines() if p):
            m = pattern.fullmatch(path)
            if not m or release_key(m["release"]) < since:
                continue
            number, line = m["number"], m["release"]
            if release is not None and line != release:
                continue
            added = repo.git("log", "--first-parent", "--diff-filter=A", "--format=%H%x00%s", head, "--", path)
            # newest first: the latest add admits the bytes present now (a delete + re-add is a new admission)
            admit_sha, subject = added.strip().splitlines()[0].split("\0", 1)
            changed = repo.git("log", "--first-parent", "--format=%H", head, "--", path).split()
            data = resolver.blob(repo_name, admit_sha, path)
            rule = {**src, **overrides.get(number, {})}
            pr = MERGE_RX.match(subject)
            row = {
                "release": line,
                "number": number,
                "locator": f"git:{repo_name}@{admit_sha}:{path}",
                "into": rule["into"].format(release=line, number=number),
                "copy_name": rule["copy_name"].format(release=line, number=number),
                "standing": rule["standing"],
                "scope": rule.get("scope"),
                "owner": f"{repo_name} (PR #{pr[1]}, FINAL_SPEC; merge {admit_sha[:8]})"
                if pr
                else f"{repo_name} (FINAL_SPEC; commit {admit_sha[:8]})",
                "sha256": sha256_hex(data),
                "final": _status_line(data.decode("utf-8", "replace")).startswith(rule["status_prefix"]),
                "amended_after_admission": [c for c in changed if c != admit_sha],
            }
            row["status"] = _standing(root, row)
            rows.append(row)
    absent = release is not None and not any(r["final"] for r in rows) and all(
        s["status"] == "OBSERVED" for s in sources
    )
    blocking = [r for r in rows if r["status"] in ("MISSING", "SUBJECT_DIFFERS", "IMPORTED_NOT_FINAL")]
    return {
        "schema": SCHEMA_PLAN,
        "release": release,
        "sources": sources,
        "premises": rows,
        "verdict": "REFUSED"
        if blocking
        else "BLOCKED(PREMISE_ABSENT:E-ADM-01)"
        if absent
        else "BLOCKED(TRANSPORT_UNAVAILABLE)"
        if any(s["status"] != "OBSERVED" for s in sources)
        else "ADMITTED",
    }


def _standing(root: Path, row: dict[str, Any]) -> str:
    imports_dir = root / row["into"]
    existing = [r for r in load_index(imports_dir).get("imports", []) if r.get("path") == f"imports/{row['copy_name']}"]
    if not existing:
        return "MISSING" if row["final"] else "NOT_ADMITTED"
    loc = parse(row["locator"])
    old = existing[0]
    same = (old.get("source_repo"), old.get("source_sha"), old.get("source_path"), old.get("sha256")) == (
        loc.repository,
        loc.sha,
        loc.path,
        row["sha256"],
    )
    if not same:
        return "SUBJECT_DIFFERS"
    return "IMPORTED" if row["final"] else "IMPORTED_NOT_FINAL"


def sync(root: Path, resolver: Resolver, release: str | None = None) -> dict[str, Any]:
    """Import every MISSING planned premise; return the re-computed plan."""
    for row in plan(root, resolver, release)["premises"]:
        if row["status"] == "MISSING":
            import_premise(
                resolver,
                row["locator"],
                root / row["into"],
                row["copy_name"],
                row["owner"],
                row["standing"],
                row["scope"],
            )
    return plan(root, resolver, release)


def plan_exit(report: dict[str, Any]) -> int:
    verdict = report["verdict"]
    return 0 if verdict == "ADMITTED" else 1 if verdict == "REFUSED" else 3


# ---------------------------------------------------------------- cli


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="premise_import", description=__doc__.split("\n\n")[0])
    ap.add_argument("--repos-root", type=Path, help="directory holding <repo> checkouts (owner-checked)")
    ap.add_argument("--no-network", action="store_true", help="never fall back to gh api")
    sub = ap.add_subparsers(dest="cmd", required=True)
    imp = sub.add_parser("import", help="copy one admitted premise into a release imports/ directory")
    imp.add_argument("locator", help="git:<owner>/<repo>@<40hex>:<path>")
    imp.add_argument("--into", type=Path, required=True, help="release/<v>/[<lane>/]imports")
    imp.add_argument("--as", dest="copy_name", required=True, help="copy file name, e.g. RFC-0006.md")
    imp.add_argument("--owner", required=True, help="owner/admission provenance, e.g. 'org/repo (PR #9, FINAL_SPEC)'")
    imp.add_argument("--standing", default="NOT_A_SPEC")
    imp.add_argument("--scope")
    imp.add_argument("--replace", action="store_true", help="rebind an existing path to a new subject")
    chk = sub.add_parser("check", help="recompute every release imports/IMPORTS.json")
    chk.add_argument("--root", type=Path, default=Path("."))
    chk.add_argument("--json", action="store_true")
    for name, text in (("plan", "derive admitted premises and their import standing"), ("sync", "import every MISSING premise")):
        p = sub.add_parser(name, help=text)
        p.add_argument("--root", type=Path, default=Path("."))
        p.add_argument("--release", help="restrict to one release line vYY.M.D")
    args = ap.parse_args(argv)

    if args.cmd in ("plan", "sync"):
        if args.repos_root is None:
            print("--repos-root is required for plan/sync", file=sys.stderr)
            return 2
        # plan/sync read owner checkouts only: never the network.
        resolver = Resolver(args.repos_root, allow_network=False)
        try:
            report = (plan if args.cmd == "plan" else sync)(args.root, resolver, args.release)
        except ImportRefused as exc:
            print(f"REFUSED[{exc.code}] {exc.detail}", file=sys.stderr)
            return 1
        print(json.dumps(report, indent=2))
        return plan_exit(report)

    if args.cmd == "import":
        if not args.into.as_posix().split("/")[-1] == "imports":
            print("IMPORT_PATH_ESCAPE:--into must name an imports/ directory", file=sys.stderr)
            return 2
        resolver = Resolver(args.repos_root or Path(".."), allow_network=not args.no_network)
        try:
            row, changed = import_premise(
                resolver, args.locator, args.into, args.copy_name, args.owner, args.standing, args.scope, args.replace
            )
        except ImportRefused as exc:
            print(f"REFUSED[{exc.code}] {exc.detail}", file=sys.stderr)
            return 1
        print(json.dumps({"changed": changed, "row": row}, indent=2))
        return 0

    resolver = Resolver(args.repos_root, allow_network=not args.no_network) if args.repos_root else None
    report = check(args.root, resolver)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for d in report["directories"]:
            print(f"{d['imports_dir']}: {d['rows_admitted']} admitted")
            for f in d["findings"]:
                print(f"  {f['code']} {f['where']} {f['detail']}")
        print(f"verdict={report['verdict']} refusals={report['refusals']} transport_unavailable={report['transport_unavailable']}")
    return 1 if report["refusals"] else 0


if __name__ == "__main__":
    sys.exit(main())
