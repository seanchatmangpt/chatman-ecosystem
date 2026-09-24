#!/usr/bin/env python3
"""CE23-12 courts: BenchmarkDesign, MSAContract, GeneratedQualificationPlan and the CE23-12 crown.

CE23-12 for v26.9.23 = BenchmarkDesign AND MSAContract AND GeneratedQualificationPlan
(release/v26.9.23/sjira/chatman-ce23-12-standings.md; goal.ttl ce:CE23-12 and its three conjunct
gates). Each court judges the exact committed head of the chatman-ecosystem checkout that holds it:

  court.py bd     BenchmarkDesign            (courts/CE23-12-BenchmarkDesign.sh)
  court.py msa    MSAContract                (courts/CE23-12-MSAContract.sh)
  court.py gqp    GeneratedQualificationPlan (courts/CE23-12-GeneratedQualificationPlan.sh)
  court.py crown  CE23-12                    (courts/CE23-12.sh: runs the three, admits their receipts)

Options: --root DIR (judge another checkout; the anti-vacuity harness uses synthetic git repositories),
--receipt-out FILE (write this run's R-schema receipt), --no-av (skip the in-court anti-vacuity corpus;
the crown passes it to nobody: every conjunct court it runs includes its corpus).

Output: one line per clause, "OK <clause> ...", "REFUSED[<code>] <clause> ...", "UNKNOWN[<code>] ...".
Exit: 0 ALIVE (every clause OK); 1 REFUSED (a clause refused; typed code names the counterexample);
75 UNKNOWN (a tool or canonical checkout the court needs is absent; nothing refused).

Standing semantics: BENCHMARK_DESIGN_ALIVE is a standing of the design only. NON_LLM_OPERATIONAL_ALIVE
is UNKNOWN for every class (n = 0 executed unseen members) and every receipt says so; the crown refuses
any receipt that claims otherwise. No LLM runs on any path: every subprocess gets env -i with a private
PATH (python3, git, ggen and /usr/bin:/bin only) and the court refuses to start (UNKNOWN) when that PATH
reaches an LLM client binary.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import time
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
PINS = tomllib.loads((HERE / "pins.toml").read_text(encoding="utf-8"))
CONJUNCTS = {"bd": "BenchmarkDesign", "msa": "MSAContract", "gqp": "GeneratedQualificationPlan"}
WRAPPERS = {
    "bd": "release/v26.9.23/courts/CE23-12-BenchmarkDesign.sh",
    "msa": "release/v26.9.23/courts/CE23-12-MSAContract.sh",
    "gqp": "release/v26.9.23/courts/CE23-12-GeneratedQualificationPlan.sh",
    "crown": "release/v26.9.23/courts/CE23-12.sh",
}
LLM_BINARIES = ("claude", "zcode", "codex", "gemini", "ollama", "openai", "aider", "llm", "cursor-agent")
NS_CE = "https://ggen-igniter.dev/sjira/chatman-26.9.23#"


class Refusal(Exception):
    pass


class Unknown(Exception):
    """An environmental absence (a tool, a checkout, the court's own scratch): standing UNKNOWN."""


# ----------------------------------------------------------------------------------------------------
# Verdicts, environment, subject


class Verdicts:
    def __init__(self, label: str):
        self.label = label
        self.lines: list[tuple[str, str, str]] = []

    def ok(self, clause: str, msg: str) -> None:
        self.lines.append(("OK", clause, msg))
        print(f"OK {clause} {msg}", flush=True)

    def refuse(self, code: str, clause: str, msg: str) -> None:
        self.lines.append((f"REFUSED[{code}]", clause, msg))
        print(f"REFUSED[{code}] {clause} {msg}", flush=True)

    def unknown(self, code: str, clause: str, msg: str) -> None:
        self.lines.append((f"UNKNOWN[{code}]", clause, msg))
        print(f"UNKNOWN[{code}] {clause} {msg}", flush=True)

    def refused(self) -> list:
        return [ln for ln in self.lines if ln[0].startswith("REFUSED")]

    def unknowns(self) -> list:
        return [ln for ln in self.lines if ln[0].startswith("UNKNOWN")]

    def exit_code(self) -> int:
        if self.refused():
            return 1
        if self.unknowns():
            return 75
        return 0


class Env:
    """env -i for every subprocess: private PATH of exactly python3, git and ggen plus /usr/bin:/bin."""

    def __init__(self, scratch: Path):
        self.scratch = scratch
        self.bin = scratch / "bin"
        self.home = scratch / "home"
        self.tmp = scratch / "tmp"
        for d in (self.bin, self.home, self.tmp):
            d.mkdir(parents=True, exist_ok=True)
        self.tools = {}
        for tool in ("python3", "git", "ggen"):
            found = shutil.which(tool)
            if found:
                real = Path(found).resolve()
                (self.bin / tool).symlink_to(real)
                self.tools[tool] = str(real)
        self.path = f"{self.bin}:/usr/bin:/bin"
        self.user_base = subprocess.run([sys.executable, "-m", "site", "--user-base"], capture_output=True,
                                        text=True).stdout.strip()

    def llm_on_path(self) -> list[str]:
        hits = []
        for d in self.path.split(":"):
            for name in LLM_BINARIES:
                p = Path(d) / name
                if p.exists():
                    hits.append(str(p))
        return hits

    def vars(self, extra: dict | None = None) -> dict:
        v = {"HOME": str(self.home), "PATH": self.path, "LANG": "en_US.UTF-8", "TMPDIR": str(self.tmp),
             "PYTHONDONTWRITEBYTECODE": "1"}
        if self.user_base:
            v["PYTHONUSERBASE"] = self.user_base
        if extra:
            v.update(extra)
        return v

    def run(self, argv: list[str], cwd: Path, timeout: int = 1200, extra: dict | None = None):
        self.alive()
        return subprocess.run(argv, cwd=str(cwd), env=self.vars(extra), capture_output=True, text=True,
                              timeout=timeout)

    def alive(self) -> None:
        if not (self.bin / "ggen").exists() or not self.tmp.is_dir():
            raise Unknown(f"the court's scratch {self.scratch} vanished during the run (removed by another process)")


def git(root: Path, *args: str, check: bool = True) -> str:
    proc = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if check and proc.returncode != 0:
        raise Refusal(f"git {' '.join(args)}: {proc.stderr.strip()[:300]}")
    return proc.stdout


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


class Ctx:
    def __init__(self, root: Path, conjunct: str, scratch: Path, verdicts: Verdicts):
        self.root = root
        self.conjunct = conjunct
        self.scratch = scratch
        self.v = verdicts
        self.env = Env(scratch)
        self.bench = root / PINS["subject"]["bench"]
        self.pack = self.bench / "pack"
        self.cache: dict = {}
        self.head = ""
        self.bench_tree = ""

    # lazily loaded pack modules (never writing bytecode into the pack)
    def mod(self, name: str):
        key = f"mod:{name}"
        if key not in self.cache:
            sys.path.insert(0, str(self.pack / "scripts"))
            try:
                self.cache[key] = load_module(f"ce23_12_{name}_{id(self)}", self.pack / "scripts" / f"{name}.py")
            finally:
                sys.path.pop(0)
        return self.cache[key]

    def union(self):
        if "union" not in self.cache:
            self.cache["union"] = self.mod("verify").load_union(self.bench)
        return self.cache["union"]


# ----------------------------------------------------------------------------------------------------
# Common clauses


def clause_tools(ctx: Ctx) -> bool:
    missing = [t for t in ("python3", "git", "ggen") if t not in ctx.env.tools]
    if missing:
        ctx.v.unknown("TOOL_MISSING", "E0", f"not on PATH: {missing}")
        return False
    hits = ctx.env.llm_on_path()
    if hits:
        ctx.v.unknown("LLM_ON_PATH", "E0", f"the court PATH reaches LLM clients {hits}")
        return False
    try:
        import pyoxigraph  # noqa: F401
        import pyshacl  # noqa: F401
        import rdflib  # noqa: F401
        import scipy  # noqa: F401
        import statsmodels  # noqa: F401
        import yaml  # noqa: F401
    except ImportError as exc:
        ctx.v.unknown("TOOL_MISSING", "E0", f"python library absent: {exc}")
        return False
    ctx.v.ok("E0", f"no-LLM environment: env -i, PATH={ctx.env.path} (python3, git, ggen only), no LLM client reachable")
    return True


def clause_subject(ctx: Ctx) -> bool:
    try:
        ctx.head = git(ctx.root, "rev-parse", "HEAD").strip()
        dirty = git(ctx.root, "status", "--porcelain", "-uall", "--", *PINS["subject"]["judged"]).strip()
        ctx.bench_tree = git(ctx.root, "rev-parse", f"HEAD:{PINS['subject']['bench']}").strip()
    except Refusal as exc:
        ctx.v.refuse("subject_unresolved", "S0", str(exc))
        return False
    if dirty:
        ctx.v.refuse("dirty_subject", "S0", f"the judged slice differs from HEAD {ctx.head[:12]}: {dirty.splitlines()[:5]}")
        return False
    court_files = [f"release/v26.9.23/courts/ce23_12/{p.name}" for p in sorted(HERE.glob("*")) if p.is_file()]
    if ctx.root.resolve() == HERE.parents[3].resolve():
        tracked = set(git(ctx.root, "ls-files", "--", "release/v26.9.23/courts/ce23_12").split())
        untracked = [f for f in court_files if f not in tracked]
        if untracked:
            ctx.v.refuse("court_not_committed", "S0", f"court files not in HEAD: {untracked}")
            return False
    ctx.v.ok("S0", f"subject {ctx.head} clean over {PINS['subject']['judged']}; bench tree {ctx.bench_tree}")
    return True


def clause_capital(ctx: Ctx) -> None:
    bad = []
    for rel, pin in PINS["capital"].items():
        p = ctx.root / rel
        if not p.is_file() or "sha256:" + sha256_bytes(p.read_bytes()) != pin:
            bad.append(rel)
    if bad:
        ctx.v.refuse("capital_changed", "K0", f"design capital differs from its goal.ttl pin: {bad}")
    else:
        ctx.v.ok("K0", "DESIGN.md, ontology-draft.ttl and orders.json equal their goal.ttl pins (design capital unedited)")


def clause_prose(ctx: Ctx) -> None:
    bad = []
    goal = (ctx.root / "release/v26.9.23/sjira/goal.ttl").read_text(encoding="utf-8")
    for rel, pin in PINS["prose"].items():
        p = ctx.root / rel
        if not p.is_file() or "sha256:" + sha256_bytes(p.read_bytes()) != pin:
            bad.append(f"{rel} bytes")
        if f'sj:sourceSha256 "{pin}"' not in goal:
            bad.append(f"{rel} not pinned by goal.ttl")
    if bad:
        ctx.v.refuse("prose_pin", "P1", f"{bad}")
    else:
        ctx.v.ok("P1", "both CE23-12 prose units byte-equal their pins and goal.ttl's sj:sourceSha256 (4146d688.., 80091c45..)")


def prose_spans_tool(ctx: Ctx) -> Path | None:
    pin = PINS["prose_spans"]
    xaas = Path(os.environ.get("XAAS_DIR", str(Path.home() / "xaas")))
    if not (xaas / ".git").exists():
        ctx.v.unknown("CHECKOUT_MISSING", "P2", f"canonical xaas checkout absent at {xaas}")
        return None
    proc = subprocess.run(["git", "-C", str(xaas), "show", f"{pin['commit']}:{pin['path']}"], capture_output=True)
    if proc.returncode != 0:
        ctx.v.unknown("CHECKOUT_MISSING", "P2", f"xaas has no {pin['commit'][:12]}:{pin['path']}")
        return None
    if sha256_bytes(proc.stdout) != pin["sha256"]:
        ctx.v.refuse("tool_pin", "P2", f"prose_spans.py at {pin['commit'][:12]} is not sha256 {pin['sha256'][:12]}")
        return None
    tool = ctx.scratch / "prose_spans.py"
    tool.write_bytes(proc.stdout)
    return tool


def clause_prose_spans(ctx: Ctx) -> None:
    tool = prose_spans_tool(ctx)
    if tool is None:
        return
    pin = PINS["prose_spans"]
    for rel, cand in PINS["candidates"].items():
        extract = cand.replace(".ttl", ".extract.json")
        proc = ctx.env.run(["python3", str(tool), "check", "--source", rel, "--candidates", cand, "--extract", extract,
                            "--namespace", pin["namespace"], "--prefix", pin["prefix"]], ctx.root)
        first = (proc.stdout.strip().splitlines() or [""])[0]
        if proc.returncode != 0:
            ctx.v.refuse("prose_span", "P2", f"{rel}: prose_spans check exit {proc.returncode}: {(proc.stdout + proc.stderr)[-400:]}")
        else:
            ctx.v.ok("P2", f"{rel}: {first}")


def run_script(ctx: Ctx, clause: str, code: str, argv: list[str], okmsg: str) -> bool:
    proc = ctx.env.run(["python3", *argv], ctx.bench)
    out = (proc.stdout + proc.stderr).strip()
    if proc.returncode == 75:
        ctx.v.unknown("TOOL_MISSING", clause, out[-300:])
        return False
    if proc.returncode != 0:
        ctx.v.refuse(code, clause, out[-600:])
        return False
    ctx.v.ok(clause, okmsg + " | " + out.splitlines()[-1][:200])
    return True


def clause_kernel(ctx: Ctx, script: str = "pack/scripts/evidence_tiers.py") -> bool:
    """K1: the statistics kernel's --check over the bench tree (the Q3 harness also runs a blinded copy)."""
    return run_script(ctx, "K1", "kernel_drift", [script, "--consumer", ".", "--check"],
                      "generated tiers and bound rows equal the kernel (scipy/statsmodels agree to 1e-9)")


def clause_generated_inputs(ctx: Ctx) -> None:
    run_script(ctx, "I1", "import_drift", ["pack/scripts/import_inputs.py", "--consumer", ".", "--check"],
               "imports/ are byte copies of the committed sjira candidates, goal graph and compiled orders")
    clause_kernel(ctx)
    run_script(ctx, "L1", "lift_drift", ["pack/scripts/lift_reference_orders.py", "--consumer", ".", "--check"],
               "generated/reference-orders.ttl equals the lift of orders.json")


def clause_ggen_version(ctx: Ctx) -> bool:
    proc = ctx.env.run(["ggen", "--version"], ctx.scratch)
    if proc.returncode != 0 or PINS["ggen"]["version"] not in proc.stdout:
        ctx.v.refuse("ggen_identity", "G0", f"ggen --version = {proc.stdout.strip()[:80]!r}, pinned {PINS['ggen']['version']}")
        return False
    ctx.v.ok("G0", f"ggen {PINS['ggen']['version']} at {ctx.env.tools['ggen']} (sha256 {sha256_bytes(Path(ctx.env.tools['ggen']).read_bytes())[:16]})")
    return True


def tracked_bench_files(ctx: Ctx) -> list[str]:
    bench_rel = PINS["subject"]["bench"]
    return [p for p in git(ctx.root, "ls-files", "--", bench_rel).splitlines() if p]


def fresh_render(ctx: Ctx, label: str) -> tuple[Path, subprocess.CompletedProcess]:
    """Copy the committed bench tree (tracked files only, out/ removed) and run ggen sync run there."""
    bench_rel = PINS["subject"]["bench"]
    dest = ctx.scratch / f"render-{label}" / "bench"
    if dest.parent.exists():
        shutil.rmtree(dest.parent)
    for rel in tracked_bench_files(ctx):
        sub = rel[len(bench_rel) + 1:]
        if sub.startswith("out/"):
            continue
        target = dest / sub
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ctx.root / rel, target)
    (dest / "templates").mkdir(exist_ok=True)
    proc = ctx.env.run(["ggen", "sync", "run"], dest, timeout=900)
    return dest, proc


