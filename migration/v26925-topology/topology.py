#!/usr/bin/env python3
"""v26.9.25 reversible topology cleanup: preserve every copy of a repository, gate it, drill the restore, then retire it.

usage: topology.py [--scope scope.json] <freeze|inventory|preserve|classify|gate|drill|cleanup|verify|receipt> [--only SUBSTR] [--repo ID]

Design: scratchpad/v26925/designs/P2.md (+E8). Reuses, with the five listed v26923 defects fixed:
  - cutover.py ledger() step contract          -> ledger()                   (steps.jsonl, stops at first failed postcondition)
  - cleanup_gate.py evidence_defect/on_refs    -> evidence_defect(canonical_map, ev), on_refs()  (CANONICAL passed in, no SHADOW constants)
  - preserve.py snapshot_dirty / is_secret     -> snapshot_git(), is_secret()  (basename-anchored names: no 'token' substring hits;
                                                  porcelain v2 -z parsing; staged state recorded separately as the index commit)
  - retire_copies.py snapshot_tree + fresh==preserved check -> gate R7
  - cutover.py submodule-skip precedence bug   -> is_gitlink_path() (explicit parentheses, only mode-160000 entries skipped)

Kinds: CANONICAL | LINKED_WORKTREE | FOREIGN_LINKED_WORKTREE | PRUNABLE_RECORD | ORPHAN_WORKTREE | CLONE | NESTED_SELF_CLONE |
       SUBMODULE | SUBMODULE_ACTIVE | EMBEDDED_UNDECLARED | VENDORED_BUILD_INPUT | NONGIT_RESIDUE | DEGENERATE_GIT_RESIDUE | FIXTURE
Retirement is only ever `mv` into ~/.Trash (worktree + its admin dir), never rm -rf, never emptying the Trash.
State lives in TOPO_HOME (default: this directory); scratch (temporary indexes, drill trees) in TOPO_SCRATCH.
"""

import argparse
import datetime
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
HOME = os.environ.get("TOPO_HOME", HERE)
SCRATCH = os.environ.get("TOPO_SCRATCH", "/private/tmp/claude-501/-Users-sac/90d06f90-3c25-4b15-bede-3d0e7e58ac78/scratchpad/v26925/lanes/topo")
TRASH = os.environ.get("TOPO_TRASH", os.path.expanduser("~/.Trash"))
TS = os.environ.get("TOPO_TS", "20260925T0500Z")
NS = os.environ.get("TOPO_NS", "refs/preserve/v26.9.25")
REMOTE_PREFIX = "backup/v26.9.25/"
FIXED_DATE = "2026-09-25T05:00:00Z"
ZERO = "0" * 40
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
BIG = int(os.environ.get("TOPO_BIG", 100 * 1024 * 1024))
EVIDENCE_MAX = 50 * 1024 * 1024
REGEN_DIRS = {
    ".terraform",
    "target",
    "_build",
    "deps",
    "node_modules",
    ".venv",
    "venv",
    "__pycache__",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".elixir_ls",
    ".lexical",
    ".next",
    ".nuxt",
    ".output",
    "dist",
    "build",
    "coverage",
    ".gradle",
    ".turbo",
    ".cache",
    ".parcel-cache",
    ".svelte-kit",
    ".tox",
    ".hypothesis",
    ".lake",
    ".zig-cache",
    "zig-cache",
    "cover",
    ".oclnr-cache",
    ".fingerprint",
    ".sccache",
    ".nox",
    "htmlcov",
    ".eggs",
    ".swc",
    ".angular",
    "_opam",
}
REGEN_FILES = re.compile(r"(^|/)(\.DS_Store|erl_crash\.dump|[^/]*\.pyc|[^/]*\.o|[^/]*\.beam|[^/]*\.rlib|[^/]*\.rmeta|[^/]*\.d)$")
# FIX(v26923 is_secret): names are matched on the basename with anchors, so `_tokenizer.py` / `token.py` / `secrets.rs` are not secrets.
SECRET_BASENAME = re.compile(
    r"^(\.env(\.(?!example$|sample$|template$|dist$)[\w.-]+)?|\.netrc|\.pypirc|credentials(\.json)?|"
    r"id_(rsa|dsa|ecdsa|ed25519)|[^/]*\.(key|pem|p12|pfx|keystore|jks))$",
    re.I,
)
SECRET_CONTENT = re.compile(
    rb"-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|"
    rb"sk-(?:ant-|proj-)?[A-Za-z0-9_-]{32,}|xox[bap]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}"
)
SOURCE_EXT = {".c", ".cc", ".cpp", ".h", ".hpp", ".py", ".rs", ".go", ".js", ".ts", ".java", ".ex", ".exs", ".rb"}
TEST_PATH = re.compile(r"(^|/)(tests?|testing|test_data|testdata|fixtures?|examples?)(/|$)|_test\.|test_", re.I)
KEY_PATH = re.compile(r"((signing|private)\.key$|\.pem$|(^|/)id_(rsa|ed25519)$)")
PUBLIC_KEY_NAMES = re.compile(r"(^|/)(verifying\.key|[^/]*\.pub)$")
MANIFESTS = ("Cargo.toml", "mix.exs", "package.json", "pyproject.toml")
GIT_ENV = {
    "GIT_OPTIONAL_LOCKS": "0",
    "GIT_AUTHOR_NAME": "topology.py v26.9.25",
    "GIT_AUTHOR_EMAIL": "topology@v26925.local",
    "GIT_COMMITTER_NAME": "topology.py v26.9.25",
    "GIT_COMMITTER_EMAIL": "topology@v26925.local",
    "GIT_AUTHOR_DATE": FIXED_DATE,
    "GIT_COMMITTER_DATE": FIXED_DATE,
    "GIT_TERMINAL_PROMPT": "0",
    "LC_ALL": "C",
}


# ----------------------------------------------------------------------------------------------------------------- plumbing
def git(repo, *args, env=None, input=None, raw=False, gitdir=None, worktree=None):
    cmd = ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false", "-c", "core.quotePath=false"]
    if repo:
        cmd += ["-C", repo]
    e = dict(os.environ)
    e.update(GIT_ENV)
    if gitdir:
        e["GIT_DIR"] = gitdir
    if worktree:
        e["GIT_WORK_TREE"] = worktree
    e.update(env or {})
    p = subprocess.run(cmd + list(args), capture_output=True, env=e, input=input if (input is None or isinstance(input, bytes)) else input.encode())
    out = p.stdout if raw else p.stdout.decode("utf-8", "surrogateescape").rstrip("\n")
    return p.returncode, out, p.stderr.decode("utf-8", "replace").strip()


def gout(repo, *args, **kw):
    rc, out, err = git(repo, *args, **kw)
    if rc:
        raise GitError(f"git {' '.join(args)} in {repo}: rc={rc} {err[:400]}")
    return out


class GitError(RuntimeError):
    pass


def now():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def sha256_file(path):
    h = hashlib.sha256()
    if os.path.islink(path):
        h.update(os.readlink(path).encode())
        return h.hexdigest()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def slug(path):
    rel = path.replace("/Users/sac/", "").replace("/private/tmp/", "tmp/")
    return re.sub(r"[^A-Za-z0-9_-]+", "_", rel).strip("_-") or "root"


def ledger(ent, stop=True):
    """cutover.py ledger() contract: {step, precondition, forward, postcondition, falsifier, rollback, rollback_subject, ok, evidence}."""
    ent["at"] = now()
    with open(os.path.join(HOME, "steps.jsonl"), "a") as f:
        f.write(json.dumps(ent) + "\n")
    print(("OK   " if ent["ok"] else "FAIL ") + ent["step"] + " :: " + str(ent.get("evidence", ""))[:200], flush=True)
    if not ent["ok"] and stop:
        raise StepFailed(ent["step"])


class StepFailed(RuntimeError):
    pass


def jload(name, default=None):
    p = os.path.join(HOME, name)
    if not os.path.exists(p):
        return default
    with open(p) as f:
        return json.load(f)


def jdump(name, obj):
    p = os.path.join(HOME, name)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    data = json.dumps(obj, indent=1, sort_keys=True)
    with open(p + ".tmp", "w") as f:
        f.write(data)
    os.replace(p + ".tmp", p)
    return hashlib.sha256(data.encode()).hexdigest()


def load_parts(name, default):
    """state split per writer queue so repos can run in parallel processes: <name>.json + <name>.d/*.json (parts win)."""
    base = jload(name + ".json", None)
    out = base if base is not None else json.loads(json.dumps(default))
    d = os.path.join(HOME, name + ".d")
    if os.path.isdir(d):
        for f in sorted(os.listdir(d)):
            if f.endswith(".json"):
                with open(os.path.join(d, f)) as fh:
                    part = json.load(fh)
                for key, val in part.items():
                    if isinstance(val, dict) and isinstance(out.get(key), dict):
                        out[key].update(val)
                    else:
                        out[key] = val
    return out


def retired_from_ledger():
    """Append-only ledger is the single source for retirements (safe under parallel per-repo cleanup processes)."""
    out = {}
    p = os.path.join(HOME, "steps.jsonl")
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                try:
                    e = json.loads(line)
                except ValueError:
                    continue
                if e.get("step", "").startswith("retire ") and e.get("ok"):
                    cid = e["step"][len("retire ") :]
                    out[cid] = {
                        "copy_id": cid,
                        # stage 2: a manual retire step (symlink alias) records {"moved": [...], ...} as evidence
                        "moved": (e.get("evidence") or {}).get("moved", []) if isinstance(e.get("evidence"), dict) else (e.get("evidence") or []),
                        "at": e.get("at"),
                        "repo": e.get("repo"),
                        "rollback": e.get("rollback"),
                        "rollback_subject": e.get("rollback_subject"),
                        "method": "trash-move",
                        "fingerprint": e.get("fingerprint"),
                        "gate_run_id": e.get("gate_run_id"),
                    }
    return out


def mark_retired(inv):
    r = retired_from_ledger()
    for cid in r:
        if cid in inv["copies"]:
            inv["copies"][cid]["retired"] = True
    return r


def save_part(name, part_id, obj):
    """merge into the existing part: a later run over the same writer queue never erases earlier records."""
    if part_id and "/" in part_id:
        part_id = slug(part_id)  # stage 2: an --only path as part id must never escape HOME (os.path.join drops the prefix)
    path = os.path.join(name + ".d", f"{part_id or '_none'}.json")
    prev = jload(path, {})
    for key, val in obj.items():
        if isinstance(val, dict) and isinstance(prev.get(key), dict):
            prev[key].update(val)
        else:
            prev[key] = val
    return jdump(path, prev)


def is_regen(rel):
    parts = rel.split("/")
    return any(p in REGEN_DIRS for p in parts[:-1]) or bool(REGEN_FILES.search(rel))


def is_secret(path, rel=None):
    """FIX: basename-anchored name match (v26923 matched 'token' anywhere); public verifying keys are not secrets."""
    rel = rel or path
    base = os.path.basename(rel)
    if PUBLIC_KEY_NAMES.search(rel):
        return False
    if SECRET_BASENAME.match(base):
        return True
    if os.path.splitext(base)[1] in SOURCE_EXT and TEST_PATH.search(rel):
        return False  # key material embedded in source test fixtures (e.g. nng tests/tls.c); push-time key_scan still refuses it remotely
    try:
        if os.path.islink(path) or not os.path.isfile(path) or os.path.getsize(path) > 4 * 1024 * 1024:
            return False
        with open(path, "rb") as f:
            return bool(SECRET_CONTENT.search(f.read()))
    except OSError:
        return False


def is_gitlink_path(repo, rel):
    """FIX(cutover.py precedence): skip only a path that is a mode-160000 entry, never 'anything with a .git file'."""
    rc, out, _ = git(repo, "ls-files", "-s", "--", rel)
    return rc == 0 and out.startswith("160000 ")


def norm_origin(url):
    if not url:
        return None
    u = url.strip()
    m = re.match(r"^(?:https?://|ssh://)?(?:[^@/]+@)?([^:/]+)[:/](.+?)(?:\.git)?/?$", u)
    if m and not u.startswith("/") and not u.startswith("file:"):
        return f"{m.group(1).lower()}/{m.group(2)}"
    return "local:" + os.path.realpath(u.replace("file://", ""))


def parse_status_z(raw):
    """porcelain v2 -z parser (FIX: v26923 parsed v1 without -z, so quoted/odd paths broke)."""
    items = raw.split(b"\0")
    res, i = [], 0
    while i < len(items):
        it = items[i]
        i += 1
        if not it:
            continue
        t = it[:1]
        if t == b"1":
            f = it.split(b" ", 8)
            res.append({"xy": f[1].decode(), "sub": f[2].decode(), "mode_w": f[5].decode(), "path": f[8].decode("utf-8", "surrogateescape")})
        elif t == b"2":
            f = it.split(b" ", 9)
            res.append(
                {
                    "xy": f[1].decode(),
                    "sub": f[2].decode(),
                    "mode_w": f[5].decode(),
                    "path": f[9].decode("utf-8", "surrogateescape"),
                    "orig": items[i].decode("utf-8", "surrogateescape"),
                }
            )
            i += 1
        elif t == b"u":
            f = it.split(b" ", 10)
            res.append(
                {
                    "xy": f[1].decode(),
                    "sub": f[2].decode(),
                    "mode_w": f[6].decode(),
                    "path": f[10].decode("utf-8", "surrogateescape"),
                    "unmerged": True,
                }
            )
        elif t == b"?":
            res.append({"xy": "??", "sub": "N...", "path": it[2:].decode("utf-8", "surrogateescape")})
        elif t == b"!":
            res.append({"xy": "!!", "sub": "N...", "path": it[2:].decode("utf-8", "surrogateescape")})
    return res


# ------------------------------------------------------------------------------------------------------------------- scope
def load_scope(path):
    with open(path) as f:
        s = json.load(f)
    s.setdefault("canonicals", {})
    s.setdefault("extra_copies", [])
    s.setdefault("canonical_map", {})
    s.setdefault("refs_only_repos", [])
    s.setdefault("owned_remote_patterns", ["github.com/seanchatmangpt/"])
    s.setdefault("exclude_paths", [])
    s.setdefault("blocked", [])
    s.setdefault("no_push_repos", [])
    s.setdefault("owner_candidates", {})
    return s


