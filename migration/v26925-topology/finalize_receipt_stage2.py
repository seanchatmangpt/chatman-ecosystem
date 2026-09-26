#!/usr/bin/env python3
"""Stage 2: adds base_sha, replay commands, typed BLOCKED items and findings to TOPOLOGY-RECEIPT.json (after `topology.py receipt`)."""

import hashlib, json, os, subprocess

H = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(H, "TOPOLOGY-RECEIPT.json")
r = json.load(open(p))


def sha(f):
    return hashlib.sha256(open(os.path.join(H, f), "rb").read()).hexdigest()


r["identity"]["base_sha"] = json.load(open(os.path.join(H, "TOPOLOGY-RECEIPT.stage1.json")))["identity"]["subject_sha"]
r["replay"]["commands"] = [
    {"cmd": "cd tests && python3 test_topology.py", "cwd": H, "exit": 0, "output_sha256": sha("verify/unittest.stage2.txt"), "summary": "27 tests OK"},
    {"cmd": "python3 replay_guard.py", "cwd": H, "exit": 0, "output_sha256": sha("verify/guard-replay.stage2.txt"), "summary": "40 cases, 0 failures"},
    {"cmd": "grep -rnE 'unittest.mock|Mock\\(|MagicMock|patch\\(|monkeypatch|Mox|Mimic|:meck' tests/", "cwd": H, "exit": 1,
     "output_sha256": sha("verify/mock-grep.stage2.txt"), "summary": "exit 1 = zero matches"},
    {"cmd": "ruff check --select E9,F . && ruff format --check .", "cwd": H, "exit": 0, "output_sha256": sha("verify/ruff.stage2.txt")},
    {"cmd": "python3 topology.py verify --scope scope.merged.json --json", "cwd": H, "exit": 1, "output_sha256": sha("verify/verify.stage2.txt"),
     "summary": "m_term.holds=false; every violation carries a typed blocked reason"},
]
r["standing"]["value"] = "PARTIAL_ALIVE"
r["standing"]["broken_term"] = "R_missing_authority"
r["standing"]["derived_from"] = ("replay commands above at subject_sha (git blob id of INVENTORY.json); gate PASS + byte-exact drill PASS for every retired "
                                 "inventory copy; verify exit 1 with only typed violations (owner sign-off / secret-unpreservable / embedded-in-foreign-repo / declared submodule)")
B = lambda item, t, bt, cl, note: {"item": item, "type": t, "broken_term": bt, "class": cl, "note": note}
r["blocked"] = [
    B("/Users/sac/work/zoela, /Users/sac/zv_regen (untracked .ggen/keys/signing.key); /Users/sac/zoela-wt/w30-jtbd-decouple, w45-pqc-receipt-signature (.env)",
      "BLOCKED(SECRET_UNPRESERVABLE)", "R_missing_authority", "AUTHORITY_FAILURE",
      "gate R16: secret files not byte-identical in canonical zoela and not archivable; everything else preserved (refs + backup branches); operator decides per key"),
    B("/Users/sac/chatmangpt/wasm4pm, /Users/sac/unrdf/packages/wasm4pm", "BLOCKED(EMBEDDED_IN_FOREIGN_REPO)", "R_missing_authority", "AUTHORITY_FAILURE",
      "wasm4pm clones embedded in chatmangpt (tracked content) and unrdf (gitlink path); preserved into wasm4pm refs + drill PASS; retiring would mutate foreign repos"),
    B("/Users/sac/xaas/worktrees/runs/* (20 orphan run worktrees)", "BLOCKED(OWNER_SIGNOFF)", "R_missing_authority", "AUTHORITY_FAILURE",
      "lane order retires ~/xaas/worktrees/runs only 'if registered'; not registered (gitdirs pointed at retired xaas-worktrees/repos); preserved + drill PASS"),
    B("/Users/sac/unibit/ostar_ref/.claude/worktrees/agent-ab316fa1, agent-ab9779ba", "BLOCKED(OWNER_SIGNOFF)", "R_missing_authority", "AUTHORITY_FAILURE", "carried from stage 1"),
    B("/Users/sac/clap-noun-verb/clap-noun-verb-any/playground/autofde-lab", "BLOCKED(SUBMODULE_OWNER_DECISION)", "R_missing_authority", "AUTHORITY_FAILURE", "carried from stage 1"),
    B("/Users/sac/autofde-lab/vendor/gyms/{enterprisebench,sregym}", "UNSUPPORTED(DECLARED_SUBMODULE)", "R_missing_authority", "AUTHORITY_FAILURE",
      "declared+active third-party submodules surfaced by promoting autofde-lab to a scanned canonical; counted by m_term class SUBMODULE_ACTIVE but not copies to retire"),
    B("/Users/sac/zoela-wt (holds w30, w45) and /Users/sac/work (holds work/zoela)", "BLOCKED(DEPENDENCY)", "R_missing_consequence", "DEPENDENCY_FAILURE",
      "roots retire only once their SECRET_UNPRESERVABLE children are resolved"),
    B("/Users/sac/chatmangpt/pictl (wasm4pm clone as declared chatmangpt submodule, 291 dirty)", "BLOCKED(SUBMODULE_OWNER_DECISION)", "R_missing_authority",
      "AUTHORITY_FAILURE", "not inventoried as a copy (declared submodule of an out-of-scope repo); not preserved by this lane"),
    B("commit TOPOLOGY-RECEIPT to chatman-ecosystem (design P8)", "BLOCKED(LANE_OCCUPIED)", "R_missing_replay", "DEPENDENCY_FAILURE",
      "chatman-ecosystem lane still writing; receipt durable only at ~/.claude/migration/v26925-topology (not a git repo)"),
]
r["findings"] = [
    "xaas/.claude/worktrees/ex4pm and ex4pm/ex4pm are symlinks to /Users/sac/ex4pm (aliases, not copies); the xaas alias was moved to Trash (ledger step 'retire symlink ...'); ex4pm/ex4pm left.",
    "zoela_phx (root 2189c151), dev-fresh/xaas (root c73cae83), ash_autofde, dev/zcode-cli (kingsword09 upstream), wasm4pm-compat: distinct repositories, not copies; untouched.",
    "~/wt holds mixed-owner v26922 logs + zcode-gall-shim + zocel-runs (non-git); owner unresolved, untouched.",
    "Canonical dirty state snapshotted to refs only (refs/preserve/v26.9.25/canonical-<repo>/{dirty,index,worktree-head}) for zoela(982) ex4pm(38) wasm4pm(197) ash_r2rml(15) xaas(4) autofde-lab(9) ggen_igniter(2) ggen-marketplace(14) chatgpt-cloud-elixir(111); see verify/canonical-snapshots.stage2.json.",
    "topology.py fixes this stage: per-file HEAD-blob subprocess only for redaction candidates (snapshot perf); drill re-extracts LFS pointer files with smudge disabled (byte-exact, never waived); drill skips retired copies; part ids from --only paths are slugged (a path part id had escaped HOME into /Users/sac/*.json, relocated to lane scratch/stray); manual retire evidence shape; receipt supersedes stale gate REFUSED parts with the retirement PASS.",
    "Rebaseline: work_zoela_ggen-v2_git-packs_github-actions-pack R1 drift was an index stat-cache rewrite by a lane diagnostic `git status`; index tree == HEAD tree verified before rebaseline (ledger step 'rebaseline ...').",
]
json.dump(r, open(p, "w"), indent=1, sort_keys=True)
print(subprocess.run(["python3", os.path.expanduser("~/.claude/dfcm/validate_receipt.py"), p], capture_output=True, text=True).stdout.strip())
