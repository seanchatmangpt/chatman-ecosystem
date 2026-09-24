#!/usr/bin/env python3
"""CE23-0 court: root identity of the chatman-ecosystem working subject (release/v26.9.23/sjira/goal.ttl ce:CE23-0).

Proposition (chatman-ce23.md CE23-0): the chatman-ecosystem working subject is bound to a GitHub
remote + exact SHA; its lineage is proven rather than inferred. Falsifier (goal.ttl
ce:CE23-0-falsifier): the court exits 0 while the working subject has no GitHub remote or no exact
SHA, or while its lineage is asserted without proof.

The working subject is the canonical checkout's exact committed head (one checkout per repository;
the single-repository migration of 20260924T0600Z moved the pre-migration local-only lineage and the
retired shadow clone's refs into this checkout's archive namespaces). Every fact below is recomputed
from git objects and refs of the checkout plus one live `git ls-remote` of its GitHub remote; nothing
is read from a receipt except in R1, which judges the receipt. Clauses:

  C1 court     the judging court (CE23-0.sh, court.py, identity.toml as loaded, and the CE23-9 member
               module that pins the receipt validator) is byte-identical to HEAD
  W1 exact     no tracked file differs from HEAD (staged or not): the working subject is exactly HEAD
  I1 remote    remote.origin.url names github.com/<repository> (https or ssh form, optional .git) and
               no url.<base>.insteadOf rule rewrites it (the observation below is GitHub's)
  I2 github    a live `git ls-remote <origin> refs/heads/main refs/heads/<branch>` observes GitHub
               main M; M is a local commit and the release base is M or an ancestor of M
  I3 lineage   the base is the head or its ancestor, and the head's root set is exactly {github_root}
               (an --allow-unrelated-histories merge of another lineage is refused)
  I4 line      the head against GitHub <branch>: equal (published), the head fast-forwards it
               (publication pending: a plain push), or GitHub moved on past the head (published);
               diverged or unrelated is refused
  K1 fact      the er:Component + er:RefObservation fact of the I2 observation is admitted by the
               vendored chatman-ecosystem-release-pack gates 020/050/060 (its own bin/run-gates.py);
               a committed fact (receipts/v26.9.23/CE23-0.identity.ttl) is admitted too and its
               observed SHA lies on the published line between the base and the live M
  O1 order     the gate's sj:courtCommand is this court and the compiled CE23 orders checkpoint at
               least one sj:WorkOrder on ce:CE23-0 (the receipt links them); goal.ttl and every
               compiled orders.ttl are read from HEAD's tree, never the working tree (an untracked
               orders file links nothing)
  L1 local     the pre-migration local-only lineage: every pinned head at its exact SHA in every
               archive namespace (and nothing else there), the pre-migration checkout HEAD ref, and
               the pinned shape (commit count, root set). Absent refs are refused while the commits
               are still in the object store; a checkout that never held them (a fresh GitHub clone)
               is UNKNOWN[LINEAGE_EVIDENCE_ABSENT]
  L2 verdict   the relation (equal | ancestor | descendant | diverged | unrelated, by merge-base) of
               every local head to the base and to the head is the pinned relation; the blob overlap
               of the local main tree and the base tree is reported
  L3 publish   whether a remote-tracking ref reaches the local root equals the pin (publishing the
               local lineage is an operator decision that moves the pin)
  S1 shadow    the retired shadow clone's refs, preserved under the archive prefix at their pinned
               SHAs; its own preservation of the local lineage agrees with L1; the shadow-era CE23-0
               commit and the shadow's published int are the head or its ancestors; the relation of
               the shadow's unpublished int to the head is reported
  P1 v26.9.1   release/v26.9.1 at the head is the base tree and the pinned tree
  R1 receipt   receipts/v26.9.23/CE23-0.json at HEAD is judged unless its blob is one of the pinned
               pre-court receipts (identity.toml [receipt_history] superseded_blobs); a receipt without
               the court's marker (court.emitted_by = the wrapper) that is not pinned is refused
               (RECEIPT_NOT_COURT_EMITTED), so an edited marker or a deleted court block never switches
               the judgment off. A court-emitted receipt: its subject is the head or an ancestor; the
               pinned generated validator (dfcm_fleet_v1) admits it; court.loaded_sha256 is exactly the
               sha256 of the court files at its subject (RECEIPT_COURT_MISMATCH); its standing, exit and
               counts derive from its own recorded clause lines, and an ALIVE one records the pinned
               lineage relation and an untouched predecessor (RECEIPT_STANDING_UNDERIVED); every claim
               it records (lineage, shadow clone, predecessor, the receipt it supersedes, GitHub
               observation, base, repository) equals this run's recomputation at its subject
  AV corpus    a synthetic GitHub (bare repository), a synthetic local lineage and a synthetic
               checkout built with git in scratch, judged by the same clauses: controls M0 (head one
               commit ahead of the published line, carrying the pinned pre-court receipt), M0p
               (published) and M0s (the court committed, then sealed with this court's own receipt
               and identity fact) must be ALIVE; 28 mutants must be refused with their expected
               codes, and the two evidence edges (M6 a clone without the archive, M15 GitHub
               unreachable) must be UNKNOWN and never refused (see mutants())

Seal: --receipt-out FILE writes the fleet R receipt of this run (validated by the pinned validator
before it is written) and --identity-out FILE the identity fact; both are court output, committed
as they are written and never edited.

Every subprocess runs real tools (git, python3, the vendored pack runner) on real repositories; there
is no test double and no LLM on any path. The synthetic corpus runs git with a fresh HOME, no system
config and no terminal prompt. The only network read is the ls-remote of I2/I4.

    sh release/v26.9.23/courts/CE23-0.sh [--no-av] [--receipt-out FILE] [--identity-out FILE]

Exit: 0 ALIVE; 1 REFUSED (typed REFUSED[<code>] lines name the counterexample); 75 UNKNOWN (typed
UNKNOWN[<code>] lines: a tool, the GitHub remote, the lineage evidence or the pinned receipt
validator is absent; nothing refused).
"""
from __future__ import annotations

import argparse
import concurrent.futures
import copy
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
_PIN_BYTES = (HERE / "identity.toml").read_bytes()
PINS = tomllib.loads(_PIN_BYTES.decode("utf-8"))
SUBJ = PINS["subject"]
SDIR = SUBJ["subject_dir"]
WRAPPER = f"{SDIR}/courts/CE23-0.sh"
COURT_CMD = f"sh {WRAPPER}"
_WRAPPER_PATH = HERE.parent / "CE23-0.sh"
# C1: the court as loaded (bytes read once, at import), keyed by committed path.
LOADED: dict[str, bytes | None] = {
    WRAPPER: _WRAPPER_PATH.read_bytes() if _WRAPPER_PATH.is_file() else None,
    f"{SDIR}/courts/ce23_0/court.py": Path(__file__).resolve().read_bytes(),
    f"{SDIR}/courts/ce23_0/identity.toml": _PIN_BYTES,
}
ER = "http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#"
SJ = "https://ggen-igniter.dev/ontology/semantic-jira#"
DCT = "http://purl.org/dc/terms/"
EXIT = {"ALIVE": 0, "REFUSED": 1, "UNKNOWN": 75}
ON_LINE = ("equal", "ancestor")
GITHUB_URL = re.compile(r"(?:https://(?:[^@/]+@)?github\.com/|ssh://git@github\.com/|git@github\.com:)"
                        r"([A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+?)(?:\.git)?/?")


# ----------------------------------------------------------------------------------------------------
# verdict bookkeeping


class Judge:
    def __init__(self, quiet: bool = False):
        self.quiet = quiet
        self.refused: list[str] = []
        self.unknown: list[str] = []
        self.lines: list[dict] = []

    def _emit(self, kind: str, clause: str, code: str, text: str) -> None:
        self.lines.append({"verdict": kind, "clause": clause, "code": code, "text": text})
        if not self.quiet:
            print(f"{kind}{f'[{code}]' if code else ''} {clause} {text}", flush=True)

    def ok(self, clause: str, text: str) -> None:
        self._emit("OK", clause, "", text)

    def refuse(self, code: str, clause: str, text: str) -> None:
        self.refused.append(code)
        self._emit("REFUSED", clause, code, text)

    def unk(self, code: str, clause: str, text: str) -> None:
        self.unknown.append(code)
        self._emit("UNKNOWN", clause, code, text)

    def verdict(self) -> str:
        return "REFUSED" if self.refused else "UNKNOWN" if self.unknown else "ALIVE"


# ----------------------------------------------------------------------------------------------------
# git


class Git:
    """git over one checkout; every answer comes from a real git process."""

    def __init__(self, root: Path, env: dict):
        self.root, self.env = root, env

    def run(self, *args: str, timeout: int = 300) -> subprocess.CompletedProcess:
        try:
            return subprocess.run(["git", "-C", str(self.root), *args], capture_output=True, text=True,
                                  env=self.env, timeout=timeout)
        except subprocess.TimeoutExpired:
            return subprocess.CompletedProcess(args, 124, "", f"timeout after {timeout}s")

    def out(self, *args: str) -> str:
        p = self.run(*args)
        return p.stdout.strip() if p.returncode == 0 else ""

    def ref(self, name: str) -> str:
        return self.out("rev-parse", "--verify", "--quiet", f"{name}^{{commit}}")

    def has_commit(self, sha: str) -> bool:
        return bool(sha) and self.run("cat-file", "-e", f"{sha}^{{commit}}").returncode == 0

    def refs(self, prefix: str) -> dict[str, str]:
        rows = self.out("for-each-ref", "--format=%(refname) %(objectname)", prefix).splitlines()
        return dict(r.split(" ", 1) for r in rows if " " in r)

    def is_ancestor(self, a: str, b: str) -> bool | None:
        rc = self.run("merge-base", "--is-ancestor", a, b).returncode
        return {0: True, 1: False}.get(rc)

    def relation(self, a: str, b: str) -> str | None:
        """Relation of commit a to commit b: equal | ancestor (a is in b's history) | descendant |
        diverged (a merge base exists, neither contains the other) | unrelated (no merge base); None
        when git cannot answer (an absent object)."""
        if not (self.has_commit(a) and self.has_commit(b)):
            return None
        if self.out("rev-parse", a) == self.out("rev-parse", b):
            return "equal"
        up, down = self.is_ancestor(a, b), self.is_ancestor(b, a)
        if up is None or down is None:
            return None
        if up:
            return "ancestor"
        if down:
            return "descendant"
        return {0: "diverged", 1: "unrelated"}.get(self.run("merge-base", a, b).returncode)

    def roots(self, *revs: str) -> list[str]:
        return sorted(self.out("rev-list", "--max-parents=0", *revs).split())

    def blob(self, rev_path: str) -> bytes | None:
        p = subprocess.run(["git", "-C", str(self.root), "cat-file", "blob", rev_path], capture_output=True, env=self.env)
        return p.stdout if p.returncode == 0 else None


