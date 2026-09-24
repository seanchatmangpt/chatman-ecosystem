#!/usr/bin/env python3
"""Replay/verify the v26922 cleanup (workflow wf_301c29f7-ec0, 2026-09-23) against its post-state.

Reads cleanup-manifest.json next to this file and re-checks, with real git/filesystem commands,
that every executed action left the state it claims:
  removals   : path gone, not in `git worktree list`, branch still exists and contains the old HEAD
               (or, for a detached HEAD, some ref still contains it)
  preserve   : refs/preserve/v26.9.23/cleanup/<slug> == recorded commit, tree == recorded tree,
               old HEAD is its parent, diff --shortstat vs HEAD == recorded, no signing.key in tree
  copies     : preserved uv.lock copies hash to the recorded sha256
  artifacts  : kept worktree still exists and is registered; every oclnr-deleted path is absent;
               native receipt has 0 failed; oclnr R projection validates with validate_receipt.py
  snapshot   : thin receipt lists thinned snapshots and snapshots_after == []
  untouched  : never-touch / rejected / skipped paths still exist (conservation twin)
Idempotent and read-only. Prints one line per check; exit 0 iff all checks pass.
"""
import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
M = json.loads((HERE / "cleanup-manifest.json").read_text())
VALIDATE = str(Path.home() / ".claude/dfcm/validate_receipt.py")
results = []


def git(repo, *args):
    p = subprocess.run(["git", "-C", repo, *args], capture_output=True, text=True)
    return p.returncode, p.stdout.strip()


def check(name, ok, detail=""):
    results.append((name, bool(ok)))
    print(("PASS " if ok else "FAIL ") + name + (" :: " + detail if detail else ""))


def registered(repo, path):
    rc, out = git(repo, "worktree", "list", "--porcelain")
    return rc == 0 and ("worktree " + path) in out.splitlines()


for r in M["removals"]:
    p, repo, head = r["path"], r["repo"], r["head"]
    check(f"removed:gone {p}", not Path(p).exists())
    check(f"removed:unregistered {p}", not registered(repo, p))
    if r["branch"]:
        ref = "refs/heads/" + r["branch"]
        rc, tip = git(repo, "rev-parse", "--verify", "-q", ref)
        check(f"branch:kept {repo} {ref}", rc == 0, f"tip={tip[:12]} head={head[:12]}")
        rc2, _ = git(repo, "merge-base", "--is-ancestor", head, ref)
        check(f"branch:contains-head {ref}", rc == 0 and rc2 == 0)
    else:
        rc, out = git(repo, "for-each-ref", "--contains", head, "--format=%(refname)")
        n = len([x for x in out.splitlines() if x])
        check(f"detached:reachable {head[:12]} in {repo}", rc == 0 and n > 0, f"{n} refs")
    pr = r.get("preserve")
    if pr:
        rc, c = git(repo, "rev-parse", "--verify", "-q", pr["ref"])
        check(f"preserve:ref {pr['ref']}", rc == 0 and c == pr["commit"], c[:12])
        _, t = git(repo, "rev-parse", pr["commit"] + "^{tree}")
        check(f"preserve:tree {pr['ref']}", t == pr["tree"], t[:12])
        _, par = git(repo, "rev-parse", pr["commit"] + "^1")
        check(f"preserve:parent-is-head {pr['ref']}", par == head)
        _, st = git(repo, "diff", "--shortstat", head, pr["commit"])
        check(f"preserve:stat {pr['ref']}", st.strip() == pr["head_stat"], st.strip())
        if pr["expect_no_signing_key"]:
            _, names = git(repo, "ls-tree", "-r", "--name-only", pr["commit"])
            sk = [x for x in names.splitlines() if x.endswith("signing.key")]
            vk = [x for x in names.splitlines() if x.endswith("verifying.key")]
            check(f"preserve:no-secret-key {pr['ref']}", not sk and vk, f"signing={len(sk)} verifying={len(vk)}")
    cp = r.get("copy")
    if cp:
        h = hashlib.sha256(Path(cp["path"]).read_bytes()).hexdigest() if Path(cp["path"]).is_file() else None
        check(f"copy:sha256 {cp['path']}", h == cp["sha256"], (h or "missing")[:12])

for a in M["artifacts"]:
    wt = a["worktree"]
    check(f"artifacts:worktree-kept {wt}", Path(wt).is_dir() and registered(a["repo"], wt))
    nat = json.loads(Path(a["native_receipt"]).read_text())["execution_record"]["results"]
    failed = [x for x in nat if x["status"] != "deleted"]
    check(f"artifacts:oclnr-all-deleted {Path(a['native_receipt']).name}", not failed and nat, f"{len(nat)} items")
    for x in nat:
        check(f"artifacts:absent {x['path']}", not Path(x["path"]).exists())
    v = subprocess.run([sys.executable, VALIDATE, a["r_receipt"]], capture_output=True, text=True)
    check(f"artifacts:R-admitted {Path(a['r_receipt']).name}", v.returncode == 0, v.stdout.strip().splitlines()[0] if v.stdout else "")

for o in M["other"]:
    if o["kind"] == "snapshot_thin":
        s = json.loads(Path(o["receipt"]).read_text())
        check("snapshot:thinned", len(s["snapshots_thinned"]) == 3 and s["snapshots_after"] == [],
              f"thinned={len(s['snapshots_thinned'])}")
        v = subprocess.run([sys.executable, VALIDATE, o["r_receipt"]], capture_output=True, text=True)
        check("snapshot:R-admitted", v.returncode == 0)

for p in M["untouched"]:
    check(f"untouched:exists {p}", Path(p).exists())

bad = [n for n, ok in results if not ok]
print(f"SUMMARY checks={len(results)} pass={len(results) - len(bad)} fail={len(bad)}")
sys.exit(1 if bad else 0)