def out_files(base: Path) -> dict[str, bytes]:
    out = base / "out"
    return {str(p.relative_to(base)): p.read_bytes() for p in sorted(out.rglob("*")) if p.is_file()} if out.exists() else {}


def projection_equal(a: dict[str, bytes], b: dict[str, bytes]) -> bool:
    """The G1 comparator: the same out/ file set and every file byte-identical."""
    return a == b


def regen_renders(ctx: Ctx) -> list[dict[str, bytes]] | None:
    """Two fresh `ggen sync run` renders of the bench tree (out/ excluded from the input); None after a
    typed G1 refusal. Cached per Ctx: the Q3 harness judges one mutant with the real and the blinded
    comparator over the same two renders."""
    if "renders" in ctx.cache:
        return ctx.cache["renders"]
    renders = []
    for label in ("a", "b"):
        dest, proc = fresh_render(ctx, label)
        if proc.returncode != 0:
            text = proc.stdout + proc.stderr
            gate = re.search(r"gate `([^`]+)`", text)
            code = "ggen_gate_refused" if gate else "ggen_sync_failed"
            ctx.v.refuse(code, "G1", f"fresh `ggen sync run` exit {proc.returncode}: {(gate.group(1) if gate else '')} "
                         f"{[ln for ln in text.splitlines() if 'ERROR' in ln][:1]}")
            return None
        renders.append(out_files(dest))
    ctx.cache["renders"] = renders
    return renders


def clause_regenerate(ctx: Ctx, same=projection_equal) -> None:
    key = "regen" if same is projection_equal else f"regen:{same.__name__}"
    if key in ctx.cache:
        ctx.v.ok("G1", ctx.cache[key])
        return
    committed = out_files(ctx.bench)
    tracked = {p[len(PINS['subject']['bench']) + 1:] for p in tracked_bench_files(ctx) if "/out/" in "/" + p[len(PINS['subject']['bench']) + 1:]}
    if set(committed) != tracked:
        ctx.v.refuse("untracked_projection", "G1", f"out/ on disk differs from out/ in HEAD: {sorted(set(committed) ^ tracked)[:5]}")
        return
    renders = regen_renders(ctx)
    if renders is None:
        return
    if not same(renders[0], renders[1]):
        diff = sorted(k for k in set(renders[0]) | set(renders[1]) if renders[0].get(k) != renders[1].get(k))
        ctx.v.refuse("nondeterministic_projection", "G1", f"two fresh renders differ: {diff[:5]}")
        return
    if not same(renders[0], committed):
        diff = sorted(k for k in set(renders[0]) | set(committed) if renders[0].get(k) != committed.get(k))
        ctx.v.refuse("projection_drift", "G1", f"committed out/ differs from a fresh render (hand edit or stale projection): {diff[:6]}")
        return
    msg = (f"two fresh `ggen sync run` renders of the committed bench tree (ggen.lock pins the pack and every "
           f"input; every pack gate admitted) are byte-identical to each other and to the committed out/ ({len(committed)} files)")
    if same is not projection_equal:
        msg = f"[comparator {same.__name__}] " + msg
    ctx.cache[key] = msg
    if same is projection_equal:
        ctx.cache["regen_files"] = committed
    ctx.v.ok("G1", msg)


def clause_headers(ctx: Ctx) -> None:
    bad = []
    files = out_files(ctx.bench)
    for rel, data in files.items():
        text = data.decode("utf-8", errors="replace")
        head = text.lstrip()[:400]
        if rel.endswith(".json"):
            try:
                ok = str(json.loads(text).get("_generated", "")).startswith("GENERATED by ggen sync")
            except json.JSONDecodeError:
                ok = False
        else:
            ok = head.startswith("# GENERATED by ggen sync") or head.startswith("<!-- GENERATED by ggen sync")
        if not ok:
            bad.append(rel)
    for rel in ("generated/evidence-tiers.ttl", "generated/bound-table.ttl", "generated/reference-orders.ttl"):
        if not (ctx.bench / rel).read_text(encoding="utf-8").startswith("# GENERATED by nonllm-class-qualification-pack"):
            bad.append(rel)
    if bad:
        ctx.v.refuse("hand_written_artifact", "G2", f"artifacts without a GENERATED header: {bad[:6]}")
    else:
        ctx.v.ok("G2", f"every benchmark artifact ({len(files)} out/ projections, 3 generated/ graphs) names its generator (GENERATED header); none is hand-written")


def cited_propositions(ctx: Ctx) -> tuple[dict, set]:
    import rdflib
    g = ctx.union()
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
    committed = set()
    for cand in PINS["candidates"].values():
        cg = rdflib.Graph().parse(ctx.root / cand, format="turtle")
        committed |= set(cg.subjects(rdflib.RDF.type, SJ.Proposition))
    design = rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle")
    cites: dict = {}
    for s, o in design.subject_objects(PROV.wasDerivedFrom):
        cites.setdefault(o, set()).add(s)
    for s, o in g.subject_objects(PROV.wasDerivedFrom):
        cites.setdefault(o, set()).add(s)
    return cites, committed


def clause_trace(ctx: Ctx, gate_key: str, clause: str) -> None:
    import rdflib
    SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
    cites, committed = cited_propositions(ctx)
    foreign = sorted(str(p) for p in cites if str(p).startswith(NS_CE + "P-") and p not in committed)
    gate = rdflib.URIRef(PINS["gates"][gate_key])
    required = set()
    for cand in PINS["candidates"].values():
        cg = rdflib.Graph().parse(ctx.root / cand, format="turtle")
        required |= set(cg.subjects(SJ.requiredBy, gate))
    uncovered = sorted(str(p).rsplit("#", 1)[-1] for p in required if p not in cites)
    if foreign:
        ctx.v.refuse("trace_to_uncommitted_proposition", clause, f"design nodes cite propositions absent from the committed candidates: {foreign[:4]}")
    elif not required:
        ctx.v.refuse("gate_without_requirement", clause, f"no committed proposition is required by {gate_key}")
    elif uncovered:
        ctx.v.refuse("uncovered_requirement", clause, f"propositions required by {gate_key} that no design node traces to: {uncovered}")
    else:
        nodes = len({s for p in required for s in cites.get(p, ())})
        ctx.v.ok(clause, f"all {len(required)} committed propositions required by ce:CE23-12{'' if gate_key == 'crown' else '-' + gate_key} are traced by {nodes} design nodes; every cited proposition is a committed, span-verified candidate")


def clause_asks(ctx: Ctx, ids: list[str], clause: str) -> None:
    import pyoxigraph as ox
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    g = ctx.union()
    design = rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle")
    asks = {str(design.value(s, NLB.predicateId)): str(q) for s, q in design.subject_objects(NLB.askQuery)}
    store = ox.Store()
    store.load(g.serialize(format="nt").encode("utf-8"), format=ox.RdfFormat.N_TRIPLES)
    results = []
    for pid in ids:
        if pid not in asks:
            ctx.v.refuse("ask_missing", clause, f"{pid} has no ASK predicate in design.ttl")
            continue
        a, b = bool(g.query(asks[pid]).askAnswer), bool(store.query(asks[pid]))
        results.append(f"{pid}={a}/{b}")
        if not (a and b):
            ctx.v.refuse("design_predicate_false", clause, f"{pid}: rdflib={a} pyoxigraph={b}")
    if all(r.endswith("True/True") for r in results) and len(results) == len(ids):
        ctx.v.ok(clause, f"design ASK predicates true on rdflib and pyoxigraph: {' '.join(results)}")


def pack_report(ctx: Ctx) -> dict:
    if "report" not in ctx.cache:
        ctx.env.alive()
        verify = ctx.mod("verify")
        corpus = verify.load_corpus(HERE / "mutations.toml")
        old_path = os.environ.get("PATH", "")
        os.environ["PATH"] = ctx.env.path
        try:
            ctx.cache["report"] = verify.judge(ctx.bench, corpus, True, None)
        finally:
            os.environ["PATH"] = old_path
        ctx.cache["report_fails"] = verify.expectations(ctx.cache["report"])
    return ctx.cache["report"]


def clause_pack(ctx: Ctx) -> None:
    report = pack_report(ctx)
    fails = ctx.cache["report_fails"]
    arts = report["artifacts"]
    good = sum(1 for a in arts if a["good"])
    if fails:
        ctx.v.refuse("pack_qualification", "D1", f"{len(fails)} expectation failures: {fails[:3]}")
    else:
        ctx.v.ok("D1", f"benchmark ontology admitted: the in-repo nonllm-class-qualification-pack (pack/) admits {good} good "
                 f"artifacts and refuses {len(arts) - good} registered mutants under their registered law on 5 instruments "
                 f"(pyshacl, SPARQL on rdflib, SPARQL on pyoxigraph, native evaluator, ggen's own gates)")


def clause_nonimplication(ctx: Ctx, clause: str) -> None:
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    ES = rdflib.Namespace("https://ggen.dev/ontology/evidence-standing#")
    g = ctx.union()
    classes = sorted(g.subjects(NLB.claimStatus, rdflib.Literal("KNOWN_CANDIDATE")))
    bad = []
    for c in classes:
        standings = [s for s in g.subjects(NLB.forClass, c) if (s, NLB.standingKind, NLB.NON_LLM_OPERATIONAL_ALIVE) in g]
        if not standings:
            bad.append(f"{c}: no NON_LLM_OPERATIONAL_ALIVE tuple")
        for s in standings:
            if (s, ES.standingState, ES.UNKNOWN) not in g or int(g.value(s, NLB.n)) != 0:
                bad.append(f"{s}: not UNKNOWN at n = 0")
    alive = [s for s in g.subjects(ES.standingState, ES.ALIVE)]
    if alive:
        bad.append(f"ALIVE standings in the design graph: {alive}")
    if (NLB.BENCHMARK_DESIGN_ALIVE, NLB.doesNotImply, NLB.NON_LLM_OPERATIONAL_ALIVE) not in g:
        bad.append("the pack lost BENCHMARK_DESIGN_ALIVE nlb:doesNotImply NON_LLM_OPERATIONAL_ALIVE")
    report = (ctx.bench / "out/QUALIFICATION_REPORT.md").read_text(encoding="utf-8")
    rows = [ln for ln in report.splitlines() if ln.startswith("| ") and "NON_LLM_OPERATIONAL_ALIVE" in ln]
    if len(rows) != len(classes) or any("| UNKNOWN |" not in r for r in rows):
        bad.append("QUALIFICATION_REPORT.md does not show every class UNKNOWN")
    if bad:
        ctx.v.refuse("operational_standing_implied", clause, f"{bad[:4]}")
    else:
        ctx.v.ok(clause, f"BENCHMARK_DESIGN_ALIVE does not imply NON_LLM_OPERATIONAL_ALIVE: all {len(classes)} KNOWN_CANDIDATE "
                 f"tuples are UNKNOWN at n = 0, no ALIVE standing exists in the design graph, the report projects every class UNKNOWN")
    ctx.cache["classes"] = [str(c).rsplit("#", 1)[-1] for c in classes]