def github_slug(url: str) -> str | None:
    m = GITHUB_URL.fullmatch(url.strip())
    return m.group(1) if m else None


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def caller_env() -> dict:
    env = dict(os.environ)
    env.update({"GIT_TERMINAL_PROMPT": "0", "PYTHONDONTWRITEBYTECODE": "1"})
    return env


# ----------------------------------------------------------------------------------------------------
# recomputable blocks (functions of the refs, the objects and one subject SHA; R1 re-derives them)


def tree_blobs(g: Git, rev: str) -> dict[str, str]:
    out = {}
    for line in g.out("ls-tree", "-r", "--full-tree", rev).splitlines():
        meta, _, path = line.partition("\t")
        parts = meta.split()
        if len(parts) == 3 and parts[1] == "blob":
            out[path] = parts[2]
    return out


def lineage_block(g: Git, pins: dict, subject: str) -> dict:
    ll, base = pins["local_lineage"], pins["subject"]["base_commit"]
    heads = ll["heads"]
    main = heads.get("main") or sorted(heads.values())[0]
    local, published = tree_blobs(g, main), tree_blobs(g, base)
    return {
        "proof": "recomputed by git merge-base / rev-list over the preserved refs of this checkout",
        "root": g.roots(*heads.values()),
        "commits": int(g.out("rev-list", "--count", *heads.values()) or -1),
        "namespaces": {ns: {ref[len(ns):]: sha for ref, sha in sorted(g.refs(ns).items())} for ns in ll["namespaces"]},
        "checkout_head": {"ref": ll["checkout_head_ref"], "sha": g.ref(ll["checkout_head_ref"])},
        "base_sha": base,
        "relation_to_base": {n: g.relation(s, base) for n, s in sorted(heads.items())},
        "relation_to_subject": {n: g.relation(s, subject) for n, s in sorted(heads.items())},
        "blob_overlap_main_vs_base": {
            "local_main_files": len(local), "base_files": len(published),
            "shared_blob_ids": len(set(local.values()) & set(published.values())),
            "shared_paths": sorted(set(local) & set(published)),
        },
        "remote_refs_reaching_local_root": sorted(g.out("for-each-ref", "--contains", ll["root"], "--format=%(refname)",
                                                        "refs/remotes").split()),
    }


def shadow_block(g: Git, pins: dict, subject: str) -> dict:
    sc, heads = pins["shadow_clone"], pins["local_lineage"]["heads"]
    refs = {rel: g.ref(sc["prefix"] + rel) for rel in sorted(sc["refs"])}
    preserve = {n: g.ref(sc["prefix"] + sc["local_lineage_prefix"] + n) for n in sorted(heads)}
    rel = {r: g.relation(sha, subject) for r, sha in sorted(sc["refs"].items())}
    merge_base = {r: g.out("merge-base", sha, subject) for r, sha in sorted(sc["refs"].items()) if rel[r] == "diverged"}
    return {
        "prefix": sc["prefix"],
        "refs": refs,
        "local_lineage_preserve": preserve,
        "relation_to_subject": rel,
        "merge_base_with_subject": merge_base,
        "identity_commit": {"sha": sc["identity_commit"], "relation_to_subject": g.relation(sc["identity_commit"], subject)},
        "refs_under_prefix": len(g.refs(sc["prefix"])),
    }


def predecessor_block(g: Git, pins: dict, subject: str) -> dict:
    s = pins["subject"]
    return {"path": s["predecessor"], "tree_at_subject": g.out("rev-parse", f"{subject}:{s['predecessor']}"),
            "tree_at_base": g.out("rev-parse", f"{s['base_commit']}:{s['predecessor']}"), "pinned_tree": s["predecessor_tree"]}


# ----------------------------------------------------------------------------------------------------
# clauses


def c1_court_at_head(root: Path, j: Judge) -> None:
    diverged = []
    for rel in SUBJ["court_files"]:
        blob = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{rel}"], capture_output=True)
        have = LOADED.get(rel)
        if have is None:
            have = (root / rel).read_bytes() if (root / rel).is_file() else None
        if blob.returncode != 0 or have != blob.stdout:
            diverged.append(f"{rel} ({'absent at HEAD' if blob.returncode != 0 else 'differs from HEAD'})")
    if diverged:
        j.refuse("COURT_NOT_AT_HEAD", "C1", f"the judging court is not the committed court: {diverged}")
    else:
        j.ok("C1", f"the judging court ({len(SUBJ['court_files'])} files, pins as loaded) is byte-identical to HEAD")


def w1_exact(g: Git, j: Judge) -> None:
    dirty = g.run("status", "--porcelain=v1", "--untracked-files=no")
    if dirty.returncode != 0:
        j.refuse("NOT_A_CHECKOUT", "W1", f"git status failed: {dirty.stderr.strip()[-200:]}")
    elif dirty.stdout.strip():
        j.refuse("WORKING_SUBJECT_NOT_EXACT", "W1", f"tracked changes against HEAD: {dirty.stdout.splitlines()[:6]}")
    else:
        j.ok("W1", "no tracked change against HEAD: the working subject is exactly HEAD")


def i1_remote(g: Git, pins: dict, j: Judge, transport: str | None) -> str | None:
    s = pins["subject"]
    url = g.out("config", "--get", "remote.origin.url")
    if not url:
        j.refuse("NO_REMOTE", "I1", "remote.origin.url is not set: the working subject is bound to no remote")
        return None
    slug = github_slug(url)
    if slug != s["repository"]:
        j.refuse("REMOTE_NOT_SUBJECT", "I1", f"remote.origin.url {url!r} names {slug or 'no GitHub repository'}, not "
                                              f"github.com/{s['repository']}")
        return None
    if transport is None:
        expanded = g.out("ls-remote", "--get-url", url)
        if expanded != url:
            j.refuse("REMOTE_TRANSPORT_REWRITTEN", "I1", f"a url.<base>.insteadOf rule rewrites {url!r} to {expanded!r}: "
                                                         "an observation through it is not GitHub's")
            return None
    others = sorted(set(g.out("remote").split()) - {"origin"})
    j.ok("I1", f"remote.origin.url {url} = github.com/{slug}" + (f" (other remotes {others} are not the binding)" if others else ""))
    return url


def observe_github(g: Git, pins: dict, url: str, transport: str | None, j: Judge) -> dict | None:
    s = pins["subject"]
    target = transport or url
    p = g.run("ls-remote", target, "refs/heads/main", f"refs/heads/{s['branch']}", timeout=int(s["ls_remote_timeout"]))
    observed_at = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    if p.returncode != 0:
        j.unk("GITHUB_UNREACHABLE", "I2", f"git ls-remote {url} exit {p.returncode}: {p.stderr.strip()[-200:]}")
        return None
    heads = {}
    for line in p.stdout.splitlines():
        sha, _, ref = line.partition("\t")
        heads[ref.strip()] = sha.strip()
    return {"remote_url": url, "main": heads.get("refs/heads/main", ""), "branch": s["branch"],
            "branch_sha": heads.get(f"refs/heads/{s['branch']}", ""), "observed_at": observed_at,
            "authority": f"git ls-remote {url} refs/heads/main refs/heads/{s['branch']}",
            "output_sha256": sha256(p.stdout.encode("utf-8"))}


def i2_github_main(g: Git, pins: dict, gh: dict, j: Judge) -> bool:
    base, main = pins["subject"]["base_commit"], gh["main"]
    if not main:
        j.refuse("GITHUB_MAIN_ABSENT", "I2", f"{gh['remote_url']} advertises no refs/heads/main")
        return False
    if not g.has_commit(main):
        j.unk("GITHUB_MAIN_NOT_FETCHED", "I2", f"GitHub main {main} is not in this checkout's object store (fetch origin)")
        return False
    rel = g.relation(base, main)
    if rel not in ON_LINE:
        j.refuse("BASE_NOT_ON_GITHUB_MAIN", "I2", f"the release base {base[:12]} is {rel} to GitHub main {main[:12]}")
        return False
    j.ok("I2", f"GitHub main = {main} ({gh['observed_at']}, live ls-remote); the release base {base[:12]} is {rel} to it")
    return True


def i3_head_lineage(g: Git, pins: dict, head: str, j: Judge) -> None:
    s = pins["subject"]
    rel = g.relation(s["base_commit"], head)
    if rel not in ON_LINE:
        j.refuse("HEAD_NOT_ON_BASE", "I3", f"the release base {s['base_commit'][:12]} is {rel} to the head {head[:12]}")
    roots = g.roots(head)
    if roots != [s["github_root"]]:
        j.refuse("FOREIGN_ROOT_IN_HEAD", "I3", f"the head's root set {[r[:12] for r in roots]} is not {{{s['github_root'][:12]}}}: "
                                               "another lineage entered its history")
    if rel in ON_LINE and roots == [s["github_root"]]:
        j.ok("I3", f"the head {head} descends from the release base {s['base_commit'][:12]} ({rel}) and its only root is the "
                   f"GitHub root {s['github_root'][:12]} ({g.out('rev-list', '--count', head)} commits)")


def i4_line(g: Git, pins: dict, gh: dict, head: str, j: Judge) -> str:
    branch, bsha = gh["branch"], gh["branch_sha"]
    if not bsha:
        j.unk("BRANCH_UNPUBLISHED", "I4", f"GitHub has no refs/heads/{branch}: the head's line is not published")
        return "unpublished"
    if not g.has_commit(bsha):
        j.unk("BRANCH_HEAD_NOT_FETCHED", "I4", f"GitHub {branch} = {bsha} is not in this checkout's object store (fetch origin)")
        return "unfetched"
    rel = g.relation(bsha, head)
    if rel == "equal":
        j.ok("I4", f"the head is GitHub {branch} ({bsha[:12]}): published")
        return "published"
    if rel == "ancestor":
        n = g.out("rev-list", "--count", f"{bsha}..{head}")
        j.ok("I4", f"the head fast-forwards GitHub {branch} ({bsha[:12]}) by {n} commits: publication pending, a plain push")
        return "publication-pending"
    if rel == "descendant":
        n = g.out("rev-list", "--count", f"{head}..{bsha}")
        j.ok("I4", f"the head is published: GitHub {branch} ({bsha[:12]}) contains it and moved on by {n} commits")
        return "published-and-moved-on"
    j.refuse("BRANCH_DIVERGED", "I4", f"the head {head[:12]} is {rel} to GitHub {branch} {bsha[:12]}: it is not a "
                                      "fast-forward of the published line")
    return str(rel)


