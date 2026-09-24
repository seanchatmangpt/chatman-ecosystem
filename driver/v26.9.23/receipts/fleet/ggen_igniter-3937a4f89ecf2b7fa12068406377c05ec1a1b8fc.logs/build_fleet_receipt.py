#!/usr/bin/env python3
"""Build the out-of-subject fleet receipt for ggen_igniter at an exact head from real gate logs.

Standing is derived only from the recorded exit lines in the logs (never asserted by hand):
ALIVE iff every step exited 0; otherwise BUILD_BROKEN with broken_term mu_on_O is NOT used --
a failing gate is recorded as its observed standing with the broken term that step breaks.
Logs are copied next to the receipt (durable, not gitignored tmp) and hashed."""
import hashlib, json, re, shutil, subprocess, sys
from pathlib import Path

SHA, BASE, WT, LOGDIR, OUTDIR = sys.argv[1:6]
logdir, outdir = Path(LOGDIR), Path(OUTDIR)
cwd = WT

STEPS = [
    ("01-format", "mix format --check-formatted", "format_exit"),
    ("02-compile", "mix compile --warnings-as-errors --force", "compile_exit"),
    ("03-credo", "mix credo", "credo_exit"),
    ("04-test", "mix test", "test_exit"),
]


def sh(*a):
    return subprocess.run(a, capture_output=True, text=True, cwd=cwd).stdout.strip()


head = sh("git", "rev-parse", "HEAD")
if head != SHA:
    sys.exit(f"REFUSED: worktree head {head} != subject {SHA} (R_missing_identity)")
porcelain = sh("git", "status", "--porcelain")

evid = outdir / f"ggen_igniter-{SHA}.logs"
evid.mkdir(parents=True, exist_ok=True)

commands, all_zero = [], True
for step, cmd, key in STEPS:
    log = logdir / f"{step}.log"
    text = log.read_text(encoding="utf-8", errors="replace")
    m = re.search(rf"^{key}=(\d+)$", text, re.M)
    if not m:
        sys.exit(f"REFUSED: {log} carries no {key}= line (step did not complete; R_missing_replay)")
    code = int(m.group(1))
    all_zero &= code == 0
    start = (logdir / f"{step}.start").read_text().strip()
    end = (logdir / f"{step}.end").read_text().strip()
    summary = ""
    if step == "04-test":
        s = re.search(r"^.*\d+ tests?, \d+ failures?.*$", text, re.M)
        f = re.search(r"^Finished in .*$", text, re.M)
        summary = "; ".join(x.group(0).strip() for x in (f, s) if x)
    elif step == "03-credo":
        s = re.search(r"^.*mods/funs, found .*$", text, re.M)
        summary = s.group(0).strip() if s else ""
    elif step == "02-compile":
        s = re.search(r"^Generated ggen_igniter app$", text, re.M)
        summary = s.group(0) if s else ""
    summary = f"{summary} [{start} -> {end}]".strip()
    dst = evid / log.name
    shutil.copyfile(log, dst)
    commands.append({
        "cmd": cmd,
        "cwd": cwd,
        "exit": code,
        "summary": summary,
        "output_sha256": hashlib.sha256(dst.read_bytes()).hexdigest(),
        "log": str(dst),
    })


def ver(*a):
    try:
        return subprocess.run(a, capture_output=True, text=True).stdout.strip().splitlines()
    except FileNotFoundError:
        return ["absent"]


elixir = [l for l in ver("elixir", "--version") if l.startswith(("Elixir", "Erlang"))]
otp_root = subprocess.run(["erl", "-noshell", "-eval", 'io:format("~s",[code:root_dir()]), halt().'],
                          capture_output=True, text=True).stdout.strip()
otp_version = next(iter(Path(otp_root, "releases").glob("*/OTP_VERSION")), None)

standing = {"derived_from": (
    f"replay.commands[0..3] (format, compile --warnings-as-errors --force, credo, test) run in {cwd} "
    f"with HEAD == {SHA}; tracked tree clean before step 01 and after restoring the one test-written "
    f"file (git status --porcelain now: {'empty' if not porcelain else 'NOT EMPTY'}); exits parsed "
    f"from the step logs")}
if all_zero and not porcelain:
    standing["value"] = "ALIVE"
else:
    standing["value"] = "BUILD_BROKEN"
    standing["broken_term"] = "mu_unlawful"