# ----------------------------------------------------------------------------------------------------
# GeneratedQualificationPlan clauses


DOE_ARGS = ["out/doe/design-matrix.json", "--ci", "out/doe/ci-matrix.json"]


def clause_doe_verifier(ctx: Ctx, script: str = "pack/scripts/doe_verify.py") -> None:
    """A1v: A1's independent DOE verifier alone, same argv, read as A1 reads it (by exit: 0 ADMITTED,
    3 REFUSED): the Q3 judge of DOE corruptions."""
    proc = ctx.env.run(["python3", script, *DOE_ARGS], ctx.bench)
    refusals = [ln for ln in proc.stdout.splitlines() if ln.startswith("REFUSED(")]
    if proc.returncode == 0:
        ctx.v.ok("A1v", f"{Path(script).name} exit 0 (ADMITTED) on the generated design and CI matrices")
    elif proc.returncode == 3 and refusals:
        ctx.v.refuse("doe_refused", "A1v", " ".join(refusals)[:500])
    elif proc.returncode == 75:
        ctx.v.unknown("TOOL_MISSING", "A1v", (proc.stdout + proc.stderr)[-300:])
    else:
        ctx.v.refuse("doe_verifier_error", "A1v", f"exit {proc.returncode}: {(proc.stdout + proc.stderr)[-300:]}")


def clause_doe(ctx: Ctx) -> None:
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    RDFS = rdflib.RDFS
    g = ctx.union()
    proc = ctx.env.run(["python3", "pack/scripts/doe_verify.py", *DOE_ARGS], ctx.bench)
    if proc.returncode != 0:
        ctx.v.refuse("doe_refused", "A1", " ".join(ln for ln in proc.stdout.splitlines() if ln.startswith("REFUSED"))[:500])
        return
    result = json.loads(proc.stdout[: proc.stdout.rindex("}") + 1])
    design = json.loads((ctx.bench / "out/doe/design-matrix.json").read_text(encoding="utf-8"))
    ci = json.loads((ctx.bench / "out/doe/ci-matrix.json").read_text(encoding="utf-8"))
    standing = json.loads((ctx.bench / "out/doe/factor-standing.json").read_text(encoding="utf-8"))
    workflow = (ctx.bench / "out/ci/bench-ce23-12-b3.yml").read_text(encoding="utf-8")
    bad = []
    designs = list(g.subjects(rdflib.RDF.type, NLB.FractionalFactorialDesign))
    if len(designs) != 1:
        bad.append(f"{len(designs)} designs in the graph")
    else:
        d = designs[0]
        if int(g.value(d, NLB.resolution)) != result["resolution"] or int(g.value(d, NLB.runCount)) != result["runs"]:
            bad.append("graph-declared resolution/run count differ from the computed design")
        varied = sorted(str(g.value(f, RDFS.label)) for f in g.objects(d, NLB.hasFactor))
        if varied != sorted(f["factor"] for f in design["factors"]):
            bad.append(f"matrix factors {sorted(f['factor'] for f in design['factors'])} != design factors {varied}")
    unsupported = sorted(str(g.value(f, RDFS.label)) for f in g.subjects(NLB.support, rdflib.Literal("UNSUPPORTED")))
    if "OS" not in unsupported:
        bad.append("the OS factor is not declared UNSUPPORTED")
    for label in unsupported:
        if label in {f["factor"] for f in design["factors"]}:
            bad.append(f"UNSUPPORTED factor {label} has a column")
        if label not in {n["factor"] for n in design["not_varied"]} or label not in ci["not_varied"]:
            bad.append(f"UNSUPPORTED factor {label} is not listed as not varied")
        entry = [f for f in standing["factors"] if f["factor"] == label]
        if not entry or entry[0]["support"] != "UNSUPPORTED" or entry[0]["column"] is not None:
            bad.append(f"factor-standing.json does not type {label} UNSUPPORTED without a column")
    if workflow.count("runs-on:") != 1 or re.search(r"^\s+(os|OS):", workflow, re.M):
        bad.append("the generated workflow varies the runner/OS")
    if bad:
        ctx.v.refuse("doe_projection", "A1", f"{bad[:4]}")
    else:
        ctx.v.ok("A1", f"DOE support matrix generated: {result['runs']}-run {design['design']} over the VARIED factors, "
                 f"computed {result['defining_relation']} resolution {result['resolution']} = declared, balanced and orthogonal; "
                 f"OS UNSUPPORTED (no column, in not_varied, one macOS runner); CI matrix = the same design")


def clause_statistics(ctx: Ctx) -> None:
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    g = ctx.union()
    tiers = sorted(((int(g.value(t, NLB.tierRank)), int(g.value(t, NLB.tierN)), float(g.value(t, NLB.zeroDefectUpperBound)))
                    for t in g.subjects(rdflib.RDF.type, NLB.EvidenceTier)))
    ns = [n for _, n, _ in tiers if n > 0]
    bad = []
    if ns != sorted(set(ns)) or ns[:4] != [30, 100, 300, 3000]:
        bad.append(f"tier N ladder {ns} is not 30 < 100 < 300 < 3000")
    bounds = {n: b for _, n, b in tiers}
    if abs(bounds.get(30, 0) - 0.095034) > 5e-7 or abs(bounds.get(300, 0) - 0.009936) > 5e-7:
        bad.append(f"tier bounds {bounds}")
    rules = (ctx.bench / "out/ACCEPTANCE_RULES.md").read_text(encoding="utf-8")
    for needle in ("0 failures in 30", "0.095034", "N_discovery < N_qualification < N_operational", PINS["statement"]["os_ceiling"]):
        if needle.lower() not in rules.lower():
            bad.append(f"ACCEPTANCE_RULES.md lacks {needle!r}")
    rules_json = json.loads((ctx.bench / "out/acceptance-rules.json").read_text(encoding="utf-8"))
    if [t["n"] for t in rules_json["tiers"] if t["n"] > 0] != ns:
        bad.append("acceptance-rules.json tiers differ from the graph")
    report = pack_report(ctx) if "report" in ctx.cache else None
    overclaim_ids = ("M2", "M3", "M4", "M5", "M6", "G1", "G2")
    if report is None:
        verify = ctx.mod("verify")
        corpus = [a for a in verify.load_corpus(HERE / "mutations.toml") if a.id in overclaim_ids]
        report = verify.judge(ctx.bench, corpus, False, set(overclaim_ids))
        fails = verify.expectations(report)
    else:
        fails = [f for f in ctx.cache["report_fails"] if any(f"FAIL {i} " in f or f"FAIL {i}:" in f for i in overclaim_ids)]
    if fails:
        bad.append(f"overclaim fixtures: {fails[:2]}")
    if bad:
        ctx.v.refuse("statistics", "A2", f"{bad[:4]}")
    else:
        ctx.v.ok("A2", "statistical acceptance rules generated from the kernel: tiers 30 < 100 < 300 < 3000 with exact 0-defect bounds "
                 "0.095034 / 0.029513 / 0.009936 / 0.000998; a zero-failure run is read only to its tier bound (overclaim fixtures "
                 "n=31 u=0.05, n=30 x=1 u=0.01, 30 observations on 1 subject, n=20 at DISCOVERY, no BoundRow refused; lawful DISCOVERY "
                 "and QUALIFICATION tuples admitted)")


def plan_graph(ctx: Ctx):
    import rdflib
    g = rdflib.Graph().parse(ctx.bench / "out/plan/orders.ttl", format="turtle")
    return g


def clause_plan(ctx: Ctx) -> None:
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
    DCT = rdflib.Namespace("http://purl.org/dc/terms/")
    design = rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle")
    handwritten = sorted(str(s) for s in design.subjects(rdflib.RDF.type, SJ.WorkOrder))
    if handwritten:
        ctx.v.refuse("handwritten_work_order", "A4", f"design.ttl holds hand-written work orders: {handwritten[:3]}")
        return
    plan = plan_graph(ctx)
    g = ctx.union() + plan
    orders = set(plan.subjects(rdflib.RDF.type, SJ.WorkOrder))
    entries = list(plan.subjects(rdflib.RDF.type, NLB.PlanEntry))
    bad = []
    if len(entries) != len(orders) or {plan.value(e, NLB.planOrder) for e in entries} != orders:
        bad.append("orders and plan entries are not one-to-one")
    classes = sorted(g.subjects(NLB.claimStatus, rdflib.Literal("KNOWN_CANDIDATE")))
    families = sorted(g.subjects(rdflib.RDF.type, NLB.BenchmarkFamily))
    courts = sorted(g.subjects(rdflib.RDF.type, NLB.MSACourt))
    gaps = sorted(g.subjects(rdflib.RDF.type, NLB.CapabilityGap))
    by_pair = {(plan.value(e, NLB.planClass), plan.value(e, NLB.planFamily)) for e in entries}
    by_source = {plan.value(e, NLB.planSource) for e in entries}
    for c in classes:
        for f in families:
            if (c, f) not in by_pair:
                bad.append(f"no generated order for {c.rsplit('#', 1)[-1]} x {f.rsplit('#', 1)[-1]}")
    for s in courts + gaps:
        if s not in by_source:
            bad.append(f"no generated order for {s.rsplit('#', 1)[-1]}")
    refs = {str(g.value(r, NLB.referenceId)) for e in entries for r in plan.objects(e, NLB.referenceOrder)}
    successor = {str(g.value(r, NLB.referenceId)) for r in g.subjects(NLB.referenceRequirement, rdflib.Literal("NON_LLM_OPERATIONAL successor"))}
    if successor - refs:
        bad.append(f"successor reference orders not covered: {sorted(successor - refs)}")
    for o in orders:
        acc, fal = plan.value(o, SJ.acceptance), plan.value(o, SJ.falsifier)
        if not acc or not fal or not str(plan.value(acc, DCT.description) or "").strip() or not str(plan.value(fal, DCT.description) or "").strip():
            bad.append(f"{o}: acceptance or falsifier missing")
    for e in entries:
        if str(plan.value(e, NLB.planKind)) == "CLASS_FAMILY_TIER":
            klass, tier = plan.value(e, NLB.planClass), plan.value(e, NLB.planTier)
            cur = [g.value(s, NLB.tier) for s in g.subjects(NLB.forClass, klass)
                   if (s, NLB.standingKind, NLB.NON_LLM_OPERATIONAL_ALIVE) in g]
            if not cur or int(g.value(tier, NLB.tierRank)) != int(g.value(cur[0], NLB.tierRank)) + 1:
                bad.append(f"{plan.value(e, NLB.planOrder)}: target tier is not the class's next tier")
    expected = len(classes) * len(families) + len(courts) + len(gaps)
    if len(orders) != expected:
        bad.append(f"{len(orders)} generated orders, the design implies {expected}")
    if bad:
        ctx.v.refuse("plan_incomplete", "A4", f"{bad[:4]}")
        return
    ctx.v.ok("A4", f"benchmark work orders generated (plan CONSTRUCT, out/plan/orders.ttl): {len(orders)} tuple-complete orders = "
             f"{len(classes)} classes x {len(families)} families (next tier DISCOVERY) + {len(courts)} MSA courts + {len(gaps)} capability gaps; "
             f"every successor reference order ({len(successor)}) covered; design.ttl holds 0 work orders")
    # semantic-jira-pack admission of the generated orders (pinned ggen_igniter commit)
    pin = PINS["semantic_jira"]
    gi = Path(os.environ.get("GGEN_IGNITER_DIR", str(Path.home() / "ggen_igniter")))
    if not (gi / ".git").exists():
        ctx.v.unknown("CHECKOUT_MISSING", "A4s", f"canonical ggen_igniter checkout absent at {gi}")
        return
    blobs = {}
    for key in ("shapes", "ontology"):
        proc = subprocess.run(["git", "-C", str(gi), "show", f"{pin['commit']}:{pin[key]}"], capture_output=True)
        if proc.returncode != 0:
            ctx.v.unknown("CHECKOUT_MISSING", "A4s", f"ggen_igniter has no {pin['commit'][:12]}:{pin[key]}")
            return
        blobs[key] = proc.stdout
    from pyshacl import validate
    data = rdflib.Graph()
    data += plan
    data.parse(data=blobs["ontology"], format="turtle")
    data.parse(ctx.bench / "imports/goal.ttl", format="turtle")
    data.parse(ctx.bench / "design.ttl", format="turtle")
    shapes = rdflib.Graph().parse(data=blobs["shapes"], format="turtle")
    conforms, report, text = validate(data, shacl_graph=shapes, inference="rdfs", advanced=True)
    if not conforms:
        ctx.v.refuse("work_order_shape", "A4s", f"semantic-jira-pack WorkOrderShape refuses generated orders: {text[:500]}")
    else:
        ctx.v.ok("A4s", f"all {len(orders)} generated orders conform to the semantic-jira-pack work-order shapes at ggen_igniter {pin['commit'][:12]} "
                 f"(closed WorkOrderShape, Friday tuple, GoalCheckpoint, Capability)")