def identity_graph(pins: dict, gh: dict, head: str):
    import rdflib  # noqa: PLC0415
    from rdflib import RDF, XSD, Literal, URIRef  # noqa: PLC0415
    er = rdflib.Namespace(ER)
    f = pins["identity_fact"]
    g = rdflib.Graph()
    g.bind("er", er)
    comp, obs = URIRef(f["component_iri"]), URIRef(f["observation_iri"])
    repo = pins["subject"]["repository"]
    for p, o in ((RDF.type, er.Component), (er.componentId, Literal(repo.split("/")[-1])), (er.repository, Literal(repo)),
                 (er.branchRef, Literal("main")), (er.commitSha, Literal(gh["main"])), (er.role, Literal(f["role"])),
                 (er.disposition, er[f["disposition"]]), (er.standing, er.UNKNOWN), (er.required, Literal(True)),
                 (er.refCheckMode, er.EXTERNAL_EXACT), (er.hasRefObservation, obs)):
        g.add((comp, p, o))
    for p, o in ((RDF.type, er.RefObservation), (er.observationAuthority, Literal(f"git ls-remote {gh['remote_url']} refs/heads/main")),
                 (er.observedRepository, Literal(repo)), (er.observedRef, Literal("main")), (er.observedSha, Literal(gh["main"])),
                 (er.observedAt, Literal(gh["observed_at"], datatype=XSD.dateTime))):
        g.add((obs, p, o))
    header = (f"# CE23-0 identity fact (court output of {COURT_CMD} at subject {head}; never hand-edited):\n"
              f"# GitHub main of {repo} observed by `{gh['authority']}` at {gh['observed_at']}.\n")
    return header + g.serialize(format="turtle")


def run_pack_gates(law_root: Path, pins: dict, ttl: Path, scratch: Path) -> tuple[int, str]:
    f = pins["identity_fact"]
    pack = law_root / f["pack"]
    gates = scratch / f"gates-{ttl.stem}"
    gates.mkdir(parents=True, exist_ok=True)
    for name in f["gates"]:
        shutil.copy2(pack / "gates" / name, gates / name)
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        p = subprocess.run([sys.executable, str(pack / "bin" / "run-gates.py"), str(ttl), str(gates)],
                           capture_output=True, text=True, env=env, timeout=300)
    except subprocess.TimeoutExpired:
        return 124, "run-gates.py timeout"
    return p.returncode, (p.stdout + p.stderr).strip()


def k1_fact(g: Git, pins: dict, gh: dict | None, head: str, law_root: Path, scratch: Path, j: Judge) -> str | None:
    """Returns the Turtle of this run's identity fact (None without a GitHub observation)."""
    import rdflib  # noqa: PLC0415
    text = None
    if gh and gh.get("main"):
        text = identity_graph(pins, gh, head)
        ttl = scratch / "identity-observed.ttl"
        ttl.write_text(text, encoding="utf-8")
        rc, out = run_pack_gates(law_root, pins, ttl, scratch)
        if rc == 0:
            j.ok("K1", f"the identity fact of this observation (er:Component {pins['subject']['repository']} @ main "
                       f"{gh['main'][:12]}, er:RefObservation by ls-remote) passes pack gates {pins['identity_fact']['gates']}")
        elif rc == 1:
            j.refuse("IDENTITY_FACT_REFUSED", "K1", f"pack gates refuse the observed identity fact: "
                                                    f"{[ln for ln in out.splitlines() if 'VIOLATION' in ln or '|' in ln][:4]}")
        else:
            j.unk("GATE_RUNNER_FAULT", "K1", f"bin/run-gates.py exit {rc}: {out[-200:]}")
    rel_path = pins["subject"]["identity"]
    committed = g.blob(f"HEAD:{rel_path}")
    if committed is None:
        j.ok("K1", f"no committed identity fact at HEAD ({rel_path}): sealed by --identity-out")
        return text
    ttl = scratch / "identity-committed.ttl"
    ttl.write_bytes(committed)
    rc, out = run_pack_gates(law_root, pins, ttl, scratch)
    if rc == 1:
        j.refuse("IDENTITY_FACT_REFUSED", "K1", f"pack gates refuse the committed {rel_path}: "
                                                f"{[ln for ln in out.splitlines() if 'VIOLATION' in ln or '|' in ln][:4]}")
        return text
    if rc != 0:
        j.unk("GATE_RUNNER_FAULT", "K1", f"bin/run-gates.py exit {rc} on {rel_path}: {out[-200:]}")
        return text
    er = rdflib.Namespace(ER)
    graph = rdflib.Graph().parse(ttl, format="turtle")
    comps = [c for c in graph.subjects(er.repository, rdflib.Literal(pins["subject"]["repository"]))]
    shas = sorted({str(graph.value(c, er.commitSha)) for c in comps})
    refs = sorted({str(graph.value(c, er.branchRef)) for c in comps})
    if len(shas) != 1 or refs != ["main"]:
        j.refuse("IDENTITY_FACT_CONTRADICTED", "K1", f"{rel_path} binds {pins['subject']['repository']} to {refs} {shas}, "
                                                     "not one GitHub main commit")
        return text
    sha, base = shas[0], pins["subject"]["base_commit"]
    if not g.has_commit(sha):
        j.refuse("IDENTITY_FACT_CONTRADICTED", "K1", f"{rel_path} observed GitHub main {sha}, which this checkout does not hold")
        return text
    rel_base = g.relation(base, sha)
    rel_now = g.relation(sha, gh["main"]) if gh and g.has_commit(gh.get("main", "")) else "unobserved"
    if rel_base not in ON_LINE or rel_now not in (*ON_LINE, "unobserved"):
        j.refuse("IDENTITY_FACT_CONTRADICTED", "K1", f"{rel_path} observed GitHub main {sha[:12]}: the base is {rel_base} to it and "
                                                     f"it is {rel_now} to the live GitHub main: not on the published line")
        return text
    j.ok("K1", f"committed {rel_path} passes the pack gates; its GitHub main {sha[:12]} is on the published line "
               f"(base {rel_base}, live main {rel_now})")
    return text


def committed_graph(lg: Git, law_root: Path, rel: str):
    """The Turtle file `rel` as committed at HEAD of `law_root` (None when HEAD does not hold it), parsed
    with the file's own URI as base, exactly as a parse of the file would."""
    import rdflib  # noqa: PLC0415
    data = lg.blob(f"HEAD:{rel}")
    if data is None:
        return None
    return rdflib.Graph().parse(data=data.decode("utf-8"), format="turtle", publicID=(law_root / rel).as_uri())


def o1_orders(law_root: Path, pins: dict, env: dict, j: Judge) -> list[str]:
    """Reads goal.ttl and the compiled orders from HEAD's tree of `law_root`: W1 ignores untracked files, so
    a working-tree glob would let an untracked orders.ttl link the gate."""
    import rdflib  # noqa: PLC0415
    from rdflib import RDF, URIRef  # noqa: PLC0415
    sj, dct = rdflib.Namespace(SJ), rdflib.Namespace(DCT)
    lg = Git(law_root, env)
    gate = URIRef(pins["subject"]["gate_iri"])
    goal_rel = f"{SDIR}/{pins['subject']['goal']}"
    goal = committed_graph(lg, law_root, goal_rel)
    if goal is None:
        j.refuse("GOAL_ABSENT", "O1", f"{goal_rel} is not committed at HEAD of {law_root}")
        return []
    cmd = str(goal.value(gate, sj.courtCommand) or "")
    if cmd != COURT_CMD:
        j.refuse("COURT_COMMAND_MISMATCH", "O1", f"{gate} sj:courtCommand is {cmd!r}, not {COURT_CMD!r}")
    orders = []
    compiled = re.compile(rf"{re.escape(SDIR)}/sjira/compiled/[^/]+/orders\.ttl")
    committed = lg.out("ls-tree", "-r", "--name-only", "HEAD", "--", f"{SDIR}/sjira/compiled").splitlines()
    for rel in sorted(p for p in committed if compiled.fullmatch(p)):
        g = committed_graph(lg, law_root, rel)
        for o in sorted(g.subjects(sj.checkpointOf, gate)):
            if (o, RDF.type, sj.WorkOrder) in g:
                subject = str(g.value(o, sj.subject) or "").rsplit("#", 1)[-1]
                orders.append(f"{g.value(o, dct.identifier)} ({rel}; subject {subject})")
    if not orders:
        j.refuse("ORDER_UNLINKED", "O1", f"no compiled sj:WorkOrder is checkpointed on {gate}")
    elif cmd == COURT_CMD:
        j.ok("O1", f"{gate.rsplit('#', 1)[-1]} court command is this court; compiled orders: {orders}")
    return orders


