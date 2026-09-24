#!/usr/bin/env python3
"""Phase 2 preservation anchors (single-repo migration). Normal git refs only; never a worktree.

  A. every local branch head + every worktree HEAD of each affected repo
       -> refs/archive/pre-single-repo-migration/<TS>/heads/<branch>, .../worktree-head/<slug>
  B. dirty/untracked (non-ignored) state of every shadow worktree and every canonical checkout
       -> snapshot commit (parent HEAD) via a temporary index -> .../dirty/<slug>   (working trees untouched)
     secrets (private keys, .env, tokens) and crash dumps are excluded; only path + sha256 recorded
  C. the chatman-ecosystem shadow clone's refs -> ~/chatman-ecosystem refs/archive/.../shadow-clone/*
  D. non-git shadow files (~/wt/v26922 minus git checkouts, caches, secrets, crash dumps)
       -> one archive commit in ~/chatman-ecosystem at refs/archive/.../shadow-files
Writes PRESERVE.json (every ref, sha, and what it anchors).
"""
import datetime
import hashlib
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
TS = "20260924T0600Z"
NS = f"refs/archive/pre-single-repo-migration/{TS}"
SHADOW = "/Users/sac/wt/v26922"
CHATMAN = "/Users/sac/chatman-ecosystem"
SHADOW_CLONE = "/Users/sac/wt/v26922/chatman-ecosystem/repo"
REPOS = {
    "xaas": "/Users/sac/xaas", "ggen_igniter": "/Users/sac/ggen_igniter", "ggen-marketplace": "/Users/sac/ggen-marketplace",
    "chatman-ecosystem": CHATMAN, "chatman-shadow-clone": SHADOW_CLONE, "ggen": "/Users/sac/ggen", "autofde-lab": "/Users/sac/autofde-lab",
    "gymact": "/Users/sac/gymact", "beam4pm": "/Users/sac/beam4pm", "beam4pm_ws2": "/Users/sac/beam4pm_ws2", "ash_a2a": "/Users/sac/ash_a2a",
    "gitvan": "/Users/sac/gitvan", "ferroplan": "/Users/sac/ferroplan", "zcode-cli": "/Users/sac/dev/zcode-cli",
    "ggen-ecosystem": "/Users/sac/ggen-ecosystem", "open-ontologies": "/Users/sac/open-ontologies", "affidavit": "/Users/sac/affidavit",
    "ash_atlassian": "/Users/sac/ash_atlassian", "ash_surface": "/Users/sac/ash_surface", "frozen-duckdb": "/Users/sac/frozen-duckdb",
}
SECRET_NAME = re.compile(r"(\.key$|\.pem$|(^|/)\.env(\..*)?$|credentials|secret|token|\.p12$|id_rsa|id_ed25519)", re.I)
SECRET_CONTENT = re.compile(rb"-----BEGIN [A-Z ]*PRIVATE KEY-----|ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|sk-[A-Za-z0-9]{32,}|xox[bap]-[A-Za-z0-9-]{20,}|AKIA[0-9A-Z]{16}")
EXCLUDE_DIRS = {"_build", "deps", "target", "node_modules", ".venv", ".elixir_ls", ".oclnr-cache", "__pycache__", ".mypy_cache", ".pytest_cache"}


def git(repo, *args, env=None, input=None):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True, env=env, input=input)
    return p.returncode, p.stdout.rstrip(), p.stderr.strip()  # rstrip: leading spaces are status columns


def slug(s):
    return re.sub(r"[^A-Za-z0-9._/-]+", "_", s.replace("/Users/sac/", "").replace("/private/tmp/", "tmp/")).strip("_/")


def is_secret(path):
    if path.endswith("verifying.key"):
        return False
    if SECRET_NAME.search(path) or path.endswith("erl_crash.dump"):
        return True
    try:
        with open(path, "rb") as f:
            return bool(SECRET_CONTENT.search(f.read(2 * 1024 * 1024)))
    except (IsADirectoryError, FileNotFoundError, PermissionError):
        return False