def clause_compile_prose(ctx: Ctx) -> None:
    script = ctx.root / "release/v26.9.23/sjira/compile_check.sh"
    proc = subprocess.run(["sh", str(script)], cwd=str(ctx.root), capture_output=True, text=True, timeout=1200,
                          env={"HOME": os.environ.get("HOME", str(Path.home())), "PATH": "/usr/bin:/bin:" + str(Path(ctx.env.tools["python3"]).parent),
                               "LANG": "en_US.UTF-8"})
    last = (proc.stdout.strip().splitlines() or [""])[-1]
    if proc.returncode == 75:
        ctx.v.unknown("TOOL_MISSING", "A4p", last[:300])
    elif proc.returncode != 0:
        ctx.v.refuse("prose_orders_drift", "A4p", f"compile_check.sh exit {proc.returncode}: {last[:300]}")
    else:
        ctx.v.ok("A4p", "prose-derived CE23-12 orders (compile_prose over both units: 9 bench + 24 standings) recompute byte-identically: " + last[:160])


def clause_os_statement(ctx: Ctx) -> None:
    needle = PINS["statement"]["os_ceiling"]
    files = ["out/ACCEPTANCE_RULES.md", "out/QUALIFICATION_REPORT.md", "out/doe/factor-standing.json", "out/acceptance-rules.json"]
    missing = [f for f in files if needle.lower() not in (ctx.bench / f).read_text(encoding="utf-8").lower()]
    if missing:
        ctx.v.refuse("os_ceiling_unstated", "O1", f"{missing}")
    else:
        ctx.v.ok("O1", f"the generated artifacts state that {needle} ({len(files)} files); no OS level appears in any run")


# ----------------------------------------------------------------------------------------------------
# MSA clauses: the measurement system of the benchmark design, measured


def bound(ctx: Ctx, n: int, x: int) -> float:
    return ctx.mod("evidence_tiers").upper_bound(n, x, 0.95)


def tier_of(ctx: Ctx, n: int, x: int) -> str:
    p = bound(ctx, n, x)
    ladder = [(3000, 0.001, "SCALE_3000"), (300, 0.01, "OPERATIONAL"), (100, 0.03, "QUALIFICATION"), (30, 0.10, "DISCOVERY")]
    for tn, nominal, name in ladder:
        if n >= tn and p <= nominal:
            return name
    return "BELOW_DISCOVERY"


def msa_row(ctx: Ctx, question: str, n: int, defects: int, unit: str, extra: dict | None = None) -> dict:
    p = bound(ctx, n, defects)
    row = {"question": question, "n": n, "defects": defects, "upper_bound_95": round(p, 6), "tier": tier_of(ctx, n, defects),
           "unit": unit, "scope": PINS["statement"]["environment_scope"]}
    if extra:
        row.update(extra)
    ctx.cache.setdefault("msa_rows", []).append(row)
    return row


def verdict_vector(ctx: Ctx, instruments: tuple[str, ...], graph_override=None, order_seed: int | None = None) -> dict:
    verify = ctx.mod("verify")
    import rdflib
    corpus = verify.load_corpus(HERE / "mutations.toml")
    base = graph_override if graph_override is not None else ctx.union()
    if order_seed is not None:
        corpus = list(corpus)
        random.Random(order_seed).shuffle(corpus)
    design = rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle")
    inst = ctx.cache.get("instruments") or verify.Instruments(ctx.bench, design)
    ctx.cache["instruments"] = inst
    out = {}
    for art in corpus:
        g = art.apply(base)
        verdicts = []
        for name in instruments:
            fn = {"native": inst.native, "sparql-oxigraph": inst.sparql_oxigraph, "sparql-rdflib": inst.sparql_rdflib,
                  "shacl": inst.shacl}[name]
            accept, laws, _ = fn(g)
            verdicts.append((name, accept, tuple(sorted(laws))))
        out[art.id] = verdicts
    return dict(sorted(out.items()))


def clause_msa_contract(ctx: Ctx) -> None:
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
    PROV = rdflib.Namespace("http://www.w3.org/ns/prov#")
    g = ctx.union()
    gate = rdflib.URIRef(PINS["gates"]["MSAContract"])
    questions = []
    for cand in PINS["candidates"].values():
        cg = rdflib.Graph().parse(ctx.root / cand, format="turtle")
        questions += [p for p in cg.subjects(SJ.requiredBy, gate) if str(cg.value(p, SJ.propositionKind)) == "Falsifier"]
    props = set(g.subjects(rdflib.RDF.type, NLB.MSAProperty))
    unmapped = [str(q).rsplit("#", 1)[-1] for q in questions
                if not any((p, PROV.wasDerivedFrom, q) in g for p in props)]
    courts = list(g.subjects(rdflib.RDF.type, NLB.MSACourt))
    alive = [str(c) for c in courts if str(g.value(c, NLB.statusToday)) not in ("HOLDS_OBSERVED_DOMAIN", "FAILS", "FAILS_CLOSED", "UNMEASURED")]
    uncovered = [str(p).rsplit("#", 1)[-1] for p in props
                 if not any((c, NLB.msaProperty, p) in g and g.value(c, NLB.verifierCommand) is not None for c in courts)]
    if uncovered:
        ctx.v.refuse("msa_property_uncovered", "C1", f"MSA properties without a court: {uncovered}")
    elif len(questions) != 7 or unmapped:
        ctx.v.refuse("msa_question_unmapped", "C1", f"{len(questions)} operator MSA questions; unmapped to an MSA property: {unmapped}")
    elif alive:
        ctx.v.refuse("msa_status_claimed", "C1", f"MSA courts with a status outside the closed set (e.g. ALIVE): {alive}")
    else:
        statuses = sorted({str(g.value(c, NLB.statusToday)) for c in courts})
        ctx.v.ok("C1", f"MSA contract defined: the 7 operator MSA questions map to {len(props)} MSA properties covered by {len(courts)} "
                 f"courts (instrument + status today {statuses}); executor MSA_ALIVE is successor work and is not claimed")


def clause_msa_repeatability(ctx: Ctx) -> None:
    report = pack_report(ctx)
    base_vec = {a["id"]: [(k, v["accept"], tuple(v["laws"])) for k, v in sorted(a["instruments"].items())] for a in report["artifacts"]}
    changed: set[str] = set()
    pairs = 0
    fast = ("native", "sparql-oxigraph")
    first = verdict_vector(ctx, fast)
    repeats = [first] + [verdict_vector(ctx, fast) for _ in range(29)]
    for art_id in first:
        for i, name in enumerate(fast):
            pairs += 1
            seen = {r[art_id][i] for r in repeats} | {next(v for v in base_vec[art_id] if v[0] == name)}
            if len(seen) != 1:
                changed.add(art_id)
    slow = ("shacl", "sparql-rdflib")
    again = verdict_vector(ctx, slow)
    for art_id in again:
        for i, name in enumerate(slow):
            pairs += 1
            if again[art_id][i] != next(v for v in base_vec[art_id] if v[0] == name):
                changed.add(art_id)
    ggen_again = verify_ggen_again(ctx)
    for art_id, verdict in ggen_again.items():
        pairs += 1
        if verdict != next(v for v in base_vec[art_id] if v[0] == "ggen"):
            changed.add(art_id)
    # n counts distinct artifacts, never (instrument, artifact) repetitions (no pseudo-replication).
    units, defects = len(base_vec), len(changed)
    row = msa_row(ctx, "repeatability", units, defects,
                  f"distinct artifact, re-judged by 5 instruments ({pairs} instrument-artifact pairs: native and pyoxigraph 31x, pyshacl, rdflib and ggen 2x); a defect = any verdict change")
    if defects:
        ctx.v.refuse("msa_repeatability", "Q1", f"{defects}/{units} artifacts changed verdict on repetition: {sorted(changed)[:5]}")
    else:
        ctx.v.ok("Q1", f"repeatability: same artifact, same verdict for {units}/{units} distinct artifacts across {pairs} re-judged "
                 f"instrument-artifact pairs (0 defects; 95% upper bound {row['upper_bound_95']}, tier {row['tier']})")


