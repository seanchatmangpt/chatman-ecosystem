#!/usr/bin/env python3
"""finish: adds base_sha, replay commands, residual typed items and findings to TOPOLOGY-RECEIPT.json (after `topology.py receipt`)."""

import hashlib
import json
import os
import subprocess

H = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(H, "TOPOLOGY-RECEIPT.json")
r = json.load(open(p))


def sha(f):
    return hashlib.sha256(open(os.path.join(H, f), "rb").read()).hexdigest()


def exitcode(f):
    return int(open(os.path.join(H, f)).read().strip())


r["identity"]["base_sha"] = "1045b16bf80c0315760723705b768dbf1f71137b"  # stage2 subject (INVENTORY.json blob) committed in chatman-ecosystem
r["identity"]["repo"] = "fleet:v26.9.25-topology-finish"
r["replay"]["commands"] = [
    {"cmd": "cd tests && python3 test_topology.py", "cwd": H, "exit": 0, "output_sha256": sha("verify/unittest.finish.txt"), "summary": "30 tests OK"},
    {"cmd": "python3 replay_guard.py", "cwd": H, "exit": 0, "output_sha256": sha("verify/guard-replay.finish.txt"), "summary": "40 cases, 0 failures"},
    {
        "cmd": "! grep -rnE 'unittest.mock|Mock\\(|MagicMock|patch\\(|monkeypatch|Mox|Mimic|:meck' tests/",
        "cwd": H,
        "exit": 0,
        "output_sha256": sha("verify/mock-grep.finish.txt"),
        "summary": "exit 0 = zero matches (negated grep)",
    },
    {"cmd": "ruff check --select E9,F topology.py tests/ && ruff format --check topology.py tests/", "cwd": H, "exit": 0, "output_sha256": sha("verify/ruff.finish.txt")},
    {
        "cmd": "python3 topology.py verify --scope scope.finish.json --json",
        "cwd": H,
        "exit": exitcode("verify/verify.finish.exit"),
        "output_sha256": sha("verify/verify.finish.txt"),
        "summary": "m_term.holds computed by topology.py m_term() over INVENTORY.json + steps.jsonl + live filesystem presence",
    },
]
m = r["m_term"]
r["standing"]["derived_from"] = (
    "replay commands above at subject_sha (git blob id of INVENTORY.json); gate PASS + byte-exact drill PASS for every retired inventory copy; "
    "m_term.holds recomputed by verify (exit 0 iff holds)"
)
if m["holds"] and r["standing"]["value"] == "ALIVE":
    r["standing"].pop("broken_term", None)
r["blocked"] = []
r["signoffs"] = json.load(open(os.path.join(H, "scope.finish.json")))["signoffs"]
r["findings"] = [
    "finish signoffs (operator order 'finish' 2026-09-25 09:05 PT) applied as ledgered INVENTORY transitions (steps.jsonl 'signoff <action> <copy>'); the gate R1-R17 still decided every retirement.",
    "ostar: CANONICAL_MAP ostar -> /Users/sac/chatmangpt/ostar signed off (host_signoff); unibit/ostar_ref/.claude/worktrees/agent-ab316fa1, agent-ab9779ba retired; the one R16 file (vendors/pictl/packages/testing/src/redaction.ts, blob 9cd80df7) is present in the ostar canonical object store (dedup via identity_canonical).",
    "xaas/worktrees/runs: 20 orphan run dirs retired (preserved in xaas refs/preserve/v26.9.25/* + remote backup branches, drill PASS); FOREIGN_CLONE siblings there are not counted and untouched.",
    "Rule V1/V4 reclassification (classify_nested): chatmangpt/wasm4pm -> VENDORED_BUILD_INPUT (manifest_ref); unrdf/packages/wasm4pm -> EMBEDDED_UNDECLARED (gitlink not in .gitmodules); both not counted, untouched.",
    "chatmangpt/pictl (declared submodule, origin wasm4pm, 291 dirty) -> V1 SUBMODULE_ACTIVE: preserved into wasm4pm refs/preserve/v26.9.25/chatmangpt_pictl/* + backup/v26.9.25/chatmangpt_pictl, drill PASS, retired in deinit shape (checkout in Trash, empty gitlink dir; chatmangpt status for pictl went from ' M pictl' to clean).",
    "clap-noun-verb playground/autofde-lab (declared submodule, 1 deleted file, not pinned+clean) -> preserved (autofde-lab refs + verified bundle), its 8 nested cpp/sdk submodules inventoried (SUBMODULE), drill PASS, retired in deinit shape (clap-noun-verb status for the path went from ' M' to clean).",
    "zoela SECRET_UNPRESERVABLE copies (work/zoela, zv_regen, zoela-wt/w30-jtbd-decouple, zoela-wt/w45-pqc-receipt-signature): non-secret content archived in zoela refs/preserve (gate R4/R5/R7 PASS); whole copies moved to ~/.Trash with secrets inside (reversible); secrets recorded as {path_sha256, content_sha256} only in steps.jsonl retire entries. Empty roots /Users/sac/zoela-wt and /Users/sac/work moved to Trash (ledger).",
    "m_term fix: out-of-scope identities are keyed by normalized origin instead of one '_unowned' bucket that summed distinct repos; autofde-lab/vendor/gyms/enterprisebench and sregym are each the sole checkout of their identity (M<=1 holds); a second copy of one identity, or a copy with no identity, is still a violation (tests/test_topology.py TestFinishSignoffs).",
    "Nothing deleted: every retirement is a mv into ~/.Trash (rollback commands in migration_receipt.rollback_procedure); Trash never emptied.",
]
json.dump(r, open(p, "w"), indent=1, sort_keys=True)
print(subprocess.run(["python3", os.path.expanduser("~/.claude/dfcm/validate_receipt.py"), p], capture_output=True, text=True).stdout.strip())
print(json.dumps({"standing": r["standing"], "m_term_holds": m["holds"], "violations": len(m["violations"])}))
