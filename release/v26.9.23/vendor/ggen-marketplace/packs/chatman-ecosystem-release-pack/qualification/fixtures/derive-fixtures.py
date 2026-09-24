#!/usr/bin/env python3
"""Re-derive the imported-crown qualification fixtures from real xaas git objects.

usage: derive-fixtures.py <xaas_repo> <out_dir>      (then: diff -r <out_dir> qualification/fixtures)

Sources are git blobs, checked by object id before use:
- positive: the V23-S smoke stop-court run at xaas 26a6a0c, committed in xaas 4b14e3f
  (STOP receipt with LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH=0 and UNRECEIPTED_ACTUATION=0,
  and the one gate receipt that run wrote, GC23-11). That run was --only GC23-11, so the STOP
  standing and the 13 gate receipts are qualification rewrites of those bytes: each rewritten
  receipt carries a `qualification_rewrite` object naming its source blob and the rewritten
  fields; every other byte-derived field (subject_sha, ggen_igniter_sha, counters) is real.
- stale-r0: the committed baseline observation R_0 of GC-26.9.23 (xaas 66b52e7), verbatim bytes.
- llm1, unreceipted-null, drop-gate, foreign-subject, gi-mismatch: one change each to positive;
  the foreign subject and foreign ggen_igniter SHA are the real R_0 subjects.
Each fixture dir carries XAAS_SHA and GI_SHA: the exact subjects an importer binds.
"""
import copy, json, subprocess, sys
from pathlib import Path

REPO, OUT = sys.argv[1], Path(sys.argv[2])
S = "4b14e3f227567846b3eceb26b104641ca7febf5c"
R0 = "66b52e74dd975d336ef66818b52676af08004f5d"
GI = "3937a4f89ecf2b7fa12068406377c05ec1a1b8fc"
STOP_SRC = (S, "receipts/v26.9.23/V23-S.gate/stop-court-STOP.receipt.json", "f028286b28a1a2797fb7c3eb0b5d6b2f2894ca01")
GATE_SRC = (S, "receipts/v26.9.23/V23-S.gate/stop-court-GC23-11.receipt.json", "f787525c2fb910a2faad0b4d994aae8edb11f39b")
R0_DIR = "docs/sjira/v26.9.23/receipts"
CP, GATES = "GC-26.9.23", [f"GC23-{i}" for i in range(13)]


def blob(rev, path, want=None):
    oid = subprocess.run(["git", "-C", REPO, "rev-parse", f"{rev}:{path}"], capture_output=True, text=True, check=True).stdout.strip()
    if want and oid != want:
        raise SystemExit(f"source drift: {rev}:{path} is {oid}, expected {want}")
    return oid, subprocess.run(["git", "-C", REPO, "cat-file", "blob", oid], capture_output=True, check=True).stdout


def dump(d):
    return (json.dumps(d, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode()


def write(name, files, xsha, gsha):
    d = OUT / f"{name}-receipts"
    d.mkdir(parents=True, exist_ok=True)
    for fname, data in files.items():
        (d / fname).write_bytes(data if isinstance(data, bytes) else dump(data))
    (d / "XAAS_SHA").write_text(xsha + "\n")
    (d / "GI_SHA").write_text(gsha + "\n")


def rewrite(doc, src, fields, why):
    doc.setdefault("qualification_rewrite", {"source": f"seanchatmangpt/xaas@{src[0]}:{src[1]}", "source_git_blob": src[2], "rewritten": [], "why": []})
    doc["qualification_rewrite"]["rewritten"] += fields
    doc["qualification_rewrite"]["why"].append(why)
    return doc


_, stop_raw = blob(*STOP_SRC)
_, gate_raw = blob(*GATE_SRC)
stop = json.loads(stop_raw)
subject = stop["identity"]["subject_sha"]
assert subject == json.loads(gate_raw)["identity"]["subject_sha"] and json.loads(gate_raw)["gate"]["ggen_igniter_sha"] == GI
stop["standing"] = {"value": "ALIVE", "derived_from": f"sj:stopQuery of {CP} at {subject}: 13/13 gates ALIVE; STOP=true"}
rewrite(stop, STOP_SRC, ["standing"], "positive witness: STOP=true at the smoke subject (the smoke run judged only GC23-11)")
positive = {"STOP-GC-26.9.23.json": stop}
for g in GATES:
    doc = json.loads(gate_raw)
    doc["gate"]["gate"], doc["gate"]["outcome"] = g, "passed"
    doc["identity"]["subject"] = f"{CP}/{g}"
    doc["standing"] = {"value": "ALIVE", "derived_from": f"qualification rewrite: {g} ALIVE at {subject}"}
    positive[f"{g}.json"] = rewrite(doc, GATE_SRC, ["gate.gate", "gate.outcome", "identity.subject", "standing"], f"positive witness: {g} ALIVE at the smoke subject")
write("positive", positive, subject, GI)

r0 = {f"{n}.json": blob(R0, f"{R0_DIR}/{n}.json")[1] for n in GATES + [f"STOP-{CP}"]}
r0_stop = json.loads(r0[f"STOP-{CP}.json"])
r0_subject, r0_gi = r0_stop["identity"]["subject_sha"], json.loads(r0["GC23-0.json"])["gate"]["ggen_igniter_sha"]
write("stale-r0", r0, R0, GI)


def mutant(name, change, why, drop=None):
    files = {k: copy.deepcopy(v) for k, v in positive.items() if k != drop}
    if change:
        fname, fields, apply = change
        apply(files[fname])
        rewrite(files[fname], STOP_SRC if fname.startswith("STOP") else GATE_SRC, fields, why)
    write(name, files, subject, GI)


mutant("llm1", ("STOP-GC-26.9.23.json", ["release_counters.LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH.value"],
                lambda d: d["release_counters"]["LLM_INVOCATIONS_ON_KNOWN_REFERENCE_PATH"].update(value=1)),
       "mutant: one LLM-provider event on the known reference path")
mutant("unreceipted-null", ("STOP-GC-26.9.23.json", ["release_counters.UNRECEIPTED_ACTUATION.value", "release_counters.UNRECEIPTED_ACTUATION.why"],
                            lambda d: d["release_counters"]["UNRECEIPTED_ACTUATION"].update(value=None, why="qualification mutant: episode ledger unreadable")),
       "mutant: the court could not read the actuation ledger and wrote null with a reason")
mutant("drop-gate", None, "", drop="GC23-12.json")
mutant("foreign-subject", ("GC23-7.json", ["identity.subject_sha"], lambda d: d["identity"].update(subject_sha=r0_subject)),
       "mutant: GC23-7 ran at the R_0 subject, not the crown subject")
mutant("gi-mismatch", ("GC23-4.json", ["gate.ggen_igniter_sha"], lambda d: d["gate"].update(ggen_igniter_sha=r0_gi)),
       "mutant: GC23-4 ran against the R_0 ggen_igniter subject")
print(f"derived 7 fixture dirs into {OUT} (positive subject {subject}, R_0 subject {r0_subject}, R_0 ggen_igniter {r0_gi})")
