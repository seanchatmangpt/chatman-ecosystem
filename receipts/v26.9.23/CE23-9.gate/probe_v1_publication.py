#!/usr/bin/env python3
"""CE23-9 repair probe: how a given CE23-1 court's V1 clause types the real vendored pin under each
marketplace publication state (skeptic reasons 1 and 2).

For each court revision (`git show <rev>:release/v26.9.23/courts/ce23_1/{court.py,subject.toml}` into a
scratch dir; `--mutate-pending-refuse` additionally judges the HEAD court with its pending branch
turned into a refusal, the revert-mutation), V1 (`vendor()`) judges this checkout's committed HEAD
against: the canonical ggen-marketplace checkout as it is (`canonical`), and synthetic marketplaces
(bare repositories over the canonical objects via git alternates, built by the HEAD court's
synthetic_marketplace(); only refs differ) in the states published / pending / diverged.
Real git, real files; nothing is written outside --scratch; the canonical checkout is only read.

    python3 probe_v1_publication.py --scratch DIR --rev b001d018 --rev HEAD --mutate-pending-refuse
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip())
REL = "release/v26.9.23/courts/ce23_1"


def load(rev: str, dest: Path, mutate: bool = False):
    dest.mkdir(parents=True)
    for name in ("court.py", "subject.toml"):
        data = subprocess.run(["git", "-C", str(ROOT), "show", f"{rev}:{REL}/{name}"], capture_output=True, check=True).stdout
        if mutate and name == "court.py":
            old = b'v.unknown("VENDOR_PUBLICATION_PENDING", "V1"'
            assert data.count(old) == 1, "mutation anchor"
            data = data.replace(old, b'v.refuse("VENDOR_PUBLICATION_PENDING", "V1"')
        (dest / name).write_bytes(data)
    tag = f"probe_court_{abs(hash((rev, mutate)))}"
    spec = importlib.util.spec_from_file_location(tag, dest / "court.py")
    court = importlib.util.module_from_spec(spec)
    sys.modules[tag] = court
    spec.loader.exec_module(court)
    return court


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--scratch", type=Path, required=True)
    ap.add_argument("--rev", action="append", required=True)
    ap.add_argument("--mutate-pending-refuse", action="store_true")
    a = ap.parse_args()
    head = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"PROBE subject {head} at {ROOT}")
    courts = [(rev, load(rev, a.scratch / f"court-{i}")) for i, rev in enumerate(a.rev)]
    if a.mutate_pending_refuse:
        courts.append(("HEAD+pending->refuse", load("HEAD", a.scratch / "court-mutant", mutate=True)))
    builder = load("HEAD", a.scratch / "court-builder")
    env = builder.Env(a.scratch / "home")
    canonical = builder.marketplace_repo()
    markets = {"canonical": canonical}
    for state in ("published", "pending", "diverged"):
        markets[state] = builder.synthetic_marketplace(env, ROOT, a.scratch / f"market-{state}.git", state)
    for name, market in markets.items():
        remote = env.out(market, "rev-parse", "--verify", "--quiet", "refs/remotes/origin/release/v26.9.23-int")
        local = env.out(market, "rev-parse", "--verify", "--quiet", "refs/heads/release/v26.9.23-int")
        print(f"MARKET {name}: origin/release/v26.9.23-int={remote} heads/release/v26.9.23-int={local}")
    for rev, court in courts:
        for name, market in markets.items():
            v = court.Verdict()
            os.environ["CE23_MARKETPLACE_REPO"] = str(market)  # the b001d018 court reads only the env var
            try:
                court.vendor(v, ROOT, head, ROOT / court.SDIR, env, market)
            except TypeError:
                court.vendor(v, ROOT, head, ROOT / court.SDIR, env)
            v1 = [line for line in v.lines if " V1:" in line and not line.startswith("OK V1: ggen.toml")]
            print(f"COURT {rev} MARKET {name}: refused={v.refused} unknown={v.unknowns}")
            for line in v1:
                print(f"    {line[:260]}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