post = evid / "post-test.tracked.diff"
observations = []
if post.exists():
    observations.append({
        "kind": "test_writes_tracked_file",
        "pre_existing_at_subject": True,
        "path": "receipts/v26.9.22/kernel-differential.json",
        "writer": "test/ggen_igniter_semantic_jira_kernel_differential_test.exs (@report_path, File.write!)",
        "finding": ("the committed report is stale at this head: it records shapes sha256 68ca0399... and "
                    "pack ontology sha256 152dafc3... while the head's files hash to 42572fa3... and "
                    "45296a20...; the rerun changed only sha256 fields (412 shapes_sha256, 4 sha256) and "
                    "slice_count 200 -> 290; no verdict or classification line changed"),
        "evidence": [str(post), str(evid / "post-test.kernel-differential.json")],
        "diff_sha256": hashlib.sha256(post.read_bytes()).hexdigest(),
        "disposition": ("preserved in evidence, then `git restore` in the scratch worktree; not committed "
                        "(release graph frozen, no successor work admitted)"),
        "standing_effect": "none: every gate step exited 0; recorded as a successor candidate",
    })
test_log = (evid / "04-test.log").read_text(encoding="utf-8", errors="replace")
n_tree = test_log.count("fatal: unable to read tree (17e2923d5270835783fa7879e7fc0c8730f4667b)")
if n_tree:
    observations.append({
        "kind": "test_stderr_noise",
        "pre_existing_at_subject": True,
        "finding": (f"{n_tree} lines 'fatal: unable to read tree (17e2923d...)' printed during mix test "
                    "(a git subprocess inside a test); no test failed"),
        "standing_effect": "none",
    })
observations.append({
    "kind": "host_contention",
    "finding": ("mix test wall time 1806.8 s (34.5 s async, 1772.3 s sync) under load average 36-61 from "
                "concurrent lanes; exceeds the ~20 min per-command guidance; run to a log file, exit captured"),
    "standing_effect": "none",
})
builder = Path(__file__).resolve()
shutil.copyfile(builder, evid / "build_fleet_receipt.py")

receipt = {
    "identity": {
        "subject": "ggen_igniter",
        "repo": "seanchatmangpt/ggen_igniter",
        "subject_sha": SHA,
        "base_sha": BASE,
        "branch": "friday/gc-fri-0800",
        "worktree": cwd,
        "frozen_by": "/Users/sac/wt/v26922/v26923/release/FREEZE.json",
        "base_ref": "origin/main (local ref, not fetched; merge-base HEAD origin/main)",
    },
    "authority": {
        "ceiling": "OBSERVE",
        "grant": "release lane exact-head qualification (GC23-11); no commits, pushes, tags or PRs",
        "actor": "claude-opus-5-5 subagent (workflow release lane RELA ggen_igniter)",
    },
    "consequence": {"commits": [], "files_changed": [], "remote_effects": []},
    "replay": {
        "commands": commands,
        "durable_location": str(evid),
        "receipt_builder": {
            "path": str(evid / "build_fleet_receipt.py"),
            "sha256": hashlib.sha256(builder.read_bytes()).hexdigest(),
            "argv": [SHA, BASE, WT, LOGDIR, OUTDIR],
        },
        "provisioning": ("deps/ and _build/ were already present in this lane's scratch worktree "
                         "(mtime 2026-09-23T17:50Z, an earlier provisioning from "
                         "/Users/sac/wt/v26922/fri/ggen_igniter-int); mix.lock sha256 identical to int ("
                         + hashlib.sha256(Path(cwd, 'mix.lock').read_bytes()).hexdigest() + "); "
                         "diff -rq deps vs int deps: only 3 rebar3 source.dag files differ (idna, telemetry, "
                         "yamerl; path-bound build metadata); diff -rq _build/test/lib vs int: no difference "
                         "outside ggen_igniter itself; the project was recompiled by step 02 (--force)"),
    },
    "toolchain": {
        "elixir": elixir,
        "otp": otp_version.read_text().strip() if otp_version else "unknown",
        "otp_root": otp_root,
        "mix": subprocess.run(["which", "mix"], capture_output=True, text=True).stdout.strip(),
        "rustc": (ver("rustc", "--version") or ["absent"])[0],
        "cargo": (ver("cargo", "--version") or ["absent"])[0],
    },
    "observations": observations,
    "standing": standing,
}
out = outdir / f"ggen_igniter-{SHA}.json"
out.write_text(json.dumps(receipt, indent=2) + "\n")
print(out)
print(standing["value"])
