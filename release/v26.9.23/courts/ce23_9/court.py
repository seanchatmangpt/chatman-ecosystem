#!/usr/bin/env python3
"""CE23-9 court: exact-head root court (release/v26.9.23/sjira/goal.ttl ce:CE23-9).

chatman-ce23.md CE23-9: "Candidate Chatman SHA passes generated-projection drift, manifest/ref
validation, unit/integration, imported receipt validation, replay, and strict release crown."

The court is generated, not written here: the members are er:Gate facts of release/v26.9.23/release.ttl
and the vendored chatman-ecosystem-release-pack (0.4.0, templates/release-court.sh.tmpl) renders them
into release/v26.9.23/out/scripts/crown_v26_9_23.sh (imports re-hashed, probes, then every member in
er:gateOrder under `bash -euo pipefail -c`, stopping at the first non-zero member with its order as
the exit status). This judge runs that rendered court on the exact committed head and types its result:

  C1  the judging court (wrapper, judge, members, runner, universe, pins, vendored validator, fixture)
      is byte-identical to HEAD
  R1  the rendered court runs exactly the release graph's er:Gate rows (order, name, command)
  K   the rendered court itself; a member that stops it is typed from its exit (0 ALIVE, 75 UNKNOWN,
      anything else REFUSED) and its MEMBER_* line; the members after it are then continued by this
      judge (same command, same shell) so every member's verdict is observed, but a continued member
      never changes the rendered court's verdict
  AV  anti-vacuity on real data: the exact-head CI law refuses the real check-runs of the pre-repair
      base c59596f5 for exactly the checks the base repair fixed (fixture), the disposition law refuses
      a stale typed row / a foreign member command / a double disposition, the vendored validator
      refuses mutated copies of a real receipt, and pack gate 090 refuses the stale 0/13 STOP crown
      (vendored fixture) while it admits the positive one

Exit: 0 ALIVE (the rendered court printed COURT_ALIVE and exited 0, every AV clause held); 1 REFUSED (a
member, C1, R1 or an AV clause refused); 75 UNKNOWN (nothing refused, and at least one member is UNKNOWN,
e.g. exact-head CI before the head is published, or CHATMAN_STOP on the operator's GC23-12 acceptance
edge); a missing tool or rendered court is UNKNOWN too.

  sh release/v26.9.23/courts/CE23-9.sh [--receipt-out FILE] [--no-av]
"""
from __future__ import annotations

import argparse
import copy
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import members  # noqa: E402

PINS, SUBJ, SDIR = members.PINS, members.SUBJ, members.SDIR
MEMBER_LINE = re.compile(r"^MEMBER_(ALIVE|REFUSED|UNKNOWN)(?:\[([^\]]*)\])? (\S+)(.*)$")
# At c59596f5 'Fast constitutional gates' and 'S0-S3 exact-head crown' failed (rustfmt drift) and 'Full
# behavior and negative fixtures' and 'Cold-cache correctness' were skipped behind them: the local members
# of those four checks refuse the base, and the CE23-9 base repair (projection render, cargo fmt, clippy
# --fix) is what the exact head adds. Every other non-success check-run at the base is typed in release.ttl.
AV_BASE_REFUSED = {"Fast constitutional gates", "S0-S3 exact-head crown",
                   "Full behavior and negative fixtures", "Cold-cache correctness"}


class Judge:
    def __init__(self):
        self.refused: list[str] = []
        self.unknown: list[str] = []

    def ok(self, clause: str, text: str) -> None:
        print(f"OK {clause} {text}", flush=True)

    def refuse(self, code: str, clause: str, text: str) -> None:
        self.refused.append(code)
        print(f"REFUSED[{code}] {clause} {text}", flush=True)

    def unk(self, code: str, clause: str, text: str) -> None:
        self.unknown.append(code)
        print(f"UNKNOWN[{code}] {clause} {text}", flush=True)