def verify_ggen_again(ctx: Ctx) -> dict:
    verify = ctx.mod("verify")
    corpus = verify.load_corpus(HERE / "mutations.toml")
    design_text = (ctx.bench / "design.ttl").read_text(encoding="utf-8")
    inst = ctx.cache.get("instruments")
    if inst is None:
        import rdflib
        inst = verify.Instruments(ctx.bench, rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle"))
        ctx.cache["instruments"] = inst
    ctx.env.alive()
    old_path = os.environ.get("PATH", "")
    os.environ["PATH"] = ctx.env.path
    try:
        out = {}
        for art in corpus:
            accept, laws, _ = inst.ggen(art, design_text)
            out[art.id] = ("ggen", accept, tuple(sorted(laws)))
        return out
    finally:
        os.environ["PATH"] = old_path


def cohen_kappa(a: list[bool], b: list[bool]) -> float | None:
    n = len(a)
    po = sum(x == y for x, y in zip(a, b)) / n
    pa, pb = sum(a) / n, sum(b) / n
    pe = pa * pb + (1 - pa) * (1 - pb)
    if pe == 1:
        return None
    return (po - pe) / (1 - pe)


# Law encodings of the five instruments (release/v26.9.23/bench/pack/scripts/verify.py Instruments): the
# law texts each instrument evaluates. Instruments that share a law text are one encoding of the law run
# on several engines; their agreement measures engine agreement, not an independent implementation of
# the law (sparql-rdflib, sparql-oxigraph and ggen all evaluate pack/gates/*.rq; both SPARQL
# instruments also evaluate the design's nlb:askQuery texts).
LAW_TEXTS = {
    "shacl": frozenset({"pack/shacl/nlb-shapes.ttl"}),
    "sparql-rdflib": frozenset({"design.ttl nlb:askQuery", "pack/gates/*.rq", "pack/templates/*.tmpl construct"}),
    "sparql-oxigraph": frozenset({"design.ttl nlb:askQuery", "pack/gates/*.rq", "pack/templates/*.tmpl construct"}),
    "ggen": frozenset({"pack/gates/*.rq", "pack/templates/*.tmpl construct"}),
    "native": frozenset({"pack/scripts/native_predicates.py"}),
}


def law_encodings(names: list[str]) -> list[list[str]]:
    """Partition registered instruments into law encodings: the connected components of 'shares a law text'."""
    groups: list[set[str]] = []
    for name in names:
        joined, rest = {name}, []
        for g in groups:
            if any(LAW_TEXTS[name] & LAW_TEXTS[m] for m in g):
                joined |= g
            else:
                rest.append(g)
        groups = rest + [joined]
    return sorted(sorted(g) for g in groups)


def clause_msa_agreement(ctx: Ctx) -> None:
    report = pack_report(ctx)
    arts = report["artifacts"]
    names = sorted(arts[0]["instruments"])
    unregistered = [n for n in names if n not in LAW_TEXTS]
    encodings = law_encodings([n for n in names if n in LAW_TEXTS])
    enc_of = {n: i for i, g in enumerate(encodings) for n in g}
    goods = sum(a["good"] for a in arts)
    disagreements = cross = same = 0
    kappas = []
    for i, x in enumerate(names):
        for y in names[i + 1:]:
            ax = [a["instruments"][x]["accept"] for a in arts]
            ay = [a["instruments"][y]["accept"] for a in arts]
            disagreements += sum(p != q for p, q in zip(ax, ay))
            kappas.append(cohen_kappa(ax, ay))
            if x in enc_of and enc_of.get(x) == enc_of.get(y):
                same += 1
            else:
                cross += 1
    pairs = len(kappas)
    units = len(arts)
    split = sum(1 for a in arts if len({v["accept"] for v in a["instruments"].values()}) != 1)
    truth_miss = sum(1 for a in arts for v in a["instruments"].values() if v["accept"] != a["good"])
    label = "; ".join(" + ".join(g) for g in encodings)
    row = msa_row(ctx, "classification agreement", units, split,
                  f"distinct artifact ({goods} good, {len(arts) - goods} bad) judged by {len(names)} instruments over {len(encodings)} "
                  f"independent law encodings ({label}): {cross} cross-encoding pairs (independent implementations of the law), "
                  f"{same} same-encoding pairs (engine agreement only); a defect = any disagreement on the artifact",
                  {"law_encodings": encodings, "cross_encoding_pairs": cross, "same_encoding_pairs": same})
    if unregistered:
        ctx.v.refuse("msa_instrument_unregistered", "Q2", f"instruments without a registered law text (independence unknown): {unregistered}")
    elif len(encodings) < 2:
        ctx.v.refuse("msa_agreement_not_independent", "Q2", f"all {len(names)} instruments evaluate one law encoding ({label}): agreement measures engines only")
    elif split or disagreements or truth_miss or any(k is None or abs(k - 1.0) > 1e-12 for k in kappas):
        ctx.v.refuse("msa_agreement", "Q2", f"{disagreements} pairwise disagreements, {truth_miss} verdicts against the registered truth, kappas {kappas}")
    else:
        ctx.v.ok("Q2", f"classification agreement: {len(names)} instruments over {len(encodings)} independent law encodings ({label}) agree on "
                 f"every artifact; Cohen's kappa = 1.0 for all {pairs} pairs ({cross} cross-encoding pairs measure independent implementations "
                 f"of the law, {same} same-encoding pairs measure engine agreement only; defined: both good and bad items judged); "
                 f"0/{units} artifacts with a disagreement (95% upper bound {row['upper_bound_95']}, tier {row['tier']})")


# ----------------------------------------------------------------------------------------------------
# Q3 mutation sensitivity. n counts distinct corrupted subjects, each judged on the mutant by the court
# instrument that guards it (never an arithmetic identity on the corruption): design mutants by the five
# pack instruments; committed-output corruptions, written one at a time into a synthetic git repository
# of HEAD and restored after each unit, by G1 (the fresh-render comparator), K1 (evidence_tiers.py
# --check), A1v (doe_verify.py, read by exit as A1 reads it) and A4 (plan coverage). Every
# committed-output unit is also judged by a blinded variant of each instrument that judges it (the one
# property that instrument checks removed): an escape of the real instrument is always counted; a
# detected unit is counted only when every blinded variant admits it (the detection is witnessed to
# come from the checked property); a detected unit that a blinded variant also refuses carries no
# information about the property and is reported as a zero-information unit, never counted.

KERNEL_BLIND = ('        if not path.is_file() or path.read_text(encoding="utf-8") != text:\n',
                '        if False:  # BLINDED by the CE23-12 Q3 harness: committed outputs never compared\n')
DOE_BLIND = ("    return 0 if not refusals else 3\n",
             "    return 0  # BLINDED by the CE23-12 Q3 harness: the exit ignores every refusal\n")
Q3_EXPECT = {  # instrument -> (expected refusal code, needle its detail must carry)
    "G1": ("projection_drift", ""),
    "K1": ("kernel_drift", "REFUSED[kernel_output_drift]"),
    "A1v": ("doe_refused", "REFUSED("),
    "A4": ("plan_incomplete", "not one-to-one"),
}
Q3_BLIND_NAMES = {"G1": "file-name comparator", "K1": "--check without the output comparison",
                  "A1v": "exit ignoring refusals", "A4": "pair-only coverage"}


def names_only(a: dict[str, bytes], b: dict[str, bytes]) -> bool:
    """Blinded G1 comparator: the same out/ file names; file contents are never compared."""
    return set(a) == set(b)


def clause_plan_pairs_only(ctx: Ctx) -> None:
    """Blinded A4: coverage read from the plan's provenance entries alone (every KNOWN_CANDIDATE class x
    benchmark family, MSA court and capability gap has an nlb:PlanEntry); orders are never matched to entries."""
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    g = ctx.union()
    plan = plan_graph(ctx)
    entries = list(plan.subjects(rdflib.RDF.type, NLB.PlanEntry))
    pairs = {(plan.value(e, NLB.planClass), plan.value(e, NLB.planFamily)) for e in entries}
    sources = {plan.value(e, NLB.planSource) for e in entries}
    classes = sorted(g.subjects(NLB.claimStatus, rdflib.Literal("KNOWN_CANDIDATE")))
    families = sorted(g.subjects(rdflib.RDF.type, NLB.BenchmarkFamily))
    others = sorted(g.subjects(rdflib.RDF.type, NLB.MSACourt)) + sorted(g.subjects(rdflib.RDF.type, NLB.CapabilityGap))
    missing = [f"{c} x {f}" for c in classes for f in families if (c, f) not in pairs] + [str(s) for s in others if s not in sources]
    if missing:
        ctx.v.refuse("plan_incomplete", "A4", f"[pair-only coverage] uncovered: {missing[:4]}")
    else:
        ctx.v.ok("A4", f"[pair-only coverage] {len(entries)} plan entries cover every class x family, MSA court and capability gap")


def blinded_script(ctx: Ctx, name: str, anchor: tuple[str, str], dest_dir: Path) -> tuple[Path | None, str]:
    """A copy of the judged tree's pack/scripts/<name>.py with one checked property removed; (None, why)
    when the tree's script has no single line to blind (then no detection by it can be witnessed informative)."""
    text = (ctx.pack / "scripts" / f"{name}.py").read_text(encoding="utf-8")
    if text.count(anchor[0]) != 1:
        return None, f"pack/scripts/{name}.py has no single line {anchor[0].strip()[:70]!r} to blind"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{name}.py"
    dest.write_text(text.replace(anchor[0], anchor[1]), encoding="utf-8")
    return dest, ""


def blind_unavailable(why: str):
    def judge(ctx: Ctx) -> None:
        raise Refusal(f"blinded variant unavailable: {why}")
    return judge


def q3_instruments(sub: Ctx) -> tuple[dict, dict]:
    """(real, blinded) judges, each a callable(ctx) that records the instrument's verdict line. An escape
    of a real judge is counted whether or not its blinded variant exists; a detection is counted only
    when the blinded variant exists and admits the unit."""
    blind_dir = sub.scratch / "q3-blinded"
    kernel_blind, kernel_why = blinded_script(sub, "evidence_tiers", KERNEL_BLIND, blind_dir)
    doe_blind, doe_why = blinded_script(sub, "doe_verify", DOE_BLIND, blind_dir)
    real = {"G1": clause_regenerate, "K1": clause_kernel, "A1v": clause_doe_verifier, "A4": clause_plan_core}
    blinded = {"G1": lambda s: clause_regenerate(s, names_only),
               "K1": (lambda s: clause_kernel(s, str(kernel_blind))) if kernel_blind else blind_unavailable(kernel_why),
               "A1v": (lambda s: clause_doe_verifier(s, str(doe_blind))) if doe_blind else blind_unavailable(doe_why),
               "A4": clause_plan_pairs_only}
    return real, blinded


def delete_order_block(text: str, order_iri: str) -> str:
    """out/plan/orders.ttl without one generated order's block (the order and its acceptance, falsifier,
    court and action nodes, which the template writes as one blank-line-terminated block)."""
    anchor = f"<{order_iri}> a sj:WorkOrder ;"
    if text.count(anchor) != 1:
        raise Refusal(f"plan order block anchor not found exactly once: {anchor[:90]}")
    start = text.index(anchor)
    end = text.index("\n\n", start)
    return text[:start] + text[end + 2:]


def q3_units(bench: Path) -> list[dict]:
    """The committed-output units of Q3 over a bench tree: one distinct corrupted subject each."""
    import rdflib
    SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
    units = []
    for rel, data in sorted(out_files(bench).items()):
        if not data:
            raise Refusal(f"Q3: {rel} is empty; a one-byte corruption is undefined")
        corrupted = bytearray(data)
        pos = len(corrupted) // 2
        corrupted[pos] = (corrupted[pos] + 1) % 256
        units.append({"class": "projection", "subject": f"{rel}@byte{pos}", "rel": rel, "bytes": bytes(corrupted), "judges": ["G1"]})
    for rel in ("generated/evidence-tiers.ttl", "generated/bound-table.ttl"):
        committed = (bench / rel).read_text(encoding="utf-8")
        for m in re.finditer(r'"(\d+\.\d{6})"\^\^', committed):
            lit = m.group(1)
            perturbed = lit[:-1] + str((int(lit[-1]) + 1) % 10)
            text = committed[: m.start(1)] + perturbed + committed[m.end(1):]
            units.append({"class": "kernel", "subject": f"{rel}@{m.start(1)}:{lit}->{perturbed}", "rel": rel,
                          "bytes": text.encode("utf-8"), "judges": ["K1"]})
    matrix_rel = "out/doe/design-matrix.json"
    design = json.loads((bench / matrix_rel).read_text(encoding="utf-8"))
    variants = []
    for r in range(len(design["runs"])):
        d = json.loads(json.dumps(design))
        d["runs"][r]["coded"]["E"] *= -1
        variants.append((f"run {design['runs'][r]['run']} E flipped", d))
    d = json.loads(json.dumps(design))
    for run in d["runs"]:
        run["coded"]["E"] = run["coded"]["A"] * run["coded"]["B"]
    variants.append(("E = AB", d))
    d = json.loads(json.dumps(design))
    d["factors"].append({"column": "G", "factor": "OS", "support": "UNSUPPORTED", "role": "base", "low": "macOS", "high": "linux"})
    for i, run in enumerate(d["runs"]):
        run["coded"]["G"] = 1 if i % 2 else -1
    variants.append(("OS column", d))
    for label, d in variants:
        units.append({"class": "doe", "subject": f"{matrix_rel}: {label}", "rel": matrix_rel,
                      "bytes": (json.dumps(d, indent=1) + "\n").encode("utf-8"), "judges": ["A1v"]})
    plan_rel = "out/plan/orders.ttl"
    text = (bench / plan_rel).read_text(encoding="utf-8")
    plan = rdflib.Graph().parse(data=text, format="turtle")
    subjects = set(plan.subjects())
    for order in sorted(plan.subjects(rdflib.RDF.type, SJ.WorkOrder)):
        mutated = delete_order_block(text, str(order))
        gone = subjects - set(rdflib.Graph().parse(data=mutated, format="turtle").subjects())
        want = {order} | {plan.value(order, p) for p in (SJ.acceptance, SJ.falsifier, SJ.requiresCourt, SJ.nextAction)}
        if gone != want:
            raise Refusal(f"Q3 plan unit {order}: the deletion removed {sorted(map(str, gone))[:3]}, not exactly the order and its 4 nodes")
        units.append({"class": "plan", "subject": f"{plan_rel} without {str(order).rsplit('#', 1)[-1]}", "rel": plan_rel,
                      "bytes": mutated.encode("utf-8"), "judges": ["G1", "A4"]})
    return units


def q3_verdict(sub: Ctx, clause: str, judge) -> tuple[str, str]:
    """Run one judge on the tree as it is on disk; return its (status, detail) for its clause."""
    q = Quiet(f"q3-{clause}")
    sub.v = q
    try:
        judge(sub)
    except Unknown:
        raise
    except Exception as exc:  # a crash is no detection
        return "CRASH", f"{type(exc).__name__}: {exc}"
    mine = [ln for ln in q.lines if ln[1] == clause]
    for prefix in ("REFUSED", "UNKNOWN"):
        hit = [ln for ln in mine if ln[0].startswith(prefix)]
        if hit:
            return hit[0][0], hit[0][2]
    return ("OK", mine[0][2]) if mine else ("SILENT", f"{clause} recorded no verdict")


def q3_run(sub: Ctx, units: list[dict], real: dict, blinded: dict) -> dict:
    """Write each unit's corruption into sub's tree, judge it with the real and the blinded instruments,
    restore the control bytes; tally per class."""
    res: dict = {"classes": {}, "escapes": [], "zero_information": [], "unknown": [], "blind_admits": {}, "judged": {}}
    for u in units:
        path = sub.bench / u["rel"]
        original = path.read_bytes()
        if u["bytes"] == original:
            raise Refusal(f"Q3 unit {u['subject']} equals the control bytes")
        path.write_bytes(u["bytes"])
        sub.cache = {k: v for k, v in sub.cache.items() if k.startswith("mod:")}
        try:
            judged = [(j, q3_verdict(sub, j, real[j]), q3_verdict(sub, j, blinded[j])) for j in u["judges"]]
        finally:
            path.write_bytes(original)
        c = res["classes"].setdefault(u["class"], {"n": 0, "misses": 0, "zero_information": 0, "instruments": list(u["judges"])})
        if any(v[0].startswith("UNKNOWN") for _, r, b in judged for v in (r, b)):
            res["unknown"].append(f"{u['subject']}: {[(j, r[0], b[0]) for j, r, b in judged]}")
            continue
        for j, _, b in judged:
            res["judged"][j] = res["judged"].get(j, 0) + 1
            res["blind_admits"][j] = res["blind_admits"].get(j, 0) + (b[0] == "OK")
        detected = all(r[0] == f"REFUSED[{Q3_EXPECT[j][0]}]" and Q3_EXPECT[j][1] in r[1] for j, r, _ in judged)
        informative = all(b[0] == "OK" for _, _, b in judged)
        if not detected:
            c["n"] += 1
            c["misses"] += 1
            res["escapes"].append(f"{u['subject']}: {[(j, r[0], r[1][:120]) for j, r, _ in judged]}")
        elif informative:
            c["n"] += 1
        else:
            c["zero_information"] += 1
            res["zero_information"].append(f"{u['subject']}: blinded {[(j, b[0]) for j, _, b in judged]}")
    return res


def clause_msa_mutation(ctx: Ctx) -> None:
    report = pack_report(ctx)
    bad_arts = [a for a in report["artifacts"] if not a["good"]]
    n_inst = len(bad_arts[0]["instruments"]) if bad_arts else 0
    # design mutants: one unit per distinct registered mutant, judged by the 5 pack instruments; a miss if any admits
    design_misses = sum(1 for a in bad_arts if any(v["accept"] for v in a["instruments"].values()))
    repo = synthetic_repo(ctx, "q3")
    sub = Ctx(repo, ctx.conjunct, ctx.scratch / "q3-judge", Quiet("q3"))
    sub.env = ctx.env
    units = q3_units(sub.bench)
    ids = [(u["rel"], sha256_bytes(u["bytes"])) for u in units]
    if len(set(ids)) != len(ids):
        ctx.v.refuse("msa_mutation_duplicate", "Q3", f"{len(ids) - len(set(ids))} committed-output units repeat a corrupted subject")
        return
    real, blinded = q3_instruments(sub)
    control = {j: q3_verdict(sub, j, real[j]) for j in sorted({j for u in units for j in u["judges"]})}
    bad_control = {j: v for j, v in control.items() if v[0] != "OK"}
    if bad_control:
        if all(v[0].startswith("UNKNOWN") for v in bad_control.values()):
            ctx.v.unknown("TOOL_MISSING", "Q3", f"an instrument could not judge the control tree: {bad_control}")
        else:
            statuses = {j: v[0] for j, v in bad_control.items()}
            ctx.v.refuse("msa_mutation_control", "Q3", f"the unmutated tree is not admitted (an instrument that refuses everything "
                         f"detects nothing): {statuses} {[v[1][:160] for v in bad_control.values()][:2]}")
        return
    res = q3_run(sub, units, real, blinded)
    dirty = git(repo, "status", "--porcelain", "-uall").strip()
    if dirty:
        ctx.v.refuse("msa_mutation_harness", "Q3", f"the synthetic repository was not restored after the units: {dirty.splitlines()[:3]}")
        return
    if res["unknown"]:
        ctx.v.unknown("TOOL_MISSING", "Q3", f"{len(res['unknown'])} units could not be judged: {res['unknown'][:2]}")
        return
    classes = {"design": {"n": len(bad_arts), "misses": design_misses, "zero_information": 0,
                          "instruments": sorted(bad_arts[0]["instruments"]) if bad_arts else []}}
    classes.update(res["classes"])
    n = sum(c["n"] for c in classes.values())
    misses = sum(c["misses"] for c in classes.values())
    zero = len(res["zero_information"])
    k = {name: classes.get(name, {}).get("n", 0) for name in ("projection", "kernel", "doe", "plan")}
    blind = ", ".join(f"{j} {Q3_BLIND_NAMES[j]} {res['blind_admits'].get(j, 0)}/{res['judged'].get(j, 0)}" for j in sorted(res["judged"]))
    row = msa_row(ctx, "mutation sensitivity", n, misses,
                  "distinct corrupted subject judged on the mutant by the instrument that guards it: design mutants (5 pack instruments; "
                  "a miss if any admits), one-byte out/ corruptions (G1), kernel literal perturbations (K1), DOE corruptions (A1v), "
                  "deleted plan orders (G1 and A4); a committed-output unit counts only as an escape or as a detection that the "
                  "blinded instrument does not reproduce (zero-information units excluded)",
                  {"classes": classes, "zero_information_units": zero, "blinded_admits": {j: [res["blind_admits"].get(j, 0), res["judged"].get(j, 0)] for j in sorted(res["judged"])}})
    if misses:
        ctx.v.refuse("msa_mutation_escape", "Q3", f"{misses}/{n} corrupted subjects escaped the instrument that guards them: {res['escapes'][:3]}")
    else:
        ctx.v.ok("Q3", f"mutation sensitivity: {n}/{n} distinct corrupted subjects refused on the mutant by the instrument that guards each "
                 f"({len(bad_arts)} design mutants by all {n_inst} pack instruments; {k['projection']} one-byte out/ corruptions by G1, "
                 f"{k['kernel']} kernel literal perturbations by K1 evidence_tiers.py --check, {k['doe']} DOE corruptions incl. E=AB and "
                 f"an OS column by A1v doe_verify.py, {k['plan']} deleted plan orders by G1 and A4); every committed-output unit written "
                 f"into a synthetic git repository of HEAD and restored (control tree admitted by {', '.join(sorted(control))}), each "
                 f"witnessed informative by its blinded instrument ({blind}); {zero} zero-information units excluded; 0 escapes "
                 f"(95% upper bound {row['upper_bound_95']}, tier {row['tier']})")


def fresh_receipt(ctx: Ctx, conjunct: str, standing: str = "ALIVE") -> dict:
    return {
        "identity": {"subject": f"CE23-12-{conjunct}" if conjunct != "crown" else "CE23-12", "repo": str(ctx.root),
                     "subject_sha": ctx.head, "bench_tree": ctx.bench_tree, "conjunct": conjunct},
        "standing": {"value": standing},
        "non_llm_operational": {c: {"standing": "UNKNOWN", "n": 0} for c in ctx.cache.get("classes", [])},
        "environment": {"scope": PINS["statement"]["environment_scope"], "os_factor": "UNSUPPORTED",
                        "statement": PINS["statement"]["os_ceiling"]},
    }


def admit_receipt(receipt: dict, conjunct: str, head: str, bench_tree: str, classes: list[str]) -> list[str]:
    """The crown's admission function for one conjunct receipt (pure; tested by Q4 and the crown AV)."""
    errs = []
    ident = receipt.get("identity", {})
    if ident.get("conjunct") != conjunct:
        errs.append(f"wrong_conjunct:{ident.get('conjunct')}")
    if ident.get("subject_sha") != head:
        errs.append("stale_receipt:subject_sha")
    if ident.get("bench_tree") != bench_tree:
        errs.append("stale_receipt:bench_tree")
    if receipt.get("standing", {}).get("value") != "ALIVE":
        errs.append(f"not_alive:{receipt.get('standing', {}).get('value')}")
    ops = receipt.get("non_llm_operational")
    if not isinstance(ops, dict) or sorted(ops) != sorted(classes):
        errs.append("classes_missing")
    else:
        for c, v in ops.items():
            if v.get("standing") != "UNKNOWN" or v.get("n") != 0:
                errs.append(f"operational_claimed:{c}")
    env = receipt.get("environment", {})
    if env.get("os_factor") != "UNSUPPORTED" or PINS["statement"]["os_ceiling"] not in env.get("statement", ""):
        errs.append("os_ceiling_unstated")
    return errs


def clause_msa_stale(ctx: Ctx) -> None:
    classes = ctx.cache.get("classes") or []
    if not classes:
        clause_nonimplication(ctx, "X2")
        classes = ctx.cache.get("classes", [])
    control = fresh_receipt(ctx, "BenchmarkDesign")
    control_errs = admit_receipt(control, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes)
    units = misses = 0
    ancestors = git(ctx.root, "rev-list", "--max-count=31", "HEAD").split()[1:]
    for sha in ancestors:
        r = json.loads(json.dumps(control))
        r["identity"]["subject_sha"] = sha
        try:
            r["identity"]["bench_tree"] = git(ctx.root, "rev-parse", f"{sha}:{PINS['subject']['bench']}").strip()
        except Refusal:
            r["identity"]["bench_tree"] = "absent"
        units += 1
        misses += not admit_receipt(r, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes)
    for i in range(len(ctx.bench_tree)):
        r = json.loads(json.dumps(control))
        t = ctx.bench_tree
        r["identity"]["bench_tree"] = t[:i] + ("0" if t[i] != "0" else "1") + t[i + 1:]
        units += 1
        misses += not admit_receipt(r, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes)
    row = msa_row(ctx, "stale receipt detection", units, misses, "receipt bound to an ancestor subject (30) or a perturbed bench tree digest (40)")
    if control_errs:
        ctx.v.refuse("msa_stale_control", "Q4", f"a fresh receipt of the exact head is refused: {control_errs}")
    elif misses:
        ctx.v.refuse("msa_stale_accept", "Q4", f"{misses}/{units} stale receipts admitted")
    else:
        ctx.v.ok("Q4", f"stale receipt detection: {units}/{units} stale receipts refused ({len(ancestors)} ancestor subjects, {len(ctx.bench_tree)} "
                 f"perturbed bench-tree digests), the fresh exact-head receipt admitted; 0 stale accepts (95% upper bound {row['upper_bound_95']}, tier {row['tier']})")


def clause_msa_ordering(ctx: Ctx) -> None:
    import rdflib
    fast = ("native", "sparql-oxigraph")
    canonical = verdict_vector(ctx, fast)
    triples = list(ctx.union())
    units = changes = 0
    for seed in range(30):
        rng = random.Random(1000 + seed)
        shuffled = list(triples)
        rng.shuffle(shuffled)
        g = rdflib.Graph()
        for t in shuffled:
            g.add(t)
        vec = verdict_vector(ctx, fast, graph_override=g, order_seed=seed)
        units += 1
        changes += vec != canonical
    row = msa_row(ctx, "ordering invariance", units, changes, "seeded permutation of triple insertion order and artifact evaluation order")
    if changes:
        ctx.v.refuse("msa_ordering", "Q5", f"{changes}/{units} permutations changed a verdict")
    else:
        ctx.v.ok("Q5", f"ordering invariance: {units}/{units} seeded permutations (triple order and artifact order) leave every verdict unchanged "
                 f"(95% upper bound {row['upper_bound_95']}, tier {row['tier']})")


ENV_PROBE = r'''
import sys, json, hashlib
sys.dont_write_bytecode = True
sys.path.insert(0, sys.argv[1] + "/pack/scripts")
import verify, rdflib
from pathlib import Path
c = Path(sys.argv[1])
corpus = verify.load_corpus(Path(sys.argv[2]))
base = verify.load_union(c)
inst = verify.Instruments(c, rdflib.Graph().parse(c / "design.ttl", format="turtle"))
out = {}
for art in corpus:
    g = art.apply(base)
    out[art.id] = [[n, *[(a, sorted(l)) for a, l, _ in [f(g)]][0]] for n, f in (("native", inst.native), ("sparql-oxigraph", inst.sparql_oxigraph))]
print(hashlib.sha256(json.dumps(out, sort_keys=True).encode()).hexdigest())
'''


def clause_msa_environment(ctx: Ctx) -> None:
    probe = ctx.scratch / "env_probe.py"
    probe.write_text(ENV_PROBE, encoding="utf-8")
    spaced = ctx.scratch / "tmp dir with spaces"
    spaced.mkdir(exist_ok=True)
    variants = {
        "env -i, fresh HOME, cwd=/": (Path("/"), {}),
        "env -i, fresh HOME, TMPDIR with spaces, cwd=scratch": (ctx.scratch, {"TMPDIR": str(spaced), "HOME": str(ctx.scratch / "home2")}),
        "env -i, PYTHONHASHSEED=1": (ctx.scratch, {"PYTHONHASHSEED": "1"}),
        "env -i, PYTHONHASHSEED=4242, LANG=C": (ctx.scratch, {"PYTHONHASHSEED": "4242", "LANG": "C"}),
    }
    (ctx.scratch / "home2").mkdir(exist_ok=True)
    digests = {}
    for label, (cwd, extra) in variants.items():
        proc = ctx.env.run(["python3", str(probe), str(ctx.bench), str(HERE / "mutations.toml")], cwd, extra=extra)
        digests[label] = proc.stdout.strip() if proc.returncode == 0 else f"exit {proc.returncode}: {proc.stderr[-200:]}"
    # cold vs warm generator state: a fresh copy (no .ggen*, no out/) renders the same bytes as a warm re-render
    cold_dest, cold = fresh_render(ctx, "cold")
    warm = ctx.env.run(["ggen", "sync", "run"], cold_dest, timeout=900)
    warm_state = out_files(cold_dest)
    units = len(digests) + 1
    in_process = hashlib.sha256(json.dumps({k: [[n, a, list(laws)] for n, a, laws in v] for k, v in verdict_vector(ctx, ("native", "sparql-oxigraph")).items()},
                                           sort_keys=True).encode()).hexdigest()
    digests["in-process (the court's own process)"] = in_process
    units += 1
    changes = len(set(digests.values())) - 1
    cold_ok = cold.returncode == 0 and warm.returncode == 0 and warm_state == ctx.cache.get("regen_files", out_files(ctx.bench))
    changes += not cold_ok
    row = msa_row(ctx, "environment / cached-state reproducibility", units, changes, "verdict vector of the corpus in fresh env -i processes (cwd, TMPDIR, HOME, hash seed, locale) + ggen cold vs warm render")
    if changes or any(d.startswith("exit") for d in digests.values()):
        ctx.v.refuse("msa_environment", "Q6", f"verdict digests {digests}; ggen cold/warm identical={cold_ok}")
    else:
        ctx.v.ok("Q6", f"environment reproducibility: {len(digests) - 1} fresh env -i processes (cwd /, TMPDIR with spaces, fresh HOME, hash seeds, LANG=C) "
                 f"and the court's own process give one verdict digest {in_process[:16]}; ggen cold and warm renders "
                 f"byte-identical; 0/{units} changes (95% upper bound {row['upper_bound_95']}, tier {row['tier']}: below N_discovery, stated as such)")


def clause_msa_boundary(ctx: Ctx) -> None:
    import rdflib
    NLB = rdflib.Namespace("https://ggen.dev/nonllm-bench#")
    ES = rdflib.Namespace("https://ggen.dev/ontology/evidence-standing#")
    verify = ctx.mod("verify")
    inst = ctx.cache.get("instruments") or verify.Instruments(ctx.bench, rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle"))
    ctx.cache["instruments"] = inst
    base = ctx.union()
    units = misses = 0
    near = sorted(base.subjects(rdflib.RDF.type, NLB.NearMissCase))
    for m in near:
        klass = base.value(m, NLB.nearClass)
        for kind in ("inClass", "expects-ALIVE"):
            g = rdflib.Graph() + base
            if kind == "inClass":
                g.add((m, NLB.inClass, klass))
            else:
                g.remove((m, NLB.expectedStanding, None))
                g.add((m, NLB.expectedStanding, ES.ALIVE))
            units += 1
            misses += any(fn(g)[0] for fn in (inst.native, inst.sparql_oxigraph))
    for c in sorted(base.subjects(NLB.claimStatus, rdflib.Literal("KNOWN_CANDIDATE"))):
        g = rdflib.Graph() + base
        for mc in list(g.objects(c, NLB.membershipClause)):
            g.remove((c, NLB.membershipClause, mc))
        label = rdflib.URIRef(str(c) + "-declared-label")
        g.add((c, NLB.membershipClause, label))
        g.add((label, NLB.clauseBasis, rdflib.Literal("DECLARED_LABEL")))
        units += 1
        misses += any(fn(g)[0] for fn in (inst.native, inst.sparql_oxigraph))
    row = msa_row(ctx, "membership boundary (near-miss vs KNOWN)", units, misses, "distinct mutated design: every near-miss made a class member or expected ALIVE, every KNOWN class reduced to a declared label (a miss if native or pyoxigraph admits)")
    if misses:
        ctx.v.refuse("msa_boundary", "Q7", f"{misses}/{units} near-miss confusions admitted")
    else:
        ctx.v.ok("Q7", f"membership boundary: {units}/{units} near-miss confusions refused (each of {len(near)} near-misses made a member or "
                 f"expected ALIVE; each KNOWN class reduced to a declared label; native + pyoxigraph); 0 false-KNOWN "
                 f"(95% upper bound {row['upper_bound_95']}, tier {row['tier']})")


# ----------------------------------------------------------------------------------------------------
# Anti-vacuity: synthetic git repositories, one mutation each, expected refusal code


def synthetic_repo(ctx: Ctx, label: str) -> Path:
    repo = ctx.scratch / f"av-{label}" / "repo"
    if repo.parent.exists():
        shutil.rmtree(repo.parent)
    repo.mkdir(parents=True)
    archive = subprocess.run(["git", "-C", str(ctx.root), "archive", "HEAD", "release/v26.9.23/bench", "release/v26.9.23/sjira",
                              "release/v26.9.23/courts"], capture_output=True, check=True).stdout
    subprocess.run(["tar", "-x", "-C", str(repo)], input=archive, check=True)
    for cmd in (["init", "-q"], ["add", "-A"], ["-c", "user.email=court@local", "-c", "user.name=ce23-12-av", "commit", "-q", "-m", "control"]):
        subprocess.run(["git", "-C", str(repo), *cmd], check=True, capture_output=True)
    return repo


def commit_all(repo: Path, msg: str) -> None:
    subprocess.run(["git", "-C", str(repo), "add", "-A"], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.email=court@local", "-c", "user.name=ce23-12-av", "commit", "-q", "-m", msg],
                   check=True, capture_output=True)


class Quiet(Verdicts):
    def ok(self, clause, msg):
        self.lines.append(("OK", clause, msg))

    def refuse(self, code, clause, msg):
        self.lines.append((f"REFUSED[{code}]", clause, msg))

    def unknown(self, code, clause, msg):
        self.lines.append((f"UNKNOWN[{code}]", clause, msg))


def run_on(ctx: Ctx, repo: Path, label: str, clauses) -> Quiet:
    q = Quiet(label)
    sub = Ctx(repo, ctx.conjunct, ctx.scratch / f"av-{label}" / "scratch", q)
    sub.env = ctx.env
    for fn in clauses:
        try:
            fn(sub)
        except Unknown:
            raise
        except Exception as exc:  # a crash is not a refusal: recorded so the AV row fails loudly
            q.lines.append(("CRASH", fn.__name__, f"{type(exc).__name__}: {exc}"))
    return q


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) < 1:
        raise Refusal(f"AV edit anchor absent in {path.name}: {old[:60]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def anti_vacuity(ctx: Ctx, cases: list[tuple[str, callable, list, str]]) -> None:
    """cases: (label, mutate(repo), clauses, expected refusal code or 'ALIVE' for the control)."""
    passed = 0
    for label, mutate, clauses, expected in cases:
        repo = synthetic_repo(ctx, label)
        if mutate is not None:
            mutate(repo)
            if expected != "dirty_subject":
                commit_all(repo, label)
        q = run_on(ctx, repo, label, clauses)
        codes = [ln[0] for ln in q.lines]
        crashed = [ln for ln in q.lines if ln[0] == "CRASH"]
        if expected == "ALIVE":
            good = not crashed and all(c == "OK" for c in codes)
        else:
            good = not crashed and any(c == f"REFUSED[{expected}]" for c in codes)
        if good:
            passed += 1
            got = "ALIVE" if expected == "ALIVE" else f"REFUSED[{expected}]"
            ctx.v.ok(f"AV:{label}", f"{'control' if expected == 'ALIVE' else 'mutant'} in a synthetic git repository -> {got}")
        else:
            ctx.v.refuse("anti_vacuity", "AV", f"{label}: expected {expected}, got {[ln for ln in q.lines if ln[0] != 'OK'][:3] or codes}")
    if passed == len(cases):
        ctx.v.ok("AV", f"anti-vacuity: control ALIVE and {len(cases) - 1} mutants in synthetic git repositories refused with their expected codes")


def mut_design(old: str, new: str):
    def f(repo: Path):
        edit(repo / "release/v26.9.23/bench/design.ttl", old, new)
    return f


def mut_file(rel: str, old: str, new: str):
    def f(repo: Path):
        edit(repo / rel, old, new)
    return f


def mut_append(rel: str, text: str):
    def f(repo: Path):
        with open(repo / rel, "a", encoding="utf-8") as fh:
            fh.write(text)
    return f


def mut_design_render(ctx: Ctx, old: str, new: str):
    """Edit design.ttl, re-render out/ with ggen in the synthetic repo, commit both: the design law
    reaches the projection, and the projection verifier must judge the regenerated matrix."""
    def f(repo: Path):
        bench = repo / "release/v26.9.23/bench"
        edit(bench / "design.ttl", old, new)
        shutil.rmtree(bench / "out")
        proc = ctx.env.run(["ggen", "sync", "run"], bench, timeout=900)
        if proc.returncode != 0:
            raise Refusal(f"AV render failed: {(proc.stdout + proc.stderr)[-300:]}")
        for d in (".ggen", ".ggen-v2"):
            shutil.rmtree(bench / d, ignore_errors=True)
    return f


def mut_dirty(repo: Path):
    (repo / "release/v26.9.23/bench/untracked.txt").write_text("not committed\n", encoding="utf-8")


def pack_quick(ctx: Ctx) -> None:
    """D1 on the artifact G0 only (the AV variant: the committed design under 4 instruments)."""
    verify = ctx.mod("verify")
    corpus = [a for a in verify.load_corpus(HERE / "mutations.toml") if a.id == "G0"]
    try:
        report = verify.judge(ctx.bench, corpus, False, {"G0"})
    except ValueError as exc:
        ctx.v.refuse("pack_qualification", "D1q", str(exc))
        return
    fails = verify.expectations(report)
    if fails:
        ctx.v.refuse("pack_qualification", "D1q", fails[0])
    else:
        ctx.v.ok("D1q", "the committed design admitted by 4 instruments")


# ----------------------------------------------------------------------------------------------------
# Conjunct courts


def court_bd(ctx: Ctx, av: bool) -> None:
    clause_capital(ctx)
    clause_prose(ctx)
    clause_prose_spans(ctx)
    clause_generated_inputs(ctx)
    if clause_ggen_version(ctx):
        clause_regenerate(ctx)
    clause_headers(ctx)
    clause_trace(ctx, "BenchmarkDesign", "T1")
    clause_asks(ctx, ["BD-D2", "BD-D3", "BD-D4", "BD-D5", "BD-D6", "BD-M1", "BD-M2", "BD-A3", "BD-X1"], "D2")
    clause_pack(ctx)
    clause_nonimplication(ctx, "X2")
    if av:
        rel = "release/v26.9.23/bench"
        cases = [
            ("control", None, [clause_subject, clause_prose, clause_prose_spans, clause_generated_inputs, clause_regenerate, pack_quick], "ALIVE"),
            ("dirty", mut_dirty, [clause_subject], "dirty_subject"),
            ("prose-byte", mut_file("release/v26.9.23/sjira/chatman-ce23-12-bench.md", "The existing no-LLM episode is necessary", "The existing no-LLM episode is necessary!"),
             [clause_prose_spans], "prose_span"),
            ("untraced-ctq", mut_file(f"{rel}/design.ttl", "  prov:wasDerivedFrom ce:P-631296cc71d3da82 .\n\n# -- Measurement model", "  .\n\n# -- Measurement model"),
             [pack_quick], "pack_qualification"),
            ("label-only-membership", mut_design("nlb:membershipClause ce23:mc-gg-1 , ce23:mc-gg-2 , ce23:mc-gg-3 , ce23:mc-gg-4 ;",
                                                 "nlb:membershipClause ce23:mc-gg-2 , ce23:mc-gg-3 , ce23:mc-gg-4 ;"), [pack_quick], "pack_qualification"),
            ("hand-edited-projection", mut_append(f"{rel}/out/CLASSES.md", "\nhand edit\n"), [clause_regenerate], "projection_drift"),
            ("import-drift", mut_append(f"{rel}/imports/goal.ttl", "\n# drift\n"), [clause_generated_inputs], "import_drift"),
            ("trace-foreign", mut_design("ce23:gap-cargo-lock-gate a nlb:CapabilityGap ;", "ce23:gap-cargo-lock-gate prov:wasDerivedFrom ce:P-0000000000000000 .\nce23:gap-cargo-lock-gate a nlb:CapabilityGap ;"),
             [clause_trace_bd], "trace_to_uncommitted_proposition"),
        ]
        anti_vacuity(ctx, cases)


def clause_trace_bd(ctx: Ctx) -> None:
    clause_trace(ctx, "BenchmarkDesign", "T1")


def court_msa(ctx: Ctx, av: bool) -> None:
    clause_prose(ctx)
    clause_generated_inputs(ctx)
    if clause_ggen_version(ctx):
        clause_regenerate(ctx)
    clause_trace(ctx, "MSAContract", "T1")
    clause_asks(ctx, ["BD-M2"], "C0")
    clause_msa_contract(ctx)
    clause_nonimplication(ctx, "X2")
    t0 = time.monotonic()
    clause_msa_repeatability(ctx)
    clause_msa_agreement(ctx)
    clause_msa_mutation(ctx)
    clause_msa_stale(ctx)
    clause_msa_ordering(ctx)
    clause_msa_environment(ctx)
    clause_msa_boundary(ctx)
    ctx.cache["msa_seconds"] = round(time.monotonic() - t0, 1)
    if av:
        cases = [
            ("control", None, [clause_subject, clause_msa_contract_only], "ALIVE"),
            ("msa-court-deleted", mut_design("ce23:M2 a nlb:MSACourt ;", "ce23:M2-deleted a nlb:Unrelated ;"), [clause_msa_contract_only], "msa_property_uncovered"),
            ("msa-property-untraced", mut_design("ce23:msa-stale a nlb:MSAProperty ; rdfs:label \"stale receipt detection\" ; prov:wasDerivedFrom ce:P-18db2cd10b35adae .",
                                                 "ce23:msa-stale a nlb:MSAProperty ; rdfs:label \"stale receipt detection\" ; prov:wasDerivedFrom ce:P-22dff21d49b9f5a6 ."),
             [clause_msa_contract_only], "msa_question_unmapped"),
            ("msa-alive-claimed", mut_design('nlb:statusToday "HOLDS_OBSERVED_DOMAIN" ;\n  nlb:evidenceNote "0/250', 'nlb:statusToday "ALIVE" ;\n  nlb:evidenceNote "0/250'),
             [clause_msa_contract_only], "msa_status_claimed"),
        ]
        anti_vacuity(ctx, cases)
        # the stale-receipt instrument itself: a receipt of HEAD~1 must be refused, the head's admitted
        classes = ctx.cache.get("classes", [])
        fresh = fresh_receipt(ctx, "MSAContract")
        stale = json.loads(json.dumps(fresh))
        stale["identity"]["subject_sha"] = git(ctx.root, "rev-parse", "HEAD~1").strip()
        if admit_receipt(fresh, "MSAContract", ctx.head, ctx.bench_tree, classes) or not admit_receipt(stale, "MSAContract", ctx.head, ctx.bench_tree, classes):
            ctx.v.refuse("anti_vacuity", "AV", "the receipt admission function does not separate the fresh receipt from HEAD~1's")
        else:
            ctx.v.ok("AV", "receipt admission separates the exact-head receipt (admitted) from HEAD~1's (REFUSED stale_receipt)")


def clause_msa_contract_only(ctx: Ctx) -> None:
    clause_msa_contract(ctx)


def court_gqp(ctx: Ctx, av: bool) -> None:
    clause_prose(ctx)
    clause_generated_inputs(ctx)
    if clause_ggen_version(ctx):
        clause_regenerate(ctx)
    clause_headers(ctx)
    clause_trace(ctx, "GeneratedQualificationPlan", "T1")
    clause_doe(ctx)
    clause_statistics(ctx)
    clause_plan(ctx)
    clause_compile_prose(ctx)
    clause_os_statement(ctx)
    clause_nonimplication(ctx, "X2")
    if av:
        rel = "release/v26.9.23/bench"
        cases = [
            ("control", None, [clause_subject, clause_generated_inputs, clause_regenerate, clause_doe, clause_plan_core], "ALIVE"),
            ("os-column", mut_design('ce23:factor-os a nlb:Factor ; rdfs:label "OS" ; nlb:support "UNSUPPORTED" ;',
                                     'ce23:factor-os a nlb:Factor ; rdfs:label "OS" ; nlb:support "UNSUPPORTED" ; nlb:column "G" ;'),
             [clause_regenerate], "ggen_gate_refused"),
            ("matrix-cell-flipped", mut_file(f"{rel}/out/doe/design-matrix.json", '"E": 1, "F": -1}},\n  {"run": 3', '"E": -1, "F": -1}},\n  {"run": 3'),
             [clause_doe], "doe_refused"),
            ("toolchain-E-AB", mut_design_render(ctx, "nlb:generatedBy ce23:factor-cold , ce23:factor-concurrency , ce23:factor-path ;",
                                                 "nlb:generatedBy ce23:factor-cold , ce23:factor-concurrency ;"), [clause_doe], "doe_refused"),
            ("b5-order-deleted", delete_plan_order("CE23-12-Q-ELIXIR-FORMAT-B5"), [clause_regenerate], "projection_drift"),
            ("handwritten-order", mut_append(f"{rel}/design.ttl", "\nce23:hand-order a sj:WorkOrder .\n"), [clause_plan_core], "handwritten_work_order"),
            ("tier-tampered", mut_file(f"{rel}/generated/evidence-tiers.ttl", '"0.095034"', '"0.050000"'), [clause_generated_inputs], "kernel_drift"),
            ("gap-dropped", mut_design("ce23:gap-os-factor a nlb:CapabilityGap ;", "ce23:gap-os-factor a nlb:RetiredGap ;"), [clause_plan_core], "plan_incomplete"),
        ]
        anti_vacuity(ctx, cases)


def clause_plan_core(ctx: Ctx) -> None:
    # A4 without the pinned semantic-jira shapes (the AV corpus judges the generated plan's coverage law)
    import rdflib
    SJ = rdflib.Namespace("https://ggen-igniter.dev/ontology/semantic-jira#")
    design = rdflib.Graph().parse(ctx.bench / "design.ttl", format="turtle")
    if list(design.subjects(rdflib.RDF.type, SJ.WorkOrder)):
        ctx.v.refuse("handwritten_work_order", "A4", "design.ttl holds a hand-written work order")
        return
    saved = os.environ.get("GGEN_IGNITER_DIR")
    os.environ["GGEN_IGNITER_DIR"] = str(ctx.scratch / "no-ggen-igniter")
    try:
        before = len(ctx.v.lines)
        clause_plan(ctx)
        ctx.v.lines = [ln for i, ln in enumerate(ctx.v.lines) if i < before or ln[1] != "A4s"]
    finally:
        if saved is None:
            os.environ.pop("GGEN_IGNITER_DIR", None)
        else:
            os.environ["GGEN_IGNITER_DIR"] = saved


def delete_plan_order(order_id: str):
    def f(repo: Path):
        path = repo / "release/v26.9.23/bench/out/plan/orders.ttl"
        path.write_text(delete_order_block(path.read_text(encoding="utf-8"), f"https://chatman.dev/release/v26.9.23#{order_id}"), encoding="utf-8")
    return f


# ----------------------------------------------------------------------------------------------------
# Crown


def run_conjunct(ctx: Ctx, key: str) -> tuple[int, dict | None, str]:
    out = ctx.scratch / f"receipt-{key}.json"
    proc = subprocess.run(["sh", str(ctx.root / WRAPPERS[key]), "--receipt-out", str(out)], cwd=str(ctx.root),
                          capture_output=True, text=True, timeout=1500, env={"HOME": os.environ.get("HOME", ""), "PATH": os.environ.get("PATH", ""),
                                                                            "LANG": "en_US.UTF-8", **{k: v for k, v in os.environ.items() if k in ("XAAS_DIR", "GGEN_IGNITER_DIR")}})
    receipt = json.loads(out.read_text(encoding="utf-8")) if out.is_file() else None
    return proc.returncode, receipt, proc.stdout


def court_crown(ctx: Ctx, av: bool) -> None:
    clause_prose(ctx)
    clause_trace(ctx, "crown", "T1")
    clause_nonimplication(ctx, "X2")
    classes = ctx.cache.get("classes", [])
    receipts = {}
    for key, name in CONJUNCTS.items():
        t0 = time.monotonic()
        code, receipt, stdout = run_conjunct(ctx, key)
        secs = round(time.monotonic() - t0, 1)
        counts = {s: sum(1 for ln in stdout.splitlines() if ln.startswith(s)) for s in ("OK ", "REFUSED", "UNKNOWN")}
        if code != 0 or receipt is None:
            code_name = "conjunct_unknown" if code == 75 else "conjunct_refused"
            ctx.v.refuse(code_name, f"C-{name}", f"{WRAPPERS[key]} exit {code} ({counts}); "
                         f"{[ln for ln in stdout.splitlines() if not ln.startswith('OK ')][:3]}")
            continue
        errs = admit_receipt(receipt, name, ctx.head, ctx.bench_tree, classes)
        if errs:
            ctx.v.refuse("conjunct_receipt", f"C-{name}", f"receipt refused: {errs}")
            continue
        receipts[name] = receipt
        ctx.v.ok(f"C-{name}", f"{WRAPPERS[key]} exit 0 in {secs}s ({counts['OK ']} OK, 0 REFUSED, 0 UNKNOWN); its receipt is ALIVE at the exact head "
                 f"{ctx.head[:12]} / bench tree {ctx.bench_tree[:12]} and records non_llm_operational UNKNOWN (n = 0) for all {len(classes)} classes")
    ctx.cache["conjunct_receipts"] = receipts
    if av:
        fresh = fresh_receipt(ctx, "BenchmarkDesign")
        variants = {
            "stale-subject": ("identity", "subject_sha", git(ctx.root, "rev-parse", "HEAD~1").strip(), "stale_receipt:subject_sha"),
            "stale-tree": ("identity", "bench_tree", "0" * 40, "stale_receipt:bench_tree"),
            "wrong-conjunct": ("identity", "conjunct", "MSAContract", "wrong_conjunct:MSAContract"),
            "refused": ("standing", "value", "REFUSED(pack_qualification)", "not_alive:REFUSED(pack_qualification)"),
        }
        bad = []
        if admit_receipt(fresh, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes):
            bad.append("control refused")
        for label, (section, field, value, code) in variants.items():
            r = json.loads(json.dumps(fresh))
            r[section][field] = value
            if code not in admit_receipt(r, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes):
                bad.append(label)
        r = json.loads(json.dumps(fresh))
        if classes:
            r["non_llm_operational"][classes[0]] = {"standing": "NON_LLM_OPERATIONAL_ALIVE", "n": 30}
            if f"operational_claimed:{classes[0]}" not in admit_receipt(r, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes):
                bad.append("operational-claimed")
            r = json.loads(json.dumps(fresh))
            r["non_llm_operational"].pop(classes[-1])
            if "classes_missing" not in admit_receipt(r, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes):
                bad.append("class-missing")
        r = json.loads(json.dumps(fresh))
        r["environment"]["os_factor"] = "VARIED"
        if "os_ceiling_unstated" not in admit_receipt(r, "BenchmarkDesign", ctx.head, ctx.bench_tree, classes):
            bad.append("os-varied")
        if bad:
            ctx.v.refuse("anti_vacuity", "AV", f"receipt admission admitted: {bad}")
        else:
            ctx.v.ok("AV", "crown receipt admission: the exact-head receipt admitted; stale subject, stale bench tree, wrong conjunct, REFUSED "
                     "standing, a class claimed NON_LLM_OPERATIONAL_ALIVE, a missing class and a varied OS factor each refused")


# ----------------------------------------------------------------------------------------------------
# Receipt


def write_receipt(ctx: Ctx, key: str, code: int, path: Path, started: float) -> None:
    name = CONJUNCTS.get(key, "crown")
    standing = "ALIVE" if code == 0 else ("UNKNOWN" if code == 75 else "REFUSED(" + (ctx.v.refused()[0][0][8:-1] if ctx.v.refused() else "court") + ")")
    receipt = fresh_receipt(ctx, name, standing)
    try:
        base = git(ctx.root, "rev-parse", "HEAD~1").strip()
    except Refusal:
        base = ctx.head
    listing = git(ctx.root, "ls-tree", "-r", f"HEAD:{PINS['subject']['bench']}")
    receipt["identity"].update({
        "repo": str(ctx.root), "repository": PINS["subject"]["repository"], "base_sha": base,
        "graph_hash": "sha256:" + sha256_bytes(listing.encode()),
        "gate": f"ce:CE23-12{'' if key == 'crown' else '-' + name} (release/v26.9.23/sjira/goal.ttl), sj:courtCommand 'sh {WRAPPERS[key]}'",
        "prose": dict(PINS["prose"]),
        "pack": "nonllm-class-qualification-pack 0.1.0 (in-repo, release/v26.9.23/bench/pack; successor home ggen-marketplace)",
        "pack_lock": (ctx.bench / "ggen.lock").read_text(encoding="utf-8").strip().splitlines()[-1] if (ctx.bench / "ggen.lock").is_file() else "",
    })
    receipt["authority"] = {"ceiling": "OBSERVE", "grant": "NONE (a court observes; it actuates nothing)", "actor": f"release/v26.9.23/courts/ce23_12/court.py {key}"}
    receipt["consequence"] = {"commits": [], "files_changed": [], "remote_effects": []}
    receipt["replay"] = {"commands": [{"cmd": f"sh {WRAPPERS[key]}", "cwd": str(ctx.root), "exit": code,
                                       "summary": f"{sum(1 for ln in ctx.v.lines if ln[0] == 'OK')} OK, {len(ctx.v.refused())} REFUSED, {len(ctx.v.unknowns())} UNKNOWN in {round(time.monotonic() - started, 1)}s"}]}
    kind = ("BENCHMARK_DESIGN_ALIVE" if key == "crown" else f"CE23-12-{name} (conjunct of BENCHMARK_DESIGN_ALIVE)") if code == 0 else "UNKNOWN"
    receipt["standing"] = {"value": standing, "standing_kind": kind,
                           "derived_from": f"sh {WRAPPERS[key]} exit {code} at {ctx.head}"}
    if code not in (0, 75):
        receipt["standing"]["broken_term"] = "admission_vacuous"
    receipt["clauses"] = [{"status": s, "clause": c, "detail": m} for s, c, m in ctx.v.lines]
    if ctx.cache.get("msa_rows"):
        receipt["msa"] = ctx.cache["msa_rows"]
    elif key == "crown" and "MSAContract" in ctx.cache.get("conjunct_receipts", {}):
        receipt["msa"] = ctx.cache["conjunct_receipts"]["MSAContract"].get("msa", [])
    if key == "crown":
        receipt["conjuncts"] = {n: {"subject_sha": r["identity"]["subject_sha"], "bench_tree": r["identity"]["bench_tree"],
                                    "standing": r["standing"]["value"], "replay": r["replay"]["commands"][0]["summary"]}
                                for n, r in ctx.cache.get("conjunct_receipts", {}).items()}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(receipt, indent=1, sort_keys=True) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("conjunct", choices=["bd", "msa", "gqp", "crown"])
    parser.add_argument("--root", type=Path, default=HERE.parents[3])
    parser.add_argument("--receipt-out", type=Path)
    parser.add_argument("--no-av", action="store_true")
    args = parser.parse_args()
    started = time.monotonic()
    label = CONJUNCTS.get(args.conjunct, "CE23-12")
    verdicts = Verdicts(label)
    # The court's scratch lives under CE23_12_TMP when set, else the system /tmp (not the caller's
    # TMPDIR: a session TMPDIR can be removed by another process mid-run; a vanished scratch is typed
    # UNKNOWN[SCRATCH_LOST], never mistaken for a missing tool).
    base = os.environ.get("CE23_12_TMP") or "/tmp"
    Path(base).mkdir(parents=True, exist_ok=True)
    scratch = Path(tempfile.mkdtemp(prefix=f"ce23-12-{args.conjunct}-", dir=base))
    try:
        ctx = Ctx(args.root.resolve(), args.conjunct, scratch, verdicts)
        if clause_tools(ctx) and clause_subject(ctx):
            try:
                {"bd": court_bd, "msa": court_msa, "gqp": court_gqp, "crown": court_crown}[args.conjunct](ctx, not args.no_av)
            except Refusal as exc:
                verdicts.refuse("court_error", "E1", str(exc))
            except Unknown as exc:
                verdicts.unknown("SCRATCH_LOST", "E1", str(exc))
            except SystemExit as exc:
                # a pack instrument's typed exit (e.g. UNKNOWN[TOOL_MISSING]) is an environmental absence
                verdicts.unknown("INSTRUMENT_EXIT", "E1", str(exc.code))
        code = verdicts.exit_code()
        if args.receipt_out:
            write_receipt(ctx, args.conjunct, code, args.receipt_out, started)
        name = "CE23-12" if args.conjunct == "crown" else f"CE23-12-{label}"
        summary = {0: "ALIVE", 1: "REFUSED", 75: "UNKNOWN"}[code]
        if code != 0:
            extra = ""
        elif args.conjunct == "crown":
            extra = " standing BENCHMARK_DESIGN_ALIVE; NON_LLM_OPERATIONAL_ALIVE UNKNOWN for every class (n = 0)"
        else:
            extra = " conjunct of BENCHMARK_DESIGN_ALIVE; NON_LLM_OPERATIONAL_ALIVE UNKNOWN for every class (n = 0)"
        print(f"{name} {summary}: {sum(1 for ln in verdicts.lines if ln[0] == 'OK')} OK, {len(verdicts.refused())} REFUSED, "
              f"{len(verdicts.unknowns())} UNKNOWN in {round(time.monotonic() - started, 1)}s;{extra}")
        return code
    finally:
        shutil.rmtree(scratch, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
