#!/usr/bin/env python3
"""Reversible cutover of one repository to its single canonical checkout (no worktree is created at any point).

usage: cutover.py <name> <canonical> <shadow_worktree|-> <target_branch>

Each step appends {step, precondition, forward, postcondition, falsifier, rollback, rollback_subject, ok, evidence} to steps.jsonl and
stops at the first failed postcondition (later steps never run on a broken precondition).
"""
import datetime
import hashlib
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TS = "20260924T0600Z"
NS = f"refs/archive/pre-single-repo-migration/{TS}"


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return p.returncode, p.stdout.rstrip(), p.stderr.strip()


def ledger(ent):
    ent["at"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(os.path.join(HERE, "steps.jsonl"), "a") as f:
        f.write(json.dumps(ent) + "\n")
    print(("OK   " if ent["ok"] else "FAIL ") + ent["step"] + " :: " + str(ent.get("evidence", ""))[:220])
    if not ent["ok"]:
        raise SystemExit(1)


def blob_of_file(path):
    return subprocess.run(["git", "hash-object", path], capture_output=True, text=True).stdout.strip()


def main():
    name, canon, shadow, target = sys.argv[1:5]
    slug = canon.replace("/Users/sac/", "").replace("/", "_")
    snap_ref = f"{NS}/dirty/{canon.replace('/Users/sac/', '')}"
    _, status, _ = git(canon, "status", "--porcelain", "--untracked-files=all")
    cur_branch = git(canon, "branch", "--show-current")[1]
    head0 = git(canon, "rev-parse", "HEAD")[1]
    arch = f"archive/wip/{slug}-{cur_branch.replace('/', '-')}-{TS}"
    paths = []
    for line in status.splitlines():
        rel = line[3:].strip('"')
        if " -> " in rel:
            rel = rel.split(" -> ", 1)[1]
        if line[:2].strip() in ("m", "M") and os.path.isdir(os.path.join(canon, rel, ".git")) or os.path.isfile(os.path.join(canon, rel, ".git")):
            continue  # submodule pointer state lives in the submodule's own repository
        paths.append((line[:2], rel))
    if paths:
        snap = git(canon, "rev-parse", "--verify", "-q", snap_ref)[1]
        mism = []
        for code, rel in paths:
            fp = os.path.join(canon, rel)
            if os.path.isfile(fp):
                want = blob_of_file(fp)
                got = git(canon, "rev-parse", "--verify", "-q", f"{snap}:{rel}")[1]
                if want != got:
                    mism.append(rel)
        ledger({"repo": name, "step": "S1 archival branch for dirty state", "precondition": f"{snap_ref} holds every dirty path byte-identically",
                "forward": f"git branch {arch} {snap}", "postcondition": f"{arch} resolves to {snap}",
                "falsifier": "a dirty file whose blob differs from the snapshot tree", "rollback": f"git branch -D {arch} (archive ref stays)",
                "rollback_subject": snap, "ok": bool(snap) and not mism and git(canon, "branch", "-f", arch, snap)[0] == 0,
                "evidence": f"{len(paths)} paths verified, mismatches {mism[:5]}"})
        rc1 = git(canon, "restore", "--staged", "--worktree", "--", ".")[0]
        for code, rel in paths:
            if code == "??" and os.path.isfile(os.path.join(canon, rel)):
                os.remove(os.path.join(canon, rel))
        left = git(canon, "status", "--porcelain")[1]
        ledger({"repo": name, "step": "S2 clean canonical working tree", "precondition": "S1 ok",
                "forward": "git restore --staged --worktree -- . ; rm the untracked files listed in the snapshot",
                "postcondition": "git status --porcelain empty (submodule pointers excepted)", "falsifier": "any remaining change",
                "rollback": f"git checkout {arch} -- <paths> && git reset -q", "rollback_subject": arch,
                "ok": rc1 == 0 and all(l.startswith((" m", " M")) and os.path.exists(os.path.join(canon, l[3:], ".git")) for l in left.splitlines()),
                "evidence": f"remaining: {left[:200]!r}"})
    if shadow != "-":
        wt_head = git(shadow, "rev-parse", "HEAD")[1]
        wt_status = git(shadow, "status", "--porcelain", "--untracked-files=no")[1]
        anchor = git(canon, "rev-parse", "--verify", "-q", f"{NS}/worktree-head/{shadow.replace('/Users/sac/', '')}")[1]
        rc, _, err = git(canon, "worktree", "remove", "--force", shadow)
        ledger({"repo": name, "step": "S3 remove shadow worktree", "precondition": f"{shadow} clean (tracked) at {wt_head[:10]}, HEAD anchored",
                "forward": f"git worktree remove --force {shadow}", "postcondition": "worktree gone; branch keeps the commits",
                "falsifier": "tracked changes in the worktree, or the anchor ref missing", "rollback":
                f"branch {target} + {NS}/worktree-head/... + {NS}/ignored/... (read with git show; no worktree needed)",
                "rollback_subject": anchor, "ok": rc == 0 and not wt_status and anchor == wt_head and not os.path.exists(shadow),
                "evidence": f"head {wt_head[:10]} anchor {anchor[:10]} {err[:120]}"})
    rc, _, err = git(canon, "switch", target)
    head = git(canon, "rev-parse", "HEAD")[1]
    tip = git(canon, "rev-parse", target)[1]
    ledger({"repo": name, "step": f"S4 switch canonical checkout to {target}", "precondition": "canonical tree clean",
            "forward": f"git switch {target}", "postcondition": f"HEAD == {target} tip, tree clean", "falsifier": "HEAD differs or tree dirty",
            "rollback": f"git switch {cur_branch or head0}", "rollback_subject": head0,
            "ok": rc == 0 and head == tip and not git(canon, "status", "--porcelain", "--untracked-files=no")[1],
            "evidence": f"{canon} on {target} @ {head[:10]} {err[:120]}"})


if __name__ == "__main__":
    main()