def l1_l3_lineage(g: Git, pins: dict, head: str, j: Judge) -> dict | None:
    ll = pins["local_lineage"]
    heads = ll["heads"]
    observed = {ns: g.refs(ns) for ns in ll["namespaces"]}
    chk = g.ref(ll["checkout_head_ref"])
    objects = {n: g.has_commit(s) for n, s in heads.items()}
    if not any(observed.values()) and not chk and not all(objects.values()):
        j.unk("LINEAGE_EVIDENCE_ABSENT", "L1", f"this checkout holds neither the local-lineage refs ({ll['namespaces']}) nor "
                                               f"their commits {sorted(n for n, ok in objects.items() if not ok)}: the lineage proof "
                                               "lives in the canonical checkout")
        return None
    bad = []
    for ns, got in observed.items():
        want = {ns + n: s for n, s in heads.items()}
        for ref, sha in sorted(want.items()):
            if got.get(ref) != sha:
                bad.append(f"{ref} {'absent' if ref not in got else 'at ' + got[ref][:12]} (pinned {sha[:12]})")
        extra = sorted(set(got) - set(want))
        if extra:
            j.refuse("LINEAGE_REF_UNPINNED", "L1", f"{ns} holds refs outside the pin {extra}: the preserved set is exactly the "
                                                   "pinned heads")
    if chk != ll["checkout_head"]:
        bad.append(f"{ll['checkout_head_ref']} {'absent' if not chk else 'at ' + chk[:12]} (pinned {ll['checkout_head'][:12]})")
    if bad:
        j.refuse("LINEAGE_UNPRESERVED", "L1", f"the local-only lineage is not preserved at its pinned SHAs: {bad}")
    if not all(objects.values()):
        j.refuse("LINEAGE_UNPRESERVED", "L1", f"local-lineage commits absent: {sorted(n for n, ok in objects.items() if not ok)}")
        return None
    block = lineage_block(g, pins, head)
    if block["commits"] != ll["commits"] or block["root"] != [ll["root"]]:
        j.refuse("LINEAGE_SHAPE_CHANGED", "L1", f"the local lineage has {block['commits']} commits and roots "
                                                f"{[r[:12] for r in block['root']]}, pinned {ll['commits']} and {ll['root'][:12]}")
    elif not bad:
        j.ok("L1", f"the local-only lineage ({len(heads)} heads, {block['commits']} commits, root {ll['root'][:12]}) is preserved "
                   f"at its pinned SHAs under {ll['namespaces']} and {ll['checkout_head_ref']}")
    changed = {f"{n}->{what}": r for what in ("relation_to_base", "relation_to_subject") for n, r in block[what].items()
               if r != ll["relation"]}
    if changed:
        j.refuse("LINEAGE_RELATION_CHANGED", "L2", f"merge-base verdicts {changed} differ from the pinned relation {ll['relation']!r}")
    else:
        ov = block["blob_overlap_main_vs_base"]
        j.ok("L2", f"every local head is {ll['relation']} to the release base {pins['subject']['base_commit'][:12]} and to the "
                   f"head (merge-base, {2 * len(heads)} pairs); local main vs base: {ov['shared_blob_ids']} shared blob ids, "
                   f"shared paths {ov['shared_paths']}")
    published = bool(block["remote_refs_reaching_local_root"])
    if published != ll["published"]:
        j.refuse("LINEAGE_PUBLICATION_CHANGED", "L3", f"remote-tracking refs reaching the local root: "
                                                      f"{block['remote_refs_reaching_local_root']} (pinned published={ll['published']}): "
                                                      "publishing the local lineage is an operator decision that moves the pin")
    else:
        j.ok("L3", f"no remote-tracking ref reaches the local root {ll['root'][:12]} (published={published}, as pinned)")
    return block


def s1_shadow(g: Git, pins: dict, head: str, j: Judge) -> dict:
    sc, heads = pins["shadow_clone"], pins["local_lineage"]["heads"]
    want = {sc["prefix"] + rel: sha for rel, sha in sc["refs"].items()}
    pres = {sc["prefix"] + sc["local_lineage_prefix"] + n: s for n, s in heads.items()}
    got = {ref: g.ref(ref) for ref in [*want, *pres]}
    if not any(got.values()):
        missing = sorted(s[:12] for s in {*want.values(), *pres.values()} if not g.has_commit(s))
        if missing:
            j.unk("SHADOW_EVIDENCE_ABSENT", "S1", f"this checkout holds no ref under {sc['prefix']} and not the commits {missing}: "
                                                  "the shadow clone's preserved refs live in the canonical checkout")
        else:
            j.refuse("SHADOW_LINEAGE_UNPRESERVED", "S1", f"no ref under {sc['prefix']} although every pinned commit is still "
                                                         "in the object store: the archive was dropped")
    else:
        bad = [f"{r} {'absent' if not got[r] else 'at ' + got[r][:12]} (pinned {s[:12]})" for r, s in sorted(want.items()) if got[r] != s]
        bad += [f"{r} absent" for r in sorted(pres) if not got[r]]
        if bad:
            j.refuse("SHADOW_LINEAGE_UNPRESERVED", "S1", f"the shadow clone's refs are not preserved at their pinned SHAs: {bad}")
        disagree = [f"{r} at {got[r][:12]} != local-lineage {s[:12]}" for r, s in sorted(pres.items()) if got[r] and got[r] != s]
        if disagree:
            j.refuse("PRESERVATIONS_DISAGREE", "S1", f"the shadow clone's preservation of the local lineage disagrees with L1: {disagree}")
        if not bad and not disagree:
            j.ok("S1", f"the shadow clone's {len(want)} pinned refs and its {len(pres)} local-lineage preserve refs hold their "
                       f"SHAs under {sc['prefix']} ({len(g.refs(sc['prefix']))} refs there); both preservations of the local "
                       "lineage agree")
    block = shadow_block(g, pins, head)
    cont = {"identity_commit": sc["identity_commit"], sc["published_int"]: sc["refs"][sc["published_int"]]}
    broken = {k: g.relation(s, head) for k, s in cont.items() if g.relation(s, head) not in ON_LINE}
    if broken:
        j.refuse("SHADOW_LINE_NOT_CONTINUED", "S1", f"the head does not continue the shadow-era line: {broken} (relation to the head)")
    else:
        rel = block["relation_to_subject"]
        j.ok("S1", f"the head continues the shadow-era line: CE23-0 commit {sc['identity_commit'][:12]} and the shadow's published "
                   f"int {sc['refs'][sc['published_int']][:12]} are its ancestors; the shadow's other preserved heads relate to "
                   f"the head as {rel} (merge bases {block['merge_base_with_subject']})")
    return block


def p1_predecessor(g: Git, pins: dict, head: str, j: Judge) -> dict:
    block = predecessor_block(g, pins, head)
    if not (block["tree_at_subject"] == block["tree_at_base"] == block["pinned_tree"]):
        j.refuse("PREDECESSOR_TOUCHED", "P1", f"{block['path']} tree at the head {block['tree_at_subject'][:12] or 'absent'}, at the "
                                              f"base {block['tree_at_base'][:12] or 'absent'}, pinned {block['pinned_tree'][:12]}")
    else:
        j.ok("P1", f"{block['path']} at the head is the base tree and the pinned tree {block['pinned_tree'][:12]}")
    return block


# ----------------------------------------------------------------------------------------------------
# R1: the committed receipt


def validator_for(scratch: Path) -> tuple[Path | None, list[tuple[str, str, str]]]:
    """The generated receipt validator CE23-9 pins (ce23_9/root.toml [validator]), read from the canonical
    ggen-marketplace checkout at its pinned commit into scratch (ce23_9/members.materialize_validator)."""
    sys.path.insert(0, str(HERE.parent / "ce23_9"))
    try:
        import members  # noqa: PLC0415
    except (ImportError, OSError, tomllib.TOMLDecodeError) as exc:
        return None, [("UNKNOWN", "VALIDATOR_PIN_UNREADABLE", f"ce23_9/members.py: {type(exc).__name__}: {exc}")]
    return members.materialize_validator(scratch / "validator")


def validate(validator: Path, doc_path: Path) -> tuple[int, str]:
    p = subprocess.run([sys.executable, str(validator), str(doc_path), "--contract", "dfcm_fleet_v1"], capture_output=True,
                       text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))
    return p.returncode, (p.stdout + p.stderr).strip()


def _obj(x) -> dict:
    return x if isinstance(x, dict) else {}


def receipt_record(g: Git, rel: str, rev: str) -> tuple[dict | None, dict | None]:
    """The supersession record of the receipt `rel` at `rev` (what a seal at `rev` supersedes: a function of
    the commit, so R1 recomputes it) and its parsed document (None when it is not a JSON object);
    (None, None) when `rev` holds no receipt."""
    data = g.blob(f"{rev}:{rel}")
    if data is None:
        return None, None
    record = {"path": rel, "blob": g.out("rev-parse", f"{rev}:{rel}"), "commit": g.out("log", "-1", "--format=%H", rev, "--", rel)}
    try:
        doc = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return record, None
    if not isinstance(doc, dict):
        return record, None
    record.update({"subject_sha": str(_obj(doc.get("identity")).get("subject_sha", "")),
                   "standing": str(_obj(doc.get("standing")).get("value", "")),
                   "emitted_by_this_court": _obj(doc.get("court")).get("emitted_by") == WRAPPER})
    return record, doc


def court_identity_mismatch(g: Git, doc: dict, subject: str) -> list[str]:
    """A court-emitted receipt names the court that sealed it: court.loaded_sha256 must be exactly the
    sha256 of each court file (the wrapper, court.py, the pins) as committed at its subject (C1 held the
    loaded court byte-identical to the subject when it sealed)."""
    court = _obj(doc.get("court"))
    loaded = _obj(court.get("loaded_sha256"))
    out = []
    if court.get("pins") != f"{SDIR}/courts/ce23_0/identity.toml":
        out.append(f"court.pins {court.get('pins')!r}")
    if set(loaded) != set(LOADED):
        out.append(f"court.loaded_sha256 names {sorted(loaded)}, not the court files {sorted(LOADED)}")
    for path in sorted(set(loaded) & set(LOADED)):
        blob = g.blob(f"{subject}:{path}")
        want = sha256(blob) if blob is not None else "(absent at the subject)"
        if loaded[path] != want:
            out.append(f"{path}: loaded {str(loaded[path])[:12]} is not the blob at the subject ({want[:12]})")
    return out


def standing_underived(doc: dict, pins: dict, subject: str) -> list[str]:
    """A court-emitted receipt's standing is derived, never stored: the verdict of its own recorded clause
    lines fixes standing.value, the replayed court command's exit and summary, and the counts in
    standing.derived_from; an ALIVE receipt must record what an ALIVE run records (the pinned lineage
    relation, an untouched predecessor)."""
    clauses = _obj(doc.get("court")).get("clauses")
    if not isinstance(clauses, list) or not clauses:
        return ["court.clauses absent: no recorded run to derive the standing from"]
    verdicts = [str(_obj(c).get("verdict")) for c in clauses]
    n = {k: verdicts.count(k) for k in ("OK", "REFUSED", "UNKNOWN")}
    out = []
    if sum(n.values()) != len(verdicts):
        out.append(f"clause verdicts outside OK/REFUSED/UNKNOWN: {sorted(set(verdicts) - set(n))}")
    verdict = "REFUSED" if n["REFUSED"] else "UNKNOWN" if n["UNKNOWN"] else "ALIVE"
    want = {"ALIVE": "ALIVE", "UNKNOWN": "UNKNOWN", "REFUSED": "BLOCKED"}[verdict]
    st = _obj(doc.get("standing"))
    if st.get("value") != want:
        out.append(f"standing.value {st.get('value')!r} but its clause lines derive {want} ({n})")
    prefix = f"{COURT_CMD} exit {EXIT[verdict]} at {subject} ({n['OK']} OK, {n['REFUSED']} REFUSED, {n['UNKNOWN']} UNKNOWN;"
    if not str(st.get("derived_from", "")).startswith(prefix):
        out.append(f"standing.derived_from does not start {prefix!r}")
    cmds = _obj(doc.get("replay")).get("commands")
    first = _obj(cmds[0]) if isinstance(cmds, list) and cmds else {}
    if (first.get("cmd"), first.get("exit"), first.get("summary")) != (COURT_CMD, EXIT[verdict], f"CE23-0 {verdict} at {subject}"):
        out.append(f"replay.commands[0] {first.get('cmd')!r} exit {first.get('exit')!r} is not the court's run ({EXIT[verdict]})")
    if want == "ALIVE":
        lineage, pred = _obj(doc.get("lineage")), _obj(doc.get("predecessor"))
        rel = pins["local_lineage"]["relation"]
        off = sorted(f"{k}->{n}" for k in ("relation_to_base", "relation_to_subject")
                     for n, r in _obj(lineage.get(k)).items() if r != rel)
        if not lineage or off:
            out.append(f"ALIVE while the recorded lineage relations {off or '(absent)'} are not the pinned {rel!r}")
        if not (pred.get("tree_at_subject") and pred.get("tree_at_subject") == pred.get("tree_at_base") == pred.get("pinned_tree")):
            out.append("ALIVE while the recorded predecessor tree is not the base tree and the pinned tree")
    return out


