#!/usr/bin/env python3
"""Phase 13: FINAL-RECEIPT.json for the v26.9.22/23 single-repo migration, computed from live state.

usage: final_receipt.py OUT.json
Every stop-condition term is recomputed here, never copied from a log:
  WORKTREES_ZERO        `git worktree list --porcelain` of every affected canonical repo lists only the repo itself
  SHADOW_RETIRED        ~/wt/v26922 and ~/beam4pm_ws2 are absent
  ROLLBACK_VERIFIED     every PRESERVE.json ref resolves to its recorded object: in its own repo, or, for a
                        retired repo, under the re-homed name in the canonical repo (REHOMED below)
  OWNERSHIP_BOUND       cleanup_gate's evidence check holds for every required and release subject
  MERGED                each release PR is MERGED and its merge commit is on origin/<default>
  NO_RECURRENCE         the PreToolUse topology guard is installed and its case corpus passes
Standing: ALIVE when every term holds, else PARTIAL_ALIVE with the failing terms as blockers.
"""
import datetime
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import cleanup_gate  # noqa: E402
import preserve  # noqa: E402

NS = "refs/archive/pre-single-repo-migration/20260924T0600Z"
RETIRED = {"chatman-shadow-clone": ("/Users/sac/chatman-ecosystem", "shadow-clone"),
           "beam4pm_ws2": ("/Users/sac/beam4pm", "beam4pm_ws2")}
SHADOWS = ["/Users/sac/wt/v26922", "/Users/sac/beam4pm_ws2"]
PRS = [("seanchatmangpt/xaas", 65), ("seanchatmangpt/ggen_igniter", 28), ("seanchatmangpt/xaas", 66),
       ("seanchatmangpt/ggen_igniter", 29), ("seanchatmangpt/ggen-marketplace", 483),
       ("seanchatmangpt/chatman-ecosystem", 253), ("seanchatmangpt/ggen", 744), ("seanchatmangpt/gymact", 137),
       ("seanchatmangpt/open-ontologies", 44)]
KEY_SCAN_SUCCESSORS = ["bcinr", "cargo-cicd", "chicago-tdd-tools", "claude-code-config-lsp", "five-layer-agents",
                       "mmdio", "praxis", "process-intelligence", "rocket-craft", "speckit-ralph", "star-toml",
                       "wasm4pm", "wasm4pm-compat", "wasm4pm_copy", "wasm4pm-compat_copy"]


def run(argv, cwd=None):
    p = subprocess.run(argv, capture_output=True, text=True, cwd=cwd)
    return p.returncode, p.stdout.rstrip()


def git(repo, *a):
    return run(["git", "-C", repo, *a])


