#!/usr/bin/env python3
"""CE23-1 court: an independent v26.9.23 release subject (release/v26.9.23/sjira/goal.ttl ce:CE23-1).

Proposition (chatman-ce23.md CE23-1): release/v26.9.23/... is added and release/v26.9.1 is
preserved untouched. Falsifier (goal.ttl ce:CE23-1-falsifier): the court exits 0 while no
release/v26.9.23 subject exists, or while any path under release/v26.9.1 differs from its
pre-v26.9.23 tree.

The subject is the ggen sub-project release/v26.9.23 (ggen.toml, release.ttl, imports/) over
the byte-identically vendored chatman-ecosystem-release-pack; out/ and ggen.lock are its
render. The court judges the exact committed head: every clause below reads `git archive
HEAD` (extracted into scratch) or git objects, never the working tree, and a working tree
that diverges from the head under release/v26.9.1 or the subject is itself refused. Clauses:

  S0 lineage     the head is a git commit and subject.base_commit (GitHub main at CE23-0)
                 is its ancestor
  P1 predecessor release/v26.9.1 at the head is the base tree and the pinned tree
  P2 checkout    the working tree holds no change under release/v26.9.1 and the manifest
                 digest is the pin
  A1 present     every pinned input and output of the subject is committed
  A2 checkout    the working tree holds no change under the subject paths
  A3 pointers    release/v26.9.23/{manifest,constitutional-role-crosswalk}.toml are
                 symlinks to their render (mode 120000, target out/<name>), not copies
  A4 independent ggen.toml is closed-world: every key is one the court judges (project.name,
                 ontology.source/prefixes, templates.dir, packs.<n>.path/lock/extra_ontologies,
                 law.rules/gates/shapes), anything else (e.g. law.reflexive, which reads the
                 uncommitted .ggen-v2/receipt-log.jsonl) is CONFIG_UNJUDGED; every path it
                 reads is relative, normalized, inside release/v26.9.23 and a committed
                 regular file or directory of the head (never a symlink or gitlink)
  A5 contained   every committed entry of the judged slice (release/v26.9.1, the subject,
                 the committed tools) is a regular file: the only symlinks are the pinned
                 line pointers (a symlink or gitlink reads bytes the commit does not carry)
  C1 court       the court judging (CE23-1.sh, court.py, subject.toml as loaded) is
                 byte-identical to the committed court at the judged head, so the pins the
                 head is judged against are the head's own
  V1 vendor      every vendor/ggen-marketplace/VENDOR.toml row: the committed tree equals
                 the row's tree and the marketplace object <commit>:<subdir>, the commit is
                 on the published marketplace ref, and ggen.toml takes every pack from a
                 vendored row with lock = true
  G1 render      `ggen sync run` on the committed subject exits 0 and writes nothing (native
                 refusals: FM-WRITE-005 hand edit, FM-PACK-008 vendored drift, FM-PACK-013
                 gate); a fresh render of out/ and a fresh ggen.lock equal the committed
                 bytes and the committed output set
  G2 gates       the pack's second executor (bin/run-gates.py, rdflib) admits the same
                 union graph: RELEASE_GATES ALIVE
  I1 import      imports/fleet-classification.ttl is the byte copy its classification
                 source names (the pinned repository and path, at the commit of that
                 repository's required component, sha256), read from its canonical checkout
  M1 manifest    the manifest the line resolves is version 26.9.23; every CriticalPath
                 repository of the imported classification is a required component with an
                 exact 40-hex SHA and every verify_release field; the crosswalk is bound to
                 26.9.23 and maps every required role
  M2 lineage     every required GitHub component commit exists in its canonical checkout
                 and is an ancestor of origin/<ref>
  T1 tool        the committed scripts/verify_release.py --release v26.9.23 (and --manifest
                 release/v26.9.23/manifest.toml) exits 0 with no finding, bound to 26.9.23,
                 over the rendered manifest's bytes
  R1 rows        out/requirements.toml has one row per checkpointed sj:WorkOrder of every
                 sjira/compiled/*/orders.ttl (independent of ggen.toml's import list), with
                 CE23-1 rows present
  AV corpus      a synthetic two-commit repository (base: release/v26.9.1 at base_commit;
                 head: the judged slice) must be ALIVE unmutated (control M0), and each of 23
                 mutants must be refused with its expected codes (and named reason): MV revert
                 of the subject; M1 hand-edited render; M2 a CriticalPath component dropped
                 from the graph, M2b also from the render; M3/M4 a v26.9.1 byte change / new
                 file, M3w uncommitted; M5 relaxed vendored gate; M6 forked pointer, M6w an
                 uncommitted subject edit; M7 edited classification import; M8 version
                 literal; M9 a compiled orders unit dropped from the imports; M10 a re-pinned
                 component; M11 an import read from release/v26.9.1; M12 a classification
                 source outside the pin; M13 the import an absolute symlink to identical bytes
                 outside the repository; M14 the import a relative symlink leaving the subject;
                 M15 law.reflexive; M16 lock = false; M17 a component re-pinned off its ref;
                 M18 committed court pins that are not the running court's; MB an orphan base
                 (see mutants())

A clause that finds a committed subject file unreadable in the slice (e.g. a dangling symlink)
refuses it typed (SUBJECT_UNREADABLE) instead of faulting.

Every subprocess runs real tools (git, ggen, python3) on real files; there is no test double.
They run under a no-LLM environment: a fresh HOME, a PATH of the resolved directories of
ggen, git, python3 and tar plus /usr/bin:/bin (UNKNOWN when any holds claude or zcode),
PYTHONUSERBASE, LANG and PYTHONDONTWRITEBYTECODE=1 only. Canonical checkouts of other
repositories are read, never written: CE23_MARKETPLACE_REPO (default ~/ggen-marketplace)
and CE23_REPO_<ID> per component (default ~/<id>, e.g. CE23_REPO_XAAS, CE23_REPO_GGEN_IGNITER).

    python3 release/v26.9.23/courts/ce23_1/court.py [--no-av] [--keep SCRATCH]

Exit: 0 ALIVE; 1 REFUSED (typed REFUSED[<code>] lines name the counterexample);
75 UNKNOWN (typed UNKNOWN[<code>] lines: a tool or a canonical checkout is absent).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import json
import os
import re
import shutil
import site
import subprocess
import sys
import tempfile
import tomllib
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
_PIN_BYTES = (HERE / "subject.toml").read_bytes()
PINS = tomllib.loads(_PIN_BYTES.decode("utf-8"))
SUBJ = PINS["subject"]
TOOLS = PINS["tools"]
SDIR = SUBJ["subject_dir"]
PRED_DIR = f"release/{SUBJ['predecessor']}"
# C1: the court as loaded (bytes read once, at import), keyed by its committed path.
_WRAPPER = HERE.parent / "CE23-1.sh"
COURT_BYTES: dict[str, bytes | None] = {
    f"{SDIR}/courts/CE23-1.sh": _WRAPPER.read_bytes() if _WRAPPER.is_file() else None,
    f"{SDIR}/courts/ce23_1/court.py": Path(__file__).resolve().read_bytes(),
    f"{SDIR}/courts/ce23_1/subject.toml": _PIN_BYTES,
}
# A4: the closed ggen.toml schema the court judges (every other key is CONFIG_UNJUDGED).
CONFIG_SCHEMA = {
    "project": {"name": "str"},
    "ontology": {"source": "path", "prefixes": "prefixes"},
    "templates": {"dir": "path"},
    "law": {"rules": "paths", "gates": "paths", "shapes": "paths"},
}
PACK_SCHEMA = {"path": "path", "lock": "bool", "extra_ontologies": "paths"}
REGULAR_MODES = ("100644", "100755")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
FM = re.compile(r"\[FM-[A-Z]+-[0-9]+\][^\n]{0,240}")
VERIFY_FIELDS = ("id", "repository", "ref", "ref_check", "sha", "role", "disposition", "standing", "required", "depends_on")
SOURCE_RE = re.compile(
    r"^(?P<repo>[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+)@(?P<sha>[0-9a-f]{40}):(?P<path>\S+) sha256:(?P<digest>[0-9a-f]{64})$"
)
SJ = "https://ggen-igniter.dev/ontology/semantic-jira#"
DCT = "http://purl.org/dc/terms/"
LLM_BINARIES = ("claude", "zcode")


class Environment(Exception):
    """A tool the court needs is absent: the court witnesses nothing (UNKNOWN)."""


class Verdict:
    def __init__(self) -> None:
        self.lines: list[str] = []
        self.refused: list[str] = []
        self.unknowns: list[str] = []

    def ok(self, clause: str, msg: str) -> None:
        self.lines.append(f"OK {clause}: {msg}")

    def refuse(self, code: str, clause: str, msg: str) -> None:
        self.refused.append(code)
        self.lines.append(f"REFUSED[{code}] {clause}: {msg}")

    def unknown(self, code: str, clause: str, msg: str) -> None:
        self.unknowns.append(code)
        self.lines.append(f"UNKNOWN[{code}] {clause}: {msg}")

    @property
    def alive(self) -> bool:
        return not self.refused and not self.unknowns


# ---------------------------------------------------------------- environment
def resolve_tool(name: str) -> str:
    found = shutil.which(name)
    if not found:
        raise Environment(f"TOOL_MISSING:{name} not on PATH")
    return os.path.realpath(found)


class Env:
    """Resolved tools and the no-LLM subprocess environment."""

    def __init__(self, home: Path) -> None:
        self.ggen = resolve_tool("ggen")
        self.git = resolve_tool("git")
        self.tar = resolve_tool("tar")
        self.python = os.path.realpath(sys.executable)
        dirs: list[str] = []
        for tool in (self.ggen, self.git, self.python, self.tar):
            d = str(Path(tool).parent)
            if d not in dirs:
                dirs.append(d)
        dirs += [d for d in ("/usr/bin", "/bin") if d not in dirs]
        for d in dirs:
            for name in LLM_BINARIES:
                if (Path(d) / name).exists():
                    raise Environment(f"LLM_ON_PATH:{Path(d) / name}")
        home.mkdir(parents=True, exist_ok=True)
        self.vars = {
            "HOME": str(home),
            "PATH": ":".join(dirs),
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONUSERBASE": site.getuserbase(),
            "GIT_CONFIG_NOSYSTEM": "1",
            "TMPDIR": str(home),
        }
        self.ggen_version = self.run([self.ggen, "--version"]).stdout.strip().splitlines()[0:1]

    def run(self, argv: list[str], cwd: Path | None = None, stdin: bytes | None = None,
            text: bool = True) -> subprocess.CompletedProcess:
        data = stdin.decode() if text and stdin is not None else stdin
        return subprocess.run(argv, cwd=cwd, env=self.vars, input=data, capture_output=True, text=text, timeout=900)

    def git_(self, repo: Path, *args: str, text: bool = True) -> subprocess.CompletedProcess:
        return self.run([self.git, "--no-optional-locks", "-C", str(repo), *args], text=text)

    def out(self, repo: Path, *args: str) -> str | None:
        proc = self.git_(repo, *args)
        return proc.stdout.strip() if proc.returncode == 0 else None

    def archive(self, repo: Path, rev: str, paths: list[str], dest: Path) -> None:
        dest.mkdir(parents=True, exist_ok=True)
        blob = self.git_(repo, "archive", "--format=tar", rev, "--", *paths, text=False)
        if blob.returncode != 0:
            raise RuntimeError(f"git archive {rev} failed: {blob.stderr.decode(errors='replace')[-300:]}")
        tar = self.run([self.tar, "-x", "-f", "-", "-C", str(dest)], stdin=blob.stdout, text=False)
        if tar.returncode != 0:
            raise RuntimeError(f"tar -x failed: {tar.stderr.decode(errors='replace')[-300:]}")

    def commit_all(self, repo: Path, message: str) -> str:
        for argv in (["add", "-A", "."],
                     ["-c", "user.name=ce23-1-court", "-c", "user.email=ce23-1-court@localhost",
                      "-c", "commit.gpgsign=false", "commit", "-q", "--allow-empty", "-m", message]):
            proc = self.git_(repo, *argv)
            if proc.returncode != 0:
                raise RuntimeError(f"git {argv[0]} in {repo}: {proc.stderr[-300:]}")
        return self.out(repo, "rev-parse", "HEAD") or ""


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def fm_codes(proc: subprocess.CompletedProcess) -> str:
    found = FM.findall((proc.stdout or "") + "\n" + (proc.stderr or ""))
    return "; ".join(dict.fromkeys(found)) or ((proc.stderr or proc.stdout or "").strip()[-240:])


def snapshot(base: Path, rels: list[str]) -> dict[str, bytes]:
    return {r: (base / r).read_bytes() for r in rels if (base / r).is_file()}


def rendered(sub: Path) -> dict[str, bytes]:
    out = sub / SUBJ["generated_dir"]
    files = sorted(p.relative_to(sub).as_posix() for p in out.rglob("*") if p.is_file()) if out.is_dir() else []
    return snapshot(sub, files + (["ggen.lock"] if (sub / "ggen.lock").is_file() else []))


def repo_for(component_id: str) -> Path:
    key = "CE23_REPO_" + re.sub(r"[^A-Za-z0-9]", "_", component_id).upper()
    return Path(os.environ.get(key) or (Path.home() / component_id)).expanduser()


# --------------------------------------------------------------------- judge
def judge(root: Path, base: str, env: Env, work: Path) -> Verdict:
    """Judge the committed head of `root` against the CE23-1 proposition."""
    v = Verdict()
    head = env.out(root, "rev-parse", "--verify", "HEAD^{commit}")
    if head is None:
        v.unknown("NOT_A_CHECKOUT", "S0", f"{root} has no HEAD commit")
        return v
    if env.git_(root, "cat-file", "-e", f"{base}^{{commit}}").returncode != 0:
        v.refuse("BASE_NOT_ANCESTOR", "S0", f"base {base} is not a commit of {root}: lineage unproven")
    elif env.git_(root, "merge-base", "--is-ancestor", base, head).returncode != 0:
        v.refuse("BASE_NOT_ANCESTOR", "S0", f"base {base} is not an ancestor of head {head}")
    else:
        v.ok("S0", f"head {head} descends from base {base}")

    # P1/P2: release/v26.9.1 untouched.
    t_head = env.out(root, "rev-parse", f"{head}:{PRED_DIR}")
    t_base = env.out(root, "rev-parse", f"{base}:{PRED_DIR}")
    if t_head is None:
        v.refuse("PREDECESSOR_CHANGED", "P1", f"{PRED_DIR} is absent at the head")
    elif t_head != SUBJ["predecessor_tree"] or (t_base is not None and t_head != t_base):
        diff = env.out(root, "diff", "--name-status", base, head, "--", PRED_DIR) or ""
        v.refuse("PREDECESSOR_CHANGED", "P1",
                 f"{PRED_DIR} tree {t_head} != pinned {SUBJ['predecessor_tree']} (base {t_base}); diff: {diff.splitlines()[:6]}")
    else:
        v.ok("P1", f"{PRED_DIR} tree {t_head} = pin = base tree")
    dirty = env.out(root, "status", "--porcelain=v1", "--untracked-files=all", "--", PRED_DIR)
    manifest = root / PRED_DIR / "manifest.toml"
    digest = sha256(manifest.read_bytes()) if manifest.is_file() else "absent"
    if dirty:
        v.refuse("PREDECESSOR_DIRTY", "P2", f"working tree changes under {PRED_DIR}: {dirty.splitlines()[:6]}")
    elif digest != SUBJ["predecessor_manifest_sha256"]:
        v.refuse("PREDECESSOR_CHANGED", "P2", f"{PRED_DIR}/manifest.toml sha256 {digest} != pin")
    else:
        v.ok("P2", f"checkout clean under {PRED_DIR}; manifest sha256 {digest}")

    # A1: the subject exists in the committed tree.
    required = [*SUBJ["inputs"], *SUBJ["outputs"], *SUBJ["line_pointers"]]
    missing = [p for p in required if not env.out(root, "ls-tree", "--name-only", head, "--", f"{SDIR}/{p}")]
    if missing:
        v.refuse("SUBJECT_ABSENT", "A1", f"no committed {SDIR}/{{{','.join(missing)}}} at {head}")
        return v
    v.ok("A1", f"{len(required)} subject paths committed under {SDIR}")
    paths = [f"{SDIR}/{p}" for p in ("ggen.toml", "ggen.lock", "release.ttl", "templates", "imports",
                                      SUBJ["generated_dir"], SUBJ["vendor_dir"], "sjira/compiled",
                                      "courts/CE23-1.sh", "courts/ce23_1", *SUBJ["line_pointers"])]
    dirty = env.out(root, "status", "--porcelain=v1", "--untracked-files=all", "--", *paths)
    if dirty:
        v.refuse("SUBJECT_DIRTY", "A2", f"working tree diverges from the head: {dirty.splitlines()[:6]}")
    else:
        v.ok("A2", "checkout clean under the subject paths")

    # A3: line pointers are projections, not copies.
    for name, target in SUBJ["line_pointers"].items():
        entry = (env.out(root, "ls-tree", head, "--", f"{SDIR}/{name}") or "").split()
        link = env.out(root, "cat-file", "blob", entry[2]) if len(entry) >= 3 else None
        if not entry or entry[0] != "120000" or link != target:
            v.refuse("LINE_POINTER_NOT_PROJECTION", "A3",
                     f"{SDIR}/{name} is {entry[:2] or 'absent'} -> {link!r}, not a symlink to {target}")
        else:
            v.ok("A3", f"{SDIR}/{name} -> {target}")

    config_law(v, root, head, env)      # A4
    self_contained(v, root, head, env)  # A5
    court_identity(v, root, head, env)  # C1

    # Materialize the exact committed slice.
    slice_dir = work / "slice"
    try:
        env.archive(root, head, slice_scope(), slice_dir)
    except RuntimeError as exc:
        v.refuse("SUBJECT_ABSENT", "A1", f"committed slice not materializable: {exc}")
        return v
    sub = slice_dir / SDIR

    def clause(name: str, fn: Callable, *args):
        # A committed subject file the slice cannot read (a dangling symlink, a missing input)
        # is a defect of the subject: typed refusal, never a court fault.
        try:
            return fn(*args)
        except OSError as exc:
            v.refuse("SUBJECT_UNREADABLE", name, f"committed subject file unreadable in the slice: {exc}")
            return None

    vendor_rows = clause("V1", vendor, v, root, head, sub, env) or []
    clause("G1", render, v, sub, env)
    clause("G2", gates, v, sub, env, vendor_rows)
    man = clause("M1", manifest_law, v, sub)
    if man is not None:
        clause("I1", import_identity, v, sub, man, env)
        clause("M2", lineage, v, man, env)
        clause("T1", tool, v, slice_dir, sub, env)
    clause("R1", rows, v, sub)
    return v


def slice_scope() -> list[str]:
    return [PRED_DIR, SDIR, TOOLS["verify_release"], *TOOLS["support"]]


def config_law(v: Verdict, root: Path, head: str, env: Env) -> None:
    """A4: ggen.toml is closed-world and every path it reads is a committed regular entry of the subject."""
    blob = env.out(root, "show", f"{head}:{SDIR}/ggen.toml")
    try:
        config = tomllib.loads(blob or "")
    except tomllib.TOMLDecodeError as exc:
        v.refuse("SUBJECT_NOT_INDEPENDENT", "A4", f"{SDIR}/ggen.toml is not TOML: {exc}")
        return
    if not config:
        v.refuse("SUBJECT_NOT_INDEPENDENT", "A4", f"{SDIR}/ggen.toml is empty at {head}")
        return
    reads: list[tuple[str, object]] = []
    unjudged: list[str] = []

    def take(where: str, kind: str, value: object) -> None:
        if kind == "path":
            reads.append((where, value))
        elif kind == "paths" and isinstance(value, list):
            reads.extend((f"{where}[{i}]", item) for i, item in enumerate(value))
        elif kind == "str" and isinstance(value, str):
            pass
        elif kind == "bool" and isinstance(value, bool):
            pass
        elif kind == "prefixes" and isinstance(value, dict) and all(isinstance(x, str) for x in value.values()):
            pass
        else:
            unjudged.append(f"{where} = {value!r} (not a {kind})")

    for top, value in config.items():
        if top == "packs" and isinstance(value, dict):
            for name, entry in value.items():
                if not isinstance(entry, dict):
                    unjudged.append(f"packs.{name} = {entry!r}")
                    continue
                for key, val in entry.items():
                    kind = PACK_SCHEMA.get(key)
                    if kind is None:
                        unjudged.append(f"packs.{name}.{key}")
                    else:
                        take(f"packs.{name}.{key}", kind, val)
            continue
        schema = CONFIG_SCHEMA.get(top)
        if schema is None or not isinstance(value, dict):
            unjudged.append(top)
            continue
        for key, val in value.items():
            kind = schema.get(key)
            if kind is None:
                unjudged.append(f"{top}.{key}")
            else:
                take(f"{top}.{key}", kind, val)
    if unjudged:
        v.refuse("CONFIG_UNJUDGED", "A4",
                 f"{SDIR}/ggen.toml carries keys the court does not judge (each may read an input the court "
                 f"never sees, e.g. law.reflexive reads the uncommitted .ggen-v2/receipt-log.jsonl): {unjudged[:6]}")
    wheres = {where.split("[")[0] for where, _ in reads}
    absent = [k for k in ("ontology.source", "templates.dir") if k not in wheres]
    bad: list[str] = []
    for where, r in reads:
        if not isinstance(r, str) or not r or r.startswith(("/", "~")) or ".." in PurePosixPath(r).parts \
                or PurePosixPath(r).as_posix() != r:
            bad.append(f"{where} = {r!r} (absolute, home-relative, '..' or not normalized)")
            continue
        entry = (env.out(root, "ls-tree", head, "--", f"{SDIR}/{r}") or "").split()
        if not entry or entry[0] not in (*REGULAR_MODES, "040000"):
            bad.append(f"{where} = {r!r} is {entry[:2] or 'not committed'} at the head, not a committed regular "
                       f"file or directory of {SDIR} (a symlink or gitlink reads outside the commit)")
    if absent or bad:
        v.refuse("SUBJECT_NOT_INDEPENDENT", "A4", f"{SDIR}/ggen.toml reads outside {SDIR}: {bad[:6]}"
                 + (f"; missing {absent}" if absent else ""))
    elif not unjudged:
        v.ok("A4", f"{SDIR}/ggen.toml is closed-world; its {len(reads)} read paths are committed regular "
                   f"entries inside {SDIR}")


def self_contained(v: Verdict, root: Path, head: str, env: Env) -> None:
    """A5: no committed symlink or gitlink in the judged slice except the pinned line pointers."""
    proc = env.git_(root, "ls-tree", "-r", "-z", head, "--", *slice_scope())
    if proc.returncode != 0:
        v.unknown("GIT_FAILED", "A5", f"git ls-tree {head}: {proc.stderr.strip()[-240:]}")
        return
    pointers = {f"{SDIR}/{name}" for name in SUBJ["line_pointers"]}
    entries, foreign = 0, []
    for record in filter(None, proc.stdout.split("\0")):
        meta, _, path = record.partition("\t")
        mode, kind, oid = meta.split()
        entries += 1
        if mode in REGULAR_MODES or (mode == "120000" and path in pointers):
            continue
        target = env.out(root, "cat-file", "blob", oid) if mode == "120000" else f"commit {oid}"
        foreign.append(f"{path} ({mode} {'symlink' if mode == '120000' else kind}) -> {target}")
    if foreign:
        v.refuse("SUBJECT_NOT_INDEPENDENT", "A5",
                 f"the judged slice holds {len(foreign)} symlink/gitlink entries beyond the pinned line pointers "
                 f"(each reads bytes the commit does not carry): {foreign[:6]}")
    else:
        v.ok("A5", f"{entries} committed entries of the judged slice are regular files except the "
                   f"{len(pointers)} pinned line-pointer symlinks")


def court_identity(v: Verdict, root: Path, head: str, env: Env) -> None:
    """C1: the court judging is the committed court of the judged head (code and pins)."""
    diverged = []
    for rel, loaded in COURT_BYTES.items():
        blob = env.git_(root, "cat-file", "blob", f"{head}:{rel}", text=False)
        if loaded is None or blob.returncode != 0 or blob.stdout != loaded:
            diverged.append(f"{rel} ({'absent at head' if blob.returncode != 0 else 'differs from the loaded court'})")
    if diverged:
        v.refuse("COURT_NOT_AT_HEAD", "C1",
                 f"the court judging is not the committed court at {head}: {diverged}")
    else:
        v.ok("C1", f"the judging court ({len(COURT_BYTES)} files: wrapper, code, pins) is byte-identical to the head's")


def vendor(v: Verdict, root: Path, head: str, sub: Path, env: Env) -> list[dict]:
    doc = tomllib.loads((sub / SUBJ["vendor_dir"] / "VENDOR.toml").read_text(encoding="utf-8"))
    packs = doc.get("pack", [])
    if not packs:
        v.refuse("VENDOR_EMPTY", "V1", f"{SUBJ['vendor_dir']}/VENDOR.toml declares no [[pack]]")
        return []
    marketplace = Path(os.environ.get("CE23_MARKETPLACE_REPO") or (Path.home() / "ggen-marketplace")).expanduser()
    for row in packs:
        rel = f"{SDIR}/{SUBJ['vendor_dir']}/{row['subdir']}"
        here = env.out(root, "rev-parse", f"{head}:{rel}")
        if here != row["tree"]:
            v.refuse("VENDOR_TREE_MISMATCH", "V1", f"{rel} tree {here} != VENDOR.toml tree {row['tree']}")
            continue
        if env.git_(marketplace, "cat-file", "-e", f"{row['commit']}^{{commit}}").returncode != 0:
            v.unknown("MARKETPLACE_UNAVAILABLE", "V1", f"{marketplace} holds no commit {row['commit']}")
            continue
        there = env.out(marketplace, "rev-parse", f"{row['commit']}:{row['subdir']}")
        if there != row["tree"]:
            v.refuse("VENDOR_NOT_BYTE_IDENTICAL", "V1", f"marketplace {row['commit']}:{row['subdir']} is {there}, vendored {row['tree']}")
            continue
        ref = f"refs/remotes/origin/{row['ref']}"
        if env.out(marketplace, "rev-parse", "--verify", f"{ref}^{{commit}}") is None:
            v.unknown("MARKETPLACE_REF_UNOBSERVED", "V1", f"{marketplace} has no {ref}")
            continue
        if env.git_(marketplace, "merge-base", "--is-ancestor", row["commit"], ref).returncode != 0:
            v.refuse("VENDOR_COMMIT_UNPUBLISHED", "V1", f"{row['commit']} is not on {ref}")
            continue
        v.ok("V1", f"{row['name']} {row['subdir']} tree {row['tree']} = marketplace {row['commit'][:12]} on origin/{row['ref']}")
    config = tomllib.loads((sub / "ggen.toml").read_text(encoding="utf-8"))
    vendored = {f"{SUBJ['vendor_dir']}/{row['subdir']}" for row in packs}
    entries = config.get("packs", {})
    if not entries:
        v.refuse("PACK_NOT_VENDORED", "V1", "ggen.toml consumes no pack")
    for name, entry in entries.items():
        if not isinstance(entry, dict) or entry.get("path") not in vendored:
            v.refuse("PACK_NOT_VENDORED", "V1", f"ggen.toml pack {name} = {entry!r} is not a vendored row")
        elif entry.get("lock") is not True:
            v.refuse("PACK_NOT_LOCKED", "V1", f"ggen.toml pack {name} has lock = {entry.get('lock')!r}")
        else:
            v.ok("V1", f"ggen.toml pack {name} from {entry['path']}, lock = true")
    return packs


def render(v: Verdict, sub: Path, env: Env) -> None:
    committed = rendered(sub)
    first = env.run([env.ggen, "sync", "run"], cwd=sub)
    if first.returncode != 0:
        v.refuse("GENERATION_REFUSED", "G1", f"ggen sync run on the committed subject exit {first.returncode}: {fm_codes(first)}")
        return
    if rendered(sub) != committed:
        changed = sorted(k for k in set(committed) | set(rendered(sub)) if committed.get(k) != rendered(sub).get(k))
        v.refuse("GENERATED_DRIFT", "G1", f"ggen sync run rewrote committed outputs: {changed}")
        return
    shutil.rmtree(sub / SUBJ["generated_dir"])
    (sub / "ggen.lock").unlink()
    fresh = env.run([env.ggen, "sync", "run"], cwd=sub)
    if fresh.returncode != 0:
        v.refuse("GENERATION_REFUSED", "G1", f"fresh ggen sync run exit {fresh.returncode}: {fm_codes(fresh)}")
        return
    again = rendered(sub)
    if set(again) != set(committed):
        v.refuse("GENERATED_SET_MISMATCH", "G1",
                 f"render set {sorted(again)} != committed {sorted(committed)}")
        return
    drift = sorted(k for k in again if again[k] != committed[k])
    if drift:
        v.refuse("GENERATED_DRIFT", "G1", f"fresh render differs from the committed bytes: {drift}")
        return
    idem = env.run([env.ggen, "sync", "run"], cwd=sub)
    if idem.returncode != 0 or rendered(sub) != committed:
        v.refuse("GENERATION_NOT_IDEMPOTENT", "G1", f"second fresh sync exit {idem.returncode}: {fm_codes(idem)}")
        return
    v.ok("G1", f"{' '.join(env.ggen_version)}: committed render and lock reproduce byte-identically "
               f"({len(committed)} files; sync on the committed tree writes nothing; idempotent)")


def gates(v: Verdict, sub: Path, env: Env, packs: list[dict]) -> None:
    for row in packs:
        runner = sub / SUBJ["vendor_dir"] / row["subdir"] / "bin" / "run-gates.py"
        if not runner.is_file():
            continue
        proc = env.run([env.python, str(runner), "release.ttl"], cwd=sub)
        if "ModuleNotFoundError" in proc.stderr:
            v.unknown("RDFLIB_MISSING", "G2", proc.stderr.strip().splitlines()[-1])
        elif proc.returncode != 0 or "RELEASE_GATES ALIVE" not in proc.stdout:
            bad = [line for line in proc.stdout.splitlines() if line.startswith("GATE_VIOLATION") or line.startswith("    ")]
            v.refuse("GATES_REFUSED", "G2", f"{row['name']} run-gates exit {proc.returncode}: {bad[:6] or proc.stderr[-240:]}")
        else:
            passed = sum(1 for line in proc.stdout.splitlines() if line.startswith("GATE_PASS"))
            v.ok("G2", f"{row['name']} bin/run-gates.py (rdflib): RELEASE_GATES ALIVE, {passed} gates")


def critical_path(sub: Path) -> list[str]:
    from rdflib import Graph, Namespace  # noqa: PLC0415 (rdflib is optional: UNKNOWN when absent)

    sj, dct = Namespace(SJ), Namespace(DCT)
    g = Graph()
    g.parse(sub / SUBJ["classification_import"], format="turtle")
    return sorted({str(g.value(s, dct.identifier)) for s in g.subjects(sj.fleetClass, sj.CriticalPath)})


def manifest_law(v: Verdict, sub: Path) -> dict | None:
    try:
        man = tomllib.loads((sub / "manifest.toml").read_text(encoding="utf-8"))
        cross = tomllib.loads((sub / "constitutional-role-crosswalk.toml").read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        v.refuse("MANIFEST_UNREADABLE", "M1", f"{SDIR}/manifest.toml: {exc}")
        return None
    release = man.get("release", {})
    if release.get("version") != SUBJ["target_version"]:
        v.refuse("MANIFEST_VERSION", "M1", f"release.version {release.get('version')!r} != {SUBJ['target_version']}")
    try:
        critical = critical_path(sub)
    except ImportError as exc:
        v.unknown("RDFLIB_MISSING", "M1", str(exc))
        return man
    if not critical:
        v.refuse("CLASSIFICATION_EMPTY", "M1", f"{SUBJ['classification_import']} names no CriticalPath repository")
    comps = [c for c in man.get("components", []) if isinstance(c, dict)]
    by_name = {str(c.get("repository", "")).split("/")[-1]: c for c in comps}
    for name in critical:
        c = by_name.get(name)
        missing = [f for f in VERIFY_FIELDS if c is None or f not in c]
        if c is None or c.get("required") is not True or c.get("disposition") != "REQUIRED" or missing \
                or not SHA40.match(str(c.get("sha", ""))):
            v.refuse("CRITICAL_PATH_NOT_REQUIRED", "M1",
                     f"CriticalPath {name}: component {None if c is None else {k: c.get(k) for k in ('repository', 'sha', 'required', 'disposition')}}, missing {missing}")
        else:
            v.ok("M1", f"CriticalPath {name} = required component {c['repository']}@{c['sha']}")
    roles = set(release.get("required_roles", []))
    mapped = {row.get("release_role") for row in cross.get("crosswalk", [])}
    if cross.get("constitutional", {}).get("version") != SUBJ["target_version"] or not roles or roles - mapped:
        v.refuse("CROSSWALK_UNBOUND", "M1",
                 f"crosswalk version {cross.get('constitutional', {}).get('version')!r}, roles {sorted(roles)}, unmapped {sorted(roles - mapped)}")
    else:
        v.ok("M1", f"manifest {release['version']}; crosswalk {SUBJ['target_version']} maps {sorted(roles)}")
    return man


def import_identity(v: Verdict, sub: Path, man: dict, env: Env) -> None:
    source = str(man.get("release", {}).get("classification_source", ""))
    m = SOURCE_RE.match(source)
    if not m:
        v.refuse("CLASSIFICATION_SOURCE_INVALID", "I1", f"classification_source {source!r}")
        return
    if (m["repo"], m["path"]) != (SUBJ["classification_repository"], SUBJ["classification_path"]):
        v.refuse("IMPORT_SOURCE_UNPINNED", "I1",
                 f"classification from {m['repo']}:{m['path']}, pinned {SUBJ['classification_repository']}:{SUBJ['classification_path']}")
        return
    pinned = {str(c.get("repository")): c for c in man.get("components", []) if c.get("required") is True}
    comp = pinned.get(m["repo"])
    if comp is None or comp.get("sha") != m["sha"]:
        v.refuse("IMPORT_NOT_PINNED", "I1",
                 f"classification from {m['repo']}@{m['sha']}; that repository's required component is "
                 f"{None if comp is None else comp.get('sha')}")
        return
    data = (sub / SUBJ["classification_import"]).read_bytes()
    if sha256(data) != m["digest"]:
        v.refuse("IMPORT_DIGEST_MISMATCH", "I1", f"{SUBJ['classification_import']} sha256 {sha256(data)} != {m['digest']}")
    repo = repo_for(str(comp["id"]))
    if env.git_(repo, "cat-file", "-e", f"{m['sha']}^{{commit}}").returncode != 0:
        v.unknown("COMPONENT_REPO_UNAVAILABLE", "I1", f"{repo} holds no commit {m['sha']}")
        return
    blob = env.git_(repo, "show", f"{m['sha']}:{m['path']}", text=False)
    if blob.returncode != 0 or blob.stdout != data:
        v.refuse("IMPORT_NOT_BYTE_COPY", "I1", f"{SUBJ['classification_import']} != {m['repo']}@{m['sha'][:12]}:{m['path']}")
    elif sha256(data) == m["digest"]:
        v.ok("I1", f"{SUBJ['classification_import']} = {m['repo']}@{m['sha'][:12]}:{m['path']} (sha256 {m['digest'][:16]})")


def lineage(v: Verdict, man: dict, env: Env) -> None:
    for c in man.get("components", []):
        if c.get("required") is not True or c.get("ref_check") != "github":
            continue
        repo, sha, ref = repo_for(str(c.get("id"))), str(c.get("sha")), f"refs/remotes/origin/{c.get('ref')}"
        if env.git_(repo, "cat-file", "-e", f"{sha}^{{commit}}").returncode != 0:
            v.unknown("COMPONENT_REPO_UNAVAILABLE", "M2", f"{repo} holds no commit {sha}")
        elif env.out(repo, "rev-parse", "--verify", f"{ref}^{{commit}}") is None:
            v.unknown("COMPONENT_REF_UNOBSERVED", "M2", f"{repo} has no {ref}")
        elif env.git_(repo, "merge-base", "--is-ancestor", sha, ref).returncode != 0:
            v.refuse("COMPONENT_NOT_ON_REF", "M2", f"{c.get('repository')}@{sha} is not an ancestor of {ref}")
        else:
            v.ok("M2", f"{c.get('repository')}@{sha[:12]} on origin/{c.get('ref')}")


def tool(v: Verdict, slice_dir: Path, sub: Path, env: Env) -> None:
    script = TOOLS["verify_release"]
    runs = [env.run([env.python, script, "--release", SUBJ["target"]], cwd=slice_dir),
            env.run([env.python, script, "--manifest", f"{SDIR}/manifest.toml"], cwd=slice_dir)]
    want = sha256((sub / "manifest.toml").read_bytes())
    for proc in runs:
        try:
            report = json.loads(proc.stdout)
        except json.JSONDecodeError:
            v.refuse("VERIFY_RELEASE_REFUSED", "T1", f"{script} exit {proc.returncode}: {(proc.stderr or proc.stdout).strip()[-240:]}")
            return
        codes = sorted({f.get("code") for f in report.get("findings", [])})
        if proc.returncode != 0 or codes or report.get("release") != SUBJ["target_version"] \
                or report.get("manifest_sha256") != want:
            v.refuse("VERIFY_RELEASE_REFUSED", "T1",
                     f"{script} exit {proc.returncode}, release {report.get('release')!r}, findings {codes}, "
                     f"manifest_sha256 {report.get('manifest_sha256')} (render {want})")
            return
    if runs[0].stdout != runs[1].stdout:
        v.refuse("VERIFY_RELEASE_REFUSED", "T1", "--release and --manifest reports differ")
        return
    v.ok("T1", f"{script} --release {SUBJ['target']}: exit 0, release {SUBJ['target_version']}, "
               f"findings [], manifest_sha256 {want[:16]} (= render)")


def rows(v: Verdict, sub: Path) -> None:
    try:
        from rdflib import RDF, Graph, Namespace  # noqa: PLC0415
    except ImportError as exc:
        v.unknown("RDFLIB_MISSING", "R1", str(exc))
        return
    sj, dct = Namespace(SJ), Namespace(DCT)
    files = sorted(sub.glob(SUBJ["orders_glob"]))
    g = Graph()
    for f in files:
        g.parse(f, format="turtle")
    orders: dict[str, str] = {}
    for o in set(g.subjects(sj.checkpointOf, None)):
        if (o, RDF.type, sj.WorkOrder) not in g:
            continue
        gate = g.value(o, sj.checkpointOf)
        orders[str(g.value(o, dct.identifier) or o)] = str(g.value(gate, dct.identifier) or str(gate).rpartition("#")[2])
    req = tomllib.loads((sub / SUBJ["generated_dir"] / "requirements.toml").read_text(encoding="utf-8"))
    got = {r.get("work_order"): r.get("gate") for r in req.get("requirement", [])}
    count = req.get("requirements", {}).get("row_count")
    ce23_1 = sorted(k for k, gate in got.items() if gate == SUBJ["gate"])
    if not orders or got != orders or count != len(orders) or len(req.get("requirement", [])) != len(orders) or not ce23_1:
        v.refuse("REQUIREMENT_ROWS_DROPPED", "R1",
                 f"{len(orders)} checkpointed orders in {len(files)} compiled units; requirements.toml row_count {count}, "
                 f"{len(req.get('requirement', []))} rows, missing {sorted(set(orders) - set(got))[:4]}, "
                 f"foreign {sorted(set(got) - set(orders))[:4]}, {SUBJ['gate']} rows {ce23_1}")
    else:
        v.ok("R1", f"requirements.toml: {count} rows = checkpointed orders of {len(files)} compiled units ({len(ce23_1)} {SUBJ['gate']})")


# ------------------------------------------------------------ anti-vacuity
@dataclass(frozen=True)
class Mutant:
    """One anti-vacuity mutant: `mutate` edits the synthetic repository in place (and may return
    a replacement base commit); it is committed unless `commit` is False (a working-tree
    mutant). The judge must refuse with every code in `expect`, and a refusal line must carry
    `mention` when set (the refusal is for the named reason, not an incidental one)."""

    id: str
    desc: str
    expect: tuple[str, ...]
    mutate: Callable[[Path], str | None]
    mention: str | None = None
    commit: bool = True


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"mutation anchor not found in {path}: {old[:60]!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def mutants(env: Env) -> list[Mutant]:
    def sub(r: Path) -> Path:
        return r / SDIR

    def regen(r: Path, relock: bool = False) -> None:
        # ggen.lock pins the pack and every extra_ontologies input (FM-PACK-008 on drift): a
        # mutant that changes an import list re-locks on purpose, as the remediation says.
        s = sub(r)
        shutil.rmtree(s / SUBJ["generated_dir"], ignore_errors=True)
        if relock:
            (s / "ggen.lock").unlink()
        proc = env.run([env.ggen, "sync", "run"], cwd=s)
        if proc.returncode != 0:
            raise RuntimeError(f"mutant regeneration refused: {fm_codes(proc)}")
        shutil.rmtree(s / ".ggen", ignore_errors=True)
        shutil.rmtree(s / ".ggen-v2", ignore_errors=True)

    def revert(r: Path) -> None:
        s = sub(r)
        for p in (*SUBJ["inputs"], *SUBJ["line_pointers"], "ggen.lock"):
            (s / p).unlink(missing_ok=True)
        for d in (SUBJ["generated_dir"], "imports", "templates", SUBJ["vendor_dir"].split("/")[0]):
            shutil.rmtree(s / d, ignore_errors=True)

    def hand_edit(r: Path) -> None:
        _edit(sub(r) / "out/manifest.toml", 'sha = "6fd59588c2e06b83d1af6ebc653e7b545de6f90f"', 'sha = "' + "0" * 40 + '"')

    def drop_gi_graph(r: Path) -> None:
        t = sub(r) / "release.ttl"
        _edit(t, 'er:requiredRole "execution-realization", "semantic-manufacture"', 'er:requiredRole "execution-realization"')
        _edit(t, "er:hasComponent r23:xaas, r23:ggen_igniter", "er:hasComponent r23:xaas")
        _edit(t, "er:hasRoleMapping r23:map-execution-realization, r23:map-semantic-manufacture",
              "er:hasRoleMapping r23:map-execution-realization")
        _edit(t, "    er:refCheckMode er:GITHUB_LIVE ;\n    er:dependsOn r23:ggen_igniter .", "    er:refCheckMode er:GITHUB_LIVE .")
        text = t.read_text(encoding="utf-8")
        text, n1 = re.subn(r"r23:ggen_igniter a er:Component ;.*?er:GITHUB_LIVE \.\n", "", text, flags=re.S)
        text, n2 = re.subn(r"r23:map-semantic-manufacture a er:RoleMapping ;.*?\"CONSTRUCT_ONLY_NO_DO\" \.\n", "", text, flags=re.S)
        if (n1, n2) != (1, 1):
            raise RuntimeError(f"ggen_igniter blocks not found ({n1}, {n2})")
        t.write_text(text, encoding="utf-8")

    def drop_gi_render(r: Path) -> None:
        drop_gi_graph(r)
        m = sub(r) / "out/manifest.toml"
        text, n = re.subn(r'\n\[\[components\]\]\nid = "ggen_igniter".*?depends_on = \[\]\n', "\n",
                          m.read_text(encoding="utf-8"), flags=re.S)
        if n != 1:
            raise RuntimeError("ggen_igniter component not found in the render")
        m.write_text(text.replace('  "semantic-manufacture",\n', "").replace('depends_on = ["ggen_igniter", ]', "depends_on = []"),
                     encoding="utf-8")

    def pred_byte(r: Path) -> None:
        with (r / PRED_DIR / "manifest.toml").open("a", encoding="utf-8") as f:
            f.write("\n")

    def pred_file(r: Path) -> None:
        (r / PRED_DIR / "NOTE.md").write_text("v26.9.23 note\n", encoding="utf-8")

    def relax_gate(r: Path) -> None:
        gate = sub(r) / SUBJ["vendor_dir"] / "packs/chatman-ecosystem-release-pack/gates/080_critical_path_coverage.rq"
        if not gate.is_file():
            raise RuntimeError(f"{gate} absent")
        gate.write_text("SELECT ?release ?reason WHERE { FILTER(false) }\n", encoding="utf-8")

    def fork_pointer(r: Path) -> None:
        p = sub(r) / "manifest.toml"
        data = p.read_bytes()
        p.unlink()
        p.write_bytes(data)

    def edit_import(r: Path) -> None:
        f = sub(r) / SUBJ["classification_import"]
        head, sep, tail = f.read_text(encoding="utf-8").partition('dcterms:identifier "ggen_igniter" ;')
        if not sep or "sj:fleetClass sj:CriticalPath" not in tail:
            raise RuntimeError("classification anchor absent")
        f.write_text(head + sep + tail.replace("sj:fleetClass sj:CriticalPath", "sj:fleetClass sj:Successor", 1), encoding="utf-8")

    def version_literal(r: Path) -> None:
        _edit(sub(r) / "release.ttl", 'er:version "26.9.23"', 'er:version "26.9.1"')
        regen(r)

    def drop_rows(r: Path) -> None:
        _edit(sub(r) / "ggen.toml", ', "sjira/compiled/chatman-ce23-12-standings/orders.ttl"', "")
        regen(r, relock=True)

    def repin(r: Path) -> None:
        # xaas re-pinned to a later commit of the same ref while the classification source still
        # names the S23 commit: the import no longer comes from the component it claims.
        _edit(sub(r) / "release.ttl", 'er:commitSha "6fd59588c2e06b83d1af6ebc653e7b545de6f90f"',
              'er:commitSha "cb3991282f73727f008f478da7f29ab487ac57c3"')
        regen(r)

    def dirty_pred(r: Path) -> None:
        pred_byte(r)

    def dirty_subject(r: Path) -> None:
        with (sub(r) / "release.ttl").open("a", encoding="utf-8") as f:
            f.write("# uncommitted\n")

    def read_predecessor(r: Path) -> None:
        _edit(sub(r) / "ggen.toml", '"imports/fleet-classification.ttl", ',
              '"imports/fleet-classification.ttl", "../v26.9.1/qlever/structural_similarity.rq", ')

    def foreign_source(r: Path) -> None:
        _edit(sub(r) / "release.ttl", ":docs/sjira/v26.9.23/fleet/classification.ttl sha256:",
              ":docs/sjira/v26.9.22/fleet/classification.ttl sha256:")
        regen(r)

    def symlink_import_absolute(r: Path) -> None:
        # The committed import becomes an absolute symlink to identical bytes outside the
        # repository: every byte and lock check still matches, but the commit carries no copy.
        f = sub(r) / SUBJ["classification_import"]
        outside = r.parent / f"{r.name}-external" / f.name
        outside.parent.mkdir(parents=True, exist_ok=True)
        outside.write_bytes(f.read_bytes())
        f.unlink()
        f.symlink_to(outside)

    def symlink_import_relative(r: Path) -> None:
        # A relative symlink leaving the subject to identical bytes committed elsewhere in the
        # repository (resolvable in a checkout, dangling in the subject slice).
        f = sub(r) / SUBJ["classification_import"]
        shadow = r / "shadow" / f.name
        shadow.parent.mkdir(parents=True)
        shadow.write_bytes(f.read_bytes())
        f.unlink()
        f.symlink_to(os.path.relpath(shadow, f.parent))

    def reflexive(r: Path) -> None:
        # ggen accepts law.reflexive and renders the same bytes, but the sync graph then reads the
        # uncommitted .ggen-v2/receipt-log.jsonl.
        with (sub(r) / "ggen.toml").open("a", encoding="utf-8") as f:
            f.write("\n[law]\nreflexive = true\n")

    def unlock(r: Path) -> None:
        _edit(sub(r) / "ggen.toml", "lock = true", "lock = false")

    def off_ref(r: Path) -> None:
        # ggen_igniter re-pinned to a commit of its canonical checkout that is not on the
        # component's ref (chosen from the checkout, so the premise holds when the ref moves).
        man = tomllib.loads((sub(r) / "out/manifest.toml").read_text(encoding="utf-8"))
        comp = next(c for c in man["components"] if c.get("id") == "ggen_igniter")
        repo, ref = repo_for("ggen_igniter"), f"refs/remotes/origin/{comp['ref']}"
        other = env.out(repo, "rev-list", "-n", "1", "--remotes", "--not", ref)
        if not other or not SHA40.match(other):
            raise RuntimeError(f"{repo} holds no remote commit off {ref} to re-pin ggen_igniter to")
        _edit(sub(r) / "release.ttl", f'er:commitSha "{comp["sha"]}"', f'er:commitSha "{other}"')
        regen(r)

    def court_pins(r: Path) -> None:
        with (sub(r) / "courts/ce23_1/subject.toml").open("a", encoding="utf-8") as f:
            f.write("# committed pins that are not the running court's\n")

    def orphan_base(r: Path) -> str:
        empty = env.run([env.git, "-C", str(r), "hash-object", "-t", "tree", "--stdin", "-w"], stdin=b"")
        proc = env.run([env.git, "-C", str(r), "-c", "user.name=ce23-1-court", "-c", "user.email=ce23-1-court@localhost",
                        "commit-tree", empty.stdout.strip(), "-m", "orphan base"])
        if proc.returncode != 0:
            raise RuntimeError(f"orphan commit: {proc.stderr[-200:]}")
        return proc.stdout.strip()

    return [
        Mutant("MV", "revert: the CE23-1 subject removed (inputs, render, vendor, pointers)", ("SUBJECT_ABSENT",), revert),
        Mutant("M1", "hand-edited committed render (xaas sha zeroed in out/manifest.toml)", ("GENERATION_REFUSED",), hand_edit,
               "FM-WRITE-005"),
        Mutant("M2", "ggen_igniter dropped consistently from release.ttl", ("GENERATION_REFUSED",), drop_gi_graph,
               "080_critical_path_coverage"),
        Mutant("M2b", "ggen_igniter dropped from release.ttl and from the committed render", ("CRITICAL_PATH_NOT_REQUIRED",),
               drop_gi_render),
        Mutant("M3", "one byte appended to release/v26.9.1/manifest.toml", ("PREDECESSOR_CHANGED",), pred_byte),
        Mutant("M4", "a new file under release/v26.9.1", ("PREDECESSOR_CHANGED",), pred_file),
        Mutant("M3w", "uncommitted byte change to release/v26.9.1/manifest.toml", ("PREDECESSOR_DIRTY",), dirty_pred, commit=False),
        Mutant("M5", "vendored gate 080 relaxed to admit everything", ("VENDOR_TREE_MISMATCH", "GENERATION_REFUSED"), relax_gate,
               "FM-PACK-008"),
        Mutant("M6", "manifest.toml pointer replaced by a copy of the render", ("LINE_POINTER_NOT_PROJECTION",), fork_pointer),
        Mutant("M6w", "uncommitted edit of release.ttl", ("SUBJECT_DIRTY",), dirty_subject, commit=False),
        Mutant("M7", "classification import edited (ggen_igniter CriticalPath -> Successor)",
               ("IMPORT_DIGEST_MISMATCH", "IMPORT_NOT_BYTE_COPY"), edit_import),
        Mutant("M8", "release version literal 26.9.1, render regenerated", ("MANIFEST_VERSION", "VERIFY_RELEASE_REFUSED"),
               version_literal, "ECOSYSTEM_VERSION_MISMATCH"),
        Mutant("M9", "one compiled orders unit dropped from ggen.toml, render regenerated", ("REQUIREMENT_ROWS_DROPPED",), drop_rows),
        Mutant("M10", "xaas re-pinned to another commit of its ref, classification source unchanged, render regenerated",
               ("IMPORT_NOT_PINNED",), repin),
        Mutant("M11", "ggen.toml reads a release/v26.9.1 file as an import", ("SUBJECT_NOT_INDEPENDENT",), read_predecessor),
        Mutant("M12", "classification source re-pointed outside the pinned path, render regenerated",
               ("IMPORT_SOURCE_UNPINNED",), foreign_source),
        Mutant("M13", "classification import an absolute symlink to identical bytes outside the repository",
               ("SUBJECT_NOT_INDEPENDENT",), symlink_import_absolute, "symlink"),
        Mutant("M14", "classification import a relative symlink leaving the subject (identical bytes in the repository)",
               ("SUBJECT_NOT_INDEPENDENT",), symlink_import_relative, "symlink"),
        Mutant("M15", "ggen.toml law.reflexive = true (sync reads the uncommitted receipt log)", ("CONFIG_UNJUDGED",),
               reflexive, "law.reflexive"),
        Mutant("M16", "ggen.toml pack lock = false (ggen.lock no longer pins the pack)",
               ("PACK_NOT_LOCKED", "GENERATED_SET_MISMATCH"), unlock),
        Mutant("M17", "ggen_igniter re-pinned to a commit off its ref, render regenerated", ("COMPONENT_NOT_ON_REF",), off_ref),
        Mutant("M18", "committed court pins differ from the pins of the court judging", ("COURT_NOT_AT_HEAD",), court_pins,
               "subject.toml"),
        Mutant("MB", "the judged head does not descend from the base (orphan base commit)", ("BASE_NOT_ANCESTOR",), orphan_base),
    ]


def anti_vacuity(root: Path, env: Env, work: Path, root_base: str | None = None) -> Verdict:
    """Judge the control and every mutant; `root_base` is the base commit in `root` (default: the pin)."""
    v = Verdict()
    head = env.out(root, "rev-parse", "HEAD")
    synth = work / "av-base"
    synth.mkdir(parents=True)
    try:
        if env.git_(synth, "init", "-q", "-b", "main").returncode != 0:
            raise RuntimeError("git init failed")
        env.archive(root, root_base or SUBJ["base_commit"], [PRED_DIR], synth)
        base = env.commit_all(synth, "base: release/v26.9.1 at the pre-v26.9.23 base")
        for child in synth.iterdir():
            if child.name != ".git":
                shutil.rmtree(child) if child.is_dir() and not child.is_symlink() else child.unlink()
        env.archive(root, str(head), [PRED_DIR, SDIR, TOOLS["verify_release"], *TOOLS["support"]], synth)
        env.commit_all(synth, f"subject: slice of {head}")
    except (RuntimeError, OSError) as exc:
        v.unknown("AV_HARNESS", "AV", f"synthetic repository: {exc}")
        return v

    def one(m: Mutant | None) -> tuple[Mutant | None, Verdict | str]:
        repo = work / f"av-{m.id if m else 'M0'}"
        shutil.copytree(synth, repo, symlinks=True)
        judged_base = base
        try:
            if m is not None:
                replacement = m.mutate(repo)
                judged_base = replacement or base
                if m.commit:
                    env.commit_all(repo, f"mutant {m.id}: {m.desc}")
        except (RuntimeError, OSError) as exc:
            return m, f"AV_CONSTRUCT: {exc}"
        try:
            return m, judge(repo, judged_base, env, work / f"av-{m.id if m else 'M0'}-work")
        except Exception as exc:  # noqa: BLE001 (a court fault witnesses nothing: typed UNKNOWN)
            return m, f"COURT_FAULT: {type(exc).__name__}: {exc}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, os.cpu_count() or 2)) as pool:
        results = list(pool.map(one, [None, *mutants(env)]))
    for m, got in results:
        mid, desc = (m.id, m.desc) if m else ("M0", "unmutated synthetic subject (control)")
        if isinstance(got, str):
            v.unknown("AV_CONSTRUCT", f"AV {mid}", f"{desc}: {got}")
        elif m is None:
            if got.alive:
                v.ok("AV M0", f"{desc}: ALIVE ({len(got.lines)} clauses)")
            else:
                v.refuse("AV_HARNESS", "AV M0", f"{desc} not ALIVE: {[line for line in got.lines if not line.startswith('OK')][:4]}")
        elif not got.refused:
            v.refuse("VACUOUS", f"AV {mid}", f"{desc}: admitted ({'UNKNOWN ' + str(got.unknowns) if got.unknowns else 'ALIVE'})")
        elif missing := [code for code in m.expect if code not in got.refused]:
            v.refuse("AV_WRONG_REFUSAL", f"AV {mid}", f"{desc}: refused {sorted(set(got.refused))}, expected {missing}")
        elif m.mention and not any(m.mention in line for line in got.lines if line.startswith("REFUSED")):
            v.refuse("AV_WRONG_REFUSAL", f"AV {mid}", f"{desc}: refused {sorted(set(got.refused))} without {m.mention}")
        else:
            v.ok(f"AV {mid}", f"{desc}: refused {sorted(set(got.refused))}" + (f" ({m.mention})" if m.mention else ""))
    return v


# ---------------------------------------------------------------------- main
def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-av", action="store_true", help="skip the anti-vacuity corpus (never ALIVE)")
    parser.add_argument("--keep", type=Path, help="scratch directory to keep (default: a removed temp dir)")
    args = parser.parse_args(argv)
    work = args.keep or Path(tempfile.mkdtemp(prefix="ce23-1-court."))
    if args.keep:
        if args.keep.exists() and any(args.keep.iterdir()):
            print(f"REFUSED[SCRATCH_NOT_EMPTY] CE23-1: {args.keep}")
            return 2
        args.keep.mkdir(parents=True, exist_ok=True)
    try:
        env = Env(work / "home")
    except Environment as exc:
        code, _, detail = str(exc).partition(":")
        print(f"UNKNOWN[{code}] CE23-1: {detail}")
        print("CE23-1 UNKNOWN")
        return 75
    try:
        head = env.out(ROOT, "rev-parse", "HEAD")
        print(f"CE23-1 court: subject {head} at {ROOT}")
        try:
            subject = judge(ROOT, SUBJ["base_commit"], env, work / "subject")
        except Exception as exc:  # noqa: BLE001 (a court fault witnesses nothing: typed UNKNOWN)
            subject = Verdict()
            subject.unknown("COURT_FAULT", "CE23-1", f"{type(exc).__name__}: {exc}")
        for line in subject.lines:
            print(line)
        if args.no_av:
            corpus = Verdict()
            corpus.unknown("AV_SKIPPED", "AV", "--no-av: the anti-vacuity corpus did not run")
        else:
            corpus = anti_vacuity(ROOT, env, work / "av")
        for line in corpus.lines:
            print(line)
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
    refused = subject.refused + corpus.refused
    unknown = subject.unknowns + corpus.unknowns
    if refused:
        print(f"CE23-1 REFUSED {sorted(set(refused))}")
        return 1
    if unknown:
        print(f"CE23-1 UNKNOWN {sorted(set(unknown))}")
        return 75
    print("CE23-1 ALIVE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