def r1_receipt(g: Git, pins: dict, head: str, gh: dict | None, scratch: Path, validator: dict, j: Judge) -> dict | None:
    """Judges the receipt at HEAD (only a pinned pre-court blob is exempt); returns its supersession record."""
    rel = pins["subject"]["receipt"]
    record, doc = receipt_record(g, rel, "HEAD")
    if record is None:
        j.ok("R1", f"no committed receipt at HEAD ({rel}): sealed by --receipt-out")
        return None
    superseded = list(_obj(pins.get("receipt_history")).get("superseded_blobs", []))
    at = f"{rel} at HEAD (blob {record['blob'][:12]}, commit {record['commit'][:12]})"
    if doc is None:
        j.refuse("RECEIPT_INVALID", "R1", f"{at} is not a JSON object")
        return record
    if not record["emitted_by_this_court"]:
        if record["blob"] in superseded:
            j.ok("R1", f"{at}, subject {record['subject_sha'][:12]}, is the pinned pre-court receipt (identity.toml "
                       "[receipt_history]): superseded by the next seal, not judged")
        else:
            j.refuse("RECEIPT_NOT_COURT_EMITTED", "R1", f"{at} carries no court.emitted_by = {WRAPPER!r} and is not a pinned "
                                                        f"pre-court receipt {[b[:12] for b in superseded]}: a receipt this "
                                                        "court did not emit is refused, never skipped")
        return record
    subject = record["subject_sha"]
    if g.relation(subject, head) not in ON_LINE:
        j.refuse("RECEIPT_SUBJECT_FOREIGN", "R1", f"{rel}: identity.subject_sha {subject!r} is not the head or its ancestor")
        return record
    if validator.get("path") is None:
        kind, code, text = validator.get("finding", ("UNKNOWN", "VALIDATOR_ABSENT", "no validator"))
        if kind == "SKIP":
            j.ok("R1", f"{rel}: {text}")
        else:
            (j.refuse if kind == "REFUSED" else j.unk)(code, "R1", f"{rel}: {text}")
    else:
        doc_path = scratch / "committed-receipt.json"
        doc_path.write_bytes(g.blob(f"HEAD:{rel}") or b"")
        rc, out = validate(validator["path"], doc_path)
        if rc != 0:
            j.refuse("RECEIPT_INVALID", "R1", f"{rel}: the pinned validator (dfcm_fleet_v1) exit {rc}: {out.splitlines()[-3:]}")
    court_off = court_identity_mismatch(g, doc, subject)
    if court_off:
        j.refuse("RECEIPT_COURT_MISMATCH", "R1", f"{rel} (subject {subject[:12]}) names a court that is not the court committed "
                                                 f"at its subject: {court_off}")
    underived = standing_underived(doc, pins, subject)
    if underived:
        j.refuse("RECEIPT_STANDING_UNDERIVED", "R1", f"{rel} (subject {subject[:12]}) records a standing its own run does not "
                                                     f"derive: {underived}")
    s = pins["subject"]
    mismatch = []
    if doc.get("supersedes") != receipt_record(g, rel, subject)[0]:
        mismatch.append("supersedes (not the receipt at its subject)")
    ident = _obj(doc.get("identity"))
    if ident.get("repo") != s["repository"] or ident.get("base_sha") != s["base_commit"]:
        mismatch.append(f"identity repo/base {ident.get('repo')}/{ident.get('base_sha')}")
    for key, fn in (("lineage", lineage_block), ("shadow_clone", shadow_block), ("predecessor", predecessor_block)):
        want = fn(g, pins, subject)
        have = doc.get(key)
        if have != want:
            diff = sorted(k for k in set(want or {}) | set(_obj(have)) if _obj(have).get(k) != _obj(want).get(k))
            mismatch.append(f"{key}.{diff}")
    claimed = _obj(doc.get("github"))
    if claimed:
        cm, cb = str(claimed.get("main", "")), str(claimed.get("branch_sha", ""))
        if g.relation(s["base_commit"], cm) not in ON_LINE:
            mismatch.append(f"github.main {cm[:12]} not on the base's line")
        if gh and g.has_commit(gh.get("main", "")) and g.relation(cm, gh["main"]) not in ON_LINE:
            mismatch.append(f"github.main {cm[:12]} is not in the live GitHub main {gh['main'][:12]}")
        if cb and g.relation(cb, subject) != claimed.get("subject_relation_to_branch_source"):
            mismatch.append(f"github.branch_sha {cb[:12]} relation to the subject")
        if cb and gh and gh.get("branch_sha") and g.has_commit(gh["branch_sha"]) and g.relation(cb, gh["branch_sha"]) not in ON_LINE:
            mismatch.append(f"github.branch_sha {cb[:12]} is not in the live GitHub {s['branch']}")
    else:
        mismatch.append("github (absent)")
    if mismatch:
        j.refuse("RECEIPT_CLAIM_MISMATCH", "R1", f"{rel} (subject {subject[:12]}) records claims this run does not recompute: {mismatch}")
    elif not court_off and not underived:
        j.ok("R1", f"{rel} (court-emitted, subject {subject[:12]}, standing {record['standing']} derived from its "
                   f"{len(_obj(doc.get('court')).get('clauses') or [])} clause lines, court = the court at its subject): every "
                   "recorded claim equals the recomputation at its subject")
    return record


# ----------------------------------------------------------------------------------------------------
# the judge


def judge(root: Path, pins: dict, j: Judge, env: dict, scratch: Path, validator: dict,
          transport: str | None = None, law_root: Path | None = None) -> dict:
    """Every clause but C1 and AV over the checkout `root`; returns the observation."""
    law_root = law_root or root
    g = Git(root, env)
    head = g.out("rev-parse", "HEAD")
    obs: dict = {"root": str(root), "head": head}
    if not head:
        j.refuse("NOT_A_CHECKOUT", "W1", f"{root} has no HEAD commit")
        return obs
    obs["branch_local"] = g.out("symbolic-ref", "--short", "-q", "HEAD") or "(detached)"
    w1_exact(g, j)
    url = i1_remote(g, pins, j, transport)
    gh = observe_github(g, pins, url, transport, j) if url else None
    if gh:
        i2_github_main(g, pins, gh, j)
        gh["subject_relation_to_branch_source"] = g.relation(gh["branch_sha"], head) if gh["branch_sha"] else None
        gh["line"] = i4_line(g, pins, gh, head, j)
    i3_head_lineage(g, pins, head, j)
    obs["github"] = gh
    obs["identity_ttl"] = k1_fact(g, pins, gh, head, law_root, scratch, j)
    obs["orders"] = o1_orders(law_root, pins, env, j)
    obs["lineage"] = l1_l3_lineage(g, pins, head, j)
    obs["shadow_clone"] = s1_shadow(g, pins, head, j)
    obs["predecessor"] = p1_predecessor(g, pins, head, j)
    obs["supersedes"] = r1_receipt(g, pins, head, gh, scratch, validator, j)
    return obs


# ----------------------------------------------------------------------------------------------------
# seal: the receipt and the identity fact of one run


def replay_assertions(pins: dict, obs: dict) -> list[tuple[str, str]]:
    """Shell assertions of the run's facts (each exits 0 when its fact holds), for replay_court.py."""
    s, ll, sc = pins["subject"], pins["local_lineage"], pins["shadow_clone"]
    head, base = obs["head"], s["base_commit"]
    out = [(f"git merge-base --is-ancestor {base} {head}", "the release base is an ancestor of the subject"),
           (f"sh -c 'test \"$(git rev-list --max-parents=0 {head})\" = {s['github_root']}'", "the subject's only root is the GitHub root"),
           (f"sh -c 'test \"$(git config --get remote.origin.url)\" = {obs['github']['remote_url']}'", "origin is the GitHub remote"),
           (f"git merge-base --is-ancestor {base} {obs['github']['main']}", "the release base is on GitHub main as observed")]
    for ns in ll["namespaces"]:
        for n, sha in sorted(ll["heads"].items()):
            out.append((f"sh -c 'test \"$(git rev-parse --verify --quiet {ns}{n})\" = {sha}'", f"local-lineage head {n} preserved"))
    main = ll["heads"].get("main") or sorted(ll["heads"].values())[0]
    out += [(f"sh -c 'git merge-base {main} {base} >/dev/null; test $? -eq 1'", "local main and the base share no ancestor"),
            (f"sh -c 'git merge-base {main} {head} >/dev/null; test $? -eq 1'", "local main and the subject share no ancestor"),
            (f"sh -c 'test \"$(git rev-list --count {' '.join(v for _, v in sorted(ll['heads'].items()))})\" = {ll['commits']}'",
             "the local lineage has the pinned commit count"),
            (f"sh -c 'test -z \"$(git for-each-ref --contains {ll['root']} refs/remotes)\"'", "no remote-tracking ref reaches the local root"),
            (f"git merge-base --is-ancestor {sc['identity_commit']} {head}", "the shadow-era CE23-0 commit is an ancestor of the subject"),
            (f"git merge-base --is-ancestor {sc['refs'][sc['published_int']]} {head}", "the shadow's published int is an ancestor of the subject")]
    for rel, sha in sorted(sc["refs"].items()):
        out.append((f"sh -c 'test \"$(git rev-parse --verify --quiet {sc['prefix']}{rel})\" = {sha}'", f"shadow ref {rel} preserved"))
    out.append((f"sh -c 'test \"$(git rev-parse {head}:{s['predecessor']})\" = {s['predecessor_tree']}'", f"{s['predecessor']} untouched"))
    return out