def git_out(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    return p.stdout.strip() if p.returncode == 0 else ""


def c1_court_at_head(root: Path, j: Judge) -> None:
    diverged = []
    for rel in SUBJ["court_files"]:
        blob = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{rel}"], capture_output=True)
        disk = (root / rel).read_bytes() if (root / rel).is_file() else None
        if blob.returncode != 0 or disk != blob.stdout:
            diverged.append(f"{rel} ({'absent at HEAD' if blob.returncode != 0 else 'differs from HEAD'})")
    if diverged:
        j.refuse("COURT_NOT_AT_HEAD", "C1", f"the judging court is not the committed court: {diverged}")
    else:
        j.ok("C1", f"the judging court ({len(SUBJ['court_files'])} files) is byte-identical to HEAD")


def rendered_gates(script: Path) -> list[dict]:
    gates = []
    for line in script.read_text(encoding="utf-8").splitlines():
        if line.startswith("run_gate "):
            _, iri, order, name, command, digest = shlex.split(line)
            gates.append({"iri": iri, "order": int(order), "name": name, "command": command, "sha256": digest})
    return gates


def r1_render_is_graph(root: Path, gates: list[dict], j: Judge) -> None:
    import rdflib  # noqa: PLC0415
    g = members.release_graph(root)
    er = rdflib.Namespace(members.ER)
    graph = sorted((int(g.value(x, er.gateOrder)), str(g.value(x, er.gateName)), str(g.value(x, er.command)))
                   for x in g.subjects(rdflib.RDF.type, er.Gate))
    render = sorted((x["order"], x["name"], x["command"]) for x in gates)
    if graph != render or not render:
        j.refuse("COURT_RENDER_MISMATCH", "R1", f"rendered members {render} != graph er:Gate rows {graph}")
    else:
        j.ok("R1", f"the rendered court runs the release graph's {len(render)} er:Gate members in er:gateOrder: "
                   f"{[n for (_, n, _) in render]}")


def run_streamed(argv: list[str], cwd: Path, env: dict) -> tuple[int, list[str]]:
    lines = []
    with subprocess.Popen(argv, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True) as proc:
        assert proc.stdout is not None
        for line in proc.stdout:
            sys.stdout.write(line)
            sys.stdout.flush()
            lines.append(line.rstrip("\n"))
        rc = proc.wait()
    return rc, lines


def member_verdicts(lines: list[str]) -> dict[str, tuple[str, str]]:
    out = {}
    for line in lines:
        m = MEMBER_LINE.match(line)
        if m:
            out[m.group(3)] = (m.group(1), m.group(2) or "")
    return out


def classify(exit_code: int) -> str:
    return "ALIVE" if exit_code == 0 else "UNKNOWN" if exit_code == 75 else "REFUSED"


def k_run_court(root: Path, script: Path, gates: list[dict], env: dict, j: Judge) -> list[dict]:
    print(f"COURT_RENDERED {script.relative_to(root)} ({len(gates)} members)", flush=True)
    rc, lines = run_streamed(["bash", str(script)], root, env)
    verdicts = member_verdicts(lines)
    table = []
    stopped = rc if 1 <= rc <= 99 else None
    if rc in (100, 101, 102, 103):
        j.refuse(f"COURT_EXIT_{rc}", "K", f"the rendered court exited {rc} before any member verdict "
                                          f"(100 import digest, 101 probe, 102 observation, 103 court root)")
        return table
    if rc == 0 and not any(line.startswith("COURT_ALIVE ") for line in lines):
        j.refuse("COURT_SILENT", "K", "the rendered court exited 0 without COURT_ALIVE")
    by_order = {g["order"]: g for g in gates}
    for g in gates:
        passed = f"COURT_GATE_PASS order={g['order']} name={g['name']}" in lines
        if stopped is None or g["order"] < stopped:
            table.append({"order": g["order"], "name": g["name"], "exit": 0 if passed else None, "source": "court"})
        elif g["order"] == stopped:
            refused_line = next((ln for ln in lines if ln.startswith(f"COURT_GATE_REFUSED order={g['order']} ")), "")
            code = int(refused_line.rsplit("exit=", 1)[-1]) if "exit=" in refused_line else None
            table.append({"order": g["order"], "name": g["name"], "exit": code, "source": "court"})
    if stopped is not None:
        stop_gate = by_order.get(stopped)
        print(f"COURT_STOPPED order={stopped} name={stop_gate['name'] if stop_gate else '?'}: continuing the remaining "
              f"members outside the rendered court (their verdicts are reported, never the rendered court's)", flush=True)
        for g in gates:
            if g["order"] <= stopped:
                continue
            print(f"COURT_CONTINUE_RUN order={g['order']} name={g['name']}", flush=True)
            crc, clines = run_streamed(["bash", "-euo", "pipefail", "-c", g["command"]], root, env)
            verdicts.update(member_verdicts(clines))
            print(f"COURT_CONTINUE order={g['order']} name={g['name']} exit={crc}", flush=True)
            table.append({"order": g["order"], "name": g["name"], "exit": crc, "source": "continued"})
    for row in table:
        mname = row["name"]
        tag = verdicts.get(mname) or verdicts.get(mname.split(".", 1)[-1]) or ("", "")
        row["verdict"] = classify(row["exit"]) if row["exit"] is not None else "UNOBSERVED"
        row["codes"] = tag[1]
        if row["verdict"] == "REFUSED":
            j.refused.append(f"MEMBER:{mname}")
        elif row["verdict"] in ("UNKNOWN", "UNOBSERVED"):
            j.unknown.append(f"MEMBER:{mname}")
    print("MEMBERS", flush=True)
    for row in table:
        print(f"  {row['order']:>2} {row['name']:<26} {row['verdict']:<8} exit={row['exit']} {row['source']}"
              f"{' [' + row['codes'] + ']' if row['codes'] else ''}", flush=True)
    j.ok("K", f"rendered court exit {rc}{' (stopped at member ' + str(stopped) + ')' if stopped else ''}")
    return table


# ----------------------------------------------------------------------------------------------------
# anti-vacuity


def av_exact_head_law(root: Path, j: Judge) -> None:
    fixture = json.loads((HERE / "fixtures" / "checkruns-c59596f5.json").read_text(encoding="utf-8"))
    facts = members.court_facts(root)
    u = members.ci_checks.universe(root, SUBJ["base_commit"], "HEAD")
    refused, _, _ = members.judge_checkruns(fixture["check_runs"], u["checks"], facts["typed"], facts["local"],
                                            set(PINS["ci"]["passing_conclusions"]))
    named = {re.search(r"'([^']+)'", text).group(1) for _, text in refused if re.search(r"'([^']+)'", text)}
    if named == AV_BASE_REFUSED:
        j.ok("AV1", f"the exact-head CI law refuses the real check-runs of base c59596f5 ({len(fixture['check_runs'])} runs) "
                    f"for exactly {sorted(named)} ({len(refused)} refusals); every other non-success base check is typed")
    else:
        j.refuse("AV_VACUOUS", "AV1", f"the exact-head CI law on base c59596f5 refused {sorted(named)}, expected {sorted(AV_BASE_REFUSED)}")


def av_disposition_law(root: Path, j: Judge) -> None:
    facts = members.court_facts(root)
    u = members.ci_checks.universe(root, SUBJ["base_commit"], "HEAD")
    index = {(r["workflow"], r["check"]): r for r in u["checks"]}
    base = members.disposition_law(index, facts["typed"], facts["local"], None)
    if base:
        j.refuse("AV_HARNESS", "AV2", f"the unmutated dispositions are refused: {base}")
        return
    cases = []
    stale = copy.deepcopy(facts["typed"])
    stale[(".github/workflows/crown.yml", "Nonexistent check")] = {"iri": "x", "class": "pre_existing", "boundary": "ROLE_SUCCESSOR"}
    cases.append(("stale typed row", members.disposition_law(index, stale, facts["local"], None), "STALE_TYPED_CHECK"))
    wrong = copy.deepcopy(facts["local"])
    key = next(iter(sorted(wrong)))
    wrong[key]["command"] = wrong[key]["command"].rsplit(" ", 1)[0] + " policy"
    cases.append(("member runs another job", members.disposition_law(index, facts["typed"], wrong, None), "MEMBER_COMMAND_MISMATCH"))
    double = copy.deepcopy(facts["typed"])
    double[key] = {"iri": "x", "class": "pre_existing", "boundary": "ROLE_SUCCESSOR"}
    cases.append(("typed and local", members.disposition_law(index, double, facts["local"], None), "DOUBLE_DISPOSITION"))
    missed = [name for name, got, code in cases if code not in {c for c, _ in got}]
    if missed:
        j.refuse("AV_VACUOUS", "AV2", f"the disposition law admitted mutants: {missed}")
    else:
        j.ok("AV2", f"the disposition law admits the committed dispositions and refuses {[c for _, _, c in cases]}")


def av_validator(root: Path, j: Judge, scratch: Path) -> None:
    receipts = members.r_receipts(root)
    src = next(((rel, doc) for rel, doc in receipts if doc.get("standing", {}).get("value") == "ALIVE"), None)
    if src is None:
        j.refuse("AV_HARNESS", "AV3", "no ALIVE receipt to mutate")
        return
    rel, doc = src
    validator = members.VALIDATOR_DIR / "unified_receipt_validator.py"
    mutants = {}
    m = copy.deepcopy(doc)
    m["identity"]["subject_sha"] = "NOTASHA"
    mutants["subject_sha NOTASHA"] = m
    m = copy.deepcopy(doc)
    m["replay"]["commands"][0]["exit"] = 75
    mutants["ALIVE with a replay exit 75"] = m
    m = copy.deepcopy(doc)
    m["standing"].pop("value", None)
    mutants["standing.value missing"] = m
    admitted = []
    control = subprocess.run([sys.executable, str(validator), str(root / rel), "--contract", "dfcm_fleet_v1"], capture_output=True, text=True)
    for name, mdoc in mutants.items():
        path = scratch / f"mut-{len(admitted)}-{abs(hash(name)) % 10**6}.json"
        path.write_text(json.dumps(mdoc), encoding="utf-8")
        p = subprocess.run([sys.executable, str(validator), str(path), "--contract", "dfcm_fleet_v1"], capture_output=True, text=True)
        if p.returncode != 1:
            admitted.append(f"{name} (exit {p.returncode})")
    foreign = subprocess.run(["git", "-C", str(root), "merge-base", "--is-ancestor", "0" * 40, "HEAD"], capture_output=True)
    if control.returncode != 0:
        j.refuse("AV_HARNESS", "AV3", f"control {rel} is not valid (exit {control.returncode})")
    elif admitted or foreign.returncode == 0:
        j.refuse("AV_VACUOUS", "AV3", f"mutated copies of {rel} admitted: {admitted}; foreign subject ancestry exit {foreign.returncode}")
    else:
        j.ok("AV3", f"the vendored validator admits {rel} and refuses {sorted(mutants)}; a foreign subject_sha is not an ancestor of HEAD")


def av_stale_crown(root: Path, j: Judge, scratch: Path) -> None:
    pack = root / SDIR / "vendor/ggen-marketplace/packs/chatman-ecosystem-release-pack"
    verdicts = {}
    for name in ("stale-r0", "positive"):
        fx = pack / "qualification" / "fixtures" / f"{name}-receipts"
        xaas, gi = (fx / "XAAS_SHA").read_text().strip(), (fx / "GI_SHA").read_text().strip()
        lift = subprocess.run([sys.executable, str(pack / "bin/import-crown-lift.py"), str(fx), xaas, gi], capture_output=True, text=True)
        ttl = scratch / f"crown-{name}.ttl"
        ttl.write_text(lift.stdout, encoding="utf-8")
        gates = subprocess.run([sys.executable, str(pack / "bin/run-gates.py"), str(ttl), str(pack / "gates")], capture_output=True, text=True)
        verdicts[name] = (lift.returncode, gates.returncode, "090_imported_crown" in gates.stdout)
    stale, pos = verdicts["stale-r0"], verdicts["positive"]
    if stale[0] == 0 and stale[1] != 0 and stale[2] and pos[0] == 0 and pos[1] == 0:
        j.ok("AV4", "pack gate 090 refuses the lifted stale STOP crown (0/13, STOP=false; vendored fixture stale-r0) and admits "
                    "the positive crown: CHATMAN_STOP cannot rest on the stale pushed receipt")
    else:
        j.refuse("AV_VACUOUS", "AV4", f"stale crown (lift, gates, 090 fired) = {stale}; positive = {pos}")


def write_receipt(path: Path, root: Path, head: str, verdict: str, table: list[dict], j: Judge, started: float) -> None:
    standing = {"ALIVE": "ALIVE", "UNKNOWN": "UNKNOWN", "REFUSED": "BLOCKED"}[verdict]
    doc = {
        "identity": {"subject": "CE23-9/exact-head-root-court", "repo": SUBJ["repository"], "subject_sha": head,
                     "base_sha": SUBJ["base_commit"], "gate": "ce:CE23-9 (release/v26.9.23/sjira/goal.ttl)"},
        "authority": {"ceiling": "SELECT", "grant": "court run (read-only on the subject)", "actor": "release/v26.9.23/courts/CE23-9.sh"},
        "consequence": {"commits": [], "files_changed": [], "members": table},
        "replay": {"commands": [{"cmd": "sh release/v26.9.23/courts/CE23-9.sh", "cwd": str(root),
                                 "exit": {"ALIVE": 0, "REFUSED": 1, "UNKNOWN": 75}[verdict]}],
                   "durable_location": f"git:{SUBJ['repository']}@{head}:{SDIR}/courts/CE23-9.sh"},
        "standing": {"value": standing, "derived_from": f"CE23-9 court exit, {time.time() - started:.0f}s, refused={sorted(set(j.refused))}, "
                                                        f"unknown={sorted(set(j.unknown))}"},
    }
    if standing != "ALIVE":
        doc["standing"]["broken_term"] = "mu_on_O" if standing == "BLOCKED" else "admission_vacuous"
    path.write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--receipt-out", type=Path)
    ap.add_argument("--no-av", action="store_true")
    a = ap.parse_args(argv)
    started = time.time()
    root = Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True, cwd=HERE).stdout.strip()).resolve()
    head = git_out(root, "rev-parse", "HEAD")
    print(f"CE23-9 court: subject {head} at {root}", flush=True)
    j = Judge()
    for tool in ("git", "bash", "ggen", "cargo"):
        if shutil.which(tool) is None:
            print(f"UNKNOWN[TOOL_MISSING] CE23-9: {tool} not on PATH", flush=True)
            return 75
    script = root / SDIR / SUBJ["court_script"]
    if not script.is_file():
        print(f"UNKNOWN[MACHINERY_ABSENT] CE23-9: {script.relative_to(root)} is not rendered", flush=True)
        return 75
    try:
        import rdflib  # noqa: F401,PLC0415
        import yaml  # noqa: F401,PLC0415
    except ModuleNotFoundError as exc:
        print(f"UNKNOWN[TOOL_MISSING] CE23-9: python module {exc.name}", flush=True)
        return 75
    c1_court_at_head(root, j)
    gates = rendered_gates(script)
    r1_render_is_graph(root, gates, j)
    scratch = Path(tempfile.mkdtemp(prefix="ce23-9-court."))
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", CE23_9_SCRATCH=str(scratch))
    env.pop("COURT_OBSERVED", None)
    table = k_run_court(root, script, gates, env, j)
    if not a.no_av:
        av_exact_head_law(root, j)
        av_disposition_law(root, j)
        av_validator(root, j, scratch)
        av_stale_crown(root, j, scratch)
    shutil.rmtree(scratch, ignore_errors=True)
    verdict = "REFUSED" if j.refused else "UNKNOWN" if j.unknown else "ALIVE"
    if a.receipt_out:
        write_receipt(a.receipt_out, root, head, verdict, table, j, started)
    tail = {"REFUSED": sorted(set(j.refused)), "UNKNOWN": sorted(set(j.unknown)), "ALIVE": []}[verdict]
    print(f"CE23-9 {verdict}{' ' + str(tail) if tail else ''} ({time.time() - started:.0f}s)", flush=True)
    return {"ALIVE": 0, "REFUSED": 1, "UNKNOWN": 75}[verdict]


if __name__ == "__main__":
    raise SystemExit(main())
