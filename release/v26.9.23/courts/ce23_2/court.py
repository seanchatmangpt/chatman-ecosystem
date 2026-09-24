#!/usr/bin/env python3
"""CE23-2 court: crosswalk the old constitutional graph (release/v26.9.23/sjira/goal.ttl ce:CE23-2).

Proposition (chatman-ce23.md CE23-2): every one of the 16 roles required by
release/v26.9.1/manifest.toml maps explicitly to REQUIRED, SUCCESSOR, BLOCKED, UNSUPPORTED or
REFUSED for the new boundary; the old release topology is not silently erased. Falsifier
(goal.ttl ce:CE23-2-falsifier): the court exits 0 while one of the 16 required roles of
release/v26.9.1/manifest.toml has no explicit classification.

The crosswalk is a projection of the byte-identically vendored chatman-ecosystem-release-pack
(law: gates 070/080, the disposition rule template, the crosswalk templates) over consumer
inputs: imports/legacy-v26.9.1.ttl (the pack's lift of the predecessor manifest),
imports/court-references.ttl (courts/ce23_2/observe_court_refs.py), the imported fleet
classification and release.ttl er:crosswalkFrom. The court judges the exact committed head
(`git archive HEAD` in scratch, git objects), never the working tree. Clauses:

  S0 lineage     the head is a commit descending from subject.base_commit
  C1 court       the judging court (CE23-2.sh, court.py, crosswalk.toml, observe_court_refs.py)
                 is byte-identical to the committed court of the head
  A2 checkout    the working tree holds no change under the predecessor manifest, the subject's
                 inputs, render, vendored pack and the CE23-2 court
  P1 predecessor release/v26.9.1/manifest.toml at the head = its blob at the base = the pinned
                 digest; its required roles are distinct and each has exactly one component
                 (the 16 roles are read from this file, never from the render or the pins)
  V1 vendor      the vendored pack tree at the head = its VENDOR.toml row
  W0 wiring      ggen.toml feeds the legacy, court-reference and classification imports to the
                 vendored pack; release.ttl has one er:Release crosswalking from the predecessor
  L1 lift        imports/legacy-v26.9.1.ttl = the vendored lift of the base manifest blob
  X1 observed    imports/court-references.ttl = a fresh observation (observe_court_refs.py) at
                 the release's xaas component commit, read from the canonical xaas checkout
  G1 render      `ggen sync run` on the committed subject exits 0 and writes nothing, and two
                 fresh renders in separate directories are byte-identical to each other and to
                 the committed out/ + ggen.lock (render twice)
  G2 gates       the pack's rdflib runner admits the union graph (second executor), and gates
                 070/080 admit the committed out/crosswalk.ttl as data (no rule applied)
  W1 total       out/legacy-role-crosswalk.toml carries exactly one row per predecessor role,
                 with that role's own component, repository, SHA and standing, one of the five
                 boundaries, a reason and exactly one of derived_by / decided_by; REQUIRED rows
                 are supplied by a required component of out/manifest.toml
  W2 agree       out/crosswalk.ttl and out/role-derivations.toml state the same 16 dispositions
  W3 rule        the disposition rule re-derived by the court (fleet class -> boundary, else no
                 GC23 court reference -> SUCCESSOR) gives every rendered undecided row; the
                 classification import is the digest release.ttl names; a role the rule cannot
                 decide (unclassified and court-executed) is refused without a decision
  D1 decisions   every er:decidedBy disposition, in the input graph or the render, is admitted
                 by crosswalk.toml [decisions] (none today)
  AV corpus      a synthetic two-commit repository (base: release/v26.9.1 at base_commit; head:
                 the judged slice) is ALIVE unmutated (control M0) and each mutant is refused
                 with its expected codes (see mutants())

Every subprocess runs real tools (git, tar, ggen, python3) on real files; there is no test
double. They run under a no-LLM environment (fresh HOME, PATH of the resolved tool directories
plus /usr/bin:/bin, UNKNOWN when any holds claude or zcode). Canonical checkouts are read, never
written: CE23_REPO_XAAS (default ~/xaas).

    python3 release/v26.9.23/courts/ce23_2/court.py [--no-av] [--keep SCRATCH]

Exit: 0 ALIVE; 1 REFUSED (typed REFUSED[<code>] lines name the counterexample);
75 UNKNOWN (typed UNKNOWN[<code>] lines: a tool or a canonical checkout is absent).
"""

from __future__ import annotations