def run_assertions(root: Path, env: dict, cmds: list[tuple[str, str]]) -> list[dict]:
    rows = []
    for cmd, summary in cmds:
        p = subprocess.run(["/bin/sh", "-c", cmd], cwd=root, capture_output=True, env=env)
        rows.append({"cmd": cmd, "cwd": str(root), "exit": p.returncode, "output_sha256": sha256(p.stdout + p.stderr),
                     "summary": summary})
    return rows


def build_receipt(pins: dict, obs: dict, j: Judge, verdict: str, av: dict | None, assertions: list[dict],
                  files: list[str], started: float) -> dict:
    s = pins["subject"]
    root, head = obs["root"], obs["head"]
    standing = {"ALIVE": "ALIVE", "UNKNOWN": "UNKNOWN", "REFUSED": "BLOCKED"}[verdict]
    n = {k: sum(1 for x in j.lines if x["verdict"] == k) for k in ("OK", "REFUSED", "UNKNOWN")}
    court_blobs = {rel: sha256(LOADED[rel]) if LOADED.get(rel) is not None else "" for rel in LOADED}
    doc = {
        "identity": {
            "subject": "CE23-0/root-identity", "repo": s["repository"], "subject_sha": head, "base_sha": s["base_commit"],
            "branch": obs.get("branch_local"), "checkout": root,
            "gate": f"ce:CE23-0 (release/v26.9.23/sjira/goal.ttl), sj:courtCommand '{COURT_CMD}'",
            "work_orders": obs.get("orders", []),
        },
        "authority": {"ceiling": "SELECT", "grant": "court run: read-only on the subject; one network read (git ls-remote of the "
                                                    "GitHub remote); writes only the files named by --receipt-out/--identity-out",
                      "actor": WRAPPER},
        "consequence": {"commits": [], "files_changed": files, "remote_effects": []},
        "github": obs.get("github"),
        "lineage": obs.get("lineage"),
        "shadow_clone": obs.get("shadow_clone"),
        "predecessor": obs.get("predecessor"),
        "supersedes": obs.get("supersedes"),
        "court": {"emitted_by": WRAPPER, "pins": f"{SDIR}/courts/ce23_0/identity.toml", "loaded_sha256": court_blobs,
                  "clauses": j.lines, "av": av},
        "replay": {"commands": [{"cmd": COURT_CMD, "cwd": root, "exit": EXIT[verdict],
                                 "summary": f"CE23-0 {verdict} at {head}"}] + assertions,
                   "durable_location": f"git:{s['repository']}@{head}:{WRAPPER}"},
        "standing": {"value": standing,
                     "derived_from": (f"{COURT_CMD} exit {EXIT[verdict]} at {head} ({n['OK']} OK, {n['REFUSED']} REFUSED, "
                                      f"{n['UNKNOWN']} UNKNOWN; refused={sorted(set(j.refused))}, unknown={sorted(set(j.unknown))}; "
                                      f"AV {av.get('summary') if av else 'not run'}; {time.time() - started:.0f}s)")},
    }
    if standing == "BLOCKED":
        doc["standing"]["broken_term"] = "R_missing_identity"
    return doc


# ----------------------------------------------------------------------------------------------------
# anti-vacuity corpus


AV_IDENT = {"GIT_AUTHOR_NAME": "ce23-0 corpus", "GIT_AUTHOR_EMAIL": "corpus@ce23-0.invalid",
            "GIT_COMMITTER_NAME": "ce23-0 corpus", "GIT_COMMITTER_EMAIL": "corpus@ce23-0.invalid",
            "GIT_AUTHOR_DATE": "2026-09-24T06:00:00Z", "GIT_COMMITTER_DATE": "2026-09-24T06:00:00Z"}
ARCHIVE = "refs/archive/pre-single-repo-migration/20260924T0600Z/"


def av_env(home: Path) -> dict:
    home.mkdir(parents=True, exist_ok=True)
    env = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "HOME": str(home), "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_TERMINAL_PROMPT": "0", "LANG": "C", "PYTHONDONTWRITEBYTECODE": "1"}
    env.update(AV_IDENT)
    return env


def sh_git(cwd: Path, env: dict, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True, env=env)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} in {cwd}: exit {p.returncode}: {p.stderr.strip()[-300:]}")
    return p.stdout.strip()


def commit_file(repo: Path, env: dict, rel: str, text: str, msg: str) -> str:
    path = repo / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    sh_git(repo, env, "add", "--", rel)
    sh_git(repo, env, "commit", "-q", "-m", msg)
    return sh_git(repo, env, "rev-parse", "HEAD")


def build_world(base: Path, env: dict, law_root: Path, with_archive: bool = True) -> tuple[Path, Path, dict]:
    """A synthetic GitHub (bare), a synthetic local-only lineage and a synthetic checkout of the GitHub lineage
    whose archive namespaces preserve the local lineage and a retired clone's refs, as the migration left the
    canonical checkout; returns (checkout, github, pins)."""
    gh, seed, local, work = base / "github.git", base / "seed", base / "local", base / "work"
    sh_git(base, env, "init", "-q", "--bare", "-b", "main", str(gh))
    sh_git(base, env, "init", "-q", "-b", "main", str(seed))
    g0 = commit_file(seed, env, "README.md", "chatman\n", "root")
    b = commit_file(seed, env, "release/v26.9.1/manifest.toml", "version = \"26.9.1\"\n", "base: v26.9.1 release")
    sh_git(seed, env, "push", "-q", str(gh), "main")
    sh_git(seed, env, "checkout", "-q", "-b", "release/v26.9.23-int")
    i1 = commit_file(seed, env, PINS["subject"]["receipt"], "{}\n", "shadow-era identity commit")
    pre_court = sh_git(seed, env, "rev-parse", f"{i1}:{PINS['subject']['receipt']}")
    sh_git(seed, env, "push", "-q", str(gh), "release/v26.9.23-int")
    # the retired clone's unpublished int: one commit past the published one, held only by the clone
    s1 = sh_git(seed, env, "commit-tree", f"{i1}^{{tree}}", "-p", i1, "-m", "shadow wip, never published")
    sh_git(seed, env, "branch", "shadow-wip", s1)
    sh_git(base, env, "init", "-q", "-b", "main", str(local))
    l0 = commit_file(local, env, "notes.md", "local 0\n", "local root")
    l1 = commit_file(local, env, "notes.md", "local 1\n", "local head")
    sh_git(local, env, "branch", "side", l0)
    sh_git(base, env, "init", "-q", "-b", "release/v26.9.23-int", str(work))
    sh_git(work, env, "config", "remote.origin.url", f"https://github.com/{PINS['subject']['repository']}.git")
    sh_git(work, env, "config", "remote.origin.fetch", "+refs/heads/*:refs/remotes/origin/*")
    sh_git(work, env, "fetch", "-q", str(gh), "+refs/heads/*:refs/remotes/origin/*")
    sh_git(work, env, "checkout", "-q", "-B", "release/v26.9.23-int", "refs/remotes/origin/release/v26.9.23-int")
    commit_file(work, env, "release/v26.9.23/README.md", "v26.9.23\n", "v26.9.23 work past the published line")
    pins = copy.deepcopy(PINS)
    pins["subject"].update({"base_commit": b, "github_root": g0, "predecessor_tree": sh_git(work, env, "rev-parse", f"{b}:release/v26.9.1")})
    pins["local_lineage"].update({"root": l0, "commits": 2, "heads": {"main": l1, "side": l0}, "checkout_head": l1})
    pins["receipt_history"] = {"superseded_blobs": [pre_court]}
    pins["shadow_clone"].update({"identity_commit": i1, "refs": {"heads/main": b, "heads/release/v26.9.23-int": s1,
                                                                 "remotes/origin/main": b, "remotes/origin/release/v26.9.23-int": i1}})
    if with_archive:
        sc = pins["shadow_clone"]
        sh_git(work, env, "fetch", "-q", str(local), "+refs/heads/*:refs/heads/archive/local-lineage/*",
               f"+refs/heads/*:{ARCHIVE}heads/*", f"+refs/heads/*:{sc['prefix']}{sc['local_lineage_prefix']}*")
        sh_git(work, env, "fetch", "-q", str(seed), f"+refs/heads/shadow-wip:{sc['prefix']}heads/release/v26.9.23-int")
        sh_git(work, env, "update-ref", pins["local_lineage"]["checkout_head_ref"], l1)
        for rel, sha in sc["refs"].items():
            sh_git(work, env, "update-ref", sc["prefix"] + rel, sha)
    return work, gh, pins


def seal_world(work: Path, env: dict, pins: dict, validator: dict, transport: str, law_root: Path, scratch: Path) -> None:
    """The court seals the synthetic checkout exactly as it seals the subject: the court (as loaded) is
    committed, then judged at that subject, emitted and committed."""
    for rel, data in LOADED.items():
        if data is not None:
            (work / rel).parent.mkdir(parents=True, exist_ok=True)
            (work / rel).write_bytes(data)
            sh_git(work, env, "add", "--", rel)
    sh_git(work, env, "commit", "-q", "-m", "the CE23-0 court committed at the subject")
    j = Judge(quiet=True)
    obs = judge(work, pins, j, env, scratch, validator, transport=transport, law_root=law_root)
    if j.verdict() != "ALIVE":
        raise RuntimeError(f"unsealable corpus world: {j.verdict()} {j.refused + j.unknown}")
    assertions = run_assertions(work, env, replay_assertions(pins, obs))
    doc = build_receipt(pins, obs, j, "ALIVE", None, assertions, [pins["subject"]["receipt"], pins["subject"]["identity"]], time.time())
    for rel, text in ((pins["subject"]["receipt"], json.dumps(doc, indent=2, sort_keys=True) + "\n"),
                      (pins["subject"]["identity"], obs["identity_ttl"])):
        (work / rel).parent.mkdir(parents=True, exist_ok=True)
        (work / rel).write_text(text, encoding="utf-8")
        sh_git(work, env, "add", "--", rel)
    sh_git(work, env, "commit", "-q", "-m", "CE23-0 seal (court output)")


