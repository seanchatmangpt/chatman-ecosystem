#!/usr/bin/env python3
"""Phase 3/4 deterministic pre-classification of shadow subjects (git object inspection only).

Shadow subjects = branches whose worktree lived under ~/wt/v26922 (collapse dry-run record + remaining shadow worktrees) and
branches this program created (name patterns below). For each: ALREADY_ON_CANONICAL (ancestor of / patch-equivalent to the
default branch), IN_RELEASE_BRANCH (ancestor of / patch-equivalent to the repo's release branch, which lands via the release
merge), else NEEDS_JUDGMENT with the unique commit list. Writes PRECLASS.json.
"""
import json
import os
import re
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
PROGRAM = re.compile(r"^(friday/|release/v26\.9\.2|v23/|ce23/|mp23/|rela/|swarm/|driver/|law-|law/|wo-|wo/|fri/|FRI-|v26922|w0/|w1/|w2/|w3/|w4/|l\d+/|lane/|v26\.9\.2[234])")
RELEASE = {"xaas": ["friday/gc-fri-0800"], "ggen_igniter": ["friday/gc-fri-0800"],
           "ggen-marketplace": ["release/v26.9.23-int"], "chatman-ecosystem": ["release/v26.9.23-int"]}
REPOS = json.load(open(os.path.join(HERE, "MANIFEST.json")))["repos"]


def git(repo, *a):
    p = subprocess.run(["git", "-C", repo, *a], capture_output=True, text=True)
    return p.returncode, p.stdout.rstrip()


def main():
    dry = json.load(open("/Users/sac/wt/v26922/v26923/disk/wt-collapse-dryrun.json"))
    shadow_branches = {}
    for r in dry["rows"]:
        if r["path"].startswith(("/Users/sac/wt/v26922", "/tmp/v23-mut", "/private/tmp")) and r["action"] == "remove":
            shadow_branches.setdefault(r["repo"], {})[r["branch"] or f"detached:{r['head']}"] = {"worktree": r["path"], "head": r["head"]}
    out = {}
    for name, gs in REPOS.items():
        for g in gs:
            repo = g["path"]
            if g.get("missing"):
                continue
            dflt = g.get("default_ref")
            rels = [b for b in RELEASE.get(name, []) if git(repo, "rev-parse", "--verify", "-q", b)[0] == 0]
            if name == "chatman-ecosystem" and repo == "/Users/sac/chatman-ecosystem":
                continue  # canonical local lineage: handled by the chatman identity step, not branch-by-branch
            if name not in RELEASE:
                rels = [b for b in ("release/v26.9.22", "feat/v26922-release") if git(repo, "rev-parse", "--verify", "-q", b)[0] == 0]
            subjects = dict(shadow_branches.get(repo, {}))
            for ref in g.get("refs", []):
                if ref["ref"].startswith("refs/heads/"):
                    b = ref["ref"][len("refs/heads/"):]
                    if PROGRAM.search(b) and b not in subjects:
                        subjects[b] = {"head": ref["sha"], "worktree": None}
            for b, info in subjects.items():
                sha = info["head"] if b.startswith("detached:") else (git(repo, "rev-parse", "--verify", "-q", b)[1] or info["head"])
                ent = {"repo": name, "checkout": repo, "branch": b, "sha": sha, "worktree_was": info.get("worktree"), "default": dflt,
                       "on_remote": git(repo, "rev-list", "--count", sha, "--not", "--remotes")[1] == "0"}
                if not sha or git(repo, "cat-file", "-t", sha)[1] != "commit":
                    ent["class"] = "MISSING_OBJECT"
                elif dflt and git(repo, "merge-base", "--is-ancestor", sha, dflt)[0] == 0:
                    ent["class"] = "ALREADY_ON_CANONICAL"
                    ent["evidence"] = f"ancestor of {dflt}"
                else:
                    uniq = [l[2:] for l in git(repo, "cherry", dflt, sha)[1].splitlines() if l.startswith("+")] if dflt else []
                    if dflt and not uniq:
                        ent["class"] = "ALREADY_ON_CANONICAL"
                        ent["evidence"] = f"every commit patch-equivalent on {dflt} (git cherry)"
                    else:
                        in_rel = None
                        for rb in rels:
                            if b == rb:
                                continue
                            if git(repo, "merge-base", "--is-ancestor", sha, rb)[0] == 0:
                                in_rel = f"ancestor of {rb}"
                                break
                            u2 = [l for l in git(repo, "cherry", rb, sha)[1].splitlines() if l.startswith("+")]
                            if not u2:
                                in_rel = f"patch-equivalent in {rb}"
                                break
                        if b in rels:
                            ent["class"] = "RELEASE_BRANCH"
                        elif in_rel:
                            ent["class"] = "IN_RELEASE_BRANCH"
                            ent["evidence"] = in_rel
                        else:
                            ent["class"] = "NEEDS_JUDGMENT"
                        ent["unique_vs_default"] = len(uniq)
                        ent["unique_commits"] = [dict(zip(("sha", "subject"), (git(repo, "log", "-1", "--format=%H%x09%s", c)[1].split("\t", 1) + [""])[:2]))
                                                 for c in uniq[:40]]
                out.setdefault(name, []).append(ent)
    json.dump(out, open(os.path.join(HERE, "PRECLASS.json"), "w"), indent=1)
    from collections import Counter
    for name, ents in out.items():
        c = Counter(e["class"] for e in ents)
        print(f"{name:18} {dict(c)}")
    print("NEEDS_JUDGMENT total", sum(1 for ents in out.values() for e in ents if e["class"] == "NEEDS_JUDGMENT"))


if __name__ == "__main__":
    main()