import argparse
import concurrent.futures
import hashlib
import os
import re
import shutil
import site
import subprocess
import sys
import tempfile
import threading
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
_PIN_BYTES = (HERE / "crosswalk.toml").read_bytes()
PINS = tomllib.loads(_PIN_BYTES.decode("utf-8"))
SUBJ = PINS["subject"]
PATHS = SUBJ["paths"]
OBS = PINS["observation"]
RULE = PINS["rule"]
ADMITTED = [tuple((d["role"], d["decided_by"], d["boundary"])) for d in PINS["decisions"]["admitted"]]
SDIR = SUBJ["subject_dir"]
PRED_DIR = f"release/{SUBJ['predecessor']}"
PRED_MANIFEST = SUBJ["predecessor_manifest"]
PACK = f"{PATHS['vendor_dir']}/{PATHS['pack_subdir']}"
OBSERVER = "courts/ce23_2/observe_court_refs.py"
CROSSWALK_LINE = f"    er:crosswalkFrom <{SUBJ['predecessor_iri']}> ;\n"
# C1: the court as loaded (bytes read once, at import), keyed by its committed path.
_WRAPPER = HERE.parent / "CE23-2.sh"
COURT_BYTES: dict[str, bytes | None] = {
    f"{SDIR}/courts/CE23-2.sh": _WRAPPER.read_bytes() if _WRAPPER.is_file() else None,
    f"{SDIR}/courts/ce23_2/court.py": Path(__file__).resolve().read_bytes(),
    f"{SDIR}/courts/ce23_2/crosswalk.toml": _PIN_BYTES,
    f"{SDIR}/{OBSERVER}": (HERE / "observe_court_refs.py").read_bytes(),
}
ER = "http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#"
SJ = "https://ggen-igniter.dev/ontology/semantic-jira#"
DCT = "http://purl.org/dc/terms/"
FM = re.compile(r"\[FM-[A-Z]+-[0-9]+\][^\n]{0,240}")
SHA40 = re.compile(r"^[0-9a-f]{40}$")
DIGEST = re.compile(r"sha256:([0-9a-f]{64})")
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

    def run(self, argv: list[str], cwd: Path | None = None, text: bool = True,
            stdin: bytes | None = None) -> subprocess.CompletedProcess:
        return subprocess.run(argv, cwd=cwd, env=self.vars, input=stdin, capture_output=True, text=text, timeout=900)

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
                     ["-c", "user.name=ce23-2-court", "-c", "user.email=ce23-2-court@localhost",
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


def rendered(sub: Path) -> dict[str, bytes]:
    out = sub / PATHS["generated_dir"]
    files = sorted(p.relative_to(sub).as_posix() for p in out.rglob("*") if p.is_file()) if out.is_dir() else []
    if (sub / "ggen.lock").is_file():
        files.append("ggen.lock")
    return {r: (sub / r).read_bytes() for r in files}


def repo_for(component_id: str) -> Path:
    key = "CE23_REPO_" + re.sub(r"[^A-Za-z0-9]", "_", component_id).upper()
    return Path(os.environ.get(key) or (Path.home() / component_id)).expanduser()


def local(iri: object) -> str:
    return str(iri).rpartition("#")[2]


# --------------------------------------------------------------------- judge
def judge(root: Path, base: str, env: Env, work: Path, xaas_repo: Path | None = None) -> Verdict:
    """Judge the committed head of `root` against the CE23-2 proposition."""
    v = Verdict()
    xaas_repo = xaas_repo or repo_for(OBS["component_id"])
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
    court_identity(v, root, head, env)                     # C1
    checkout(v, root, env)                                 # A2
    pred = predecessor(v, root, head, base, env)           # P1

    slice_dir = work / "slice"
    try:
        env.archive(root, head, [PRED_MANIFEST, SDIR], slice_dir)
    except RuntimeError as exc:
        v.refuse("SUBJECT_ABSENT", "W0", f"committed slice not materializable: {exc}")
        return v
    sub = slice_dir / SDIR
    if not (sub / "ggen.toml").is_file() or not (sub / "release.ttl").is_file():
        v.refuse("SUBJECT_ABSENT", "W0", f"no committed {SDIR}/ggen.toml + release.ttl at {head}")
        return v

    def clause(name: str, fn: Callable, *args):
        # A committed subject file the slice cannot read is a defect of the subject: typed
        # refusal, never a court fault.
        try:
            return fn(*args)
        except (OSError, tomllib.TOMLDecodeError, ValueError) as exc:
            v.refuse("SUBJECT_UNREADABLE", name, f"committed subject file unreadable in the slice: {exc}")
            return None

    try:
        import rdflib  # noqa: F401, PLC0415
    except ImportError as exc:
        v.unknown("RDFLIB_MISSING", "W0", str(exc))
        return v
    clause("V1", vendor, v, root, head, sub, env)
    clause("W0", wiring, v, sub)
    if pred is not None:
        clause("L1", lift, v, sub, pred, env, work)
    clause("X1", observed, v, sub, env, xaas_repo)
    clause("G1", render, v, sub, env, work)
    clause("G2", gates, v, sub, env)
    rows = clause("W1", totality, v, sub, pred) if pred is not None else None
    if rows is not None:
        clause("W2", agree, v, sub, rows)
        clause("W3", rule, v, sub, pred, rows)
    clause("D1", decisions, v, sub, rows or {})
    return v


def court_identity(v: Verdict, root: Path, head: str, env: Env) -> None:
    """C1: the court judging is the committed court of the judged head (code, pins, observer)."""
    diverged = []
    for rel, loaded in COURT_BYTES.items():
        blob = env.git_(root, "cat-file", "blob", f"{head}:{rel}", text=False)
        if loaded is None or blob.returncode != 0 or blob.stdout != loaded:
            diverged.append(f"{rel} ({'absent at head' if blob.returncode != 0 else 'differs from the loaded court'})")
    if diverged:
        v.refuse("COURT_NOT_AT_HEAD", "C1", f"the court judging is not the committed court at {head}: {diverged}")
    else:
        v.ok("C1", f"the judging court ({len(COURT_BYTES)} files: wrapper, code, pins, observer) is byte-identical to the head's")


def checkout(v: Verdict, root: Path, env: Env) -> None:
    """A2: the working tree does not diverge from the head under the judged paths."""
    paths = [PRED_MANIFEST, *(f"{SDIR}/{p}" for p in ("ggen.toml", "ggen.lock", "release.ttl", "imports",
                                                       PATHS["generated_dir"], PATHS["vendor_dir"],
                                                       "courts/CE23-2.sh", "courts/ce23_2"))]
    dirty = env.out(root, "status", "--porcelain=v1", "--untracked-files=all", "--", *paths)
    if dirty:
        v.refuse("SUBJECT_DIRTY", "A2", f"working tree diverges from the head: {dirty.splitlines()[:6]}")
    else:
        v.ok("A2", f"checkout clean under {PRED_MANIFEST} and the CE23-2 subject paths")


def predecessor(v: Verdict, root: Path, head: str, base: str, env: Env) -> dict | None:
    """P1: the predecessor manifest is untouched and defines a role -> component function."""
    at_head = env.git_(root, "cat-file", "blob", f"{head}:{PRED_MANIFEST}", text=False)
    at_base = env.git_(root, "cat-file", "blob", f"{base}:{PRED_MANIFEST}", text=False)
    if at_head.returncode != 0 or at_base.returncode != 0:
        v.refuse("PREDECESSOR_ABSENT", "P1",
                 f"{PRED_MANIFEST} absent at {'the head' if at_head.returncode else 'the base'}")
        return None
    digest = sha256(at_head.stdout)
    if at_head.stdout != at_base.stdout or digest != SUBJ["predecessor_manifest_sha256"]:
        diff = env.out(root, "diff", "--stat", base, head, "--", PRED_MANIFEST) or ""
        v.refuse("PREDECESSOR_CHANGED", "P1",
                 f"{PRED_MANIFEST} at the head (sha256 {digest}) != base blob / pin "
                 f"{SUBJ['predecessor_manifest_sha256']}: {diff.splitlines()[:3]}")
        return None
    pred, problem = role_function(at_base.stdout)
    if pred is None:
        v.refuse("PREDECESSOR_ROLE_AMBIGUOUS", "P1", f"{PRED_MANIFEST}: {problem}")
        return None
    v.ok("P1", f"{PRED_MANIFEST} = base blob = pin (sha256 {digest[:16]}); {len(pred['roles'])} distinct required "
               f"roles, each with exactly one component")
    return pred


def role_function(data: bytes) -> tuple[dict | None, str]:
    """The predecessor's required roles and the one component that fills each, or why not."""
    man = tomllib.loads(data.decode("utf-8"))
    roles = list(man.get("release", {}).get("required_roles", []))
    by_role: dict[str, list[dict]] = {}
    for c in man.get("components", []):
        if isinstance(c, dict):
            by_role.setdefault(str(c.get("role")), []).append(c)
    bad = [r for r in roles if len(by_role.get(r, [])) != 1]
    outside = sorted(set(by_role) - set(roles))
    if not roles or len(set(roles)) != len(roles) or bad or outside:
        return None, (f"{len(roles)} roles ({len(set(roles))} distinct), roles without exactly one component {bad}, "
                      f"component roles outside required_roles {outside}")
    return {"roles": roles, "by_role": {r: by_role[r][0] for r in roles}, "bytes": data}, ""


def vendor(v: Verdict, root: Path, head: str, sub: Path, env: Env) -> None:
    doc = tomllib.loads((sub / PATHS["vendor_dir"] / "VENDOR.toml").read_text(encoding="utf-8"))
    row = next((p for p in doc.get("pack", []) if p.get("subdir") == PATHS["pack_subdir"]), None)
    here = env.out(root, "rev-parse", f"{head}:{SDIR}/{PACK}")
    if row is None:
        v.refuse("VENDOR_TREE_MISMATCH", "V1", f"VENDOR.toml has no row for {PATHS['pack_subdir']}")
    elif here != row.get("tree"):
        v.refuse("VENDOR_TREE_MISMATCH", "V1", f"{SDIR}/{PACK} tree {here} != VENDOR.toml tree {row.get('tree')}")
    else:
        v.ok("V1", f"{PACK} tree {here} = VENDOR.toml row (marketplace {str(row.get('commit'))[:12]})")


def pack_entry(sub: Path) -> dict:
    config = tomllib.loads((sub / "ggen.toml").read_text(encoding="utf-8"))
    for entry in config.get("packs", {}).values():
        if isinstance(entry, dict) and entry.get("path") == PACK:
            return entry
    return {}


def input_graph(sub: Path, extra: list[str] | None = None):
    """release.ttl + every extra_ontologies input of the vendored pack entry (+ `extra`)."""
    from rdflib import Graph  # noqa: PLC0415

    g = Graph()
    g.parse(sub / "release.ttl", format="turtle")
    for rel in [*pack_entry(sub).get("extra_ontologies", []), *(extra or [])]:
        if (sub / rel).is_file():
            g.parse(sub / rel, format="turtle")
    return g


def wiring(v: Verdict, sub: Path) -> None:
    """W0: the crosswalk inputs reach the vendored pack and the release crosswalks from v26.9.1."""
    from rdflib import RDF, Graph, Namespace, URIRef  # noqa: PLC0415

    er = Namespace(ER)
    extras = pack_entry(sub).get("extra_ontologies", [])
    need = [PATHS["legacy_import"], PATHS["court_references_import"], PATHS["classification_import"]]
    missing = [p for p in need if p not in extras]
    g = Graph().parse(sub / "release.ttl", format="turtle")
    releases = sorted(set(g.subjects(RDF.type, er.Release)))
    edges = sorted((str(r), str(o)) for r in releases for o in g.objects(r, er.crosswalkFrom))
    want = URIRef(SUBJ["predecessor_iri"])
    if missing or len(releases) != 1 or edges != [(str(releases[0]), str(want))]:
        v.refuse("CROSSWALK_NOT_WIRED", "W0",
                 f"ggen.toml pack {PACK} lacks extra_ontologies {missing}; release.ttl er:Release {len(releases)}, "
                 f"er:crosswalkFrom {edges} (want exactly one edge to <{want}>)")
    else:
        v.ok("W0", f"ggen.toml feeds {need} to the vendored pack; <{releases[0]}> er:crosswalkFrom <{want}>")


def lift(v: Verdict, sub: Path, pred: dict, env: Env, work: Path) -> None:
    """L1: the committed legacy import is the vendored lift of the base manifest blob."""
    imp = sub / PATHS["legacy_import"]
    if not imp.is_file():
        v.refuse("LEGACY_IMPORT_NOT_LIFT", "L1", f"{PATHS['legacy_import']} is not committed")
        return
    manifest = work / "predecessor-manifest.toml"
    manifest.write_bytes(pred["bytes"])
    proc = env.run([env.python, str(sub / PACK / PATHS["lift"]), str(manifest), SUBJ["predecessor_iri"],
                    SUBJ["source_label"]], text=False)
    if proc.returncode != 0:
        v.refuse("LEGACY_IMPORT_NOT_LIFT", "L1", f"lift exit {proc.returncode}: {proc.stderr.decode(errors='replace')[-240:]}")
        return
    got = imp.read_bytes()
    if proc.stdout != got:
        a, b = proc.stdout.decode().splitlines(), got.decode(errors="replace").splitlines()
        first = next((i for i, (x, y) in enumerate(zip(a, b)) if x != y), min(len(a), len(b)))
        v.refuse("LEGACY_IMPORT_NOT_LIFT", "L1",
                 f"{PATHS['legacy_import']} (sha256 {sha256(got)[:16]}, {len(b)} lines) != lift of the base manifest "
                 f"blob (sha256 {sha256(proc.stdout)[:16]}, {len(a)} lines); first difference at line {first + 1}")
    else:
        v.ok("L1", f"{PATHS['legacy_import']} = {PACK}/{PATHS['lift']} of {PRED_MANIFEST}@{SUBJ['base_commit'][:12]} "
                   f"(sha256 {sha256(got)[:16]})")


_OBS_CACHE: dict[str, subprocess.CompletedProcess] = {}
_OBS_LOCK = threading.Lock()


def observed(v: Verdict, sub: Path, env: Env, xaas_repo: Path) -> None:
    """X1: the committed court-reference import is a fresh observation at the xaas component commit."""
    imp = sub / PATHS["court_references_import"]
    if not imp.is_file():
        v.refuse("COURT_REFERENCES_NOT_OBSERVATION", "X1", f"{PATHS['court_references_import']} is not committed")
        return
    legacy = sub / PATHS["legacy_import"]
    key = sha256(b"\0".join([(sub / OBSERVER).read_bytes(), (sub / "release.ttl").read_bytes(),
                              legacy.read_bytes() if legacy.is_file() else b"", str(xaas_repo).encode()]))
    with _OBS_LOCK:
        proc = _OBS_CACHE.get(key)
    if proc is None:
        proc = env.run([env.python, str(sub / OBSERVER), "--subject", str(sub), "--xaas-repo", str(xaas_repo)],
                       text=False)
        with _OBS_LOCK:
            _OBS_CACHE[key] = proc
    err = proc.stderr.decode(errors="replace").strip()
    if proc.returncode != 0 and "holds no commit" in err:
        v.unknown("XAAS_COMMIT_UNAVAILABLE", "X1", err[-240:])
        return
    if proc.returncode != 0:
        v.refuse("COURT_REFERENCES_NOT_OBSERVATION", "X1", f"observation exit {proc.returncode}: {err[-240:]}")
        return
    got = imp.read_bytes()
    if proc.stdout != got:
        fresh = {line for line in proc.stdout.decode().splitlines() if line.startswith("<")}
        mine = {line for line in got.decode(errors="replace").splitlines() if line.startswith("<")}
        v.refuse("COURT_REFERENCES_NOT_OBSERVATION", "X1",
                 f"{PATHS['court_references_import']} != a fresh observation at the release's "
                 f"{OBS['repository']} commit: {len(mine - fresh)} committed facts not observed "
                 f"{sorted(mine - fresh)[:2]}, {len(fresh - mine)} observed facts not committed {sorted(fresh - mine)[:2]}")
    else:
        facts = sum(1 for line in got.decode().splitlines() if line.startswith("<"))
        v.ok("X1", f"{PATHS['court_references_import']} = fresh observation ({facts} court facts; "
                   f"xaas checkout {xaas_repo.name}, read-only)")


def render(v: Verdict, sub: Path, env: Env, work: Path) -> None:
    """G1: the committed render reproduces; two fresh renders are byte-identical."""
    committed = rendered(sub)
    first = env.run([env.ggen, "sync", "run"], cwd=sub)
    if first.returncode != 0:
        v.refuse("GENERATION_REFUSED", "G1", f"ggen sync run on the committed subject exit {first.returncode}: {fm_codes(first)}")
        return
    now = rendered(sub)
    if now != committed:
        changed = sorted(k for k in set(committed) | set(now) if committed.get(k) != now.get(k))
        v.refuse("GENERATED_DRIFT", "G1", f"ggen sync run rewrote committed outputs: {changed}")
        return
    renders = []
    for tag in ("a", "b"):
        fresh = work / f"fresh-{tag}"
        shutil.copytree(sub, fresh, symlinks=True, ignore=shutil.ignore_patterns(".ggen", ".ggen-v2"))
        shutil.rmtree(fresh / PATHS["generated_dir"], ignore_errors=True)
        (fresh / "ggen.lock").unlink(missing_ok=True)
        proc = env.run([env.ggen, "sync", "run"], cwd=fresh)
        if proc.returncode != 0:
            v.refuse("GENERATION_REFUSED", "G1", f"fresh render {tag} exit {proc.returncode}: {fm_codes(proc)}")
            return
        renders.append(rendered(fresh))
    if renders[0] != renders[1]:
        diff = sorted(k for k in set(renders[0]) | set(renders[1]) if renders[0].get(k) != renders[1].get(k))
        v.refuse("RENDER_NOT_DETERMINISTIC", "G1", f"two fresh renders differ: {diff}")
        return
    if set(renders[0]) != set(committed):
        v.refuse("GENERATED_SET_MISMATCH", "G1", f"render set {sorted(renders[0])} != committed {sorted(committed)}")
        return
    drift = sorted(k for k in committed if renders[0][k] != committed[k])
    if drift:
        v.refuse("GENERATED_DRIFT", "G1", f"fresh render differs from the committed bytes: {drift}")
        return
    v.ok("G1", f"{' '.join(env.ggen_version)}: sync on the committed subject writes nothing; two fresh renders in "
               f"separate directories are byte-identical to each other and to the committed {len(committed)} files")


def gates(v: Verdict, sub: Path, env: Env) -> None:
    """G2: the pack's rdflib runner admits the union graph; gates 070/080 admit the committed projection."""
    runner = sub / PACK / "bin" / "run-gates.py"
    proc = env.run([env.python, str(runner), "release.ttl"], cwd=sub)
    if "ModuleNotFoundError" in proc.stderr:
        v.unknown("RDFLIB_MISSING", "G2", proc.stderr.strip().splitlines()[-1])
        return
    if proc.returncode != 0 or "RELEASE_GATES ALIVE" not in proc.stdout:
        bad = [line.strip() for line in proc.stdout.splitlines() if line.startswith(("GATE_VIOLATION", "    "))]
        v.refuse("GATES_REFUSED", "G2", f"run-gates exit {proc.returncode}: {bad[:8] or proc.stderr[-240:]}")
    else:
        passed = sum(1 for line in proc.stdout.splitlines() if line.startswith("GATE_PASS"))
        v.ok("G2", f"{PACK}/bin/run-gates.py (rdflib): RELEASE_GATES ALIVE, {passed} gates")
    g = input_graph(sub)
    g.parse(sub / PACK / "ontology.ttl", format="turtle")
    g.parse(sub / PATHS["crosswalk_ttl"], format="turtle")
    rows = []
    for gate in ("070_role_crosswalk_total.rq", "080_critical_path_coverage.rq"):
        rows += [f"{gate}: {' | '.join(str(x) for x in r)}"
                 for r in g.query((sub / PACK / "gates" / gate).read_text(encoding="utf-8"))]
    if rows:
        v.refuse("PROJECTION_NOT_TOTAL", "G2", f"gates 070/080 over the committed {PATHS['crosswalk_ttl']} (no rule "
                                              f"applied) return {len(rows)} rows: {rows[:4]}")
    else:
        v.ok("G2", f"gates 070/080 admit the committed {PATHS['crosswalk_ttl']} as data (no rule applied)")


def totality(v: Verdict, sub: Path, pred: dict) -> dict[str, dict]:
    """W1: one typed, provenanced row per predecessor role, carrying the role's own component."""
    doc = tomllib.loads((sub / PATHS["crosswalk_toml"]).read_text(encoding="utf-8"))
    roles = pred["roles"]
    head = doc.get("crosswalk", {})
    want = {"source_release": SUBJ["predecessor_iri"], "source_version": SUBJ["predecessor_version"],
            "target_version": SUBJ["target_version"], "role_count": len(roles)}
    wrong = {k: head.get(k) for k, x in want.items() if head.get(k) != x}
    if wrong:
        v.refuse("CROSSWALK_HEADER", "W1", f"{PATHS['crosswalk_toml']} [crosswalk] {wrong} != {want}")
    rows: dict[str, list[dict]] = {}
    for row in doc.get("role", []):
        rows.setdefault(str(row.get("legacy_role")), []).append(row)
    unmapped = [r for r in roles if r not in rows]
    if unmapped:
        v.refuse("ROLE_UNMAPPED", "W1", f"{len(unmapped)} of the {len(roles)} roles of {PRED_MANIFEST} have no row in "
                                       f"{PATHS['crosswalk_toml']}: {unmapped}")
    dup = sorted(r for r, xs in rows.items() if len(xs) > 1)
    if dup:
        v.refuse("ROLE_DUPLICATED", "W1", f"roles with more than one row: {dup}")
    foreign = sorted(set(rows) - set(roles))
    if foreign:
        v.refuse("ROLE_FOREIGN", "W1", f"rows for roles {PRED_MANIFEST} does not require: {foreign}")
    man = tomllib.loads((sub / PATHS["manifest_render"]).read_text(encoding="utf-8"))
    required = {str(c.get("id")) for c in man.get("components", []) if c.get("required") is True}
    boundaries = SUBJ["boundaries"]
    single: dict[str, dict] = {}
    for role in roles:
        if len(rows.get(role, [])) != 1:
            continue
        row, comp = rows[role][0], pred["by_role"][role]
        single[role] = row
        topo = {"legacy_component": comp.get("id"), "legacy_repository": comp.get("repository"),
                "legacy_sha": comp.get("sha"), "legacy_standing": comp.get("standing")}
        off = {k: (row.get(k), x) for k, x in topo.items() if row.get(k) != x}
        if off:
            v.refuse("LEGACY_TOPOLOGY_ALTERED", "W1", f"{role}: row (rendered, manifest) differs: {off}")
        if row.get("boundary") not in boundaries:
            v.refuse("BOUNDARY_UNTYPED", "W1", f"{role}: boundary {row.get('boundary')!r} not one of {boundaries}")
        derived, decided = bool(row.get("derived_by")), bool(row.get("decided_by"))
        if not str(row.get("reason", "")).strip() or derived == decided:
            v.refuse("PROVENANCE_MISSING", "W1", f"{role}: reason {bool(row.get('reason'))}, derived_by "
                                                 f"{row.get('derived_by')!r}, decided_by {row.get('decided_by')!r} "
                                                 f"(need a reason and exactly one of them)")
        if row.get("boundary") == "REQUIRED" and str(row.get("supplied_by")) not in required:
            v.refuse("REQUIRED_NOT_SUPPLIED", "W1", f"{role}: REQUIRED but supplied_by {row.get('supplied_by')!r} is not "
                                                   f"a required component of {PATHS['manifest_render']} {sorted(required)}")
        v.ok("W1", f"{role} <- {comp.get('id')}@{str(comp.get('sha'))[:12]} ({comp.get('standing')}): "
                   f"{row.get('boundary')} by {row.get('derived_by') or row.get('decided_by')}")
    counts: dict[str, int] = {}
    for row in single.values():
        counts[str(row.get("boundary"))] = counts.get(str(row.get("boundary")), 0) + 1
    if not (wrong or unmapped or dup or foreign):
        v.ok("W1", f"{len(single)}/{len(roles)} roles of {PRED_MANIFEST} disposed exactly once in "
                   f"{PATHS['crosswalk_toml']}: {dict(sorted(counts.items()))}")
    return single


def agree(v: Verdict, sub: Path, rows: dict[str, dict]) -> None:
    """W2: out/crosswalk.ttl and out/role-derivations.toml state the same dispositions as the TOML rows."""
    from rdflib import RDF, Graph, Namespace  # noqa: PLC0415

    er = Namespace(ER)
    g = Graph().parse(sub / PATHS["crosswalk_ttl"], format="turtle")
    ttl: dict[str, list[tuple]] = {}
    for d in g.subjects(RDF.type, er.RoleDisposition):
        comp = str(g.value(d, er.legacyComponent) or "").rpartition("/component/")[2]
        ttl.setdefault(str(g.value(d, er.legacyRole)), []).append((
            local(g.value(d, er.boundary) or "").removeprefix("ROLE_"), str(g.value(d, er.derivedBy) or ""),
            str(g.value(d, er.decidedBy) or ""), str(g.value(d, er.reason) or ""), comp,
            str(g.value(d, er.legacySha) or "")))
    toml_rows = {r: [(x.get("boundary"), x.get("derived_by"), x.get("decided_by"), x.get("reason"),
                      x.get("legacy_component"), x.get("legacy_sha"))] for r, x in rows.items()}
    ttl_off = sorted(r for r in set(ttl) | set(toml_rows) if ttl.get(r) != toml_rows.get(r))
    der = tomllib.loads((sub / PATHS["derivations_toml"]).read_text(encoding="utf-8"))
    dv = {x.get("legacy_role"): (x.get("boundary"), x.get("rule"), "") for x in der.get("derived", [])}
    dv.update({x.get("legacy_role"): (x.get("boundary"), "", x.get("decided_by")) for x in der.get("decided", [])})
    count = der.get("derivations", {})
    want = {r: (x.get("boundary"), x.get("derived_by"), x.get("decided_by")) for r, x in rows.items()}
    der_off = sorted(r for r in set(dv) | set(want) if dv.get(r) != want.get(r))
    n = len(der.get("derived", [])) + len(der.get("decided", []))
    if ttl_off or der_off or n != len(rows) or count.get("derived_count", 0) + count.get("decided_count", 0) != n:
        v.refuse("PROJECTIONS_DISAGREE", "W2",
                 f"{PATHS['crosswalk_ttl']} disagrees on {ttl_off[:6]}; {PATHS['derivations_toml']} disagrees on "
                 f"{der_off[:6]} ({n} rows, counts {count})")
    else:
        v.ok("W2", f"{PATHS['crosswalk_ttl']} ({len(ttl)} er:RoleDisposition) and {PATHS['derivations_toml']} "
                   f"({count.get('derived_count')} derived, {count.get('decided_count')} decided) state the same "
                   f"{len(rows)} dispositions")


def decided_in_graph(sub: Path) -> dict[str, list[tuple[str, str]]]:
    from rdflib import Namespace  # noqa: PLC0415

    er = Namespace(ER)
    g = input_graph(sub)
    out: dict[str, list[tuple[str, str]]] = {}
    for d, authority in g.subject_objects(er.decidedBy):
        out.setdefault(str(g.value(d, er.legacyRole)), []).append(
            (str(authority), local(g.value(d, er.boundary) or "").removeprefix("ROLE_")))
    return out


def rule(v: Verdict, sub: Path, pred: dict, rows: dict[str, dict]) -> None:
    """W3: the court's own executor of the disposition rule gives every rendered undecided row."""
    from rdflib import Graph, Namespace  # noqa: PLC0415

    er, sj, dct = Namespace(ER), Namespace(SJ), Namespace(DCT)
    data = (sub / PATHS["classification_import"]).read_bytes()
    rel = Graph().parse(sub / "release.ttl", format="turtle")
    named = {m for s in rel.objects(None, er.classificationSource) for m in DIGEST.findall(str(s))}
    if named != {sha256(data)}:
        v.refuse("CLASSIFICATION_NOT_PINNED", "W3", f"{PATHS['classification_import']} sha256 {sha256(data)} is not the "
                                                    f"digest release.ttl er:classificationSource names {sorted(named)}")
    cg = Graph().parse(data=data.decode("utf-8"), format="turtle")
    classes: dict[str, list[str]] = {}
    for fc in set(cg.subjects(sj.fleetClass, None)):
        for ident in cg.objects(fc, dct.identifier):
            classes.setdefault(str(ident), []).extend(sorted(local(c) for c in cg.objects(fc, sj.fleetClass)))
    refs = Graph().parse(sub / PATHS["court_references_import"], format="turtle")
    executed = {str(o) for o in refs.objects(None, er.courtReferencesComponent)}
    decided = decided_in_graph(sub)
    derived = mismatched = 0
    for role in pred["roles"]:
        if role in decided:
            continue
        comp = pred["by_role"][role]
        repo = str(comp.get("repository"))
        name = repo.rsplit("/", 1)[-1]
        cls = classes.get(name)
        if cls and len(cls) != 1:
            v.refuse("CLASSIFICATION_AMBIGUOUS", "W3", f"{role}: {name} has fleet classes {cls}")
            continue
        if cls:
            want = (RULE["classes"].get(cls[0], "UNCLASSIFIED"), RULE["classified"])
        elif repo in executed:
            v.refuse("ROLE_UNDECIDABLE", "W3", f"{role}: {repo} is unclassified and a GC23 court executes it; the rule "
                                              f"decides nothing and no admitted er:decidedBy fact disposes it")
            continue
        else:
            want = (RULE["unexecuted_boundary"], RULE["unclassified_unexecuted"])
        row = rows.get(role)
        got = (row.get("boundary"), row.get("derived_by")) if row else None
        if want[0] not in SUBJ["boundaries"] or got != want:
            mismatched += 1
            v.refuse("DISPOSITION_NOT_DERIVED", "W3", f"{role} ({repo}): rule gives {want}, rendered {got}")
        else:
            derived += 1
    if not mismatched:
        v.ok("W3", f"court re-derivation of the disposition rule agrees on {derived} undecided roles "
                   f"({len(classes)} classified repositories, {len(executed)} court-executed repositories)")


def decisions(v: Verdict, sub: Path, rows: dict[str, dict]) -> None:
    """D1: every explicit decision (input graph or render) is admitted by the pins."""
    seen = {(role, a, b) for role, xs in decided_in_graph(sub).items() for a, b in xs}
    seen |= {(r, str(x.get("decided_by")), str(x.get("boundary"))) for r, x in rows.items() if x.get("decided_by")}
    unadmitted = sorted(seen - set(ADMITTED))
    absent = sorted(set(ADMITTED) - seen)
    if unadmitted:
        v.refuse("DECISION_UNADMITTED", "D1", f"explicit decisions no crosswalk.toml [decisions] entry admits: {unadmitted}")
    if absent:
        v.refuse("DECISION_NOT_RENDERED", "D1", f"admitted decisions absent from the graph/render: {absent}")
    if not unadmitted and not absent:
        v.ok("D1", f"{len(seen)} explicit decisions, all admitted ({len(ADMITTED)} admitted in crosswalk.toml)")


# ------------------------------------------------------------ anti-vacuity
@dataclass(frozen=True)
class Mutant:
    """One anti-vacuity mutant: `mutate` edits the synthetic repository in place (and may return a
    replacement base commit); it is committed unless `commit` is False. The judge must refuse with
    every code in `expect`, and a refusal line must carry `mention` when set."""

    id: str
    desc: str
    expect: tuple[str, ...]
    mutate: Callable[[Path], str | None]
    mention: str | None = None
    commit: bool = True


def _edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise RuntimeError(f"mutation anchor not unique in {path}: {old[:60]!r} ({text.count(old)})")
    path.write_text(text.replace(old, new), encoding="utf-8")


def _sub_re(path: Path, pattern: str, new: str) -> None:
    text, n = re.subn(pattern, new, path.read_text(encoding="utf-8"), count=1, flags=re.S)
    if n != 1:
        raise RuntimeError(f"mutation pattern not found in {path}: {pattern[:60]!r}")
    path.write_text(text, encoding="utf-8")


def mutants(env: Env, xaas_repo: Path) -> list[Mutant]:
    def sub(r: Path) -> Path:
        return r / SDIR

    def regen(r: Path, relock: bool = False) -> None:
        # ggen.lock pins the pack and every extra_ontologies input (FM-PACK-008 on drift): a
        # mutant that changes an import re-locks on purpose, as the subject README says.
        s = sub(r)
        shutil.rmtree(s / PATHS["generated_dir"], ignore_errors=True)
        if relock:
            (s / "ggen.lock").unlink()
        proc = env.run([env.ggen, "sync", "run"], cwd=s)
        if proc.returncode != 0:
            raise RuntimeError(f"mutant regeneration refused: {fm_codes(proc)}")
        shutil.rmtree(s / ".ggen", ignore_errors=True)
        shutil.rmtree(s / ".ggen-v2", ignore_errors=True)

    def relock(r: Path) -> None:
        # The input changed and the lock is dropped so the sync reaches the gates; the committed
        # render is the old one (a regeneration would be refused).
        (sub(r) / "ggen.lock").unlink()

    def reclass(r: Path, name: str, cls: str) -> None:
        _sub_re(sub(r) / PATHS["classification_import"],
                r'(dcterms:identifier "' + re.escape(name) + r'" ;.*?sj:fleetClass )sj:\w+', r"\1" + cls)

    def row_block(role: str) -> str:
        return r'\n\[\[role\]\]\nlegacy_role = "' + re.escape(role) + r'"\n.*?(?=\n\[\[role\]\]|\Z)'

    def decision(role: str) -> str:
        return (f"\nr23:decision-{role} a er:RoleDisposition ;\n    er:legacyRole \"{role}\" ;\n"
                f"    er:sourceRelease <{SUBJ['predecessor_iri']}> ;\n    er:targetRelease r23:release ;\n"
                f"    er:boundary er:ROLE_REFUSED ;\n    er:decidedBy \"operator\" ;\n"
                f"    er:reason \"mutant: an explicit decision no crosswalk.toml entry admits\" .\n")

    def xaas_sha(r: Path) -> str:
        m = re.search(r"/xaas/blob/([0-9a-f]{40})/", (sub(r) / PATHS["court_references_import"]).read_text(encoding="utf-8"))
        if not m:
            raise RuntimeError("no xaas commit in the court-reference import")
        return m[1]

    def revert(r: Path) -> None:
        s = sub(r)
        _edit(s / "release.ttl", CROSSWALK_LINE, "")
        _edit(s / "ggen.toml", f'"{PATHS["legacy_import"]}", "{PATHS["court_references_import"]}", ', "")
        (s / PATHS["legacy_import"]).unlink()
        (s / PATHS["court_references_import"]).unlink()
        regen(r, relock=True)

    def cut_row(r: Path) -> None:
        f = sub(r) / PATHS["crosswalk_toml"]
        _sub_re(f, row_block("formal-proof"), "")
        _edit(f, "role_count = 16", "role_count = 15")

    def erase_role(r: Path) -> None:
        f = sub(r) / PATHS["legacy_import"]
        comp = f"<{SUBJ['predecessor_iri']}/component/mfact>"
        _edit(f, '    er:legacyRequiredRole "formal-proof" ;\n', "")
        _edit(f, f"    er:legacyComponent {comp} ;\n", "")
        _sub_re(f, r"\n" + re.escape(comp) + r" a er:LegacyComponent ;.*?\.\n", "")
        regen(r, relock=True)

    def unclassify(r: Path) -> None:
        reclass(r, "open-ontologies", "sj:Deferred")
        relock(r)

    def court_ref(r: Path) -> None:
        f = sub(r) / PATHS["court_references_import"]
        with f.open("a", encoding="utf-8") as out:
            out.write(f"<https://github.com/{OBS['repository']}/blob/{xaas_sha(r)}/docs/sjira/v26.9.23/courts/GC23-9.sh> "
                      f'er:courtReferencesComponent "seanchatmangpt/mfact" .\n')
        relock(r)

    def drop_gi(r: Path) -> None:
        t = sub(r) / "release.ttl"
        _edit(t, 'er:requiredRole "execution-realization", "semantic-manufacture"', 'er:requiredRole "execution-realization"')
        _edit(t, "er:hasComponent r23:xaas, r23:ggen_igniter", "er:hasComponent r23:xaas")
        _edit(t, "er:hasRoleMapping r23:map-execution-realization, r23:map-semantic-manufacture",
              "er:hasRoleMapping r23:map-execution-realization")
        _edit(t, "    er:refCheckMode er:GITHUB_LIVE ;\n    er:dependsOn r23:ggen_igniter .", "    er:refCheckMode er:GITHUB_LIVE .")
        _sub_re(t, r"r23:ggen_igniter a er:Component ;.*?er:GITHUB_LIVE \.\n", "")
        _sub_re(t, r"r23:map-semantic-manufacture a er:RoleMapping ;.*?\"CONSTRUCT_ONLY_NO_DO\" \.\n", "")

    def open_critical(r: Path) -> None:
        reclass(r, "open-ontologies", "sj:CriticalPath")
        relock(r)

    def hand_edit(r: Path) -> None:
        _sub_re(sub(r) / PATHS["crosswalk_toml"], r'(legacy_role = "formal-proof"\n(?:[^\[]*?\n)?boundary = )"SUCCESSOR"',
                r'\1"REQUIRED"')

    def unadmitted(r: Path) -> None:
        with (sub(r) / "release.ttl").open("a", encoding="utf-8") as f:
            f.write(decision("formal-proof"))
        regen(r)

    def overriding(r: Path) -> None:
        with (sub(r) / "release.ttl").open("a", encoding="utf-8") as f:
            f.write(decision("manufacture"))

    def stale_obs(r: Path) -> None:
        f = sub(r) / PATHS["court_references_import"]
        old = xaas_sha(r)
        f.write_text(f.read_text(encoding="utf-8").replace(old, "f" * 40), encoding="utf-8")
        regen(r, relock=True)

    def repin_xaas(r: Path) -> None:
        old = xaas_sha(r)
        parent = env.out(xaas_repo, "rev-parse", f"{old}^")
        if not parent or not SHA40.match(parent):
            raise RuntimeError(f"{xaas_repo} holds no parent of {old}")
        _edit(sub(r) / "release.ttl", f'er:commitSha "{old}"', f'er:commitSha "{parent}"')
        regen(r)

    def rename_role(r: Path) -> None:
        _edit(r / PRED_MANIFEST, '  "capstone",\n', '  "capstone-successor",\n')

    def dirty_render(r: Path) -> None:
        with (sub(r) / PATHS["crosswalk_toml"]).open("a", encoding="utf-8") as f:
            f.write("# uncommitted\n")

    def court_pins(r: Path) -> None:
        with (sub(r) / "courts/ce23_2/crosswalk.toml").open("a", encoding="utf-8") as f:
            f.write("# committed pins that are not the running court's\n")

    def unwire_legacy(r: Path) -> None:
        _edit(sub(r) / "ggen.toml", f'"{PATHS["legacy_import"]}", ', "")
        regen(r, relock=True)

    def relax_gate(r: Path) -> None:
        (sub(r) / PACK / "gates/070_role_crosswalk_total.rq").write_text(
            "SELECT ?subject ?reason WHERE { FILTER(false) }\n", encoding="utf-8")

    def orphan_base(r: Path) -> str:
        empty = env.run([env.git, "-C", str(r), "hash-object", "-t", "tree", "--stdin", "-w"], stdin="")
        proc = env.run([env.git, "-C", str(r), "-c", "user.name=ce23-2-court", "-c", "user.email=ce23-2-court@localhost",
                        "commit-tree", empty.stdout.strip(), "-m", "orphan base"])
        if proc.returncode != 0:
            raise RuntimeError(f"orphan commit: {proc.stderr[-200:]}")
        return proc.stdout.strip()

    return [
        Mutant("MV", "CE23-2 reverted: crosswalkFrom and both imports removed, render regenerated (the two-repo "
                     "release with the old 16-role topology silently erased; every pack gate admits it)",
               ("CROSSWALK_NOT_WIRED", "ROLE_UNMAPPED"), revert, "16 roles"),
        Mutant("M1", "the formal-proof row cut from the committed legacy-role-crosswalk.toml (role_count 15)",
               ("GENERATION_REFUSED", "ROLE_UNMAPPED", "CROSSWALK_HEADER"), cut_row, "FM-WRITE-005"),
        Mutant("M1b", "formal-proof erased consistently from the lifted import (role and mfact component), render "
                      "regenerated: 15 rows and every pack gate admits it",
               ("LEGACY_IMPORT_NOT_LIFT", "ROLE_UNMAPPED"), erase_role, "formal-proof"),
        Mutant("M2", "open-ontologies classified outside the five classes (sj:Deferred), relocked",
               ("GENERATION_REFUSED", "CLASSIFICATION_NOT_PINNED"), unclassify, "070_role_crosswalk_total"),
        Mutant("M3", "a GC23 court observed executing seanchatmangpt/mfact (court-reference import edited), relocked",
               ("GENERATION_REFUSED", "COURT_REFERENCES_NOT_OBSERVATION", "ROLE_UNDECIDABLE"), court_ref,
               "070_role_crosswalk_total"),
        Mutant("M4", "ggen_igniter dropped consistently from release.ttl", ("GENERATION_REFUSED",), drop_gi,
               "080_critical_path_coverage"),
        Mutant("M5", "open-ontologies reclassified CriticalPath in the classification import, relocked",
               ("GENERATION_REFUSED", "GATES_REFUSED", "CLASSIFICATION_NOT_PINNED"), open_critical,
               "required-role-not-supplied"),
        Mutant("M6", "hand edit of the committed render: formal-proof SUCCESSOR -> REQUIRED",
               ("GENERATION_REFUSED", "PROJECTIONS_DISAGREE", "REQUIRED_NOT_SUPPLIED", "DISPOSITION_NOT_DERIVED"),
               hand_edit, "FM-WRITE-005"),
        Mutant("M7", "an explicit decision no pin admits (formal-proof REFUSED by 'operator'), render regenerated: "
                     "every pack gate admits it", ("DECISION_UNADMITTED",), unadmitted, "formal-proof"),
        Mutant("M8", "an explicit decision overriding the fleet classification (manufacture / ggen)",
               ("GENERATION_REFUSED", "DECISION_UNADMITTED"), overriding, "070_role_crosswalk_total"),
        Mutant("M9", "court-reference import naming another xaas commit, render regenerated",
               ("COURT_REFERENCES_NOT_OBSERVATION",), stale_obs),
        Mutant("M10", "xaas component re-pinned to its parent commit, render regenerated, courts not re-observed",
               ("COURT_REFERENCES_NOT_OBSERVATION",), repin_xaas),
        Mutant("M11", "a role renamed in the committed release/v26.9.1/manifest.toml", ("PREDECESSOR_CHANGED",),
               rename_role),
        Mutant("M12", "uncommitted edit of out/legacy-role-crosswalk.toml", ("SUBJECT_DIRTY",), dirty_render,
               commit=False),
        Mutant("M13", "committed court pins differ from the pins of the court judging", ("COURT_NOT_AT_HEAD",),
               court_pins, "crosswalk.toml"),
        Mutant("M14", "the legacy import unwired from ggen.toml (file and crosswalkFrom kept), render regenerated: "
                      "every pack gate admits the empty crosswalk", ("CROSSWALK_NOT_WIRED", "ROLE_UNMAPPED"),
               unwire_legacy),
        Mutant("M15", "vendored gate 070 relaxed to admit everything", ("VENDOR_TREE_MISMATCH", "GENERATION_REFUSED"),
               relax_gate, "FM-PACK-008"),
        Mutant("MB", "the judged head does not descend from the base (orphan base commit)", ("BASE_NOT_ANCESTOR",),
               orphan_base),
    ]


def anti_vacuity(root: Path, env: Env, work: Path, xaas_repo: Path, root_base: str | None = None) -> Verdict:
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
        env.archive(root, str(head), [PRED_DIR, SDIR], synth)
        env.commit_all(synth, f"subject: slice of {head}")
    except (RuntimeError, OSError) as exc:
        v.unknown("AV_HARNESS", "AV", f"synthetic repository: {exc}")
        return v

    def one(m: Mutant | None) -> tuple[Mutant | None, Verdict | str]:
        mid = m.id if m else "M0"
        repo = work / f"av-{mid}"
        shutil.copytree(synth, repo, symlinks=True)
        judged_base = base
        try:
            if m is not None:
                judged_base = m.mutate(repo) or base
                if m.commit:
                    env.commit_all(repo, f"mutant {m.id}: {m.desc}")
        except (RuntimeError, OSError) as exc:
            return m, f"AV_CONSTRUCT: {exc}"
        try:
            return m, judge(repo, judged_base, env, work / f"av-{mid}-work", xaas_repo)
        except Exception as exc:  # noqa: BLE001 (a court fault witnesses nothing: typed UNKNOWN)
            return m, f"COURT_FAULT: {type(exc).__name__}: {exc}"

    with concurrent.futures.ThreadPoolExecutor(max_workers=min(6, os.cpu_count() or 2)) as pool:
        results = list(pool.map(one, [None, *mutants(env, xaas_repo)]))
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
    work = args.keep or Path(tempfile.mkdtemp(prefix="ce23-2-court."))
    if args.keep:
        if args.keep.exists() and any(args.keep.iterdir()):
            print(f"REFUSED[SCRATCH_NOT_EMPTY] CE23-2: {args.keep}")
            return 2
        args.keep.mkdir(parents=True, exist_ok=True)
    try:
        env = Env(work / "home")
    except Environment as exc:
        code, _, detail = str(exc).partition(":")
        print(f"UNKNOWN[{code}] CE23-2: {detail}")
        print("CE23-2 UNKNOWN")
        return 75
    xaas_repo = repo_for(OBS["component_id"])
    try:
        head = env.out(ROOT, "rev-parse", "HEAD")
        print(f"CE23-2 court: subject {head} at {ROOT}")
        try:
            subject = judge(ROOT, SUBJ["base_commit"], env, work / "subject", xaas_repo)
        except Exception as exc:  # noqa: BLE001 (a court fault witnesses nothing: typed UNKNOWN)
            subject = Verdict()
            subject.unknown("COURT_FAULT", "CE23-2", f"{type(exc).__name__}: {exc}")
        for line in subject.lines:
            print(line)
        if args.no_av:
            corpus = Verdict()
            corpus.unknown("AV_SKIPPED", "AV", "--no-av: the anti-vacuity corpus did not run")
        else:
            corpus = anti_vacuity(ROOT, env, work / "av", xaas_repo)
        for line in corpus.lines:
            print(line)
    finally:
        if not args.keep:
            shutil.rmtree(work, ignore_errors=True)
    refused = subject.refused + corpus.refused
    unknown = subject.unknowns + corpus.unknowns
    if refused:
        print(f"CE23-2 REFUSED {sorted(set(refused))}")
        return 1
    if unknown:
        print(f"CE23-2 UNKNOWN {sorted(set(unknown))}")
        return 75
    print("CE23-2 ALIVE")
    return 0


if __name__ == "__main__":
    sys.exit(main())
