#!/usr/bin/env python3
"""Phase 3 close-out: bind every UNIQUE_AND_REQUIRED subject and every release subject of OWNERSHIP.json to
structured canonical evidence {repo, commit, path, kind}, which cleanup_gate.py verifies (object exists at the
commit, commit on a pushed ref). Idempotent; matches subjects by a key substring and refuses an unmatched key
or an unbound required subject.

kinds: MOVED (unique file now committed in its canonical owner), RECEIPT (the order's work and receipt are in
the canonical repo), ORDER_OPEN (the order is not finished; its only unique state is the order itself, which
lives in the canonical goal graph), MERGED (release branch merged to the default branch).
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CE, XA, GI, MP = "chatman-ecosystem", "xaas", "ggen_igniter", "ggen-marketplace"
GOAL = (CE, "1a59285f", "release/v26.9.23/sjira/goal.ttl", "ORDER_OPEN")

SUBJECTS = [  # (key substring of "repo | subject", repo, commit, path, kind)
    ("DRIVER.md (driver log", CE, "b9f0065e", "migration/v26923-single-repo/driver/DRIVER.md", "MOVED"),
    ("bench/DESIGN.md, bench/ontology-draft.ttl", CE, "aa4e3873", "release/v26.9.23/bench/DESIGN.md", "MOVED"),
    ("lanes/release.py + lanes/chain-release.sh", XA, "65466f8", "scripts/sjira/release_v26_9_23.py", "MOVED"),
    ("lanes/scan-plan.json", CE, "b9f0065e", "release/v26.9.23/sjira/annex/scan-plan.json", "MOVED"),
    ("(4b) CE23-12 benchmark design capital", CE, "aa4e3873", "release/v26.9.23/bench/DESIGN.md", "MOVED"),
    ("CE23-0 root identity", CE, "1785806d", "receipts/v26.9.23/CE23-0.json", "RECEIPT"),
    ("CE23-1 independent release", CE, "b0d5add2", "receipts/v26.9.23/CE23-1.json", "RECEIPT"),
    ("CE23-2 16-role legacy crosswalk", CE, "8c150da2", "receipts/v26.9.23/CE23-2.json", "RECEIPT"),
    ("CE23-3 import the Semantic Manufacturing crown", *GOAL),
    ("CE23-4 close GC23-12", *GOAL),
    ("CE23-5 close GC23-11", *GOAL),
    ("CE23-6 fleet typing", *GOAL),
    ("CE23-7 version-fence", CE, "077a729d", "receipts/v26.9.23/CE23-7.json", "RECEIPT"),
    ("CE23-8 zero-intelligence KNOWN path", *GOAL),
    ("CE23-9 exact-head root court", CE, "2f2a0df8", "receipts/v26.9.23/CE23-9.json", "RECEIPT"),
    ("CE23-10 root release receipt", *GOAL),
    ("CE23-11 tag only the crowned subject", *GOAL),
    ("CE23-12 BENCHMARK_DESIGN_ALIVE", CE, "c636def7", "receipts/v26.9.23/CE23-12.json", "RECEIPT"),
    ("CE23 scan-verified implementation specs", CE, "044c9a2e", "release/v26.9.23/sjira/annex/specs/CE23-9-root-court.txt", "MOVED"),
    ("release/v26.9.23-int pushed segment 420bc91e7..e3988aba4", MP, "dafc1d45", "packs/receipt-provenance-unification-pack/pack.toml", "MERGED"),
    ("mp23/MP-RELPACK-COURT", MP, "dafc1d45", "receipts/v26.9.23/MP-RELPACK-COURT.json", "MERGED"),
    ("chatman-ecosystem-release-pack 0.2.0 + 0.3.0", MP, "dafc1d45", "packs/chatman-ecosystem-release-pack/pack.toml", "MERGED"),
    ("chatman-ecosystem-release-pack 0.4.0", MP, "dafc1d45", "packs/chatman-ecosystem-release-pack/gates/097_root_receipt.rq", "MERGED"),
    ("receipt-provenance-unification-pack (MP-RPV", MP, "dafc1d45", "packs/receipt-provenance-unification-pack/PROVENANCE.md", "MERGED"),
]
RELEASE = {  # (repo, subject) -> (repo, merge commit, path, kind)
    (XA, "friday/gc-fri-0800"): (XA, "5f408767", "docs/sjira/v26.9.23/goal.ttl", "MERGED"),
    (GI, "friday/gc-fri-0800"): (GI, "fe92e611", "mix.exs", "MERGED"),
    (CE, "release/v26.9.23-int"): (CE, "1a59285f", "release/v26.9.23/sjira/goal.ttl", "MERGED"),
    (MP, "release/v26.9.23-int"): (MP, "dafc1d45", "receipts/v26.9.23/MP-RELPACK-COURT.json", "MERGED"),
}


def ev(repo, commit, path, kind):
    return {"repo": repo, "commit": commit, "path": path, "kind": kind}


def main():
    p = os.path.join(HERE, "OWNERSHIP.json")
    own = json.load(open(p))
    used, unbound = set(), []
    for s in own["subjects"]:
        if s.get("disposition") != "UNIQUE_AND_REQUIRED":
            continue
        label = f"{s.get('repo')} | {s.get('subject')}"
        hits = [row for row in SUBJECTS if row[0] in label]
        if len(hits) != 1:
            unbound.append((label[:100], len(hits)))
            continue
        used.add(hits[0][0])
        s["canonical_final"] = ev(*hits[0][1:])
    for r in own.get("release_subjects", []):
        key = (r["repo"], r["subject"])
        if key not in RELEASE:
            unbound.append((str(key), 0))
            continue
        r["canonical_final"] = ev(*RELEASE[key])
    unused = [row[0] for row in SUBJECTS if row[0] not in used]
    if unbound or unused:
        print(json.dumps({"unbound": unbound, "unused_keys": unused}, indent=1))
        sys.exit(1)
    json.dump(own, open(p, "w"), indent=1, ensure_ascii=False)
    open(p, "a").write("\n")
    print(f"bound {len(used)} required subjects + {len(own.get('release_subjects', []))} release subjects")


if __name__ == "__main__":
    main()