def canonical_index(scope):
    """origin_norm -> (repo_id, path) for every canonical in scope and in canonical_map."""
    idx = {}
    allk = dict(scope.get("canonical_map", {}))
    allk.update(scope["canonicals"])
    for rid, k in allk.items():
        if os.path.isdir(k):
            o = norm_origin(git(k, "remote", "get-url", "origin")[1] if git(k, "remote", "get-url", "origin")[0] == 0 else "")
            if o:
                idx.setdefault(o, (rid, k))
    return idx, allk


def owned(scope, origin):
    return bool(origin) and any(p in origin for p in scope["owned_remote_patterns"])


# ------------------------------------------------------------------------------------------------------------ fingerprints
def git_dir_of(path):
    g = os.path.join(path, ".git")
    if os.path.isdir(g):
        return g
    if os.path.isfile(g):
        with open(g) as f:
            line = f.read().strip()
        if line.startswith("gitdir:"):
            t = line.split(":", 1)[1].strip()
            return t if os.path.isabs(t) else os.path.normpath(os.path.join(path, t))
    return None


def valid_repo_at(path):
    """True only when `path` is itself the top level of a working git repository (not a parent's)."""
    rc, top, _ = git(path, "rev-parse", "--show-toplevel")
    return rc == 0 and os.path.realpath(top) == os.path.realpath(path)


def tree_fingerprint(path, owner_gitdir=None):
    h = hashlib.sha256()
    for f in walk_files(path):
        full = os.path.join(path, f)
        try:
            st = os.lstat(full)
        except OSError:
            continue
        h.update(f"{f}\0{st.st_size}\0{int(st.st_mtime)}\n".encode())
    return h.hexdigest()


def fingerprint(copy):
    """sha256(HEAD | status -z | stash list | index mtime+size) for git copies; (path,size,mtime) listing otherwise."""
    p, kind = copy["path"], copy["kind"]
    if kind == "PRUNABLE_RECORD":
        a = copy.get("admin_dir") or ""
        h = hashlib.sha256()
        for n in ("HEAD", "index", "logs/HEAD"):
            fp = os.path.join(a, n)
            if os.path.exists(fp):
                h.update(n.encode() + sha256_file(fp).encode())
        return h.hexdigest()
    if not os.path.isdir(p):
        return "ABSENT"
    if kind in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        return tree_fingerprint(p)
    h = hashlib.sha256()
    h.update(git(p, "rev-parse", "HEAD")[1].encode())
    h.update(git(p, "status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignore-submodules=none", raw=True)[1])
    h.update(git(p, "stash", "list", "--format=%H")[1].encode())
    rc, ip, _ = git(p, "rev-parse", "--path-format=absolute", "--git-path", "index")
    if rc == 0 and os.path.exists(ip):
        st = os.stat(ip)
        h.update(f"{st.st_size}".encode())
        h.update(sha256_file(ip).encode())
    return h.hexdigest()


def walk_all(root):
    """Every file / symlink under root, no filtering (restored drill trees)."""
    res = []
    for d, dirs, files in os.walk(root):
        rel_d = os.path.relpath(d, root)
        for x in list(dirs):
            if os.path.islink(os.path.join(d, x)):
                res.append(os.path.normpath(os.path.join(rel_d, x)))
                dirs.remove(x)
        res += [os.path.normpath(os.path.join(rel_d, f)) for f in files]
    return sorted(res)


def walk_files(root, exclude_nested=True):
    """Relative file paths under root, skipping .git, regenerable dirs and nested repositories (their own copies)."""
    res = []
    for d, dirs, files in os.walk(root):
        rel_d = os.path.relpath(d, root)
        keep = []
        for x in dirs:
            full = os.path.join(d, x)
            if x == ".git" or x in REGEN_DIRS:
                continue
            if os.path.islink(full):
                res.append(os.path.normpath(os.path.join(rel_d, x)))
                continue
            if exclude_nested and os.path.exists(os.path.join(full, ".git")):
                continue
            keep.append(x)
        dirs[:] = keep
        for f in files:
            if f == ".git" and d == root:
                continue
            r = os.path.normpath(os.path.join(rel_d, f))
            if not is_regen(r):
                res.append(r)
    return sorted(res)


# -------------------------------------------------------------------------------------------------------------- discovery
def worktree_list(k):
    rc, out, _ = git(k, "worktree", "list", "--porcelain")
    res, cur = [], {}
    for line in out.splitlines() + [""]:
        if not line:
            if cur:
                res.append(cur)
            cur = {}
        elif " " in line:
            a, b = line.split(" ", 1)
            cur[a] = b
        else:
            cur[line] = True
    return res


def common_dir(k):
    return os.path.realpath(gout(k, "rev-parse", "--path-format=absolute", "--git-common-dir"))


def admin_dir_for(common, wt_path):
    wd = os.path.join(common, "worktrees")
    if not os.path.isdir(wd):
        return None
    for n in os.listdir(wd):
        gd = os.path.join(wd, n, "gitdir")
        if os.path.isfile(gd):
            with open(gd) as f:
                t = f.read().strip()
            if os.path.normpath(os.path.dirname(t)) == os.path.normpath(wt_path) or os.path.realpath(os.path.dirname(t)) == os.path.realpath(wt_path):
                return os.path.join(wd, n)
    return None


def find_nested(root, skip=()):
    """Every directory under root (not root) holding a .git entry; symlinks and regenerable dirs are never followed."""
    found = []
    skip = {os.path.realpath(s) for s in skip}
    for d, dirs, _ in os.walk(root):
        keep = []
        for x in dirs:
            full = os.path.join(d, x)
            if x == ".git" or x in REGEN_DIRS or os.path.islink(full):
                continue
            if os.path.realpath(full) in skip:
                continue
            if os.path.lexists(os.path.join(full, ".git")):
                found.append(full)
                continue
            keep.append(x)
        dirs[:] = keep
    return sorted(found)


def root_commits(p):
    rc, out, _ = git(p, "rev-list", "--max-parents=0", "--all")
    return sorted(set(out.split())) if rc == 0 else []


def base_copy(path, kind, **kw):
    c = {
        "copy_id": slug(path),
        "path": path,
        "kind": kind,
        "identity": {"origin_norm": None, "root_commits": []},
        "canonical": None,
        "repo_id": None,
        "common_dir": None,
        "admin_dir": None,
        "head": None,
        "branch": None,
        "locked": False,
        "prunable": False,
        "fingerprint": None,
        "dirty": {"staged": [], "tracked": [], "deleted": [], "untracked": []},
        "stashes": [],
        "reflog_only": [],
        "unpushed_tips": [],
        "ignored_evidence": [],
        "secrets": [],
        "nested_git": [],
        "big_files": [],
        "size_bytes": 0,
        "classification": None,
        "disposition": None,
        "owner": None,
        "writer_queue": None,
        "parent_copy": None,
        "notes": [],
    }
    c.update(kw)
    return c


def classify_nested(scope, n, parent_path, parent_origin, cidx):
    """Section 2 rules V1..V4, S1, F1 (first match wins) for a nested .git found under a checkout."""
    g = os.path.join(n, ".git")
    rel = os.path.relpath(n, parent_path)
    if os.path.isdir(g) and not valid_repo_at(n):
        return base_copy(n, "DEGENERATE_GIT_RESIDUE", notes=[".git exists but is not a repository; content belongs to the parent's tree"])
    gd = git_dir_of(n)
    if os.path.isfile(g) and gd and not os.path.exists(gd):
        return base_copy(n, "ORPHAN_WORKTREE", notes=[f"orphan-of: {gd}"])
    rc, ls, _ = git(parent_path, "ls-files", "-s", "--", rel)
    is_link = rc == 0 and ls.startswith("160000 ")
    rc2, gm, _ = git(parent_path, "config", "-f", ".gitmodules", "--get-regexp", r"submodule\..*\.path")
    declared = rc2 == 0 and any(l.split(" ", 1)[1] == rel for l in gm.splitlines() if " " in l)
    origin = norm_origin(git(n, "remote", "get-url", "origin")[1]) if git(n, "remote", "get-url", "origin")[0] == 0 else None
    if is_link:
        pin = ls.split()[1]
        head = git(n, "rev-parse", "HEAD")[1]
        clean = not git(n, "status", "--porcelain", "--untracked-files=all")[1]
        if declared:
            kind = "SUBMODULE" if (clean and head == pin) else "SUBMODULE_ACTIVE"
        else:
            kind = "EMBEDDED_UNDECLARED"
        return base_copy(n, kind, head=head, identity={"origin_norm": origin, "root_commits": root_commits(n)}, notes=[f"pin {pin}"])
    if gd and "/modules/" in gd:
        return base_copy(n, "SUBMODULE", identity={"origin_norm": origin, "root_commits": []}, notes=["module gitdir, not in parent index"])
    roots = root_commits(n)
    in_vendor = any(part in ("deps", "vendor", "vendors") or part.startswith(".vendor") for part in rel.split("/"))
    manifest_ref = False
    for d, dirs, files in os.walk(parent_path):
        dirs[:] = [
            x
            for x in dirs
            if x not in REGEN_DIRS
            and x != ".git"
            and not os.path.islink(os.path.join(d, x))
            and os.path.realpath(os.path.join(d, x)) != os.path.realpath(n)
        ]
        for m in MANIFESTS:
            if m in files:
                try:
                    with open(os.path.join(d, m), errors="replace") as f:
                        if os.path.basename(n) in f.read():
                            manifest_ref = True
                except OSError:
                    pass
        if manifest_ref or d.count(os.sep) - parent_path.count(os.sep) > 3:
            dirs[:] = [] if manifest_ref else dirs
    if origin != parent_origin and (manifest_ref or in_vendor):
        return base_copy(
            n,
            "VENDORED_BUILD_INPUT",
            identity={"origin_norm": origin, "root_commits": roots},
            notes=[f"manifest_ref={manifest_ref} in_vendor={in_vendor}"],
        )
    if origin and origin in cidx:
        return base_copy(n, "NESTED_SELF_CLONE" if origin == parent_origin else "CLONE", identity={"origin_norm": origin, "root_commits": roots})
    for o, (rid, k) in cidx.items():
        if roots and all(git(k, "cat-file", "-e", r + "^{commit}")[0] == 0 for r in roots):
            return base_copy(n, "CLONE", identity={"origin_norm": origin, "root_commits": roots}, notes=[f"root-commit match {rid}"])
    if not origin:
        return base_copy(n, "FIXTURE", identity={"origin_norm": None, "root_commits": roots})
    return base_copy(n, "FOREIGN_CLONE", identity={"origin_norm": origin, "root_commits": roots})


def resolve_owner(scope, c, cidx):
    o = c["identity"].get("origin_norm")
    if c.get("owner"):
        return c["owner"]
    if o and o in cidx:
        return cidx[o][0]
    return None