def sha(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for c in iter(lambda: f.read(1 << 20), b""):
            h.update(c)
    return h.hexdigest()


def worktrees(repo):
    rc, out, _ = git(repo, "worktree", "list", "--porcelain")
    res, cur = [], {}
    for line in out.splitlines() + [""]:
        if not line:
            if cur:
                res.append(cur)
            cur = {}
        elif " " in line:
            k, v = line.split(" ", 1)
            cur[k] = v
    return res


def snapshot_dirty(repo_for_refs, path, name, rec):
    """Commit tracked changes + untracked non-ignored files of `path` onto a ref, without touching its index or files."""
    rc, status, _ = git(path, "status", "--porcelain", "--untracked-files=all")
    if not status:
        return
    idx = f"/private/tmp/claude-501/preserve-{hashlib.sha1(path.encode()).hexdigest()[:10]}.index"
    env = dict(os.environ, GIT_INDEX_FILE=idx)
    git(path, "read-tree", "HEAD", env=env)
    excluded = []
    for line in status.splitlines():
        code, rel = line[:2], line[3:].strip('"')
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        full = os.path.join(path, rel)
        if any(part in EXCLUDE_DIRS for part in rel.split("/")):
            continue
        if os.path.isfile(full) and is_secret(full):
            excluded.append({"path": full, "sha256": sha(full), "reason": "secret-or-crash-dump: recorded only"})
            continue
        if code.strip() == "D" or not os.path.exists(full):
            git(path, "rm", "-q", "--cached", "--ignore-unmatch", "--", rel, env=env)
        else:
            git(path, "add", "-f", "--", rel, env=env)
    rc, tree, err = git(path, "write-tree", env=env)
    head = git(path, "rev-parse", "HEAD")[1]
    rc, c, err = git(path, "commit-tree", tree, "-p", head, "-m",
                     f"archive(pre-single-repo-migration {TS}): dirty + untracked state of {path}\n\nPreserved before the operator-directed "
                     f"collapse to one canonical checkout per repository; working tree untouched. Secrets/crash dumps excluded "
                     f"(path + sha256 in PRESERVE.json).")
    os.remove(idx)
    ref = f"{NS}/dirty/{slug(path)}"
    git(repo_for_refs, "update-ref", ref, c)
    rec.append({"repo": name, "ref": ref, "sha": c, "anchors": f"dirty state of {path}", "lines": len(status.splitlines()),
                "excluded": excluded})


def main():
    rec, errors = [], []
    for name, repo in REPOS.items():
        if not os.path.exists(f"{repo}/.git"):
            errors.append(f"{name}: missing {repo}")
            continue
        rc, out, _ = git(repo, "for-each-ref", "--format=%(refname)%09%(objectname)", "refs/heads")
        for line in out.splitlines():
            ref, s = line.split("\t")
            a = f"{NS}/heads/{ref[len('refs/heads/'):]}"
            git(repo, "update-ref", a, s)
            rec.append({"repo": name, "ref": a, "sha": s, "anchors": ref})
        for w in worktrees(repo):
            p, h = w.get("worktree", ""), w.get("HEAD", "")
            if h and len(h) == 40:
                a = f"{NS}/worktree-head/{slug(p)}"
                git(repo, "update-ref", a, h)
                rec.append({"repo": name, "ref": a, "sha": h, "anchors": f"HEAD of worktree {p} ({w.get('branch', 'detached')})"})
            if os.path.isdir(p):
                snapshot_dirty(repo, p, name, rec)
    # C. shadow clone refs into the canonical chatman checkout
    rc, out, err = git(CHATMAN, "fetch", "--no-tags", SHADOW_CLONE, f"+refs/*:{NS}/shadow-clone/*")
    if rc:
        errors.append(f"shadow clone fetch: {err[-300:]}")
    rc, out, _ = git(CHATMAN, "for-each-ref", "--format=%(refname)%09%(objectname)", f"{NS}/shadow-clone")
    for line in out.splitlines():
        ref, s = line.split("\t")
        rec.append({"repo": "chatman-ecosystem", "ref": ref, "sha": s, "anchors": "shadow clone ref " + ref.split("/shadow-clone/", 1)[1]})
    # D. non-git shadow files -> one archive commit in chatman-ecosystem
    idx = "/private/tmp/claude-501/preserve-shadow-files.index"
    if os.path.exists(idx):
        os.remove(idx)
    env = dict(os.environ, GIT_INDEX_FILE=idx, GIT_DIR=f"{CHATMAN}/.git", GIT_WORK_TREE=SHADOW)
    excluded, added = [], 0
    for dirpath, dirs, files in os.walk(SHADOW):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and d != ".git" and not os.path.exists(os.path.join(dirpath, d, ".git"))]
        for f in files:
            fp = os.path.join(dirpath, f)
            if os.path.islink(fp) or not os.path.isfile(fp):
                continue
            if is_secret(fp):
                excluded.append({"path": fp, "sha256": sha(fp), "size": os.path.getsize(fp), "reason": "secret-or-crash-dump"})
                continue
            rel = os.path.relpath(fp, SHADOW)
            p = subprocess.run(["git", "update-index", "--add", "--", rel], cwd=SHADOW, env=env, capture_output=True, text=True)
            if p.returncode:
                errors.append(f"add {rel}: {p.stderr.strip()[:200]}")
            else:
                added += 1
    p = subprocess.run(["git", "write-tree"], cwd=SHADOW, env=env, capture_output=True, text=True)
    tree = p.stdout.strip()
    p = subprocess.run(["git", "commit-tree", tree, "-m", f"archive(pre-single-repo-migration {TS}): non-git files of {SHADOW}\n\n"
                        f"{added} files; git checkouts, build caches, secrets and crash dumps excluded (see PRESERVE.json)."],
                       cwd=SHADOW, env=env, capture_output=True, text=True)
    c = p.stdout.strip()
    git(CHATMAN, "update-ref", f"{NS}/shadow-files", c)
    os.remove(idx)
    rec.append({"repo": "chatman-ecosystem", "ref": f"{NS}/shadow-files", "sha": c, "anchors": f"{added} non-git files of {SHADOW}",
                "excluded": excluded})
    out = {"migration_id": "v26923-single-repo", "phase": "2-preserve", "namespace": NS, "refs": rec, "errors": errors,
           "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
    json.dump(out, open(os.path.join(HERE, "PRESERVE.json"), "w"), indent=1)
    print(json.dumps({"refs": len(rec), "dirty_snapshots": sum(1 for r in rec if "/dirty/" in r["ref"]),
                      "shadow_files_added": added, "excluded": sum(len(r.get("excluded", [])) for r in rec), "errors": errors[:10]}, indent=1))


if __name__ == "__main__":
    main()
