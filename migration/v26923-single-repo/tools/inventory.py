#!/usr/bin/env python3
"""Phase 1 immutable inventory for the single-repo migration (operator 2026-09-23 ~23:10 PT).

Writes MANIFEST.json (+ MANIFEST.sha256) next to this script, never under the shadow tree it inventories.
Read-only: no ref, index or working-tree change anywhere.
"""
import datetime
import hashlib
import json
import os
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
SHADOW = "/Users/sac/wt/v26922"
SCRATCH = "/private/tmp/claude-501/v23-scratch"
CACHE_DIRS = {"_build", "deps", "target", "node_modules", ".venv", ".elixir_ls", ".oclnr-cache", "__pycache__", ".mypy_cache",
              ".pytest_cache", ".ggen-cache", "cover", ".turbo", "dist", ".next"}
CHECKOUTS = {
    "xaas": ["/Users/sac/xaas"], "ggen_igniter": ["/Users/sac/ggen_igniter"], "ggen-marketplace": ["/Users/sac/ggen-marketplace"],
    "chatman-ecosystem": ["/Users/sac/chatman-ecosystem", "/Users/sac/wt/v26922/chatman-ecosystem/repo"],
    "ggen": ["/Users/sac/ggen"], "autofde-lab": ["/Users/sac/autofde-lab"], "gymact": ["/Users/sac/gymact"],
    "beam4pm": ["/Users/sac/beam4pm", "/Users/sac/beam4pm_ws2"], "ash_a2a": ["/Users/sac/ash_a2a"], "gitvan": ["/Users/sac/gitvan"],
    "ferroplan": ["/Users/sac/ferroplan"], "zcode-cli": ["/Users/sac/dev/zcode-cli"], "ggen-ecosystem": ["/Users/sac/ggen-ecosystem"],
    "open-ontologies": ["/Users/sac/open-ontologies"], "affidavit": ["/Users/sac/affidavit"],
}


def run(cmd, cwd=None, timeout=600):
    p = subprocess.run(cmd, cwd=cwd, shell=True, capture_output=True, text=True, timeout=timeout)
    return p.returncode, p.stdout, p.stderr


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def default_branch(repo):
    rc, out, _ = run(f"git -C {repo} symbolic-ref --short refs/remotes/origin/HEAD")
    if rc == 0 and out.strip():
        return out.strip()
    for cand in ("origin/main", "origin/master", "fork/main", "main", "master"):
        if run(f"git -C {repo} rev-parse --verify -q {cand}")[0] == 0:
            return cand
    return None


def git_inventory(name, path):
    g = {"name": name, "path": path}
    if not os.path.exists(f"{path}/.git"):
        g["missing"] = True
        return g
    for key, cmd in (("toplevel", "rev-parse --show-toplevel"), ("head", "rev-parse HEAD"), ("branch", "branch --show-current"),
                     ("remotes", "remote -v"), ("status_short", "status --short"), ("worktree_list", "worktree list --porcelain"),
                     ("stash_list", "stash list --format='%H %gs'")):
        rc, out, err = run(f"git -C {path} {cmd}")
        g[key] = out.strip() if rc == 0 else f"ERROR {rc}: {err.strip()[:200]}"
    g["is_linked_worktree"] = os.path.isfile(f"{path}/.git")
    dflt = default_branch(path)
    g["default_ref"] = dflt
    rc, out, _ = run(f"git -C {path} for-each-ref --format='%(refname)%09%(objectname)%09%(upstream)%09%(committerdate:iso-strict)'")
    refs = []
    for line in out.splitlines():
        ref, sha, up, date = (line.split("\t") + ["", "", "", ""])[:4]
        if ref.startswith("refs/remotes/"):
            continue
        r = {"ref": ref, "sha": sha, "upstream": up, "date": date}
        if not ref.startswith("refs/stash"):
            r["not_on_any_remote"] = int(run(f"git -C {path} rev-list --count {sha} --not --remotes")[1].strip() or 0)
            if dflt:
                r["ahead_of_default"] = int(run(f"git -C {path} rev-list --count {dflt}..{sha}")[1].strip() or 0)
                if r["ahead_of_default"] and r["ahead_of_default"] <= 400:
                    rc2, ch, _ = run(f"git -C {path} cherry {dflt} {sha}", timeout=300)
                    r["patch_unique_vs_default"] = sum(1 for l in ch.splitlines() if l.startswith("+"))
        refs.append(r)
    g["refs"] = refs
    rc, out, _ = run(f"git -C {path} rev-list --all --not --remotes --count")
    g["commits_not_on_any_remote"] = int(out.strip() or 0)
    rc, out, _ = run(f"git -C {path} rev-list --all --not --remotes --format='%H %P' --no-commit-header | head -400")
    g["local_only_commits"] = [dict(zip(("sha", "parents"), (l.split(" ", 1) + [""])[:2])) for l in out.splitlines()]
    rc, out, _ = run(f"git -C {path} log --all --decorate --oneline | wc -l")
    g["log_all_count"] = int(out.strip() or 0)
    return g


def classify(rel):
    low = rel.lower()
    if any(k in low for k in ("signing.key", ".key")) and not low.endswith("verifying.key"):
        return "secret"
    if low.endswith("erl_crash.dump") or "crash" in low and low.endswith(".dump"):
        return "crash_dump"
    if "/receipts/" in low or low.startswith("receipts/") or low.endswith((".receipt.json", ".r.json", ".affidavit.json")):
        return "evidence"
    if low.endswith((".log", ".out", ".err")):
        return "evidence_log"
    if low.endswith((".md", ".ttl", ".json", ".jsonl", ".rq", ".txt", ".tsv")):
        return "document_or_data"
    if low.endswith((".py", ".js", ".sh", ".mjs", ".ts", ".ex", ".exs")):
        return "tooling"
    return "other"


