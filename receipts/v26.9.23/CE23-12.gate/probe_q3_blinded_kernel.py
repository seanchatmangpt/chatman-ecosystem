#!/usr/bin/env python3
"""CE23-12 skeptic-repair probe: does the Q3 mutation-sensitivity count depend on the instrument?

Subject: a synthetic git repository of the chatman-ecosystem HEAD (release/v26.9.23/bench, sjira,
courts) in which the K1 instrument is blind: pack/scripts/evidence_tiers.py --check no longer compares
the committed generated/ tables with a fresh kernel computation (one line, the same edit as the court's
KERNEL_BLIND); ggen.lock is re-locked (`ggen sync run` after deleting ggen.lock, as ggen.toml
prescribes after an intended pack change) and the tree committed. Every perturbed kernel literal in
that subject escapes its guarding instrument, so an honest Q3 must count those escapes.

The probe loads the Q3 clause of the court at --court-rev (release/v26.9.23/courts/ce23_12 extracted
with git archive; nothing in the checkout is modified), runs E0, S0 and Q3 on the subject, and prints
the verdict lines.

  probe_q3_blinded_kernel.py --court-rev REV

Exit: 0 the court's Q3 REFUSED[msa_mutation_escape] and counted every kernel-literal unit as an escape
(the count follows the instrument); 3 the court's Q3 admitted the blind-K1 subject (the count does not
follow the instrument); 1 anything else (setup failure, another verdict).
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
BENCH_REL = "release/v26.9.23/bench"
KERNEL_LINE = '        if not path.is_file() or path.read_text(encoding="utf-8") != text:\n'
KERNEL_BLIND = '        if False:  # BLINDED by the CE23-12 Q3 probe: committed outputs never compared\n'


def run(argv: list[str], cwd: Path, **kw) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=str(cwd), capture_output=True, text=True, check=True, **kw)


def blind_k1_subject(scratch: Path) -> Path:
    repo = scratch / "subject"
    repo.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", "HEAD", BENCH_REL, "release/v26.9.23/sjira", "release/v26.9.23/courts"],
                             capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(repo)], input=archive, check=True)
    ident = ["-c", "user.email=probe@local", "-c", "user.name=ce23-12-q3-probe"]
    run(["git", "init", "-q"], repo)
    run(["git", "add", "-A"], repo)
    run(["git", *ident, "commit", "-q", "-m", "control: HEAD"], repo)
    bench = repo / BENCH_REL
    script = bench / "pack/scripts/evidence_tiers.py"
    text = script.read_text(encoding="utf-8")
    if text.count(KERNEL_LINE) != 1:
        raise SystemExit("probe setup: the K1 comparison line is not in evidence_tiers.py exactly once")
    script.write_text(text.replace(KERNEL_LINE, KERNEL_BLIND), encoding="utf-8")
    before = {p.relative_to(bench): p.read_bytes() for p in sorted((bench / "out").rglob("*")) if p.is_file()}
    (bench / "ggen.lock").unlink()
    run(["ggen", "sync", "run"], bench, timeout=900)
    for d in (".ggen", ".ggen-v2"):
        shutil.rmtree(bench / d, ignore_errors=True)
    after = {p.relative_to(bench): p.read_bytes() for p in sorted((bench / "out").rglob("*")) if p.is_file()}
    if before != after:
        raise SystemExit("probe setup: re-locking changed out/; the subject would differ in more than K1")
    run(["git", "add", "-A"], repo)
    run(["git", *ident, "commit", "-q", "-m", "K1 blinded: evidence_tiers.py --check never compares the committed tables; re-locked"], repo)
    changed = run(["git", "diff", "--name-only", "HEAD~1", "HEAD"], repo).stdout.split()
    if sorted(changed) != sorted([f"{BENCH_REL}/ggen.lock", f"{BENCH_REL}/pack/scripts/evidence_tiers.py"]):
        raise SystemExit(f"probe setup: the blinded subject changes {changed}, not exactly the K1 script and ggen.lock")
    print(f"SUBJECT {run(['git', 'rev-parse', 'HEAD'], repo).stdout.strip()} = HEAD {run(['git', 'rev-parse', 'HEAD'], ROOT).stdout.strip()[:12]} "
          f"with K1 blinded (changed: {', '.join(changed)})")
    return repo


def load_court(rev: str, scratch: Path):
    dest = scratch / "court"
    dest.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(ROOT), "archive", rev, "release/v26.9.23/courts/ce23_12"], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(dest)], input=archive, check=True)
    path = dest / "release/v26.9.23/courts/ce23_12/court.py"
    spec = importlib.util.spec_from_file_location("probe_court", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules["probe_court"] = module
    spec.loader.exec_module(module)
    print(f"COURT {rev} = {run(['git', 'rev-parse', rev], ROOT).stdout.strip()[:12]} release/v26.9.23/courts/ce23_12/court.py")
    return module


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--court-rev", required=True)
    args = parser.parse_args()
    base = os.environ.get("CE23_12_TMP") or "/tmp"
    scratch = Path(tempfile.mkdtemp(prefix="ce23-12-q3-probe-", dir=base))
    try:
        court = load_court(args.court_rev, scratch)
        repo = blind_k1_subject(scratch)
        verdicts = court.Verdicts("probe")
        ctx = court.Ctx(repo, "msa", scratch / "judge", verdicts)
        if not (court.clause_tools(ctx) and court.clause_subject(ctx)):
            return 1
        court.clause_msa_mutation(ctx)
        q3 = [ln for ln in verdicts.lines if ln[1] == "Q3"]
        rows = [r for r in ctx.cache.get("msa_rows", []) if r["question"] == "mutation sensitivity"]
        kernel_units = sum(len(re.findall(r'"(\d+\.\d{6})"\^\^', (repo / BENCH_REL / rel).read_text(encoding="utf-8")))
                           for rel in ("generated/evidence-tiers.ttl", "generated/bound-table.ttl"))
        if rows:
            r = rows[0]
            print(f"ROW n={r['n']} defects={r['defects']} upper_bound_95={r['upper_bound_95']} tier={r['tier']} "
                  f"kernel={r.get('classes', {}).get('kernel')}")
        if not q3:
            print("PROBE: the court recorded no Q3 verdict")
            return 1
        status = q3[0][0]
        if status == "REFUSED[msa_mutation_escape]" and rows and rows[0].get("classes", {}).get("kernel", {}).get("misses") == kernel_units:
            print(f"PROBE: Q3 follows the instrument: all {kernel_units} kernel-literal units escape the blinded K1 and Q3 is REFUSED")
            return 0
        if status == "OK":
            print(f"PROBE: Q3 admitted a subject whose K1 is blind ({kernel_units} kernel-literal corruptions undetected by K1): "
                  f"the count does not follow the instrument")
            return 3
        print(f"PROBE: unexpected Q3 verdict {status}")
        return 1
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