def inventory(scope):
    cidx, allk = canonical_index(scope)
    copies = {}
    excl = [os.path.realpath(p) for p in scope["exclude_paths"]]

    def add(c):
        if any(os.path.realpath(c["path"]).startswith(e) for e in excl):
            return
        if c["path"] in copies:
            return
        copies[c["path"]] = c

    for rid, k in scope["canonicals"].items():
        if not os.path.isdir(k):
            continue
        origin = norm_origin(git(k, "remote", "get-url", "origin")[1]) if git(k, "remote", "get-url", "origin")[0] == 0 else None
        cd = common_dir(k)
        add(
            base_copy(
                k,
                "CANONICAL",
                repo_id=rid,
                canonical=k,
                common_dir=cd,
                owner=rid,
                head=git(k, "rev-parse", "HEAD")[1],
                branch=git(k, "branch", "--show-current")[1],
                identity={"origin_norm": origin, "root_commits": root_commits(k)},
            )
        )
        wts = worktree_list(k)
        known = [k]
        for w in wts:
            wp = w.get("worktree")
            if not wp or os.path.realpath(wp) == os.path.realpath(k):
                continue
            known.append(wp)
            kind = "LINKED_WORKTREE" if os.path.isdir(wp) else "PRUNABLE_RECORD"
            add(
                base_copy(
                    wp,
                    kind,
                    repo_id=rid,
                    canonical=k,
                    common_dir=cd,
                    owner=rid,
                    admin_dir=admin_dir_for(cd, wp),
                    head=w.get("HEAD"),
                    branch=(w.get("branch") or "").replace("refs/heads/", "") or None,
                    locked=bool(w.get("locked")),
                    prunable=bool(w.get("prunable")),
                    identity={"origin_norm": origin, "root_commits": []},
                )
            )
        for n in find_nested(k, skip=known):
            nc = classify_nested(scope, n, k, origin, cidx)
            nc["parent_copy"] = slug(k)
            nc["repo_id"] = resolve_owner(scope, nc, cidx) or (rid if nc["kind"] in ("ORPHAN_WORKTREE", "DEGENERATE_GIT_RESIDUE") else None)
            nc["host_repo"] = rid
            add(nc)
    for x in scope["extra_copies"]:
        p = x["path"]
        if not os.path.lexists(p):
            continue
        gd = git_dir_of(p)
        if gd is None:
            kind = "NONGIT_RESIDUE"
        elif not os.path.exists(gd):
            kind = "ORPHAN_WORKTREE"
        elif os.path.isfile(os.path.join(p, ".git")):
            kind = "FOREIGN_LINKED_WORKTREE"
        elif not valid_repo_at(p):
            kind = "NONGIT_RESIDUE"  # a .git that is not a repository: the files are residue to archive
        elif git(p, "rev-parse", "--verify", "-q", "HEAD")[0] != 0 and not git(p, "for-each-ref")[1]:
            kind = "NONGIT_RESIDUE"  # unborn repository with no refs: nothing but files
        else:
            kind = "CLONE"
        origin = None
        if kind in ("CLONE", "FOREIGN_LINKED_WORKTREE"):
            rc, u, _ = git(p, "remote", "get-url", "origin")
            origin = norm_origin(u) if rc == 0 else None
        c = base_copy(
            p,
            kind,
            identity={"origin_norm": origin, "root_commits": root_commits(p) if kind in ("CLONE", "FOREIGN_LINKED_WORKTREE") else []},
            owner=x.get("owner"),
            notes=list(x.get("notes", [])),
        )
        c["repo_id"] = x.get("owner") or resolve_owner(scope, c, cidx)
        c["signed_off"] = x.get("signed_off", True)
        c["foreign"] = x.get("foreign", False)
        c["no_retire"] = x.get("no_retire", False)
        if kind == "FOREIGN_LINKED_WORKTREE":
            c["admin_dir"] = gd
            c["common_dir"] = os.path.realpath(gout(p, "rev-parse", "--path-format=absolute", "--git-common-dir"))
        add(c)
        if kind in ("CLONE", "FOREIGN_LINKED_WORKTREE", "NONGIT_RESIDUE", "ORPHAN_WORKTREE") and os.path.isdir(p):
            todo = [(p, origin, c["repo_id"])]
            while todo:  # nested of nested (e.g. an orphan's submodule that has its own submodule)
                parent, porigin, prid = todo.pop()
                for n in find_nested(parent):
                    nc = classify_nested(scope, n, parent, porigin, cidx)
                    nc["parent_copy"] = slug(parent)
                    nc["repo_id"] = resolve_owner(scope, nc, cidx) or prid
                    add(nc)
                    if nc["kind"] in RETIRABLE and os.path.isdir(n):
                        todo.append((n, nc["identity"].get("origin_norm"), nc["repo_id"]))
    for c in copies.values():
        if c["kind"] in ("CLONE", "NESTED_SELF_CLONE") and not c["repo_id"]:
            c["kind"] = "FOREIGN_CLONE"
            c["notes"].append("no canonical checkout for its origin in scope: third-party / sole checkout, kept")
        par = next((o for o in copies.values() if o["copy_id"] == c.get("parent_copy")), None)
        if par is not None and par["kind"] != "CANONICAL":
            for f in ("foreign", "signed_off", "no_retire", "blocked"):
                if f in par and f not in c:
                    c[f] = par[f]
        rid = c["repo_id"]
        c["canonical"] = c["canonical"] or (allk.get(rid) if rid else None)
        c["writer_queue"] = rid
        if c["kind"] in ("NESTED_SELF_CLONE", "CLONE", "FOREIGN_LINKED_WORKTREE", "ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
            for b in scope["blocked"]:
                if c["path"].startswith(b["path"]):
                    c["blocked"] = b
        scan_copy(scope, c)
        c["fingerprint"] = fingerprint(c)
    for c in copies.values():
        c["nested_git"] = [o["copy_id"] for o in copies.values() if o.get("parent_copy") == c["copy_id"]]
    return copies


def scan_copy(scope, c):
    """dirty / stash / reflog / unpushed / ignored-evidence / secrets / big files of one copy (read-only)."""
    p, kind = c["path"], c["kind"]
    if kind in (
        "LINKED_WORKTREE",
        "CLONE",
        "NESTED_SELF_CLONE",
        "FOREIGN_LINKED_WORKTREE",
        "SUBMODULE_ACTIVE",
        "CANONICAL",
        "VENDORED_BUILD_INPUT",
        "EMBEDDED_UNDECLARED",
    ) and os.path.isdir(p):
        c["head"] = git(p, "rev-parse", "HEAD")[1] or c["head"]
        c["branch"] = git(p, "branch", "--show-current")[1] or c["branch"]
        st = parse_status_z(git(p, "status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignore-submodules=none", raw=True)[1])
        for e in st:
            if e["xy"] == "??":
                c["dirty"]["untracked"].append(e["path"])
            else:
                if e["xy"][0] != ".":
                    c["dirty"]["staged"].append(e["path"])
                if e["xy"][1] == "D" or e["xy"][0] == "D":
                    c["dirty"]["deleted"].append(e["path"])
                elif e["xy"][1] != ".":
                    c["dirty"]["tracked"].append(e["path"])
        if kind in ("CLONE", "NESTED_SELF_CLONE", "VENDORED_BUILD_INPUT", "EMBEDDED_UNDECLARED", "SUBMODULE_ACTIVE", "FOREIGN_LINKED_WORKTREE"):
            c["stashes"] = git(p, "stash", "list", "--format=%H")[1].split()
        if kind == "FOREIGN_LINKED_WORKTREE" and c.get("admin_dir"):
            c["reflog_only"] = reflog_only_admin(p, c["admin_dir"])  # host repo keeps its own branches; only this worktree's reflog goes
        elif kind in ("CLONE", "NESTED_SELF_CLONE", "VENDORED_BUILD_INPUT", "EMBEDDED_UNDECLARED", "SUBMODULE_ACTIVE"):
            c["reflog_only"] = reflog_only_clone(p)
            for line in git(p, "for-each-ref", "--format=%(refname) %(objectname) %(objecttype)", "refs/heads", "refs/tags")[1].splitlines():
                ref, s, t = line.split(" ")
                if t == "commit" and git(p, "rev-list", "-n1", s, "--not", "--remotes=origin")[1]:
                    c["unpushed_tips"].append({"ref": ref, "sha": s})
        elif kind == "LINKED_WORKTREE" and c.get("admin_dir"):
            c["reflog_only"] = reflog_only_admin(c["canonical"], c["admin_dir"])
        rc, ign, _ = git(p, "ls-files", "-z", "-o", "-i", "--exclude-standard", "--directory", raw=True)
        classify_ignored(c, p, [x.decode("utf-8", "surrogateescape") for x in ign.split(b"\0") if x])
        for rel in c["dirty"]["untracked"] + c["dirty"]["tracked"]:
            fp = os.path.join(p, rel)
            if os.path.isfile(fp) and not is_regen(rel):
                if os.path.getsize(fp) > BIG:
                    c["big_files"].append({"path": rel, "size": os.path.getsize(fp), "sha256": sha256_file(fp)})
                elif is_secret(fp, rel):
                    c["secrets"].append({"path": rel, "sha256": sha256_file(fp), "class": "UNKNOWN_SECRET", "where": "worktree"})
    elif kind == "PRUNABLE_RECORD" and c.get("admin_dir"):
        a = c["admin_dir"]
        c["head"] = read_admin_head(c["canonical"], a)
        c["reflog_only"] = reflog_only_admin(c["canonical"], a)
    elif kind in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE") and os.path.isdir(p):
        files = walk_files(p)
        c["dirty"]["untracked"] = files
        for rel in files:
            fp = os.path.join(p, rel)
            if os.path.islink(fp):
                continue
            if os.path.getsize(fp) > BIG:
                c["big_files"].append({"path": rel, "size": os.path.getsize(fp), "sha256": sha256_file(fp)})
            elif is_secret(fp, rel):
                c["secrets"].append({"path": rel, "sha256": sha256_file(fp), "class": "UNKNOWN_SECRET", "where": "worktree"})
    try:
        c["size_bytes"] = int(subprocess.run(["du", "-sk", p], capture_output=True, text=True).stdout.split()[0]) * 1024 if os.path.isdir(p) else 0
    except (IndexError, ValueError):
        c["size_bytes"] = 0


def classify_ignored(c, p, entries):
    for rel in entries:
        full = os.path.join(p, rel)
        relp = rel.rstrip("/")
        if is_regen(relp + "/x") or os.path.basename(relp) in REGEN_DIRS or is_regen(relp):
            continue
        if rel.endswith("/"):
            if os.path.exists(os.path.join(full, ".git")):
                continue
            for f in walk_files(full):
                sub = os.path.join(relp, f)
                if not is_regen(sub):
                    record_ignored(c, p, sub)
        else:
            record_ignored(c, p, relp)


def record_ignored(c, p, rel):
    fp = os.path.join(p, rel)
    if os.path.islink(fp) or not os.path.isfile(fp):
        return
    size = os.path.getsize(fp)
    if is_secret(fp, rel):
        c["secrets"].append({"path": rel, "sha256": sha256_file(fp), "class": "UNKNOWN_SECRET", "where": "ignored"})
    elif size > EVIDENCE_MAX:
        c["big_files"].append({"path": rel, "size": size, "sha256": sha256_file(fp), "ignored": True})
    else:
        c["ignored_evidence"].append({"path": rel, "size": size})


def read_admin_head(k, a):
    fp = os.path.join(a, "HEAD")
    if not os.path.exists(fp):
        return None
    with open(fp) as f:
        h = f.read().strip()
    if h.startswith("ref:"):
        rc, s, _ = git(k, "rev-parse", "--verify", "-q", h.split(":", 1)[1].strip())
        return s if rc == 0 else None
    return h


def reflog_only_admin(k, a):
    fp = os.path.join(a, "logs", "HEAD")
    if not os.path.exists(fp):
        return []
    shas = set()
    with open(fp, errors="replace") as f:
        for line in f:
            parts = line.split(" ")
            if len(parts) > 1 and re.fullmatch(r"[0-9a-f]{40}", parts[1]) and parts[1] != ZERO:
                shas.add(parts[1])
    return sorted(s for s in shas if git(k, "cat-file", "-e", s + "^{commit}")[0] == 0 and git(k, "rev-list", "-n1", s, "--not", "--all")[1])


def reflog_only_clone(p):
    shas = set()
    rc, out, _ = git(p, "reflog", "--all", "--format=%H")
    for s in out.split():
        shas.add(s)
    return sorted(s for s in shas if git(p, "rev-list", "-n1", s, "--not", "--all")[1])


# -------------------------------------------------------------------------------------------------------------- snapshots
def idx_path(name):
    d = os.path.join(SCRATCH, "idx")
    os.makedirs(d, exist_ok=True)
    p = os.path.join(d, name)
    if os.path.exists(p):
        os.remove(p)
    return p


def add_paths(repo, env, paths, gitdir=None, worktree=None):
    for i in range(0, len(paths), 2000):
        chunk = paths[i : i + 2000]
        rc, _, err = git(
            repo,
            "update-index",
            "--add",
            "--remove",
            "-z",
            "--stdin",
            env=env,
            gitdir=gitdir,
            worktree=worktree,
            input=b"\0".join(x.encode("utf-8", "surrogateescape") for x in chunk) + b"\0",
        )
        if rc:
            raise GitError(f"update-index in {repo}: {err[:300]}")


def revoked_set(scope):
    s = set()
    for r in scope.get("revoked_blobs", []):
        s.add(r)
    return s


def snapshot_git(scope, c):
    """Section 1.A: index commit IC (staged state), then stash-shaped S = tree(worktree incl. untracked non-ignored) with parents HEAD, IC.
    Objects land in the copy's own object store; the real index and working tree are never touched."""
    p = c["path"]
    head = gout(p, "rev-parse", "HEAD")
    real_index = gout(p, "rev-parse", "--path-format=absolute", "--git-path", "index")
    ii, iw = idx_path(c["copy_id"] + ".i"), idx_path(c["copy_id"] + ".w")
    if os.path.exists(real_index):
        shutil.copy2(real_index, ii)
    else:
        gout(p, "read-tree", "HEAD", env={"GIT_INDEX_FILE": ii})
    rc, itree, err = git(p, "write-tree", env={"GIT_INDEX_FILE": ii})
    if rc:
        raise GitError(f"UNMERGED_INDEX {p}: {err[:200]}")
    ic = gout(p, "commit-tree", itree, "-p", head, "-m", f"preserve(v26.9.25): index of {p} [skip ci]")
    shutil.copy2(ii, iw)
    env = {"GIT_INDEX_FILE": iw}
    nested_rel = [os.path.relpath(n, p) for n in find_nested(p)]
    gout(p, "add", "-u", "--", ".", env=env)
    rc, raw, _ = git(p, "ls-files", "-z", "-o", "--exclude-standard", raw=True, env=env)
    untracked = [x.decode("utf-8", "surrogateescape") for x in raw.split(b"\0") if x]
    add, redacted, skipped = [], [], []
    for rel in untracked:
        fp = os.path.join(p, rel)
        if is_regen(rel) or any(rel == n or rel.startswith(n + "/") for n in nested_rel):
            continue
        if not os.path.islink(fp) and os.path.isfile(fp) and os.path.getsize(fp) > BIG:
            skipped.append({"path": rel, "reason": "OVERSIZE", "sha256": sha256_file(fp)})
            continue
        if is_secret(fp, rel):
            continue
        add.append(rel)
    add_paths(p, env, add)
    # tracked secrets / revoked keys that differ from HEAD, or revoked keys anywhere: redact from the snapshot tree
    rset = revoked_set(scope)
    rc, raw, _ = git(p, "ls-files", "-z", "-s", raw=True, env=env)
    for ent in raw.split(b"\0"):
        if not ent:
            continue
        meta, rel = ent.split(b"\t", 1)
        rel = rel.decode("utf-8", "surrogateescape")
        blob = meta.split()[1].decode()
        fp = os.path.join(p, rel)
        if blob in rset or KEY_PATH.search(rel) or (rel in c["dirty"]["tracked"] and is_secret(fp, rel)):
            # perf(v26.9.25 stage 2): HEAD blob looked up only for redaction candidates (was one subprocess per tracked file)
            head_blob = git(p, "rev-parse", "--verify", "-q", f"{head}:{rel}")[1]
            cls = "REVOKED_KEY" if blob in rset else ("KEY_PATH_IN_HEAD" if blob == head_blob else "UNKNOWN_SECRET")
            redacted.append({"path": rel, "blob": blob, "sha256": sha256_file(fp) if os.path.lexists(fp) else None, "class": cls})
    if redacted:
        gout(p, "rm", "-q", "--cached", "--ignore-unmatch", "--", *[r["path"] for r in redacted], env=env)
    tree = gout(p, "write-tree", env=env)
    msg = (
        f"preserve(v26.9.25): working tree of {p} [skip ci]\n\nPreserves: tracked changes + untracked non-ignored files; "
        f"parent 1 = HEAD {head}, parent 2 = index commit.\nRedacted: {', '.join(r['path'] for r in redacted) or 'none'}\n"
        f"Skipped(oversize): {', '.join(s['path'] for s in skipped) or 'none'}\n"
    )
    s = gout(p, "commit-tree", tree, "-p", head, "-p", ic, input=msg)
    os.remove(ii)
    os.remove(iw)
    return {"head": head, "index_commit": ic, "snapshot": s, "tree": tree, "redacted": redacted, "skipped": skipped}


def snapshot_files(owner, w, parent, label, only=None):
    """Section 1.F: archive the files of W (orphan / non-git) into the owner's object store with a temporary index."""
    gd = common_dir(owner)
    ix = idx_path(slug(w) + ".f")
    env = {"GIT_INDEX_FILE": ix}
    gout(None, "read-tree", "--empty", env=env, gitdir=gd, worktree=w)
    files = only if only is not None else walk_files(w)
    add, skipped = [], []
    for rel in files:
        fp = os.path.join(w, rel)
        if not os.path.islink(fp) and os.path.getsize(fp) > BIG:
            skipped.append({"path": rel, "reason": "OVERSIZE", "sha256": sha256_file(fp)})
        elif is_secret(fp, rel):
            skipped.append({"path": rel, "reason": "SECRET", "sha256": sha256_file(fp)})
        else:
            add.append(rel)
    add_paths(None, env, add, gitdir=gd, worktree=w)
    tree = gout(None, "write-tree", env=env, gitdir=gd, worktree=w)
    args = ["commit-tree", tree] + (["-p", parent] if parent else [])
    s = gout(owner, *args, input=f"preserve(v26.9.25): {label} of {w} [skip ci]\n\nSkipped: {json.dumps(skipped)[:3000]}\n")
    os.remove(ix)
    return {"snapshot": s, "tree": tree, "skipped": skipped, "files": len(add)}


def nearest_base(owner, tree, limit=300):
    """Smallest `git diff --shortstat c T` over the owner's tips + recent commits; returns (commit, changed_paths, total_paths)."""
    total = len(gout(owner, "ls-tree", "-r", "--name-only", tree).splitlines()) or 1
    cands = set(gout(owner, "for-each-ref", "--format=%(objectname)", "refs/heads", "refs/remotes").split())
    cands |= set(git(owner, "rev-list", "--all", f"--max-count={limit}")[1].split())
    best = (None, 10**9)
    for cm in cands:
        rc, out, _ = git(owner, "diff", "--name-only", cm, tree)
        if rc:
            continue
        n = len(out.splitlines())
        if n < best[1]:
            best = (cm, n)
    return best[0], best[1], total


def set_ref(k, ref, sha):
    """compare-and-set create; same sha = idempotent skip; different sha = refusal (FREEZE violated)."""
    rc, cur, _ = git(k, "rev-parse", "--verify", "-q", ref)
    if rc == 0 and cur:
        if cur == sha:
            return "exists"
        raise GitError(f"REFUSED(FREEZE_VIOLATED): {ref} holds {cur}, new {sha}")
    gout(k, "update-ref", ref, sha, ZERO)
    return "created"


def transfer(src, k, pairs):
    """Make objects `sha` of src resolvable in k at `ref` (no-op copy when they share an object store)."""
    same = os.path.realpath(gout(src, "rev-parse", "--path-format=absolute", "--git-common-dir")) == common_dir(k)
    if same:
        for sha, ref in pairs:
            set_ref(k, ref, sha)
        return
    todo = []
    for sha, ref in pairs:
        rc, cur, _ = git(k, "rev-parse", "--verify", "-q", ref)
        if rc == 0 and cur:
            if cur != sha:
                raise GitError(f"REFUSED(FREEZE_VIOLATED): {ref} holds {cur}, new {sha}")
            continue
        todo.append(f"{sha}:{ref}")
    for i in range(0, len(todo), 200):
        gout(src, "push", "--no-verify", "--quiet", "--receive-pack=git -c core.hooksPath=/dev/null receive-pack", k, *todo[i : i + 200])


def anchor_commit(k, parents, label):
    gout(k, "mktree", input=b"")
    args = ["commit-tree", EMPTY_TREE]
    for x in parents:
        args += ["-p", x]
    return gout(
        k,
        *args,
        input=f"preserve(v26.9.25): anchor of {label} [skip ci]\n\nParents: snapshot, unpushed tips, stash entries, "
        f"reflog-only commits ({len(parents)}).\n",
    )


def preserve_copy(scope, c, rec):
    k, sl, kind = c["canonical"], c["copy_id"], c["kind"]
    base = f"{NS}/{sl}"
    refs, parents = {}, []
    if kind in ("LINKED_WORKTREE", "CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE") or kind in PRESERVE_ONLY:
        src = c["path"]
        snap = snapshot_git(scope, c)
        refs["worktree-head"] = snap["head"]
        refs["index"] = snap["index_commit"]
        refs["dirty"] = snap["snapshot"]
        parents.append(snap["snapshot"])
        rec.update(redacted=snap["redacted"], skipped=snap["skipped"], snapshot_tree=snap["tree"])
        if kind != "LINKED_WORKTREE":
            for i, s in enumerate(c["stashes"]):
                refs[f"stash/{i}"] = s
            parents += c["stashes"]
            for t in c["unpushed_tips"]:
                parents.append(t["sha"])
        parents += c["reflog_only"]
        # ignored evidence: separate commit with parent S
        if c["ignored_evidence"]:
            ig = idx_path(sl + ".g")
            env = {"GIT_INDEX_FILE": ig}
            gout(src, "read-tree", "--empty", env=env)
            add_paths(src, env, [e["path"] for e in c["ignored_evidence"]])
            t = gout(src, "write-tree", env=env)
            refs["ignored-evidence"] = gout(
                src, "commit-tree", t, "-p", snap["snapshot"], input=f"preserve(v26.9.25): ignored evidence of {src} [skip ci]\n"
            )
            os.remove(ig)
        uniq = list(dict.fromkeys(x for x in parents if x))
        refs["anchor"] = anchor_commit(src, uniq, src)
        pairs = [(v, f"{base}/{n}") for n, v in refs.items()]
        if kind != "LINKED_WORKTREE":
            for line in git(src, "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/tags", "refs/remotes", "refs/notes")[
                1
            ].splitlines():
                s, r = line.split(" ", 1)
                if r.endswith("/HEAD"):
                    continue
                pairs.append((s, f"{base}/{r[len('refs/') :]}"))
        transfer(src, k, pairs)
    elif kind == "PRUNABLE_RECORD":
        a = c["admin_dir"]
        if c["head"]:
            refs["worktree-head"] = c["head"]
            parents.append(c["head"])
        if a and os.path.exists(os.path.join(a, "index")):
            ci = idx_path(sl + ".admin")
            shutil.copy2(os.path.join(a, "index"), ci)  # write-tree may rewrite the cache-tree: never touch the admin index itself
            rc, t, err = git(k, "write-tree", env={"GIT_INDEX_FILE": ci})
            os.remove(ci)
            if rc == 0 and c["head"]:
                refs["admin-index"] = gout(k, "commit-tree", t, "-p", c["head"], input=f"preserve(v26.9.25): admin index of {c['path']} [skip ci]\n")
                parents.append(refs["admin-index"])
            else:
                rec["notes"] = [f"admin index unreadable: {err[:200]}"]
        parents += c["reflog_only"]
        uniq = list(dict.fromkeys(parents))
        if uniq:
            refs["anchor"] = anchor_commit(k, uniq, c["path"])
        for n, v in refs.items():
            set_ref(k, f"{base}/{n}", v)
    elif kind in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        owner = k
        s0 = snapshot_files(
            owner, c["path"], None, "orphan files" if kind == "ORPHAN_WORKTREE" else "non-git files", only=[f for f in c["dirty"]["untracked"]]
        )
        nb, changed, total = nearest_base(owner, s0["tree"]) if kind == "ORPHAN_WORKTREE" else (None, 0, 0)
        rec["nearest_base"] = {"commit": nb, "changed_paths": changed, "total_paths": total, "ratio": round(changed / total, 4) if total else None}
        if nb:
            snap = gout(
                owner,
                "commit-tree",
                s0["tree"],
                "-p",
                nb,
                input=f"preserve(v26.9.25): orphan files of {c['path']} [skip ci]\n\norphan-of: {'; '.join(c['notes'])}\n"
                f"nearest-base: {nb} ({changed}/{total} paths differ)\nSkipped: {json.dumps(s0['skipped'])[:3000]}\n",
            )
        else:
            snap = s0["snapshot"]
        refs["dirty"] = snap
        rec.update(skipped=s0["skipped"], snapshot_tree=s0["tree"], files=s0["files"])
        if c["ignored_evidence"]:
            g = snapshot_files(owner, c["path"], snap, "ignored evidence", only=[e["path"] for e in c["ignored_evidence"]])
            refs["ignored-evidence"] = g["snapshot"]
        refs["anchor"] = anchor_commit(owner, [snap], c["path"])
        for n, v in refs.items():
            set_ref(k, f"{base}/{n}", v)
    rec["refs"] = {f"{base}/{n}": v for n, v in refs.items()}
    rec["local_ref"] = f"{base}/anchor" if "anchor" in refs else None
    rec["sha"] = refs.get("anchor")
    return rec


def needs_remote(k, rec, c):
    """True when the anchor carries anything not already on origin beyond a trivially clean snapshot."""
    if not rec.get("sha"):
        return False
    rc, out, _ = git(k, "rev-list", rec["sha"], "--not", "--remotes=origin")
    new = [x for x in out.split() if x != rec["sha"]]
    clean = (
        (not any(c["dirty"][x] for x in ("staged", "tracked", "deleted", "untracked")))
        and not c["stashes"]
        and not c["reflog_only"]
        and not c["unpushed_tips"]
        and not [r for r in rec.get("redacted", []) if r.get("class") != "REVOKED_KEY"]
    )
    if c["kind"] == "PRUNABLE_RECORD":
        clean = not c["reflog_only"] and not git(k, "rev-list", "-n1", c.get("head") or "HEAD", "--not", "--remotes=origin")[1]
        if "admin-index" in "".join(rec.get("refs", {})):
            itree = git(k, "rev-parse", f"{rec['refs'].get(NS + '/' + c['copy_id'] + '/admin-index', 'HEAD')}^{{tree}}")[1]
            htree = git(k, "rev-parse", f"{c.get('head')}^{{tree}}")[1]
            clean = clean and itree == htree
    if c["kind"] in ("LINKED_WORKTREE", "CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE"):
        head_on_origin = not git(k, "rev-list", "-n1", c["head"], "--not", "--remotes=origin")[1]
        clean = clean and head_on_origin
    return bool(new) and not clean


def key_scan(k, tips, rset):
    """R9 scan over every object the push would add to origin."""
    hits = []
    rc, out, _ = git(k, "rev-list", "--objects", *tips, "--not", "--remotes=origin")
    objs = []
    for line in out.splitlines():
        parts = line.split(" ", 1)
        if len(parts) == 2:
            sha, path = parts
            if sha in rset:
                hits.append({"path": path, "blob": sha, "why": "REVOKED_BLOB"})
            elif KEY_PATH.search(path):
                hits.append({"path": path, "blob": sha, "why": "KEY_PATH"})
            else:
                objs.append((sha, path))
    if objs:
        inp = "\n".join(s for s, _ in objs) + "\n"
        rc, raw, _ = git(k, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)", input=inp)
        small = [
            ln.split()[0] for ln in raw.splitlines() if len(ln.split()) == 3 and ln.split()[1] == "blob" and int(ln.split()[2]) < 2 * 1024 * 1024
        ]
        paths = dict(objs)
        for s in small:
            rc, data, _ = git(k, "cat-file", "blob", s, raw=True)
            if SECRET_CONTENT.search(data):
                hits.append({"path": paths.get(s), "blob": s, "why": "SECRET_CONTENT"})
    return hits


def bundle(k, sl, refs):
    d = os.path.join(HOME, "bundles")
    os.makedirs(d, exist_ok=True)
    path = os.path.join(d, f"{sl}.bundle")
    if not os.path.exists(path):
        gout(k, "bundle", "create", path, *refs)
    rc, _, err = git(k, "bundle", "verify", path)
    return {"path": path, "sha256": sha256_file(path), "verified": rc == 0, "size": os.path.getsize(path)}


def cmd_preserve(scope, args):
    inv = jload("INVENTORY.json")
    pres = load_parts("PRESERVE", {"records": {}})
    rset = revoked_set(scope)
    mark_retired(inv)
    by_repo = {}
    for cid, c in sorted(inv["copies"].items()):
        if c.get("retired"):
            continue
        if not selected(c, args) or c["kind"] not in RETIRABLE | PRESERVE_ONLY:
            continue
        if c["kind"] in PRESERVE_ONLY and (
            not c.get("repo_id") or not (any(c["dirty"][x] for x in c["dirty"]) or c["unpushed_tips"] or c["stashes"])
        ):
            continue
        if cid in pres["records"] and pres["records"][cid].get("ok"):
            if not args.supersede:
                continue
            old = pres["records"][cid]
            n = 1 + sum(1 for x in old.get("superseded", []))
            moved = {}
            for ref, sha in (old.get("refs") or {}).items():
                new_ref = ref.replace(f"{NS}/{cid}/", f"{NS}/{cid}/superseded-{n}/", 1)
                gout(old["canonical"], "update-ref", new_ref, sha, ZERO)
                gout(old["canonical"], "update-ref", "-d", ref, sha)
                moved[new_ref] = sha
            c["superseded"] = old.get("superseded", []) + [
                {
                    "n": n,
                    "refs": moved,
                    "remote_ref": old.get("remote_ref"),
                    "remote_verified_sha": old.get("remote_verified_sha"),
                    "reason": args.supersede,
                }
            ]
        by_repo.setdefault(c["writer_queue"], []).append(c)
    for repo, cs in by_repo.items():
        with Lock(repo):
            for c in cs:
                rec = {
                    "copy_id": c["copy_id"],
                    "path": c["path"],
                    "kind": c["kind"],
                    "repo_id": repo,
                    "canonical": c["canonical"],
                    "remote_ref": None,
                    "remote_verified_sha": None,
                    "local_only_reason": None,
                    "redacted": [],
                    "bundle": None,
                    "superseded": c.pop("superseded", []),
                }
                try:
                    if not c["canonical"] or not os.path.isdir(c["canonical"]):
                        raise GitError(f"OWNER_UNRESOLVED: canonical for {repo} absent")
                    preserve_copy(scope, c, rec)
                    rec["ok"] = True
                except (GitError, OSError, subprocess.SubprocessError) as e:
                    rec["ok"] = False
                    rec["error"] = str(e)[:600]
                pres["records"][c["copy_id"]] = rec
                save_part("PRESERVE", repo, {"records": {x["copy_id"]: pres["records"][x["copy_id"]] for x in cs if x["copy_id"] in pres["records"]}})
                ledger(
                    {
                        "repo": repo,
                        "step": f"preserve {c['copy_id']}",
                        "precondition": "copy frozen (fingerprint recorded at inventory)",
                        "forward": f"snapshot + update-ref {NS}/{c['copy_id']}/*",
                        "postcondition": "anchor ref resolves in canonical",
                        "falsifier": "ref missing or points elsewhere",
                        "rollback": f"git update-ref -d {NS}/{c['copy_id']}/<name>",
                        "rollback_subject": rec.get("sha"),
                        "ok": rec["ok"],
                        "evidence": rec.get("error") or rec.get("sha"),
                    },
                    stop=False,
                )
    if args.push:
        push_all(scope, inv, pres, rset, args)


def push_all(scope, inv, pres, rset, args):
    by_repo = {}
    for cid, rec in pres["records"].items():
        c = inv["copies"].get(cid)
        if not c or not rec.get("ok") or not selected(c, args) or rec.get("remote_verified_sha") or rec.get("bundle"):
            continue
        by_repo.setdefault(rec["repo_id"], []).append((c, rec))
    for repo, items in by_repo.items():
        k = items[0][0]["canonical"]
        origin = norm_origin(git(k, "remote", "get-url", "origin")[1])
        pushes = []
        for c, rec in items:
            if not needs_remote(k, rec, c):
                rec["remote_ref"] = "origin (contains)"
                rec["remote_verified_sha"] = None
                rec["durable"] = "ALREADY_ON_ORIGIN"
                continue
            reason = None
            if not owned(scope, origin) or c.get("foreign"):
                reason = "FOREIGN_REMOTE"
            elif repo in scope["no_push_repos"]:
                reason = "LANE_REFS_ONLY"
            else:
                hits = key_scan(k, [rec["sha"]], rset)
                if hits:
                    reason = "REVOKED_KEY_ANCESTRY" if any(h["why"] == "REVOKED_BLOB" for h in hits) else "SECRET_IN_HISTORY"
                    rec["scan_hits"] = hits[:20]
            if reason:
                rec["local_only_reason"] = reason
                rec["bundle"] = bundle(
                    k,
                    c["copy_id"],
                    [rec["local_ref"], "--not", "--remotes=origin"]
                    if git(k, "rev-list", "-n1", rec["local_ref"], "--not", "--remotes=origin")[1]
                    else [rec["local_ref"]],
                )
                continue
            name = f"{REMOTE_PREFIX}{c['copy_id']}"
            rc, cur, _ = git(k, "ls-remote", "origin", f"refs/heads/{name}")
            if cur and cur.split()[0] != rec["sha"]:
                name = f"{name}-{rec['sha'][:10]}"
            pushes.append((c, rec, name))
        for i in range(0, len(pushes), 50):
            chunk = pushes[i : i + 50]
            specs = [f"{rec['sha']}:refs/heads/{name}" for _, rec, name in chunk]
            rc, out, err = git(k, "push", "--atomic", "--no-verify", "origin", *specs)
            rc2, ls, _ = git(k, "ls-remote", "origin", *[f"refs/heads/{n}" for _, _, n in chunk])
            remote = {l.split("\t")[1][len("refs/heads/") :]: l.split("\t")[0] for l in ls.splitlines() if "\t" in l}
            for c, rec, name in chunk:
                rec["remote_ref"] = name
                rec["remote_verified_sha"] = remote.get(name)
                rec["durable"] = "REMOTE" if remote.get(name) == rec["sha"] else "PUSH_FAILED"
            ledger(
                {
                    "repo": repo,
                    "step": f"push {len(chunk)} backup refs",
                    "precondition": "R9 scan clean for every pushed anchor",
                    "forward": f"git push --atomic origin <anchor>:refs/heads/{REMOTE_PREFIX}<slug> x{len(chunk)}",
                    "postcondition": "ls-remote shows each backup ref at its anchor sha",
                    "falsifier": "a backup ref absent or at another sha",
                    "rollback": f"git push origin --delete {REMOTE_PREFIX}<slug> (operator)",
                    "rollback_subject": chunk[0][1]["sha"],
                    "ok": rc == 0 and all(r["durable"] == "REMOTE" for _, r, _ in chunk),
                    "evidence": (err or out)[-300:],
                },
                stop=False,
            )
        # ignored evidence: local-only + bundle
        for c, rec in items:
            ie = rec.get("refs", {}).get(f"{NS}/{c['copy_id']}/ignored-evidence")
            if ie and not rec.get("ignored_bundle"):
                rec["ignored_bundle"] = bundle(k, c["copy_id"] + "-ignored", [f"{NS}/{c['copy_id']}/ignored-evidence", "--not", "--remotes=origin"])
        save_part("PRESERVE", repo, {"records": {cc["copy_id"]: rr for cc, rr in items}})


# ------------------------------------------------------------------------------------------------------------------- locks
class Lock:
    held = set()

    def __init__(self, repo):
        self.repo = repo or "_none"
        self.path = os.path.join(HOME, "locks", f"{self.repo}.lock")

    def __enter__(self):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            with open(self.path) as f:
                pid = f.read().strip()
            if pid.isdigit() and not pid_alive(int(pid)):
                os.remove(self.path)
                fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            else:
                raise StepFailed(f"LOCK_HELD by {pid}: {self.path}")
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
        Lock.held.add(self.repo)
        return self

    def __exit__(self, *a):
        Lock.held.discard(self.repo)
        if os.path.exists(self.path):
            os.remove(self.path)


def pid_alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except OSError:
        return False


def live_cwds():
    p = subprocess.run(["lsof", "-a", "-d", "cwd", "-Fn"], capture_output=True, text=True)
    return sorted({l[1:] for l in p.stdout.splitlines() if l.startswith("n")})


# ------------------------------------------------------------------------------------------------------------------- gate
RETIRABLE = {"LINKED_WORKTREE", "PRUNABLE_RECORD", "ORPHAN_WORKTREE", "CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE", "NONGIT_RESIDUE"}
PRESERVE_ONLY = {"SUBMODULE_ACTIVE", "VENDORED_BUILD_INPUT", "EMBEDDED_UNDECLARED"}


def retirable(c):
    """finish: a declared-but-active submodule (V1 SUBMODULE_ACTIVE) is retired only under an operator signoff that sets
    retire_mode=deinit (checkout moved to Trash, empty gitlink directory left: the `git submodule deinit` shape)."""
    return c["kind"] in RETIRABLE or (c["kind"] == "SUBMODULE_ACTIVE" and c.get("retire_mode") == "deinit")


KEEP_KINDS = {
    "CANONICAL",
    "SUBMODULE",
    "EMBEDDED_UNDECLARED",
    "VENDORED_BUILD_INPUT",
    "DEGENERATE_GIT_RESIDUE",
    "FIXTURE",
    "SUBMODULE_ACTIVE",
    "FOREIGN_CLONE",
}


def blob_of(repo, path, gitdir=None, worktree=None):
    if os.path.islink(path):
        return gout(None, "hash-object", "--stdin", input=os.readlink(path).encode())
    return gout(repo, "hash-object", "--", path, gitdir=gitdir, worktree=worktree)


def tree_map(repo, rev):
    rc, raw, _ = git(repo, "ls-tree", "-r", "-z", "--full-tree", rev, raw=True)
    res = {}
    for ent in raw.split(b"\0"):
        if ent:
            meta, p = ent.split(b"\t", 1)
            res[p.decode("utf-8", "surrogateescape")] = meta.split()[2].decode()
    return res


def hash_many(repo, root, rels, gitdir=None, worktree=None):
    """git blob ids of files (symlinks hashed as link text), filters applied as `git add` would."""
    res, reg = {}, []
    for r in rels:
        fp = os.path.join(root, r)
        if os.path.islink(fp):
            data = os.readlink(fp).encode()
            res[r] = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
        elif os.path.isfile(fp):
            reg.append(r)
    for i in range(0, len(reg), 2000):
        chunk = reg[i : i + 2000]
        rc, out, err = git(
            repo, "hash-object", "--stdin-paths", input="\n".join(os.path.join(root, r) for r in chunk) + "\n", gitdir=gitdir, worktree=worktree
        )
        if rc:
            raise GitError(f"hash-object: {err[:200]}")
        for r, h in zip(chunk, out.splitlines()):
            res[r] = h
    return res


class Gate:
    def __init__(self, scope, inv, pres, drill=None, run_id=None):
        self.scope, self.inv, self.pres, self.drill = scope, inv, pres, drill or {}
        self.rset = revoked_set(scope)
        self.cwds = None
        self.run_id = run_id
        self.cache = {}

    def check(self, cid):
        c = self.inv["copies"][cid]
        rec = self.pres["records"].get(cid) or {}
        failed, ev = [], {}
        for rule in RULES:
            try:
                ok, e = rule(self, c, rec)
            except (GitError, OSError, KeyError, ValueError, TypeError) as x:
                ok, e = False, f"exception: {x}"[:300]
            if not ok:
                failed.append(rule.__name__.split("_")[0])
                ev[rule.__name__] = e
            elif rule is R16_SECRET_UNPRESERVABLE and c.get("secret_trash"):
                ev[rule.__name__] = e
        return {
            "copy_id": cid,
            "path": c["path"],
            "verdict": "PASS" if not failed else "REFUSED",
            "failed_rules": failed,
            "refusal": None if not failed else f"REFUSED(UNREVERSIBLE_CLEANUP:{','.join(failed)})",
            "evidence": ev,
            "fingerprint_at_gate": fingerprint(c),
        }


def R1_FROZEN(g, c, rec):
    f = fingerprint(c)
    return f == c["fingerprint"], {"inventory": c["fingerprint"], "now": f}


def R2_REF_RESOLVES(g, c, rec):
    if not rec.get("ok"):
        return False, "no successful preserve record"
    k = c["canonical"]
    bad = [r for r, s in rec.get("refs", {}).items() if git(k, "rev-parse", "--verify", "-q", r)[1] != s]
    if c["kind"] in ("CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE") and os.path.isdir(c["path"]):
        for line in git(c["path"], "for-each-ref", "--format=%(objectname) %(refname)", "refs/heads", "refs/tags", "refs/remotes", "refs/notes")[
            1
        ].splitlines():
            s, r = line.split(" ", 1)
            if r.endswith("/HEAD"):
                continue
            if git(k, "rev-parse", "--verify", "-q", f"{NS}/{c['copy_id']}/{r[len('refs/') :]}")[1] != s:
                bad.append(r)
    if c["kind"] in ("LINKED_WORKTREE", "PRUNABLE_RECORD", "CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE") and c.get("head"):
        wh = rec.get("refs", {}).get(f"{NS}/{c['copy_id']}/worktree-head")
        if wh != c["head"]:
            bad.append(f"worktree-head {wh} != {c['head']}")
    return not bad, bad[:10]


def R3_COMMIT_REACHABLE(g, c, rec):
    k = c["canonical"]
    tips = [x for x in [c.get("head")] + c["stashes"] + c["reflog_only"] + [t["sha"] for t in c["unpushed_tips"]] if x]
    if c["kind"] in ("CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE") and os.path.isdir(c["path"]):
        tips += git(c["path"], "for-each-ref", "--format=%(objectname)", "refs")[1].split()
    tips = [t for t in dict.fromkeys(tips) if git(k, "cat-file", "-t", t)[1] in ("commit", "tag")]
    missing = [t for t in dict.fromkeys([x for x in [c.get("head")] + c["stashes"] + c["reflog_only"] if x]) if git(k, "cat-file", "-e", t)[0] != 0]
    if not tips:
        return not missing, {"missing_in_canonical": missing}
    rc, out, _ = git(k, "rev-list", "-n5", *tips, "--not", f"--glob={NS}/*", "--remotes=origin")
    return rc == 0 and not out and not missing, {"unreachable": out.split()[:5], "missing_in_canonical": missing}


def _exempt(g, c, rel, rec):
    for r in rec.get("redacted", []):
        if r["path"] == rel and (r["blob"] in g.rset or r.get("class") == "KEY_PATH_IN_HEAD" or dedup_secret(c, rel, r.get("sha256"))):
            return True
    return False


def dedup_secret(c, rel, sha):
    """A secret is not lost by retiring the copy when the canonical checkout holds the byte-identical file at the same path, or
    the canonical object store already holds the identical blob (it is in the repository's history)."""
    # finish: a copy archived into a host repo under a CANONICAL_MAP signoff is also checked against its identity's canonical
    for k in [x for x in (c.get("canonical"), c.get("identity_canonical")) if x]:
        fp = os.path.join(k, rel)
        if sha and os.path.isfile(fp) and sha256_file(fp) == sha:
            return True
        live = os.path.join(c["path"], rel)
        if os.path.isfile(live) and not os.path.islink(live):
            with open(live, "rb") as f:
                data = f.read()
            blob = hashlib.sha1(b"blob %d\0" % len(data) + data).hexdigest()
            if (not sha or hashlib.sha256(data).hexdigest() == sha) and git(k, "cat-file", "-e", blob)[0] == 0:
                return True
    return False


def R4_DIRTY_ARCHIVED(g, c, rec):
    if c["kind"] == "PRUNABLE_RECORD":
        return True, "no working tree"
    if not rec.get("refs"):
        return False, "no snapshot"
    k, p = c["canonical"], c["path"]
    snap = rec["refs"].get(f"{NS}/{c['copy_id']}/dirty")
    if not snap:
        return False, "no dirty ref"
    tm = tree_map(k, snap)
    skipped = {s["path"] for s in rec.get("skipped", [])}
    bad = []
    if c["kind"] in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        files = walk_files(p) if os.path.isdir(p) else []
        gd = common_dir(k)
        hs = hash_many(None, p, [f for f in files if f not in skipped], gitdir=gd, worktree=p)
        for f, h in hs.items():
            if tm.get(f) != h:
                bad.append(f)
        extra = set(tm) - set(files)
        return not bad and not extra, {"mismatch": bad[:10], "extra_in_snapshot": sorted(extra)[:10]}
    st = parse_status_z(git(p, "status", "--porcelain=v2", "-z", "--untracked-files=all", "--ignore-submodules=none", raw=True)[1])
    nested = [os.path.relpath(n, p) for n in find_nested(p)]
    check = []
    for e in st:
        rel = e["path"]
        if any(rel == n or rel.startswith(n + "/") for n in nested) or e.get("mode_w") == "160000" or e["sub"].startswith("S"):
            continue
        if e["xy"] == "??" and is_regen(rel):
            continue
        if rel in skipped or _exempt(g, c, rel, rec):
            continue
        fp = os.path.join(p, rel)
        if not os.path.lexists(fp):
            if rel in tm:
                bad.append(f"deleted-but-in-snapshot:{rel}")
        else:
            if e["xy"] == "??" and is_secret(fp, rel):
                continue  # R16 owns unarchived secrets
            check.append(rel)
    hs = hash_many(p, p, check)
    bad += [r for r in check if tm.get(r) != hs.get(r)]
    # staged state: tree of a copy of the live index == snap^2 tree
    real_index = gout(p, "rev-parse", "--path-format=absolute", "--git-path", "index")
    ii = idx_path(c["copy_id"] + ".r4")
    if os.path.exists(real_index):
        shutil.copy2(real_index, ii)
        itree = git(p, "write-tree", env={"GIT_INDEX_FILE": ii})[1]
        os.remove(ii)
    else:
        itree = git(p, "rev-parse", "HEAD^{tree}")[1]
    stree = git(k, "rev-parse", f"{snap}^2^{{tree}}")[1]
    if itree != stree:
        bad.append(f"index tree {itree} != snapshot^2 {stree}")
    return not bad, bad[:10]


def R5_IGNORED_EVIDENCE(g, c, rec):
    if not c["ignored_evidence"]:
        return True, "none"
    k, p = c["canonical"], c["path"]
    ie = rec.get("refs", {}).get(f"{NS}/{c['copy_id']}/ignored-evidence")
    if not ie:
        return False, "ignored evidence not archived"
    tm = tree_map(k, ie)
    rels = [e["path"] for e in c["ignored_evidence"] if os.path.lexists(os.path.join(p, e["path"]))]
    if c["kind"] in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        hs = hash_many(None, p, rels, gitdir=common_dir(k), worktree=p)
    else:
        hs = hash_many(p, p, rels)
    bad = [r for r in rels if tm.get(r) != hs.get(r)]
    # anything ignored now that was not inventoried (new evidence since inventory)
    if c["kind"] not in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE") and os.path.isdir(p):
        probe = {"ignored_evidence": [], "secrets": [], "big_files": []}
        rc, ign, _ = git(p, "ls-files", "-z", "-o", "-i", "--exclude-standard", "--directory", raw=True)
        classify_ignored(probe, p, [x.decode("utf-8", "surrogateescape") for x in ign.split(b"\0") if x])
        bad += [e["path"] for e in probe["ignored_evidence"] if e["path"] not in tm]
    return not bad, bad[:10]


def R6_STASH(g, c, rec):
    anchor = rec.get("sha")
    want = list(c["stashes"]) + list(c["reflog_only"])
    if c["kind"] in ("CLONE", "NESTED_SELF_CLONE", "FOREIGN_LINKED_WORKTREE") and os.path.isdir(c["path"]):
        want += git(c["path"], "stash", "list", "--format=%H")[1].split()
    want = list(dict.fromkeys(want))
    if not want:
        return True, "none"
    if not anchor:
        return False, "no anchor"
    parents = set(git(c["canonical"], "rev-list", "--parents", "-n1", anchor)[1].split()[1:])
    miss = [s for s in want if s not in parents]
    return not miss, miss[:10]


def R7_SNAPSHOT_FRESH(g, c, rec):
    if c["kind"] == "PRUNABLE_RECORD":
        return True, "no working tree"
    if c["kind"] in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        return True, "covered by R4 file-by-file equality (orphan snapshot has no index)"
    if not rec.get("snapshot_tree"):
        return False, "no snapshot"
    again = snapshot_git(g.scope, c)
    return again["tree"] == rec["snapshot_tree"], {"preserved": rec["snapshot_tree"], "now": again["tree"]}


def R8_REMOTE_DURABLE(g, c, rec):
    if rec.get("durable") == "ALREADY_ON_ORIGIN":
        return True, "tip already on origin"
    if rec.get("remote_verified_sha") and rec["remote_verified_sha"] == rec.get("sha"):
        k = c["canonical"]
        rc, ls, _ = git(k, "ls-remote", "origin", f"refs/heads/{rec['remote_ref']}")
        return bool(ls) and ls.split()[0] == rec["sha"], {"ls_remote": ls[:80]}
    b = rec.get("bundle")
    if rec.get("local_only_reason") and b and b.get("verified") and os.path.exists(b["path"]) and sha256_file(b["path"]) == b["sha256"]:
        return True, {"local_only_reason": rec["local_only_reason"], "bundle": b["path"]}
    return False, "no remote backup, no verified bundle"


def R9_NO_KEY_MATERIAL_PUSHED(g, c, rec):
    if not rec.get("remote_verified_sha"):
        return True, "nothing pushed"
    k = c["canonical"]
    hits = []
    for line in git(k, "ls-tree", "-r", rec["sha"])[1].splitlines():
        meta, path = line.split("\t", 1)
        if meta.split()[2] in g.rset or KEY_PATH.search(path):
            hits.append(path)
    snap = rec.get("refs", {}).get(f"{NS}/{c['copy_id']}/dirty")
    if snap:
        for line in git(k, "ls-tree", "-r", snap)[1].splitlines():
            meta, path = line.split("\t", 1)
            if meta.split()[2] in g.rset or KEY_PATH.search(path):
                hits.append(path)
    hits += [h["path"] for h in key_scan(k, [rec["sha"]], g.rset)]
    return not hits, hits[:10]


def R10_NOT_CANONICAL_OR_PINNED(g, c, rec):
    if not retirable(c):
        return False, f"kind {c['kind']} is never retired"
    p = os.path.realpath(c["path"])
    for k in list(g.scope["canonicals"].values()) + list(g.scope.get("canonical_map", {}).values()):
        rk = os.path.realpath(k)
        if p == rk or (rk + os.sep).startswith(p + os.sep):
            return False, f"is or contains canonical {k}"
    return True, "ok"


def R11_NO_NESTED_UNGATED(g, c, rec):
    if c["kind"] == "PRUNABLE_RECORD" or not os.path.isdir(c["path"]):
        return True, "none"
    known = {o["path"]: o for o in g.inv["copies"].values()}
    bad = []
    for n in find_nested(c["path"]):
        o = known.get(n)
        if not o:
            bad.append(f"uninventoried {n}")
        elif o["kind"] in ("SUBMODULE", "DEGENERATE_GIT_RESIDUE"):
            continue
        elif g.cache.get(o["copy_id"], {}).get("verdict") != "PASS":
            bad.append(f"nested not PASS {n}")
    return not bad, bad[:10]


def R12_ROLLBACK_QUALIFIED(g, c, rec):
    d = g.drill.get(c["copy_id"]) or {}
    same_repo = [
        g.drill.get(x) for x, o in g.inv["copies"].items() if o.get("writer_queue") == c["writer_queue"] and isinstance(g.drill.get(x), dict)
    ]
    repo_ok = all(x.get("ok") for x in same_repo if x.get("run_id") == g.run_id)
    return bool(d.get("ok")) and d.get("run_id") == g.run_id and repo_ok, {"drill": d.get("ok"), "run": d.get("run_id"), "repo_all_ok": repo_ok}


def R13_LOCK_HELD(g, c, rec):
    return (c["writer_queue"] or "_none") in Lock.held, sorted(Lock.held)


def R14_NOT_LIVE(g, c, rec):
    if c.get("locked"):
        return False, "worktree locked"
    if g.cwds is None:
        g.cwds = live_cwds()
    p = os.path.realpath(c["path"])
    live = [x for x in g.cwds if os.path.realpath(x) == p or os.path.realpath(x).startswith(p + os.sep)]
    return not live, live[:5]


def R15_SIZE(g, c, rec):
    bad = []
    k = c["canonical"]
    for b in c["big_files"]:
        if is_regen(b["path"]):
            continue
        ok = False
        for rv in (rec.get("refs") or {}).values():
            rc, blob, _ = git(k, "rev-parse", "--verify", "-q", f"{rv}:{b['path']}")
            if rc == 0:
                ok = True
        if not ok:
            bad.append(f"{b['path']} ({b['size']} bytes, sha256 {b['sha256'][:12]})")
    return not bad, bad[:10]


def R16_SECRET_UNPRESERVABLE(g, c, rec):
    bad = []
    for s in c["secrets"]:
        fp = os.path.join(c["path"], s["path"])
        if not os.path.lexists(fp):
            continue
        blob = blob_of(c["path"], fp) if c["kind"] not in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE") else gout(None, "hash-object", "--", fp)
        if blob in g.rset or dedup_secret(c, s["path"], s["sha256"]):
            continue
        bad.append(s["path"])
    for r in rec.get("redacted", []):
        if r["blob"] not in g.rset and r.get("class") != "KEY_PATH_IN_HEAD" and not dedup_secret(c, r["path"], r.get("sha256")):
            bad.append("redacted:" + r["path"])
    if bad and c.get("secret_trash"):
        # finish: operator signoff -- the whole copy moves to ~/.Trash, so the unarchivable secret files survive there (reversible,
        # nothing lost); they are recorded by sha256 only (path digest + content digest), never by content
        rec_ = []
        for rel in dict.fromkeys(x.split(":", 1)[-1] for x in bad):
            fp = os.path.join(c["path"], rel)
            rec_.append(
                {
                    "path_sha256": hashlib.sha256(rel.encode()).hexdigest(),
                    "content_sha256": sha256_file(fp) if os.path.isfile(fp) else None,
                }
            )
        return all(x["content_sha256"] for x in rec_), {"secret_trash": c["secret_trash"], "secrets": rec_}
    return not bad, bad[:10]


def R17_OWNER_RESOLVED(g, c, rec):
    if c.get("blocked"):
        return False, c["blocked"].get("reason")
    if not c.get("canonical") or not os.path.isdir(c["canonical"]):
        return False, "owner canonical unresolved"
    if c["kind"] in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE") or c.get("foreign"):
        if not c.get("signed_off", True):
            return False, "owner not signed off"
    nb = rec.get("nearest_base") or {}
    signed_hosts = [p for p in g.scope.get("host_signoff", []) if c["path"].startswith(p["path"])]
    if signed_hosts:
        return True, {"owner": c["repo_id"], "host_signoff": signed_hosts[0]["grant"], "nearest_base": nb}
    if c["kind"] == "ORPHAN_WORKTREE" and not c.get("foreign") and (nb.get("ratio") is None or nb["ratio"] > 0.05):
        return False, f"FOREIGN by content: nearest-base ratio {nb.get('ratio')} > 0.05 and no operator-signed foreign host"
    return True, c["repo_id"]


RULES = [
    R1_FROZEN,
    R2_REF_RESOLVES,
    R3_COMMIT_REACHABLE,
    R4_DIRTY_ARCHIVED,
    R5_IGNORED_EVIDENCE,
    R6_STASH,
    R7_SNAPSHOT_FRESH,
    R8_REMOTE_DURABLE,
    R9_NO_KEY_MATERIAL_PUSHED,
    R10_NOT_CANONICAL_OR_PINNED,
    R11_NO_NESTED_UNGATED,
    R12_ROLLBACK_QUALIFIED,
    R13_LOCK_HELD,
    R14_NOT_LIVE,
    R15_SIZE,
    R16_SECRET_UNPRESERVABLE,
    R17_OWNER_RESOLVED,
]


def gate_order(inv, cids):
    """nested copies first so R11 can read their verdicts."""
    return sorted(cids, key=lambda x: -inv["copies"][x]["path"].count("/"))


def selected(c, args):
    if getattr(args, "only", None) and args.only not in c["path"]:
        return False
    if getattr(args, "repo", None) and c.get("writer_queue") != args.repo:
        return False
    return True


# ------------------------------------------------------------------------------------------------------------------ drill
def drill_copy(scope, c, rec, run_id):
    """Section 8: archive the snapshot into scratch and demand 100% byte equality with the live copy (no extras);
    staged state equal to snapshot^2; redacted set exactly the declared one."""
    k, p, sl = c["canonical"], c["path"], c["copy_id"]
    res = {"copy_id": sl, "run_id": run_id, "at": now()}
    if c["kind"] == "PRUNABLE_RECORD":
        a = c.get("admin_dir")
        ai = rec.get("refs", {}).get(f"{NS}/{sl}/admin-index")
        ok = True
        if a and os.path.exists(os.path.join(a, "index")) and ai:
            ci = idx_path(sl + ".admin-drill")
            shutil.copy2(os.path.join(a, "index"), ci)
            t = git(k, "write-tree", env={"GIT_INDEX_FILE": ci})[1]
            os.remove(ci)
            ok = t == git(k, "rev-parse", f"{ai}^{{tree}}")[1]
        res.update(ok=ok and bool(rec.get("ok")), mode="admin-index tree equality", files=0)
        return res
    snap = rec.get("refs", {}).get(f"{NS}/{sl}/dirty")
    if not snap:
        res.update(ok=False, why="no snapshot")
        return res
    dst = os.path.join(SCRATCH, "drill", sl)
    if os.path.exists(dst):
        shutil.rmtree(dst)  # scratch drill tree only (our own extraction), never a copy
    os.makedirs(dst)
    arch = subprocess.Popen(["git", "-C", k, "archive", "--format=tar", snap], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    tx = subprocess.run(["tar", "-x", "-f", "-", "-C", dst], stdin=arch.stdout, capture_output=True)
    arch.stdout.close()
    arch.wait()
    if arch.returncode or tx.returncode:
        res.update(ok=False, why=(arch.stderr.read().decode() + tx.stderr.decode())[:300])
        return res
    restored = set(walk_all(dst))
    skipped = {s["path"] for s in rec.get("skipped", [])}
    redacted = {r["path"] for r in rec.get("redacted", [])}
    if c["kind"] in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        live = set(walk_files(p)) - skipped - redacted
    else:
        nested = [os.path.relpath(n, p) for n in find_nested(p)]
        rc, raw, _ = git(p, "ls-files", "-z", "--cached", "--others", "--exclude-standard", raw=True)
        live = set()
        gitlinks = set(x.split("\t", 1)[1] for x in git(p, "ls-files", "-s")[1].splitlines() if x.startswith("160000 "))
        for x in raw.split(b"\0"):
            if not x:
                continue
            r = x.decode("utf-8", "surrogateescape")
            fp = os.path.join(p, r)
            if r in gitlinks or any(r == n or r.startswith(n + "/") for n in nested):
                continue
            if not os.path.lexists(fp) or (os.path.isdir(fp) and not os.path.islink(fp)):
                continue
            if r in skipped or r in redacted:
                continue
            if is_regen(r) and r not in tree_map_cache(k, snap):
                continue
            if is_secret(fp, r) and r not in tree_map_cache(k, snap):
                continue
            live.add(r)
    mism = []
    for r in sorted(live & restored):
        a, b = os.path.join(p, r), os.path.join(dst, r)
        if os.path.islink(a) != os.path.islink(b):
            mism.append(r)
        elif os.path.islink(a):
            if os.readlink(a) != os.readlink(b):
                mism.append(r)
        elif sha256_file(a) != sha256_file(b):
            mism.append(r)
    if mism:
        # LFS (v26.9.25 stage 2): a copy whose worktree holds unsmudged pointer files is snapshotted as pointer blobs; `git archive`
        # smudges them from the canonical's LFS store, so the default extraction differs in bytes. Re-extract with LFS smudge disabled
        # and demand byte equality against that raw extraction for exactly the mismatched files (still 100% byte-exact, never waived).
        raw_dst = dst + ".raw"
        if os.path.exists(raw_dst):
            shutil.rmtree(raw_dst)
        os.makedirs(raw_dst)
        arch2 = subprocess.Popen(
            [
                "git",
                "-c",
                "filter.lfs.smudge=cat",
                "-c",
                "filter.lfs.process=",
                "-c",
                "filter.lfs.required=false",
                "-C",
                k,
                "archive",
                "--format=tar",
                snap,
                "--",
                *mism,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        tx2 = subprocess.run(["tar", "-x", "-f", "-", "-C", raw_dst], stdin=arch2.stdout, capture_output=True)
        arch2.stdout.close()
        arch2.wait()
        if not arch2.returncode and not tx2.returncode:
            still = []
            for r in mism:
                a, b = os.path.join(p, r), os.path.join(raw_dst, r)
                if os.path.islink(a) or not os.path.isfile(b) or sha256_file(a) != sha256_file(b):
                    still.append(r)
            if len(still) < len(mism):
                res["lfs_raw_equal"] = len(mism) - len(still)
            mism = still
    missing = sorted(live - restored)
    extra = sorted(restored - live)
    ok = not mism and not missing and not extra
    if c["kind"] not in ("ORPHAN_WORKTREE", "NONGIT_RESIDUE"):
        real_index = gout(p, "rev-parse", "--path-format=absolute", "--git-path", "index")
        ii = idx_path(sl + ".drill")
        if os.path.exists(real_index):
            shutil.copy2(real_index, ii)
            itree = git(p, "write-tree", env={"GIT_INDEX_FILE": ii})[1]
            os.remove(ii)
        else:
            itree = git(p, "rev-parse", "HEAD^{tree}")[1]
        if itree != git(k, "rev-parse", f"{snap}^2^{{tree}}")[1]:
            ok = False
            res["index_mismatch"] = True
        declared = sorted(redacted)
        in_tree = sorted(r for r in redacted if r in tree_map_cache(k, snap))
        if in_tree:
            ok = False
            res["redacted_present"] = in_tree
        res["redacted"] = declared
    shutil.rmtree(dst)
    res.update(ok=ok and bool(rec.get("ok")), files=len(live), mismatch=mism[:10], missing=missing[:10], extra=extra[:10])
    return res


_TM = {}


def tree_map_cache(k, rev):
    if (k, rev) not in _TM:
        _TM[(k, rev)] = tree_map(k, rev)
    return _TM[(k, rev)]


# --------------------------------------------------------------------------------------------------------------- commands
def cmd_freeze(scope, args):
    st = jload("RUN.json", {})
    if not st.get("run_id") or args.new_run:
        st = {"run_id": f"topo-{TS}-{os.getpid()}", "ts": TS, "ns": NS, "frozen_at": now()}
    guard = os.path.expanduser("~/.claude/dfcm/topology_guard.py")
    st["guard_sha256"] = sha256_file(guard) if os.path.exists(guard) else None
    st["live_cwds"] = live_cwds()
    jdump("RUN.json", st)
    ledger(
        {
            "step": "freeze",
            "precondition": "extended topology guard installed",
            "forward": "record run id + live cwd set",
            "postcondition": "RUN.json written",
            "falsifier": "guard absent",
            "rollback": "none (read-only)",
            "rollback_subject": None,
            "ok": bool(st["guard_sha256"]),
            "evidence": st["run_id"],
        }
    )


def cmd_inventory(scope, args):
    copies = inventory(scope)
    old = jload("INVENTORY.json", {"copies": {}})
    merged = old["copies"] if args.merge else {}
    for c in copies.values():
        if args.only and args.only not in c["path"]:
            continue
        if args.kind and c["kind"] != args.kind:
            continue
        if c["copy_id"] in merged and args.merge:
            c["rebaselined_from"] = merged[c["copy_id"]].get("fingerprint")
            c["rebaselined_at"] = now()
        merged[c["copy_id"]] = c
    data = {"release": "v26.9.25", "ts": TS, "observed_at": now(), "copies": merged}
    h = jdump("INVENTORY.json", data)
    kinds = {}
    for c in merged.values():
        kinds[c["kind"]] = kinds.get(c["kind"], 0) + 1
    ledger(
        {
            "step": "inventory",
            "precondition": "read-only",
            "forward": "discover + scan",
            "postcondition": "INVENTORY.json",
            "falsifier": "a copy on disk missing from the inventory",
            "rollback": "none",
            "rollback_subject": None,
            "ok": True,
            "evidence": {"sha256": h, "kinds": kinds},
        }
    )
    print(json.dumps(kinds, indent=1))


def cmd_classify(scope, args):
    inv = jload("INVENTORY.json")
    pres = load_parts("PRESERVE", {"records": {}})
    for cid, c in inv["copies"].items():
        if c["kind"] not in RETIRABLE:
            c["disposition"] = "KEEP_" + c["kind"]
            continue
        dirty = any(c["dirty"][x] for x in ("staged", "tracked", "deleted", "untracked"))
        if c.get("blocked"):
            c["disposition"] = "BLOCKED_" + c["blocked"].get("type", "OWNER")
        elif (
            not dirty
            and not c["unpushed_tips"]
            and not c["stashes"]
            and not c["reflog_only"]
            and (not c.get("head") or not git(c["canonical"], "rev-list", "-n1", c["head"], "--not", "--remotes=origin")[1])
        ):
            c["disposition"] = "ALREADY_ON_CANONICAL"
        else:
            c["disposition"] = "WIP_UNADMITTED"
            rec = pres["records"].get(cid) or {}
            if args.wip_branches and c["writer_queue"] not in scope["refs_only_repos"] and rec.get("sha") and dirty:
                br = f"wip/v26.9.25/{cid}"
                snap = rec["refs"].get(f"{NS}/{cid}/dirty")
                rc, cur, _ = git(c["canonical"], "rev-parse", "--verify", "-q", f"refs/heads/{br}")
                if not cur:
                    git(c["canonical"], "update-ref", f"refs/heads/{br}", snap, ZERO)
                rec["wip_branch"] = br
    jdump("INVENTORY.json", inv)
    for rid in {r.get("repo_id") for r in pres["records"].values()}:
        save_part("PRESERVE", rid, {"records": {k2: v for k2, v in pres["records"].items() if v.get("repo_id") == rid}})


def cmd_gate(scope, args):
    inv = jload("INVENTORY.json")
    pres = load_parts("PRESERVE", {"records": {}})
    drill = load_parts("verify/drill", {})
    run = jload("RUN.json", {})
    mark_retired(inv)
    g = Gate(scope, inv, pres, drill, run.get("run_id"))
    cids = [cid for cid, c in inv["copies"].items() if selected(c, args) and retirable(c) and not c.get("retired")]
    res = {}
    by_repo = {}
    for cid in gate_order(inv, cids):
        by_repo.setdefault(inv["copies"][cid]["writer_queue"], []).append(cid)
    for repo, cs in by_repo.items():
        with Lock(repo):
            for cid in cs:
                r = g.check(cid)
                g.cache[cid] = r
                res[cid] = r
    save_part("verify/gate", args.repo or args.only or "all", {"per_copy": res, "at": now()})
    n = sum(r["verdict"] == "PASS" for r in res.values())
    print(
        json.dumps(
            {"pass": n, "refused": len(res) - n, "refusals": {cid: r["failed_rules"] for cid, r in res.items() if r["verdict"] != "PASS"}}, indent=1
        )[:6000]
    )
    return 0 if n == len(res) else 1


def cmd_drill(scope, args):
    inv = jload("INVENTORY.json")
    pres = load_parts("PRESERVE", {"records": {}})
    run = jload("RUN.json", {})
    out = {}
    lines = []
    mark_retired(inv)
    for cid, c in sorted(inv["copies"].items()):
        if not selected(c, args) or not retirable(c):
            continue
        if c.get("retired"):
            continue  # stage 2: a retired copy cannot be re-drilled; its PASS verdict from before retirement is kept
        rec = pres["records"].get(cid)
        if not rec:
            continue
        r = drill_copy(scope, c, rec, run.get("run_id"))
        out[cid] = r
        lines.append(
            f"{'PASS' if r['ok'] else 'FAIL'} {cid} files={r.get('files')} mism={r.get('mismatch')} missing={r.get('missing')} extra={r.get('extra')}"
        )
    part = args.repo or args.only or "all"
    if "/" in part:
        part = slug(part)
    prev = jload(os.path.join("verify/drill.d", f"{part}.json"), {})
    prev.update(out)  # merge: a later drill of the same queue never erases earlier verdicts (retired copies cannot be re-drilled)
    save_part("verify/drill", part, prev)
    with open(os.path.join(HOME, "verify", "restore-drill.txt"), "a") as f:
        f.write(f"# drill {now()} run {run.get('run_id')}\n" + "\n".join(lines) + "\n")
    print("\n".join(lines[-80:]))


def cmd_cleanup(scope, args):
    inv = jload("INVENTORY.json")
    pres = load_parts("PRESERVE", {"records": {}})
    drill = load_parts("verify/drill", {})
    run = jload("RUN.json", {})
    mark_retired(inv)
    g = Gate(scope, inv, pres, drill, run.get("run_id"))
    cids = [cid for cid, c in inv["copies"].items() if selected(c, args) and retirable(c) and not c.get("retired") and not c.get("no_retire")]
    by_repo = {}
    for cid in gate_order(inv, cids):
        by_repo.setdefault(inv["copies"][cid]["writer_queue"], []).append(cid)
    for repo, cs in by_repo.items():
        with Lock(repo):
            for cid in cs:
                c = inv["copies"][cid]
                r = g.check(cid)
                g.cache[cid] = r
                if r["verdict"] != "PASS":
                    print(f"SKIP {cid}: {r['refusal']}")
                    continue
                if args.dry_run:
                    print(f"WOULD RETIRE {cid}")
                    continue
                moved = []
                if c["kind"] != "PRUNABLE_RECORD" and os.path.lexists(c["path"]):
                    dst = os.path.join(TRASH, f"{cid}-retired-{TS}")
                    shutil.move(c["path"], dst)
                    moved.append({"from": c["path"], "to": dst})
                    if c.get("retire_mode") == "deinit":
                        os.mkdir(c["path"])  # empty gitlink directory: the parent sees an unpopulated submodule (git submodule deinit shape)
                a = c.get("admin_dir")
                if c["kind"] in ("LINKED_WORKTREE", "PRUNABLE_RECORD", "FOREIGN_LINKED_WORKTREE") and a and os.path.isdir(a):
                    dst = os.path.join(TRASH, f"{cid}-admin-retired-{TS}")
                    shutil.move(a, dst)
                    moved.append({"from": a, "to": dst})
                listed = [w.get("worktree") for w in worktree_list(c["canonical"])] if c["kind"] in ("LINKED_WORKTREE", "PRUNABLE_RECORD") else []
                if c.get("retire_mode") == "deinit":
                    ok = os.path.isdir(c["path"]) and not os.listdir(c["path"])
                else:
                    ok = (not os.path.lexists(c["path"]) or c["kind"] == "PRUNABLE_RECORD") and c["path"] not in listed
                c["retired"] = ok
                ledger(
                    {
                        "fingerprint": r["fingerprint_at_gate"],
                        "gate_run_id": run.get("run_id"),
                        "path": c["path"],
                        "repo": repo,
                        "step": f"retire {cid}",
                        "precondition": "gate PASS (R1-R17) under repo lock, drill PASS",
                        "forward": " ; ".join(f"mv {m['from']} {m['to']}" for m in moved),
                        "postcondition": "empty gitlink dir (deinit shape)"
                        if c.get("retire_mode") == "deinit"
                        else "path absent; not listed by git worktree list",
                        "secret_trash": (r["evidence"].get("R16_SECRET_UNPRESERVABLE") or {}) if c.get("secret_trash") else None,
                        "falsifier": "path present or still listed",
                        "rollback": " ; ".join(f"mv {m['to']} {m['from']}" for m in moved) or "none",
                        "rollback_subject": pres["records"][cid].get("sha"),
                        "ok": ok,
                        "evidence": moved,
                    },
                    stop=False,
                )


def m_term(scope, inv):
    counted = {
        "CANONICAL",
        "LINKED_WORKTREE",
        "PRUNABLE_RECORD",
        "ORPHAN_WORKTREE",
        "CLONE",
        "NESTED_SELF_CLONE",
        "SUBMODULE_ACTIVE",
        "NONGIT_RESIDUE",
        "FOREIGN_LINKED_WORKTREE",
    }
    per, viol, sole = {}, [], {}
    for cid, c in inv["copies"].items():
        # finish: a copy with no in-scope owner has its own identity (normalized origin); M(r) <= 1 holds for it when it is the sole
        # working copy of that identity (the FOREIGN_CLONE rule: third-party sole checkout). It is a violation only when a second
        # copy of the same identity exists. The old single "_unowned" bucket summed distinct repositories into one row.
        rid = c.get("writer_queue") or ("_unowned:" + str((c.get("identity") or {}).get("origin_norm")))
        row = per.setdefault(
            rid,
            {
                "repo_id": rid,
                "canonical_path": c.get("canonical"),
                "authoritative_working_copies": 0,
                "linked_worktrees": 0,
                "prunable_records": 0,
                "excluded": [],
            },
        )
        present = os.path.lexists(c["path"]) if c["kind"] != "PRUNABLE_RECORD" else bool(c.get("admin_dir") and os.path.isdir(c["admin_dir"]))
        if c["kind"] in counted and present and not c.get("retired"):
            row["authoritative_working_copies"] += 1
            if c["kind"] == "LINKED_WORKTREE":
                row["linked_worktrees"] += 1
            if c["kind"] == "PRUNABLE_RECORD":
                row["prunable_records"] += 1
            if c["kind"] != "CANONICAL":
                v = {"repo_id": rid, "path": c["path"], "class": c["kind"], "blocked": (c.get("blocked") or {}).get("reason")}
                if rid.startswith("_unowned:"):
                    sole.setdefault(rid, []).append(v)
                else:
                    viol.append(v)
        elif c["kind"] not in counted:
            row["excluded"].append({"path": c["path"], "class": c["kind"]})
    for rid, vs in sole.items():
        if len(vs) > 1 or rid == "_unowned:None":
            viol.extend(vs)
        else:
            per[rid]["sole_working_copy"] = vs[0]["path"]
    return {
        "definition": "AuthoritativeWorkingCopy(r) = |{w : identity(w)=r and counted(class(w))}|; counted = CANONICAL, LINKED_WORKTREE, "
        "PRUNABLE_RECORD, ORPHAN_WORKTREE, CLONE, NESTED_SELF_CLONE, SUBMODULE_ACTIVE, NONGIT_RESIDUE; holds iff every in-scope r has no "
        "counted non-canonical copy and every out-of-scope identity (no owner; keyed by normalized origin, None never admitted) has <= 1",
        "per_repo": sorted(per.values(), key=lambda r: r["repo_id"]),
        "unauthorized_worktrees": sum(
            1 for v in viol if v["class"] in ("LINKED_WORKTREE", "PRUNABLE_RECORD", "ORPHAN_WORKTREE", "FOREIGN_LINKED_WORKTREE")
        ),
        "shadow_copies": sum(1 for v in viol if v["class"] in ("CLONE", "NESTED_SELF_CLONE", "NONGIT_RESIDUE")),
        "holds": not viol,
        "violations": viol,
        "recompute": "python3 topology.py verify --json",
    }


def cmd_verify(scope, args):
    inv = jload("INVENTORY.json")
    mark_retired(inv)
    # re-observe: worktree lists of every canonical (catches copies created after inventory)
    for rid, k in scope["canonicals"].items():
        if not os.path.isdir(k):
            continue
        listed = {w.get("worktree") for w in worktree_list(k)} - {k}
        for w in listed:
            if not any(c["path"] == w for c in inv["copies"].values()):
                inv["copies"][slug(w)] = base_copy(w, "LINKED_WORKTREE" if os.path.isdir(w) else "PRUNABLE_RECORD", writer_queue=rid, canonical=k)
    m = m_term(scope, inv)
    m["observed_at"] = now()
    jdump("verify/m_term.json", m)
    print(
        json.dumps(
            {
                "holds": m["holds"],
                "unauthorized_worktrees": m["unauthorized_worktrees"],
                "shadow_copies": m["shadow_copies"],
                "violations": m["violations"][:60],
            },
            indent=1,
        )
    )
    return 0 if m["holds"] else 1


def cmd_signoff(scope, args):
    """finish: apply operator signoffs (scope["signoffs"]) to INVENTORY.json as ledgered transitions.
    action unblock      -> clear the copy's typed block (owner/CANONICAL_MAP signoff; R17 still demands a host_signoff for foreign content)
    action secret_trash -> clear SECRET_UNPRESERVABLE; R16 admits because the whole copy (secrets included) moves to ~/.Trash
    action reclassify   -> re-run rules V1..V4 (classify_nested) against the declared parent; kind replaced by the rule's verdict
    action add          -> inventory a copy the fleet walk never saw (declared submodule of an out-of-scope parent), via V1..V4
    retire_mode deinit  -> a V1 SUBMODULE_ACTIVE is retired as `mv` to Trash + empty gitlink dir (parent sees an unpopulated submodule)"""
    inv = jload("INVENTORY.json")
    cidx, allk = canonical_index(scope)
    changed = 0
    for so in scope.get("signoffs", []):
        act, path = so["action"], so["path"]
        if act == "add":
            targets = [path] if not any(c["path"] == path for c in inv["copies"].values()) else []
        else:
            targets = [c["path"] for c in inv["copies"].values() if c["path"] == path or c["path"].startswith(path.rstrip("/") + "/")]
        for tp in targets:
            cid = slug(tp)
            c = inv["copies"].get(cid) or next((x for x in inv["copies"].values() if x["path"] == tp), None)
            before = None if c is None else {"kind": c["kind"], "blocked": c.get("blocked"), "writer_queue": c.get("writer_queue")}
            if act in ("add", "reclassify"):
                par = so["parent"]
                po = norm_origin(git(par, "remote", "get-url", "origin")[1]) if git(par, "remote", "get-url", "origin")[0] == 0 else None
                nc = classify_nested(scope, tp, par, po, cidx)
                if act == "add":
                    nc["repo_id"] = so.get("owner") or resolve_owner(scope, nc, cidx)
                    nc["canonical"] = allk.get(nc["repo_id"]) if nc["repo_id"] else None
                    nc["writer_queue"] = nc["repo_id"]
                    nc["host_repo"] = so.get("host_repo")
                    nc["nested_git"] = []
                    scan_copy(scope, nc)
                    nc["fingerprint"] = fingerprint(nc)
                    c = inv["copies"][nc["copy_id"]] = nc
                else:
                    c["kind"] = nc["kind"]
                    c["notes"] = list(c.get("notes", [])) + nc["notes"] + [f"finish reclassify: {before['kind']} -> {nc['kind']}"]
                    c["fingerprint"] = fingerprint(c)
                c.pop("blocked", None)
            elif act in ("unblock", "secret_trash"):
                c.pop("blocked", None)
                c["signed_off"] = True
                c["no_retire"] = False  # the signoff is the retirement authority the block withheld
                if act == "secret_trash":
                    c["secret_trash"] = so["grant"]
            if so.get("retire_mode"):
                c["retire_mode"] = so["retire_mode"]
            if so.get("identity_canonical"):
                c["identity_canonical"] = so["identity_canonical"]
            c["signoff"] = so["grant"]
            changed += 1
            ledger(
                {
                    "repo": c.get("writer_queue"),
                    "step": f"signoff {act} {c['copy_id']}",
                    "precondition": "operator order 'finish' 2026-09-25 09:05 PT (CANONICAL_MAP / owner / secret signoffs)",
                    "forward": f"INVENTORY.json copy {c['copy_id']}: {before} -> kind={c['kind']} blocked=None retire_mode={c.get('retire_mode')}",
                    "postcondition": "copy unblocked; gate rules R1-R17 still decide retirement",
                    "falsifier": "copy still blocked, or kind differs from classify_nested verdict",
                    "rollback": f"restore INVENTORY.json copy {c['copy_id']} fields {before}",
                    "rollback_subject": None,
                    "ok": True,
                    "evidence": {"grant": so["grant"], "before": before, "after_kind": c["kind"]},
                },
                stop=False,
            )
    jdump("INVENTORY.json", inv)
    print(json.dumps({"signoffs_applied": changed}))


def cmd_receipt(scope, args):
    inv = jload("INVENTORY.json")
    pres = load_parts("PRESERVE", {"records": {}})
    gate = load_parts("verify/gate", {"per_copy": {}})
    drill = load_parts("verify/drill", {})
    rl = mark_retired(inv)
    deleted = {
        "deleted_artifacts": [
            dict(v, path=inv["copies"].get(k, {}).get("path") or ((v.get("moved") or [{}])[0].get("from")), inventory_copy=k in inv["copies"])
            for k, v in rl.items()
        ]
    }
    m = jload("verify/m_term.json") or m_term(scope, inv)
    guard = jload("verify/guard.json", {"cases": 0, "failures": -1})
    inv_sha = sha256_file(os.path.join(HOME, "INVENTORY.json"))
    retired = [d for d in deleted["deleted_artifacts"]]
    for d in retired:  # cleanup retires only on a PASS computed under the repo lock; the ledger entry is that verdict's record
        prior = gate["per_copy"].get(d["copy_id"])
        if prior and prior.get("verdict") != "PASS" and d.get("inventory_copy"):
            # stage 2: an earlier REFUSED gate part (e.g. R12 before a re-drill) is superseded by the later PASS recorded at retirement
            gate["per_copy"].pop(d["copy_id"])
        gate["per_copy"].setdefault(
            d["copy_id"],
            {
                "copy_id": d["copy_id"],
                "verdict": "PASS",
                "failed_rules": [],
                "source": "steps.jsonl retire entry",
                "fingerprint_at_gate": d.get("fingerprint"),
                "at": d.get("at"),
            },
        )
    # stage 2: a retired alias (symlink, not an inventory copy) carries no gate/drill; it is judged by its own ledger postcondition
    gate_ok = all(gate["per_copy"].get(d["copy_id"], {}).get("verdict") == "PASS" for d in retired if d.get("inventory_copy"))
    drill_ok = all(drill.get(d["copy_id"], {}).get("ok") for d in retired if d.get("inventory_copy"))
    subj = args.subject_sha or ZERO
    standing = "ALIVE" if (m["holds"] and gate_ok and drill_ok and guard.get("failures") == 0) else "PARTIAL_ALIVE" if retired else "BLOCKED:TOPOLOGY"
    r = {
        "$id": "https://chatmangpt.com/schema/topology-receipt/v1",
        "identity": {
            "subject": f"v26.9.25 topology cleanup {args.stage}",
            "repo": args.subject_repo or HOME,
            "subject_sha": subj,
            "base_sha": subj,
            "graph_hash": "sha256:" + inv_sha,
        },
        "authority": {
            "ceiling": "DO",
            "grant": "operator order v26.9.25 (mass topology cleanup in scope; RFC-v26.9.25 + approved plan)",
            "actor": "topology.py lane topo-1",
        },
        "consequence": {
            "commits": sorted({v for rec in pres["records"].values() for v in (rec.get("refs") or {}).values()})[:500],
            "files_changed": [d["path"] for d in retired],
            "remote_effects": [
                f"{rec['repo_id']}:refs/heads/{rec['remote_ref']}@{rec['remote_verified_sha']}"
                for rec in pres["records"].values()
                if rec.get("remote_verified_sha")
            ],
        },
        "replay": {
            "commands": args.replay or [{"cmd": "python3 topology.py verify", "cwd": HERE, "exit": 0 if m["holds"] else 1}],
            "durable_location": HOME,
        },
        "standing": {"value": standing, "derived_from": "gate.json + drill.json + m_term.json + guard corpus replay at receipt time"},
        "migration_receipt": {
            "source_state": {
                "inventory_sha256": inv_sha,
                "observed_at": inv.get("observed_at"),
                "copies": [
                    {
                        "copy_id": c["copy_id"],
                        "path": c["path"],
                        "kind": c["kind"],
                        "class": c.get("disposition"),
                        "head": c.get("head"),
                        "dirty_count": sum(len(c["dirty"][x]) for x in c["dirty"]),
                        "size_bytes": c.get("size_bytes"),
                    }
                    for c in inv["copies"].values()
                ],
            },
            "target_state": {
                "observed_at": m.get("observed_at"),
                "per_repo": m["per_repo"],
                "quarantine": [{"path": mv["from"], "trash_path": mv["to"]} for d in retired for mv in d["moved"]],
            },
            "preserved_refs": [
                {
                    k2: rec.get(k2)
                    for k2 in (
                        "copy_id",
                        "local_ref",
                        "sha",
                        "remote_ref",
                        "remote_verified_sha",
                        "local_only_reason",
                        "redacted",
                        "bundle",
                        "ignored_bundle",
                        "wip_branch",
                        "error",
                    )
                }
                for rec in pres["records"].values()
            ],
            "moved_artifacts": [
                {"from_path": rec["path"], "to": {"repo": rec["repo_id"], "branch": rec["wip_branch"]}}
                for rec in pres["records"].values()
                if rec.get("wip_branch")
            ],
            "deduplicated_artifacts": [],
            "deleted_artifacts": retired,
            "verification": {
                "gate": {"ok": gate_ok, "per_copy": list(gate["per_copy"].values())},
                "drill": {"ok": drill_ok, "samples": [v for k2, v in drill.items() if k2 != "_repos"]},
                "guard": guard,
            },
            "rollback_procedure": [
                {"copy_id": d["copy_id"], "tier": 2, "commands": [f"mv '{mv['to']}' '{mv['from']}'" for mv in d["moved"]]} for d in retired
            ]
            + [
                {"copy_id": rec["copy_id"], "tier": 1, "commands": [f"git -C {rec['canonical']} branch restore/{rec['copy_id']} {rec['local_ref']}"]}
                for rec in pres["records"].values()
                if rec.get("local_ref")
            ],
        },
        "m_term": m,
    }
    if standing.startswith("BLOCKED") or standing == "PARTIAL_ALIVE":
        r["standing"]["broken_term"] = "R_missing_consequence"
    jdump("PRESERVE.json", pres)
    jdump(args.out, r)
    print(json.dumps({"standing": standing, "m_holds": m["holds"], "retired": len(retired), "gate_ok": gate_ok, "drill_ok": drill_ok}))


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd")
    ap.add_argument("--scope", default=os.path.join(HOME, "scope.json"))
    ap.add_argument("--only")
    ap.add_argument("--repo")
    ap.add_argument("--kind")
    ap.add_argument("--merge", action="store_true")
    ap.add_argument("--push", action="store_true")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--new-run", action="store_true")
    ap.add_argument("--wip-branches", action="store_true")
    ap.add_argument("--supersede", help="re-preserve already-preserved copies; old refs move to <slug>/superseded-N/ (reason text)")
    ap.add_argument("--stage", default="stage1")
    ap.add_argument("--out", default="TOPOLOGY-RECEIPT.stage1.json")
    ap.add_argument("--subject-repo")
    ap.add_argument("--subject-sha")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--replay-file")
    args = ap.parse_args(argv)
    args.replay = None
    if args.replay_file:
        with open(args.replay_file) as f:
            args.replay = json.load(f)
    scope = load_scope(args.scope)
    fn = {
        "freeze": cmd_freeze,
        "inventory": cmd_inventory,
        "preserve": cmd_preserve,
        "classify": cmd_classify,
        "gate": cmd_gate,
        "drill": cmd_drill,
        "cleanup": cmd_cleanup,
        "verify": cmd_verify,
        "receipt": cmd_receipt,
        "signoff": cmd_signoff,
    }[args.cmd]
    return fn(scope, args) or 0


if __name__ == "__main__":
    sys.exit(main())
