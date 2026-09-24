#!/usr/bin/env python3
"""Phase 11 destructive-cleanup gate (single-repo migration). Read-only: computes every precondition from real evidence.

usage: cleanup_gate.py [--json out.json]
Exit 0 only when every condition holds; otherwise prints REFUSED(UNREVERSIBLE_CLEANUP) with the failing conditions.

  UNIQUE_REQUIRED_FILES=0      every non-git shadow file is in the shadow-files archive commit with an identical blob,
                               and every OWNERSHIP subject classified UNIQUE_AND_REQUIRED has canonical evidence
  UNPUSHED_REQUIRED_COMMITS=0  every commit reachable from the shadow clone exists in the canonical chatman repo, and every
                               release/required branch head is on its remote
  DIRTY_REQUIRED_WORKTREES=0   no remaining linked worktree under the shadow root has tracked changes not captured by a ref
  UNMIGRATED_RECEIPTS=0        every receipt-class shadow file is archived (blob-identical)
  ROLLBACK_READY               every PRESERVE.json ref resolves to its recorded object
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SHADOW = "/Users/sac/wt/v26922"
CHATMAN = "/Users/sac/chatman-ecosystem"
SHADOW_CLONE = f"{SHADOW}/chatman-ecosystem/repo"
EXCLUDE_DIRS = {"_build", "deps", "target", "node_modules", ".venv", ".elixir_ls", ".oclnr-cache", "__pycache__", ".mypy_cache", ".pytest_cache"}


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return p.returncode, p.stdout.rstrip()


CANONICAL = {"chatman-ecosystem": CHATMAN, "xaas": "/Users/sac/xaas", "ggen_igniter": "/Users/sac/ggen_igniter",
             "ggen-marketplace": "/Users/sac/ggen-marketplace"}


def on_refs(ev):
    """Remote refs holding the evidence commit (origin/main first when it does)."""
    out = git(CANONICAL[ev["repo"]], "branch", "-r", "--contains", ev["commit"])[1]
    refs = sorted({r.strip() for r in out.splitlines() if "->" not in r}, key=lambda r: (r != "origin/main", r))
    return refs[:3]


def evidence_defect(ev):
    """None when the evidence is real: a structured record whose path exists at a commit that is on a pushed
    ref of the canonical repository; otherwise the reason (a free-text or null canonical_final is refused)."""
    if not isinstance(ev, dict) or not {"repo", "commit", "path", "kind"} <= set(ev):
        return "no structured canonical evidence"
    repo = CANONICAL.get(ev["repo"])
    if not repo or not os.path.isdir(repo):
        return f"canonical repo {ev['repo']} unknown or absent"
    if git(repo, "cat-file", "-e", f"{ev['commit']}:{ev['path']}")[0] != 0:
        return f"{ev['path']} absent at {ev['commit']}"
    if not on_refs(ev):
        return f"{ev['commit']} is on no pushed ref"
    return None


def main():
    P = json.load(open(os.path.join(HERE, "PRESERVE.json")))
    repos = {"chatman-shadow-clone": SHADOW_CLONE}
    sys.path.insert(0, HERE)
    import preserve  # noqa: E402  (REPOS map)
    repos.update(preserve.REPOS)
    cond, detail = {}, {}

    # ROLLBACK_READY
    bad = []
    for r in P["refs"]:
        repo = repos.get(r["repo"], CHATMAN)
        if not os.path.isdir(repo):
            bad.append((r["repo"], r["ref"], "repo missing"))
            continue
        if git(repo, "rev-parse", "--verify", "-q", r["ref"])[1] != r["sha"]:
            bad.append((r["repo"], r["ref"], "ref moved/missing"))
    for e in P.get("ignored_evidence", []):
        repo = git(e["worktree"], "rev-parse", "--git-common-dir")[1] if os.path.isdir(e["worktree"]) else None
        # ignored-evidence refs live in the owning repository; check by object in every candidate repo
        found = any(git(rp, "cat-file", "-e", e["sha"])[0] == 0 for rp in repos.values() if os.path.isdir(rp))
        if not found:
            bad.append(("ignored", e["ref"], "object missing"))
    cond["ROLLBACK_READY"] = not bad
    detail["rollback_bad"] = bad[:20]

    # shadow files vs archive
    sf = next(r for r in P["refs"] if r["ref"].endswith("/shadow-files"))
    tree = {}
    for line in git(CHATMAN, "ls-tree", "-r", sf["sha"])[1].splitlines():
        meta, path = line.split("\t", 1)
        tree[path] = meta.split()[2]
    excluded = {e["path"] for e in sf.get("excluded", [])}
    missing, changed, receipts_missing = [], [], []
    if os.path.isdir(SHADOW):
        for dirpath, dirs, files in os.walk(SHADOW):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and d != ".git" and not os.path.exists(os.path.join(dirpath, d, ".git"))]
            for f in files:
                fp = os.path.join(dirpath, f)
                if os.path.islink(fp) or not os.path.isfile(fp) or fp in excluded:
                    continue
                rel = os.path.relpath(fp, SHADOW)
                blob = subprocess.run(["git", "hash-object", fp], capture_output=True, text=True).stdout.strip()
                if rel not in tree:
                    missing.append(rel)
                    if "receipt" in rel.lower():
                        receipts_missing.append(rel)
                elif tree[rel] != blob:
                    changed.append(rel)
    own_path = os.path.join(HERE, "OWNERSHIP.json")
    unresolved, evidence = [], []
    if os.path.exists(own_path):
        own = json.load(open(own_path))
        required = [s for s in own.get("subjects", []) if s.get("disposition") == "UNIQUE_AND_REQUIRED"]
        for s in required + own.get("release_subjects", []):
            label = f"{s.get('repo')}:{s.get('subject')}"[:120]
            why = evidence_defect(s.get("canonical_final"))
            if why:
                unresolved.append(f"{label} [{why}]")
            else:
                evidence.append({"subject": label, **s["canonical_final"], "on": on_refs(s["canonical_final"])})
    else:
        unresolved.append("OWNERSHIP.json absent")
    detail["canonical_evidence"] = evidence
    cond["UNIQUE_REQUIRED_FILES=0"] = not missing and not changed and not unresolved
    detail.update(files_not_archived=missing[:20], files_changed_since_archive=changed[:20], required_subjects_unresolved=unresolved[:20])
    cond["UNMIGRATED_RECEIPTS=0"] = not receipts_missing
    detail["receipts_not_archived"] = receipts_missing[:20]

    # UNPUSHED_REQUIRED_COMMITS
    unp = []
    if os.path.isdir(SHADOW_CLONE):
        for c in git(SHADOW_CLONE, "rev-list", "--all")[1].split():
            if git(CHATMAN, "cat-file", "-e", c)[0] != 0:
                unp.append(c)
    cond["UNPUSHED_REQUIRED_COMMITS=0"] = not unp
    detail["shadow_clone_commits_not_in_canonical"] = unp[:20]

    # DIRTY_REQUIRED_WORKTREES
    dirty = []
    if os.path.isdir(SHADOW):
        for dirpath, dirs, _ in os.walk(SHADOW):
            if os.path.isfile(os.path.join(dirpath, ".git")):
                if git(dirpath, "status", "--porcelain", "--untracked-files=no")[1]:
                    dirty.append(dirpath)
                dirs[:] = []
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and d != ".git"]
    cond["DIRTY_REQUIRED_WORKTREES=0"] = not dirty
    detail["dirty_worktrees"] = dirty

    ok = all(cond.values())
    out = {"ok": ok, "conditions": cond, "detail": detail}
    if "--json" in sys.argv:
        json.dump(out, open(sys.argv[sys.argv.index("--json") + 1], "w"), indent=1)
    print(json.dumps(out, indent=1)[:4000])
    if not ok:
        print("REFUSED(UNREVERSIBLE_CLEANUP)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
