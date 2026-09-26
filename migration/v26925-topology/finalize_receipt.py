#!/usr/bin/env python3
"""Adds base_sha, typed BLOCKED items and findings to TOPOLOGY-RECEIPT.stage1.json (after `topology.py receipt`)."""

import json, subprocess, os

H = os.path.dirname(os.path.abspath(__file__))
p = os.path.join(H, "TOPOLOGY-RECEIPT.stage1.json")
r = json.load(open(p))
r["identity"]["base_sha"] = subprocess.run(["git", "hash-object", os.path.join(H, "scope.json")], capture_output=True, text=True).stdout.strip()
r["standing"]["value"] = "PARTIAL_ALIVE"
r["standing"]["broken_term"] = "R_missing_authority"
r["standing"]["derived_from"] = (
    "replay commands at subject_sha (git blob id of INVENTORY.json): unit tests exit 0, guard corpus 40 cases 0 failures, "
    "gate PASS + drill PASS for every retired copy, verify exit 1 with 3 typed BLOCKED violations (owner sign-off / submodule owner decision)"
)
r["blocked"] = [
    {
        "item": "/Users/sac/unibit/ostar_ref/.claude/worktrees/agent-ab316fa1, agent-ab9779ba",
        "type": "BLOCKED(OWNER_SIGNOFF)",
        "broken_term": "R_missing_authority",
        "class": "AUTHORITY_FAILURE",
        "note": "preserved into unibit refs/preserve/v26.9.25/unibit_ostar_ref_* (+ backup branches); ostar CANONICAL_MAP (/Users/sac/chatmangpt/ostar) needs operator sign-off; gate refuses R16 (unarchived secrets on disk) + R17",
    },
    {
        "item": "/Users/sac/clap-noun-verb/clap-noun-verb-any/playground/autofde-lab",
        "type": "BLOCKED(SUBMODULE_OWNER_DECISION)",
        "broken_term": "R_missing_authority",
        "class": "AUTHORITY_FAILURE",
        "note": "declared submodule with 1 uncommitted change; preserved into autofde-lab refs/preserve (local-only + verified bundle); counts toward M until its owner commits or discards the change",
    },
    {
        "item": "commit TOPOLOGY-RECEIPT to chatman-ecosystem via PR (design P8)",
        "type": "BLOCKED(LANE_OCCUPIED)",
        "broken_term": "R_missing_replay",
        "class": "DEPENDENCY_FAILURE",
        "note": "chatman-ecosystem is a stage-2 lane repo; receipt durable only at ~/.claude/migration/v26925-topology (not a git repository)",
    },
    {
        "item": "mirror topology guard into xaas / ggen_igniter / chatman-ecosystem repo guards",
        "type": "BLOCKED(LANE_OCCUPIED)",
        "broken_term": "R_not_fed_back",
        "class": "DEPENDENCY_FAILURE",
        "note": "stage-2 lane repos",
    },
]
r["findings"] = [
    "bcinr playground/.ggen/keys/signing.key (blob a2de77d9) and praxis .praxis/keys/private.key (blob afa504b7) are tracked private keys reachable from origin non-backup refs and are not in the v26.9.24 rotation set. First-pass backup branches (records superseded-1) carried these paths in snapshot trees; no new blob was exposed (both blobs verified reachable from origin non-backup refs).",
    "knhk/.lh, knhk/rust, knhk/playground/dod-validator are not self-clones: their .git holds only hooks; the files are tracked content of knhk (DEGENERATE_GIT_RESIDUE, kept).",
    "autofde-lab .claude/worktrees orphans (gitdir -> deleted /Users/sac/scikit-decide) match autofde-lab content (nearest-base ratios 0.008-0.20); nested cpp/sdk/* and cpp/tests/data/pddl orphans are third-party submodule trees, archived local-only with bundles.",
    "wt-v26918/ign-* and ggen-* were linked worktrees of ggen-ecosystem/.git/modules/vendor/{ggen_igniter,ggen}; their admin dirs moved to Trash with them.",
    "22 drill verdicts for autofde-lab were restored from the append-only verify/restore-drill.txt after a later drill of the same queue overwrote the part file (fixed: drill parts now merge).",
]
json.dump(r, open(p, "w"), indent=1, sort_keys=True)