def walk_files(root, skip_git_tracked_in=None):
    files, caches = [], []
    for dirpath, dirs, fnames in os.walk(root):
        keep = []
        for d in dirs:
            full = os.path.join(dirpath, d)
            if d == ".git":
                continue
            if d in CACHE_DIRS:
                rc, out, _ = run(f"du -sk '{full}'", timeout=300)
                caches.append({"path": full, "kb": int((out.split() or ["0"])[0]), "class": "build_cache_reproducible"})
                continue
            if os.path.isfile(os.path.join(full, ".git")) or os.path.isdir(os.path.join(full, ".git")):
                caches.append({"path": full, "class": "git_checkout", "note": "inventoried as git"})
                continue
            keep.append(d)
        dirs[:] = keep
        for f in fnames:
            fp = os.path.join(dirpath, f)
            if os.path.islink(fp) or not os.path.isfile(fp):
                continue
            rel = fp[len(root) + 1:]
            c = classify(rel)
            ent = {"path": fp, "size": os.path.getsize(fp), "class": c}
            ent["sha256"] = None if c in ("secret", "crash_dump") and os.path.getsize(fp) > 0 and c == "crash_dump" else sha256(fp)
            files.append(ent)
    return files, caches


def worktree_extras(path):
    """Untracked (not ignored) and ignored files of a git worktree (tracked content lives in git objects)."""
    rc, out, _ = run(f"git -C {path} status --porcelain --ignored --untracked-files=all")
    ents = []
    for line in out.splitlines():
        code, rel = line[:2], line[3:]
        full = os.path.join(path, rel)
        top = rel.split("/")[0]
        if code == "!!":
            if any(part in CACHE_DIRS for part in rel.rstrip("/").split("/")):
                continue
            kind = "ignored"
        elif code == "??":
            kind = "untracked"
        else:
            kind = "tracked_modified"
        e = {"path": full, "git_status": kind, "class": classify(rel)}
        if os.path.isfile(full):
            e["size"] = os.path.getsize(full)
            e["sha256"] = sha256(full) if e["class"] != "crash_dump" else None
        elif os.path.isdir(full):
            e["dir"] = True
        ents.append(e)
    return ents


def main():
    ts = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    man = {"migration_id": "v26923-single-repo", "phase": "1-inventory", "generated_at": ts, "shadow_root": SHADOW,
           "source_topology": "canonical checkouts + git worktrees under ~/wt/v26922 (int, lane, witness, scratch) + shadow clone + driver substrate",
           "target_topology": "one canonical checkout per repository, normal branches, zero auxiliary worktrees",
           "shadow_mutation_frozen": True, "repos": {}, "shadow_files": [], "shadow_caches": [], "shadow_worktrees": [],
           "scratch": []}
    for name, paths in CHECKOUTS.items():
        man["repos"][name] = [git_inventory(name, p) for p in paths]
    for entry in sorted(os.listdir(SHADOW)):
        full = os.path.join(SHADOW, entry)
        if os.path.isdir(full):
            # linked worktrees and the shadow clone below this level
            for dirpath, dirs, _ in os.walk(full):
                if os.path.exists(os.path.join(dirpath, ".git")):
                    man["shadow_worktrees"].append({"path": dirpath, "linked": os.path.isfile(os.path.join(dirpath, ".git")),
                                                    "head": run(f"git -C {dirpath} rev-parse HEAD")[1].strip(),
                                                    "branch": run(f"git -C {dirpath} branch --show-current")[1].strip(),
                                                    "extras": worktree_extras(dirpath)})
                    dirs[:] = []
                    continue
                dirs[:] = [d for d in dirs if d not in CACHE_DIRS and d != ".git"]
    files, caches = walk_files(SHADOW)
    man["shadow_files"], man["shadow_caches"] = files, caches
    if os.path.isdir(SCRATCH):
        for d in sorted(os.listdir(SCRATCH)):
            full = os.path.join(SCRATCH, d)
            rc, out, _ = run(f"du -sk '{full}'", timeout=300)
            n = run(f"find '{full}' -type f | wc -l", timeout=300)[1].strip()
            man["scratch"].append({"path": full, "kb": int((out.split() or ["0"])[0]), "files": int(n or 0)})
    out = os.path.join(HERE, "MANIFEST.json")
    json.dump(man, open(out, "w"), indent=1, sort_keys=True)
    open(os.path.join(HERE, "MANIFEST.sha256"), "w").write(f"{sha256(out)}  MANIFEST.json\n")
    summ = {"repos": {k: [{"path": g["path"], "branch": g.get("branch"), "dirty": len((g.get("status_short") or "").splitlines()),
                           "local_only": g.get("commits_not_on_any_remote"), "worktrees": len([l for l in (g.get("worktree_list") or "").splitlines() if l.startswith("worktree ")])}
                          for g in v] for k, v in man["repos"].items()},
            "shadow_files": len(files), "shadow_file_bytes": sum(f["size"] for f in files),
            "classes": {c: sum(1 for f in files if f["class"] == c) for c in {f["class"] for f in files}},
            "shadow_worktrees": [(w["path"], w["branch"], w["head"][:10], len(w["extras"])) for w in man["shadow_worktrees"]],
            "caches_kb": sum(c.get("kb", 0) for c in caches)}
    print(json.dumps(summ, indent=1))


if __name__ == "__main__":
    main()