def edit_json(path: Path, fn) -> None:
    doc = json.loads(path.read_text(encoding="utf-8"))
    fn(doc)
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def mutants(pins: dict, env: dict) -> list[dict]:
    """(id, world, mutation, expected verdict, expected codes). world: 'open' (unsealed), 'sealed' (carrying the
    court's own receipt + identity fact) or 'bare' (a checkout that never held the archive). A mutation gets
    (checkout, github, env) and changes them with git only."""
    ll, sc, s = pins["local_lineage"], pins["shadow_clone"], pins["subject"]
    l0, l1 = ll["heads"]["side"], ll["heads"]["main"]
    b = s["base_commit"]

    def git(w: Path, *a: str) -> str:
        return sh_git(w, env, *a)

    def commit(w: Path, rel: str, text: str) -> None:
        commit_file(w, env, rel, text, f"mutant: {rel}")

    def fetch_gh(w: Path, gh: Path) -> None:
        git(w, "fetch", "-q", str(gh), "+refs/heads/*:refs/remotes/origin/*")

    def rewrite_main(w: Path, gh: Path) -> None:
        orphan = sh_git(gh, env, "commit-tree", "4b825dc642cb6eb9a060e54bf8d69288fbee4904", "-m", "force-pushed main")
        sh_git(gh, env, "update-ref", "refs/heads/main", orphan)
        fetch_gh(w, gh)

    def diverge_branch(w: Path, gh: Path) -> None:
        d = sh_git(gh, env, "commit-tree", f"{b}^{{tree}}", "-p", b, "-m", "diverged published int")
        sh_git(gh, env, "update-ref", f"refs/heads/{s['branch']}", d)
        fetch_gh(w, gh)

    def publish(w: Path, gh: Path) -> None:
        git(w, "push", "-q", str(gh), f"HEAD:refs/heads/{s['branch']}")
        fetch_gh(w, gh)

    def drop_archive_refs(w: Path, gh: Path) -> None:
        for ref in [*git(w, "for-each-ref", "--format=%(refname)", "refs/heads/archive/").split(),
                    *git(w, "for-each-ref", "--format=%(refname)", ARCHIVE).split()]:
            git(w, "update-ref", "-d", ref)

    def drop_side(w: Path, gh: Path) -> None:
        for ns in ll["namespaces"]:
            git(w, "update-ref", "-d", f"{ns}side")
        git(w, "update-ref", "-d", f"{sc['prefix']}{sc['local_lineage_prefix']}side")

    def lie(w: Path, gh: Path) -> None:
        edit_json(w / s["receipt"], lambda d: d["lineage"]["relation_to_base"].update({"main": "descendant"}))
        git(w, "commit", "-q", "-am", "mutant: receipt claims a descendant lineage")

    def foreign_subject(w: Path, gh: Path) -> None:
        edit_json(w / s["receipt"], lambda d: d["identity"].update({"subject_sha": l1}))
        git(w, "commit", "-q", "-am", "mutant: receipt subject is the local lineage")

    def forge(fn, what: str):
        def mutate(w: Path, gh: Path) -> None:
            edit_json(w / s["receipt"], fn)
            git(w, "commit", "-q", "-am", f"mutant: {what}")
        return mutate

    def false_lineage(d: dict) -> None:
        d["lineage"]["relation_to_base"].update({"main": "descendant"})

    def hand_receipt(w: Path, gh: Path) -> None:
        head = git(w, "rev-parse", "HEAD")
        (w / s["receipt"]).write_text(json.dumps({"identity": {"subject_sha": head, "repo": s["repository"]},
                                                  "standing": {"value": "ALIVE"}}, indent=2) + "\n", encoding="utf-8")
        git(w, "commit", "-q", "-am", "mutant: a hand-written receipt replaces the pinned pre-court one")

    def fact(observed_only: bool):
        def mutate(w: Path, gh: Path) -> None:
            p = w / s["identity"]
            text = p.read_text(encoding="utf-8")
            main = text.split('er:observedSha "', 1)[1].split('"', 1)[0]
            text = text.replace(f'er:observedSha "{main}"', f'er:observedSha "{l1}"')
            if not observed_only:
                text = text.replace(f'er:commitSha "{main}"', f'er:commitSha "{l1}"')
            p.write_text(text, encoding="utf-8")
            git(w, "commit", "-q", "-am", "mutant: identity fact")
        return mutate

    def orphan_head(w: Path, gh: Path) -> None:
        git(w, "checkout", "-q", "--orphan", "orphan")
        git(w, "commit", "-q", "-m", "orphan head")

    def rebuilt_head(w: Path, gh: Path) -> None:
        tree = git(w, "rev-parse", "HEAD^{tree}")
        c = git(w, "commit-tree", tree, "-p", b, "-m", "the int rebuilt on the base, dropping the shadow-era line")
        git(w, "update-ref", f"refs/heads/{s['branch']}", c)

    return [
        {"id": "M0", "world": "open", "mutate": None, "verdict": "ALIVE", "codes": [],
         "why": "control: the head one commit ahead of the published line (publication pending)"},
        {"id": "M0p", "world": "open", "mutate": publish, "verdict": "ALIVE", "codes": [], "why": "control: the head published"},
        {"id": "M0s", "world": "sealed", "mutate": None, "verdict": "ALIVE", "codes": [],
         "why": "control: sealed with the court's own receipt and identity fact"},
        {"id": "M1", "world": "open", "mutate": lambda w, g: git(w, "config", "remote.origin.url", "https://github.com/someone/else.git"),
         "verdict": "REFUSED", "codes": ["REMOTE_NOT_SUBJECT"], "why": "origin is another GitHub repository"},
        {"id": "M2", "world": "open", "mutate": lambda w, g: git(w, "config", "--unset", "remote.origin.url"),
         "verdict": "REFUSED", "codes": ["NO_REMOTE"], "why": "no remote"},
        {"id": "M3", "world": "open", "mutate": lambda w, g: git(w, "merge", "-q", "--allow-unrelated-histories", "-m", "merge local",
                                                                 "refs/heads/archive/local-lineage/main"),
         "verdict": "REFUSED", "codes": ["FOREIGN_ROOT_IN_HEAD", "LINEAGE_RELATION_CHANGED"], "why": "the local lineage merged into the head"},
        {"id": "M4", "world": "open", "mutate": lambda w, g: git(w, "update-ref", "refs/heads/archive/local-lineage/main", l0),
         "verdict": "REFUSED", "codes": ["LINEAGE_UNPRESERVED"], "why": "an archive ref repointed"},
        {"id": "M5", "world": "open", "mutate": drop_side, "verdict": "REFUSED", "codes": ["LINEAGE_UNPRESERVED"],
         "why": "one local head dropped from every preservation (its commit still reachable)"},
        {"id": "M6", "world": "bare", "mutate": None, "verdict": "UNKNOWN", "codes": ["LINEAGE_EVIDENCE_ABSENT", "SHADOW_EVIDENCE_ABSENT"],
         "why": "edge: a checkout that never held the archive (a fresh GitHub clone)"},
        {"id": "M6r", "world": "open", "mutate": drop_archive_refs, "verdict": "REFUSED",
         "codes": ["LINEAGE_UNPRESERVED", "SHADOW_LINEAGE_UNPRESERVED"],
         "why": "every archive ref dropped while the commits are still in the object store (the twin of M6)"},
        {"id": "M7", "world": "open", "mutate": orphan_head, "verdict": "REFUSED", "codes": ["HEAD_NOT_ON_BASE", "FOREIGN_ROOT_IN_HEAD"],
         "why": "an orphan head"},
        {"id": "M8", "world": "open", "mutate": rewrite_main, "verdict": "REFUSED", "codes": ["BASE_NOT_ON_GITHUB_MAIN"],
         "why": "GitHub main force-pushed off the base"},
        {"id": "M9", "world": "open", "mutate": diverge_branch, "verdict": "REFUSED", "codes": ["BRANCH_DIVERGED"],
         "why": "the published line diverged from the head"},
        {"id": "M10", "world": "open", "mutate": lambda w, g: commit(w, "release/v26.9.1/manifest.toml", "version = \"26.9.1-edited\"\n"),
         "verdict": "REFUSED", "codes": ["PREDECESSOR_TOUCHED"], "why": "release/v26.9.1 edited"},
        {"id": "M11", "world": "sealed", "mutate": lie, "verdict": "REFUSED", "codes": ["RECEIPT_CLAIM_MISMATCH"],
         "why": "the sealed receipt claims a descendant lineage"},
        {"id": "M12", "world": "sealed", "mutate": fact(True), "verdict": "REFUSED", "codes": ["IDENTITY_FACT_REFUSED"],
         "why": "the sealed identity fact's observed SHA differs from its commit SHA (pack gate 050)"},
        {"id": "M12b", "world": "sealed", "mutate": fact(False), "verdict": "REFUSED", "codes": ["IDENTITY_FACT_CONTRADICTED"],
         "why": "the sealed identity fact binds main to a local-lineage commit (gates pass, the published line does not)"},
        {"id": "M13", "world": "open", "mutate": lambda w, g: git(w, "update-ref", "refs/remotes/origin/leak", l1),
         "verdict": "REFUSED", "codes": ["LINEAGE_PUBLICATION_CHANGED"], "why": "the local lineage published"},
        {"id": "M14", "world": "open",
         "mutate": lambda w, g: git(w, "update-ref", f"{sc['prefix']}{sc['local_lineage_prefix']}main", l0),
         "verdict": "REFUSED", "codes": ["PRESERVATIONS_DISAGREE"], "why": "the shadow's preservation of local main repointed"},
        {"id": "M15", "world": "open", "mutate": None, "transport": "missing.git", "verdict": "UNKNOWN", "codes": ["GITHUB_UNREACHABLE"],
         "why": "edge: GitHub unreachable"},
        {"id": "M16", "world": "open", "mutate": lambda w, g: (w / "README.md").write_text("dirty\n", encoding="utf-8"),
         "verdict": "REFUSED", "codes": ["WORKING_SUBJECT_NOT_EXACT"], "why": "a tracked file changed and not committed"},
        {"id": "M17", "world": "open", "mutate": lambda w, g: git(w, "update-ref", "refs/heads/archive/local-lineage/extra", l0),
         "verdict": "REFUSED", "codes": ["LINEAGE_REF_UNPINNED"], "why": "an unpinned ref in an archive namespace"},
        {"id": "M18", "world": "open", "mutate": rebuilt_head, "verdict": "REFUSED", "codes": ["SHADOW_LINE_NOT_CONTINUED"],
         "why": "the int rebuilt on the base, dropping the shadow-era line"},
        {"id": "M19", "world": "sealed", "mutate": foreign_subject, "verdict": "REFUSED", "codes": ["RECEIPT_SUBJECT_FOREIGN"],
         "why": "the sealed receipt's subject is a local-lineage commit"},
        {"id": "M20", "world": "open", "mutate": lambda w, g: git(w, "config", f"url.{g}.insteadOf",
                                                                  f"https://github.com/{s['repository']}.git"),
         "transport": "", "verdict": "REFUSED", "codes": ["REMOTE_TRANSPORT_REWRITTEN"],
         "why": "an insteadOf rule reroutes the GitHub remote (judged without a corpus transport)"},
        {"id": "M21", "world": "open", "mutate": lambda w, g: git(w, "update-ref", pins["local_lineage"]["checkout_head_ref"], l0),
         "verdict": "REFUSED", "codes": ["LINEAGE_UNPRESERVED"], "why": "the pre-migration checkout HEAD ref repointed"},
        {"id": "M22", "world": "sealed",
         "mutate": forge(lambda d: (false_lineage(d), d["court"].update({"emitted_by": "hand"})), "false claim, marker rewritten"),
         "verdict": "REFUSED", "codes": ["RECEIPT_NOT_COURT_EMITTED"],
         "why": "the sealed receipt claims a descendant lineage and its court marker is rewritten (M11 without the marker)"},
        {"id": "M23", "world": "sealed", "mutate": forge(lambda d: (false_lineage(d), d.pop("court")), "false claim, court block deleted"),
         "verdict": "REFUSED", "codes": ["RECEIPT_NOT_COURT_EMITTED"],
         "why": "the sealed receipt claims a descendant lineage and its court block is deleted"},
        {"id": "M24", "world": "sealed",
         "mutate": forge(lambda d: (d["identity"].update({"subject_sha": l1}), d["court"].update({"emitted_by": "hand"})),
                         "local-lineage subject, marker rewritten"),
         "verdict": "REFUSED", "codes": ["RECEIPT_NOT_COURT_EMITTED"],
         "why": "the sealed receipt's subject is a local-lineage commit and its court marker is rewritten (M19 without the marker)"},
        {"id": "M25", "world": "sealed",
         "mutate": forge(lambda d: d["court"]["loaded_sha256"].update({f"{SDIR}/courts/ce23_0/court.py": "0" * 64}), "court digest"),
         "verdict": "REFUSED", "codes": ["RECEIPT_COURT_MISMATCH"],
         "why": "the sealed receipt names a court.py that is not the court committed at its subject"},
        {"id": "M26", "world": "sealed",
         "mutate": forge(lambda d: d["court"]["clauses"].append({"verdict": "REFUSED", "clause": "P1", "code": "PREDECESSOR_TOUCHED",
                                                                 "text": "a recorded refusal"}), "refusal under ALIVE"),
         "verdict": "REFUSED", "codes": ["RECEIPT_STANDING_UNDERIVED"],
         "why": "the sealed receipt records a refused clause and keeps its ALIVE standing"},
        {"id": "M27", "world": "sealed", "mutate": forge(lambda d: d["supersedes"].update({"blob": "0" * 40}), "supersession"),
         "verdict": "REFUSED", "codes": ["RECEIPT_CLAIM_MISMATCH"],
         "why": "the sealed receipt claims to supersede a receipt that was not at its subject"},
        {"id": "M28", "world": "open", "mutate": hand_receipt, "verdict": "REFUSED", "codes": ["RECEIPT_NOT_COURT_EMITTED"],
         "why": "a hand-written ALIVE receipt replaces the pinned pre-court receipt"},
    ]