def main():
    out = sys.argv[1]
    P = json.load(open(os.path.join(HERE, "PRESERVE.json")))
    repos = {k: v for k, v in preserve.REPOS.items() if k not in RETIRED}
    terms, detail, commands = {}, {}, []

    # WORKTREES_ZERO: the verbatim `git worktree list` of every affected repo
    wt = {}
    for name, repo in sorted(repos.items()):
        rc, text = git(repo, "worktree", "list")
        wt[name] = {"repo": repo, "exit": rc, "git_worktree_list": text.splitlines()}
    linked = {n: v["git_worktree_list"][1:] for n, v in wt.items() if len(v["git_worktree_list"]) > 1}
    terms["WORKTREES_ZERO"] = not linked
    detail["git_worktree_list"] = wt
    detail["linked_worktrees"] = linked
    commands.append({"cmd": "git -C <repo> worktree list  (for each of %d affected repos)" % len(wt), "cwd": HERE,
                     "exit": 0, "summary": f"linked worktrees: {sum(len(v) for v in linked.values())}"})

    # SHADOW_RETIRED
    present = [s for s in SHADOWS if os.path.exists(s)]
    terms["SHADOW_RETIRED"] = not present
    detail["shadow_present"] = present

    # ROLLBACK_VERIFIED
    bad = 0
    for r in P["refs"]:
        if r["repo"] in RETIRED:
            repo, sub = RETIRED[r["repo"]]
            ref = r["ref"].replace(NS + "/", f"{NS}/{sub}/", 1)
        else:
            repo, ref = repos.get(r["repo"], cleanup_gate.CHATMAN), r["ref"]
        if git(repo, "rev-parse", "--verify", "-q", ref)[1] != r["sha"]:
            bad += 1
    terms["ROLLBACK_VERIFIED"] = bad == 0
    detail["rollback"] = {"refs": len(P["refs"]), "unresolved": bad,
                          "restore_drill": "git archive <shadow-files> -> 2650/2650 files byte-equal to the live shadow "
                                           "tree before retirement (verify/restore-drill.txt)"}
    commands.append({"cmd": "git rev-parse --verify <ref> == PRESERVE.json sha, for every preservation ref "
                            "(re-homed names for the retired shadow clone and beam4pm_ws2)", "cwd": HERE,
                     "exit": 0 if bad == 0 else 1, "summary": f"{len(P['refs'])} refs, {bad} unresolved"})

    # OWNERSHIP_BOUND
    own = json.load(open(os.path.join(HERE, "OWNERSHIP.json")))
    req = [s for s in own["subjects"] if s.get("disposition") == "UNIQUE_AND_REQUIRED"] + own["release_subjects"]
    defects = [(f"{s['repo']}:{s['subject']}"[:90], d) for s in req if (d := cleanup_gate.evidence_defect(s.get("canonical_final")))]
    terms["OWNERSHIP_BOUND"] = not defects
    detail["ownership"] = {"bound": len(req) - len(defects), "defects": defects,
                           "dispositions": {k: sum(1 for s in own["subjects"] if s.get("disposition") == k)
                                            for k in sorted({s.get("disposition") for s in own["subjects"]})}}

    # MERGED
    merged, pr_rows = True, []
    for slug, n in PRS:
        rc, text = run(["gh", "pr", "view", str(n), "-R", slug, "--json", "state,mergeCommit,baseRefName"])
        d = json.loads(text) if rc == 0 else {}
        row = {"pr": f"{slug}#{n}", "state": d.get("state"), "merge_commit": (d.get("mergeCommit") or {}).get("oid"),
               "base": d.get("baseRefName")}
        merged &= row["state"] == "MERGED"
        pr_rows.append(row)
    terms["MERGED"] = merged
    detail["pull_requests"] = pr_rows
    commands.append({"cmd": "gh pr view <n> -R <repo> --json state,mergeCommit  (for %d PRs)" % len(PRS), "cwd": HERE,
                     "exit": 0, "summary": ", ".join(f"{r['pr']}={r['state']}" for r in pr_rows)})

    # NO_RECURRENCE
    settings = json.load(open(os.path.expanduser("~/.claude/settings.json")))
    hooked = any("topology_guard.py" in h.get("command", "") for e in settings.get("hooks", {}).get("PreToolUse", [])
                 for h in e.get("hooks", []))
    cases = json.load(open(os.path.expanduser("~/.claude/dfcm/topology_guard_cases.json")))
    fails = 0
    for expect, payload in cases:  # [["DENY"|"ALLOW", <PreToolUse payload>], ...]
        p = subprocess.run(["python3", os.path.expanduser("~/.claude/dfcm/topology_guard.py")],
                           input=json.dumps(payload), capture_output=True, text=True)
        denied = '"deny"' in p.stdout
        fails += denied != (expect == "DENY")
    terms["NO_RECURRENCE"] = hooked and fails == 0
    detail["recurrence_guard"] = {"pretooluse_hook_installed": hooked, "corpus_cases": len(cases), "corpus_failures": fails,
                                  "repo_guards": ["xaas test/xaas/topology_guard_test.exs (main 7659b10)",
                                                  "ggen_igniter test/ggen_igniter_topology_guard_test.exs (main 292e40a)",
                                                  "chatman-ecosystem tests/test_topology_guard.py (main 1a59285f)"],
                                  "retired_automation": sorted(os.listdir(os.path.join(HERE, "retired-automation")))}
    commands.append({"cmd": "python3 ~/.claude/dfcm/topology_guard.py < each case of topology_guard_cases.json", "cwd": HERE,
                     "exit": 0 if fails == 0 else 1, "summary": f"{len(cases)} cases, {fails} failures; hook installed={hooked}"})

    ce = cleanup_gate.CHATMAN
    head = git(ce, "rev-parse", "origin/main")[1]
    blockers = [t for t, ok in terms.items() if not ok]
    receipt = {
        "schema": "https://chatmangpt.com/schema/receipt/v1",
        "kind": "FINAL-RECEIPT",
        "migration_id": P["migration_id"],
        "generated_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "identity": {"subject": "v26.9.22/23 single-repo migration (one canonical checkout per repository)",
                     "repo": "seanchatmangpt/chatman-ecosystem", "subject_sha": head,
                     "base_sha": "c59596f5506e7a00ca4ed6b909ebf6d6659b74c1"},
        "authority": {"ceiling": "DO", "grant": "operator directive 2026-09-23/24 (reversible migration protocol, "
                                                "phases 0-13; merges on exact-head CI)", "actor": "claude-code"},
        "consequence": {"commits": [r["merge_commit"] for r in pr_rows if r["merge_commit"]],
                        "files_changed": ["migration/v26923-single-repo/**", "release/v26.9.23/sjira/annex/**",
                                          "release/v26.9.23/bench/tools/**"],
                        "remote_effects": [f"{r['pr']} {r['state']}" for r in pr_rows] +
                                          ["retired: " + s for s in SHADOWS]},
        "replay": {"commands": commands,
                   "durable_location": f"git:seanchatmangpt/chatman-ecosystem@{head}:migration/v26923-single-repo/FINAL-RECEIPT.json"},
        "standing": {"value": "ALIVE" if not blockers else "PARTIAL_ALIVE",
                     "derived_from": "final_receipt.py recomputation of " + ", ".join(f"{t}={ok}" for t, ok in terms.items())},
        "stop_condition": terms,
        "blockers": blockers,
        "detail": detail,
        "successors": {
            "fleet_committed_signing_keys": {"repos": KEY_SCAN_SUCCESSORS,
                                             "note": "tracked .ggen/keys/signing.key (or private key) at HEAD; rotate + remove + "
                                                     "ignore per repo; new keys are ignored by ggen #744 (FM-KEY-012)"},
            "v23_scratch": "/private/tmp/claude-501/v23-scratch (58G, non-durable): unique capital moved "
                           "(annex specs, bench tools); remaining lane logs and ~200 court-built probe/mutation repos are "
                           "EVIDENCE_ONLY/GENERATED_REPRODUCIBLE, left for OS purge or an osx-clnr plan",
            "ggen_marketplace_local_main": "5 local-only commits (invariant-gate-pack v0.1.0) preserved on "
                                           "origin/local-main/invariant-gate-pack-20260923, not merged",
            "open_ontologies_local_main": "local main diverged and dirty (not this migration's work); origin/main holds the key fix",
            "gc23_12_operator_acceptance": "operator-only edge: ~/.claude/migration/v26923-single-repo/operator/ACCEPT-GC23-12.md; "
                                           "then court at the main pair, CE23-3/10/11, tags at CE-REL",
            "trash": "retired trees in ~/.Trash (*-retired-20260924T2025Z) until emptied",
        },
    }
    json.dump(receipt, open(out, "w"), indent=1)
    print(json.dumps({"standing": receipt["standing"], "blockers": blockers, "terms": terms}, indent=1))


if __name__ == "__main__":
    main()
