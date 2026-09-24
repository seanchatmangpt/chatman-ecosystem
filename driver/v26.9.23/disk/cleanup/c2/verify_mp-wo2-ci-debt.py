#!/usr/bin/env python3
"""Replay checks for cleanup-2 of /Users/sac/wt/v26922/mp-wo2-ci-debt (ggen-marketplace).

Reads everything from the preserve ref in the common git dir, so it runs both before and after
the worktree is removed.  Usage:
  verify_mp-wo2-ci-debt.py --phase pre|post [--mutate blob|sig|keyhash]
--mutate corrupts one expectation in memory; the run must then FAIL (anti-vacuity).
Exit 0 = every check passed.
"""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

GIT_DIR = "/Users/sac/ggen-marketplace/.git"
WT = "/Users/sac/wt/v26922/mp-wo2-ci-debt"
REF = "refs/preserve/v26.9.23/cleanup/mp-wo2-ci-debt"
HEAD = "46122984e0ecb8ca92feb89b7e68c16af24b0ec5"
BRANCH = "refs/heads/fix/ci-debt-26922"
HERE = Path(__file__).resolve().parent
EVIDENCE_TSV = HERE / "mp-wo2-ci-debt.evidence.tsv"
KEYHASH_TSV = HERE / "mp-wo2-ci-debt.signing-key-sha256.tsv"
PACK = "packs/xaas-public-ash-projection-pack"
EVIDENCE = [
    ".ggen-v2/receipt-log.jsonl",
    ".ggen-v2/receipt.json",
    ".ggen/keys/verifying.key",
    f"{PACK}/.ggen-v2/receipt-log.jsonl",
    f"{PACK}/.ggen-v2/receipt.json",
    f"{PACK}/.ggen/keys/verifying.key",
]
SIGNING = [".ggen/keys/signing.key", f"{PACK}/.ggen/keys/signing.key"]

results = []


def git(*args, check=True):
    p = subprocess.run(["git", f"--git-dir={GIT_DIR}", *args], capture_output=True)
    if check and p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.decode().strip()}")
    return p.stdout


def rec(name, ok, detail=""):
    results.append((name, bool(ok), detail))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", choices=["pre", "post"], required=True)
    ap.add_argument("--mutate", choices=["blob", "sig", "keyhash"])
    a = ap.parse_args()

    c = git("rev-parse", "--verify", REF + "^{commit}").decode().strip()
    rec("ref_exists", re.fullmatch(r"[0-9a-f]{40}", c), c)
    parents = git("rev-list", "--parents", "-n1", c).decode().split()[1:]
    rec("parent_is_head", parents == [HEAD], " ".join(parents))

    ns = git("diff-tree", "-r", "--no-renames", "--name-status", HEAD, c).decode().splitlines()
    got = sorted(tuple(l.split("\t", 1)) for l in ns)
    rec("diff_is_exactly_evidence_added", got == sorted(("A", p) for p in EVIDENCE), repr(got))

    # evidence.tsv rows: path<TAB>git_blob<TAB>sha256
    rows = [l.split("\t") for l in EVIDENCE_TSV.read_text().splitlines() if l.strip()]
    expected = {r[0]: r[1] for r in rows}
    if a.mutate == "blob":
        k = EVIDENCE[0]
        expected[k] = expected[k][:-1] + ("0" if expected[k][-1] != "0" else "1")
    rec("evidence_rows_cover_all", sorted(expected) == sorted(EVIDENCE))
    for p in EVIDENCE:
        blob = git("rev-parse", f"{c}:{p}").decode().strip()
        rec(f"blob:{p}", blob == expected.get(p), blob)

    tree_paths = git("ls-tree", "-r", "--name-only", c).decode().splitlines()
    bad = [p for p in tree_paths
           if "signing" in p.lower() or (p.endswith(".key") and not p.endswith("verifying.key"))]
    rec("no_private_key_in_tree", not bad, repr(bad))

    msg = git("cat-file", "commit", c).decode()
    keyrows = [l.split("\t") for l in KEYHASH_TSV.read_text().splitlines() if l.strip()]
    keyhash = {r[0]: r[1] for r in keyrows}
    if a.mutate == "keyhash":
        k = SIGNING[0]
        keyhash[k] = keyhash[k][:-1] + ("0" if keyhash[k][-1] != "0" else "1")
    for p in SIGNING:
        h = keyhash.get(p, "")
        rec(f"keyhash_in_message:{p}", re.fullmatch(r"[0-9a-f]{64}", h) and f"{p} sha256={h}" in msg, h)

    from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey
    nsig = 0
    for d in [".", PACK]:
        pre = "" if d == "." else d + "/"
        vk = bytes.fromhex(git("cat-file", "blob", f"{c}:{pre}.ggen/keys/verifying.key").decode().strip())
        pk = Ed25519PublicKey.from_public_bytes(vk)
        recs = [json.loads(git("cat-file", "blob", f"{c}:{pre}.ggen-v2/receipt.json"))["record"]]
        for line in git("cat-file", "blob", f"{c}:{pre}.ggen-v2/receipt-log.jsonl").decode().splitlines():
            if line.strip():
                o = json.loads(line)
                recs.append(o.get("record", o))
        for r in recs:
            m = r["chain_hash_hex"]
            if a.mutate == "sig":
                m = m[:-1] + ("0" if m[-1] != "0" else "1")
            try:
                pk.verify(bytes.fromhex(r["signature_hex"]), m.encode())
                ok = True
            except Exception:
                ok = False
            nsig += 1
            rec(f"sig:{pre or './'}{r['chain_hash_hex'][:12]}", ok)
    rec("sig_count", nsig == 7, str(nsig))

    br = git("rev-parse", "--verify", BRANCH).decode().strip()
    rec("branch_unchanged", br == HEAD, br)

    wtl = git("worktree", "list", "--porcelain").decode()
    listed = f"worktree {WT}\n" in wtl + "\n"
    if a.phase == "pre":
        rec("worktree_listed", listed)
        rec("worktree_dir_exists", Path(WT).is_dir())
    else:
        rec("worktree_not_listed", not listed)
        rec("worktree_dir_absent", not Path(WT).exists())
        rec("admin_dir_absent", not Path(GIT_DIR, "worktrees", "mp-wo2-ci-debt").exists())

    fails = 0
    for n, ok, d in results:
        print(("PASS " if ok else "FAIL ") + n + (f"  {d}" if d and not ok else ""))
        fails += not ok
    print(f"{len(results) - fails}/{len(results)} passed (phase={a.phase}, mutate={a.mutate})")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