def run_av(law_root: Path, validator: dict, j: Judge) -> dict:
    scratch = Path(tempfile.mkdtemp(prefix="ce23-0-av."))
    results = []
    try:
        env = av_env(scratch / "home")
        worlds = {}
        for name, archive in (("open", True), ("bare", False)):
            (scratch / name).mkdir()
            worlds[name] = build_world(scratch / name, env, law_root, with_archive=archive)
        work, gh, pins = worlds["open"]
        (scratch / "sealed").mkdir()
        shutil.copytree(work, scratch / "sealed" / "work", symlinks=True)
        shutil.copytree(gh, scratch / "sealed" / "github.git", symlinks=True)
        seal_world(scratch / "sealed" / "work", env, pins, validator, str(scratch / "sealed" / "github.git"), law_root,
                   scratch / "sealed")
        worlds["sealed"] = (scratch / "sealed" / "work", scratch / "sealed" / "github.git", pins)
        table = mutants(pins, env)

        def one(m: dict) -> dict:
            src_work, src_gh, wpins = worlds[m["world"]]
            d = scratch / "m" / m["id"]
            d.mkdir(parents=True)
            w, g = d / "work", d / "github.git"
            shutil.copytree(src_work, w, symlinks=True)
            shutil.copytree(src_gh, g, symlinks=True)
            try:
                if m["mutate"]:
                    m["mutate"](w, g)
            except Exception as exc:  # a mutation that cannot be applied is a corpus fault, typed below
                return {"id": m["id"], "verdict": "FAULT", "codes": [f"{type(exc).__name__}: {exc}"[:300]]}
            transport = m.get("transport")
            transport = str(g) if transport is None else (str(d / transport) if transport else None)
            mj = Judge(quiet=True)
            judge(w, wpins, mj, env, d, validator, transport=transport, law_root=law_root)
            return {"id": m["id"], "verdict": mj.verdict(), "codes": sorted(set(mj.refused if mj.refused else mj.unknown))}

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = list(pool.map(one, table))
        for m, r in zip(table, results):
            good = r["verdict"] == m["verdict"] and set(m["codes"]) <= set(r["codes"])
            r.update({"expected": m["verdict"], "expected_codes": m["codes"], "why": m["why"], "held": good})
            if good:
                j.ok("AV", f"{m['id']} {r['verdict']} {r['codes']} as expected: {m['why']}")
            elif m["verdict"] == "ALIVE":
                j.refuse("AV_CONTROL_NOT_ALIVE", "AV", f"{m['id']} ({m['why']}) judged {r['verdict']} {r['codes']}")
            else:
                j.refuse("AV_MUTANT_ADMITTED", "AV", f"{m['id']} ({m['why']}) judged {r['verdict']} {r['codes']}, expected "
                                                     f"{m['verdict']} {m['codes']}")
    except (RuntimeError, OSError) as exc:
        j.refuse("AV_CORPUS_FAULT", "AV", f"the synthetic corpus could not be built: {exc}")
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    held = sum(1 for r in results if r.get("held"))
    controls = sum(1 for r in results if r.get("expected") == "ALIVE" and r.get("held"))
    edges = sum(1 for r in results if r.get("expected") == "UNKNOWN" and r.get("held"))
    return {"summary": f"{held}/{len(results)} corpus cases held ({controls} controls ALIVE, {edges} edges UNKNOWN, "
                       f"{held - controls - edges} mutants refused)", "cases": results}


# ----------------------------------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--no-av", action="store_true", help="skip the anti-vacuity corpus")
    ap.add_argument("--receipt-out", type=Path, help="write this run's fleet R receipt (court output)")
    ap.add_argument("--identity-out", type=Path, help="write this run's er:Component + er:RefObservation fact (court output)")
    a = ap.parse_args(argv)
    started = time.time()
    for tool in ("git",):
        if shutil.which(tool) is None:
            print(f"UNKNOWN[TOOL_MISSING] CE23-0: {tool} not on PATH", flush=True)
            return 75
    try:
        import rdflib  # noqa: F401,PLC0415
        import yaml  # noqa: F401,PLC0415
    except ModuleNotFoundError as exc:
        print(f"UNKNOWN[TOOL_MISSING] CE23-0: python module {exc.name}", flush=True)
        return 75
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=HERE).stdout.strip()).resolve()
    env = caller_env()
    head = Git(root, env).out("rev-parse", "HEAD")
    print(f"CE23-0 court: subject {head} at {root}", flush=True)
    j = Judge()
    c1_court_at_head(root, j)
    scratch = Path(tempfile.mkdtemp(prefix="ce23-0-court."))
    try:
        path, findings = validator_for(scratch)
        kind, code, text = findings[0] if findings else ("UNKNOWN", "VALIDATOR_ABSENT", "no finding")
        validator = {"path": path if kind == "OK" else None, "finding": (kind, code, text)}
        if kind == "OK":
            print(f"   validator: {text}", flush=True)
        obs = judge(root, PINS, j, env, scratch, validator)
        # the corpus judges synthetic receipts with the same validator; without one (typed above on the subject)
        # the corpus skips only that check, so a missing validator never reads as a refused mutant or control
        corpus_validator = validator if validator["path"] else {
            "path": None, "finding": ("SKIP", "", f"validator unavailable ({validator['finding'][1]}): corpus skips validation")}
        av = None if a.no_av else run_av(root, corpus_validator, j)
        if av:
            print(f"   AV: {av['summary']}", flush=True)
        verdict = j.verdict()
        if a.receipt_out or a.identity_out:
            if not obs.get("github") or not obs.get("identity_ttl"):
                j.unk("SEAL_WITHOUT_OBSERVATION", "SEAL", "no GitHub observation in this run: nothing to seal")
            elif validator["path"] is None:
                (j.refuse if validator["finding"][0] == "REFUSED" else j.unk)(validator["finding"][1], "SEAL",
                                                                             f"receipt validator: {validator['finding'][2]}")
            else:
                files = [str(p.resolve().relative_to(root)) if p.resolve().is_relative_to(root) else str(p)
                         for p in (a.receipt_out, a.identity_out) if p]
                assertions = run_assertions(root, env, replay_assertions(PINS, obs))
                failed = [x["cmd"] for x in assertions if x["exit"] != 0]
                if failed and verdict == "ALIVE":
                    j.refuse("REPLAY_ASSERTION_FAILED", "SEAL", f"shell assertions disagree with the ALIVE clauses: {failed}")
                verdict = j.verdict()
                doc = build_receipt(PINS, obs, j, verdict, av, assertions, files, started)
                staged = scratch / "receipt.json"
                staged.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")
                rc, out = validate(validator["path"], staged)
                if rc != 0:
                    j.refuse("EMITTED_RECEIPT_INVALID", "SEAL", f"the pinned validator refuses this run's receipt: {out.splitlines()[-4:]}")
                else:
                    if a.receipt_out:
                        a.receipt_out.parent.mkdir(parents=True, exist_ok=True)
                        shutil.copy2(staged, a.receipt_out)
                        print(f"SEAL receipt {a.receipt_out} ({doc['standing']['value']}, validator: {out.splitlines()[0]})", flush=True)
                    if a.identity_out:
                        a.identity_out.parent.mkdir(parents=True, exist_ok=True)
                        a.identity_out.write_text(obs["identity_ttl"], encoding="utf-8")
                        print(f"SEAL identity fact {a.identity_out}", flush=True)
    finally:
        shutil.rmtree(scratch, ignore_errors=True)
    verdict = j.verdict()
    tail = {"REFUSED": sorted(set(j.refused)), "UNKNOWN": sorted(set(j.unknown)), "ALIVE": []}[verdict]
    print(f"CE23-0 {verdict}{' ' + str(tail) if tail else ''} ({time.time() - started:.0f}s)", flush=True)
    return EXIT[verdict]


if __name__ == "__main__":
    raise SystemExit(main())
