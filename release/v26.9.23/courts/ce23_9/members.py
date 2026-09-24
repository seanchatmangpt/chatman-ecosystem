#!/usr/bin/env python3
"""CE23-9 root court members (release/v26.9.23/sjira/goal.ttl ce:CE23-9, chatman-ce23.md CE23-9).

Each member is one er:Gate of release/v26.9.23/release.ttl; the vendored chatman-ecosystem-release-pack
renders them, in er:gateOrder, into release/v26.9.23/out/scripts/crown_v26_9_23.sh, which runs each
er:command from the chatman-ecosystem root (er:courtRoot "../.."). A member judges the exact committed
head of the checkout it runs in and ends with exactly one verdict line:

  MEMBER_ALIVE <member> ...                exit 0
  MEMBER_REFUSED[<code>,...] <member> ...  exit 1   (a counterexample on the subject)
  MEMBER_UNKNOWN[<code>,...] <member> ...  exit 75  (an edge the subject cannot close: an absent tool,
                                                     an unpublished head, the operator's GC23-12
                                                     acceptance; nothing refused)

  members.py subject-clean       the checkout is exactly HEAD (no tracked, staged or untracked change)
                                 and HEAD descends from the release base
  members.py projection-drift    generated-projection drift: a cold `ggen sync run` of the committed
                                 release subject and of its bench sub-project reproduces the committed
                                 out/ (+ ggen.lock) byte for byte and a second sync writes nothing;
                                 `ecosystem projection check` admits views/generated
  members.py manifest-refs       manifest/ref validation: verify_release --release v26.9.23 --check-refs
  members.py imported-receipts   every receipt of the release (receipts/v26.9.23/**/*.json in the R shape)
                                 is valid under the vendored generated validator (dfcm_fleet_v1) and its
                                 subject is a commit of this history at or before HEAD; imported crown
                                 receipts (none until CE23-3) are reported
  members.py ci-dispositions     every CI check the exact head carries (ci_checks.py universe) has exactly
                                 one disposition: a local member (er:Gate ce9:reproducesCheck), a typed
                                 er:CheckDisposition, or its check-run at the exact head; no stale row
  members.py replay              renders replay byte-identically from a second cold location, and every
                                 CE23 gate with an ALIVE receipt replays its court at HEAD with exit 0
  members.py exact-head-ci       the GitHub check-runs of HEAD: every non-success check is typed, every
                                 local member also passed in CI (UNKNOWN until HEAD is published and CI ran)
  members.py chatman-stop        CHATMAN_STOP: the courts of every crown gate without a replayed receipt
                                 exit 0 and the imported Semantic Manufacturing crown is STOP=true
                                 (UNKNOWN on the operator's GC23-12 acceptance edge while STOP=false)

Options: --root DIR (default: the git top level of the working directory). No member writes to the
checkout: scratch lives under $CE23_9_SCRATCH or a fresh temporary directory. No LLM on any path.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import ci_checks  # noqa: E402

PINS = tomllib.loads((HERE / "root.toml").read_text(encoding="utf-8"))
SUBJ = PINS["subject"]
SDIR = SUBJ["subject_dir"]
ER = "http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#"
CE9 = "https://github.com/seanchatmangpt/chatman-ecosystem/release/v26.9.23/court#"
SJ = "https://ggen-igniter.dev/ontology/semantic-jira#"
DCT = "http://purl.org/dc/terms/"
SHA40 = re.compile(r"^[0-9a-f]{40}$")
R_KEYS = {"identity", "authority", "consequence", "replay", "standing"}
EXIT = {"ALIVE": 0, "REFUSED": 1, "UNKNOWN": 75}


class Verdict:
    def __init__(self, member: str):
        self.member, self.refused, self.unknown = member, [], []

    def line(self, text: str) -> None:
        print(f"  {text}", flush=True)

    def refuse(self, code: str, text: str) -> None:
        self.refused.append(code)
        print(f"  REFUSED[{code}] {text}", flush=True)

    def unk(self, code: str, text: str) -> None:
        self.unknown.append(code)
        print(f"  UNKNOWN[{code}] {text}", flush=True)

    def close(self, summary: str) -> int:
        if self.refused:
            kind, codes = "REFUSED", self.refused
        elif self.unknown:
            kind, codes = "UNKNOWN", self.unknown
        else:
            kind, codes = "ALIVE", []
        tag = f"[{','.join(dict.fromkeys(codes))}]" if codes else ""
        print(f"MEMBER_{kind}{tag} {self.member} {summary}", flush=True)
        return EXIT[kind]


def run(argv: list[str], cwd: Path, timeout: int = 1200, env: dict | None = None) -> subprocess.CompletedProcess:
    e = dict(os.environ if env is None else env)
    e["PYTHONDONTWRITEBYTECODE"] = "1"
    try:
        return subprocess.run(argv, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=e)
    except subprocess.TimeoutExpired as exc:
        return subprocess.CompletedProcess(argv, 124, exc.stdout or "", f"timeout after {timeout}s")


def git(root: Path, *args: str) -> str:
    p = run(["git", "-C", str(root), *args], root)
    return p.stdout.strip() if p.returncode == 0 else ""


def scratch_dir(tag: str) -> Path:
    base = os.environ.get("CE23_9_SCRATCH")
    if base:
        Path(base).mkdir(parents=True, exist_ok=True)
    return Path(tempfile.mkdtemp(prefix=f"ce23-9-{tag}.", dir=base or None))


def archive(root: Path, rev: str, path: str, dest: Path) -> bool:
    arch = subprocess.run(["git", "-C", str(root), "archive", rev, path], capture_output=True)
    if arch.returncode != 0:
        return False
    return subprocess.run(["tar", "-x", "-C", str(dest)], input=arch.stdout).returncode == 0


def fm_codes(p: subprocess.CompletedProcess) -> list[str]:
    return sorted(set(re.findall(r"FM-[A-Z]+-\d+", p.stdout + p.stderr)))


def release_graph(root: Path):
    import rdflib  # noqa: PLC0415 (typed UNKNOWN by the caller when absent)
    return rdflib.Graph().parse(root / SDIR / SUBJ["release_graph"], format="turtle")


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ----------------------------------------------------------------------------------------------------
# subject-clean


def m_subject_clean(root: Path, v: Verdict) -> int:
    head = git(root, "rev-parse", "HEAD")
    status = git(root, "status", "--porcelain", "--untracked-files=all")
    if not SHA40.match(head):
        v.refuse("NO_HEAD", f"{root} has no commit")
    elif status:
        v.refuse("SUBJECT_DIRTY", f"the checkout differs from HEAD {head[:12]}: {status.splitlines()[:6]}")
    base = SUBJ["base_commit"]
    if run(["git", "-C", str(root), "merge-base", "--is-ancestor", base, "HEAD"], root).returncode != 0:
        v.refuse("BASE_NOT_ANCESTOR", f"HEAD does not descend from the release base {base[:12]}")
    return v.close(f"head={head} base={base[:12]} clean={not status}")


# ----------------------------------------------------------------------------------------------------
# projection-drift (and the render half of replay)


GGEN_SURFACES = {SDIR: ("out", True), f"{SDIR}/bench": ("out", True)}


def committed_render(root: Path, surface: str, out: str, locked: bool) -> dict[str, bytes]:
    files = git(root, "ls-tree", "-r", "--name-only", "HEAD", f"{surface}/{out}/").splitlines()
    if locked:
        files.append(f"{surface}/ggen.lock")
    return {f[len(surface) + 1:]: subprocess.run(["git", "-C", str(root), "show", f"HEAD:{f}"], capture_output=True).stdout
            for f in files if f}


def cold_render(root: Path, surface: str, out: str, locked: bool, tag: str) -> tuple[dict[str, bytes] | None, str]:
    s = scratch_dir(tag)
    if not archive(root, "HEAD", SDIR, s):
        return None, f"git archive HEAD {SDIR} failed"
    sub = s / surface
    for d in (out, ".ggen", ".ggen-v2"):
        shutil.rmtree(sub / d, ignore_errors=True)
    if locked:
        (sub / "ggen.lock").unlink(missing_ok=True)
    first = run(["ggen", "sync", "run"], sub, timeout=900)
    if first.returncode != 0:
        return None, f"ggen sync run exit {first.returncode} {fm_codes(first)}"

    def collect() -> dict[str, bytes]:
        got = {str(p.relative_to(sub)): p.read_bytes() for p in (sub / out).rglob("*") if p.is_file()}
        if locked:
            got["ggen.lock"] = (sub / "ggen.lock").read_bytes()
        return got

    rendered = collect()
    second = run(["ggen", "sync", "run"], sub, timeout=900)
    if second.returncode != 0 or collect() != rendered:
        return None, f"second sync exit {second.returncode} {fm_codes(second)} or changed the render (not idempotent)"
    shutil.rmtree(s, ignore_errors=True)
    return rendered, "ok"


def m_projection_drift(root: Path, v: Verdict) -> int:
    if shutil.which("ggen") is None:
        v.unk("TOOL_MISSING", "ggen is not on PATH")
        return v.close("no render")
    total = 0
    for surface, (out, locked) in GGEN_SURFACES.items():
        committed = committed_render(root, surface, out, locked)
        fresh, why = cold_render(root, surface, out, locked, "render")
        if fresh is None:
            v.refuse("GENERATION_REFUSED", f"{surface}: {why}")
            continue
        if set(fresh) != set(committed):
            v.refuse("PROJECTION_SET_DRIFT", f"{surface}: fresh {sorted(set(fresh) - set(committed))[:5]} "
                                             f"committed-only {sorted(set(committed) - set(fresh))[:5]}")
            continue
        drift = sorted(k for k in fresh if fresh[k] != committed[k])
        if drift:
            v.refuse("PROJECTION_DRIFT", f"{surface}: committed bytes differ from a fresh render: {drift[:6]}")
            continue
        total += len(fresh)
        v.line(f"OK {surface}: {len(fresh)} generated files reproduce byte for byte (cold sync; second sync idempotent)")
    views = run(["cargo", "run", "--locked", "--quiet", "-p", "ecosystem-cli", "--bin", "ecosystem", "--", "projection", "check"], root)
    if shutil.which("cargo") is None:
        v.unk("TOOL_MISSING", "cargo is not on PATH (views/generated not judged)")
    elif views.returncode != 0 or "PROJECTION_ALIVE" not in views.stdout:
        v.refuse("VIEWS_PROJECTION_DRIFT", f"ecosystem projection check exit {views.returncode}: {(views.stdout + views.stderr).strip()[-300:]}")
    else:
        v.line(f"OK views/generated: {views.stdout.strip()}")
    v.line("TYPED root ggen.toml (soc2-readiness-pack by the absolute path /Users/sac/ggen-marketplace/..., no "
           "templates/ dir): not a hermetic generator surface; `ggen sync run` refuses FM-CONFIG-004 already at "
           "base c59596f5 and no CI check runs it; SUCCESSOR (GC-26.9.24: vendor the pack by relative path)")
    return v.close(f"{total} release-subject projections + views/generated")


# ----------------------------------------------------------------------------------------------------
# manifest-refs


def m_manifest_refs(root: Path, v: Verdict) -> int:
    p = run([sys.executable, "scripts/verify_release.py", "--release", "v26.9.23", "--check-refs"], root)
    try:
        report = json.loads(p.stdout)
    except json.JSONDecodeError:
        report = {}
    findings = report.get("findings") or []
    limited = [f for f in findings if f.get("code") == "ECOSYSTEM_REF_CHECK_BLOCKED" and "rate limit" in str(f.get("detail", ""))]
    if not report:
        v.refuse("MANIFEST_REFUSED", f"verify_release exit {p.returncode}: {(p.stdout + p.stderr).strip()[-400:]}")
    else:
        if limited:
            v.unk("GITHUB_RATE_LIMITED", f"{len(limited)} ref observations refused by GitHub's API rate limit "
                                         f"({sorted({f.get('subject') for f in limited})}): an infrastructure edge, not a "
                                         f"finding on the manifest; export GITHUB_TOKEN or GH_TOKEN, or rerun after the reset")
        if len(findings) > len(limited) or (p.returncode != 0 and not limited):
            v.refuse("MANIFEST_FINDINGS", f"verify_release exit {p.returncode}: {[f for f in findings if f not in limited][:5]}")
        if report.get("release") != "26.9.23" or report.get("refs_checked") is not True:
            v.refuse("MANIFEST_UNBOUND", f"release={report.get('release')} refs_checked={report.get('refs_checked')}")
        v.line(f"verify_release --release v26.9.23 --check-refs: components={report.get('component_count')} "
               f"refs={report.get('ref_coverage')} manifest_sha256={report.get('manifest_sha256')} "
               f"standing={report.get('standing')} (standing ALIVE is judged by chatman-stop, not here)")
    return v.close(f"exit={p.returncode}")


# ----------------------------------------------------------------------------------------------------
# imported-receipts


def validator_identity(root: Path, v: Verdict) -> Path | None:
    prov = tomllib.loads((HERE / "unified_receipt_validator.provenance.toml").read_text(encoding="utf-8"))["validator"]
    local = HERE / "unified_receipt_validator.py"
    got = sha256(local.read_bytes())
    committed = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{local.relative_to(root)}"], capture_output=True).stdout
    if got != prov["sha256"] or sha256(committed) != prov["sha256"]:
        v.refuse("VALIDATOR_DRIFT", f"{local.name} sha256 {got} (committed {sha256(committed)}) != provenance {prov['sha256']}")
        return None
    market = Path(os.environ.get("CE23_MARKETPLACE_REPO") or (Path.home() / "ggen-marketplace")).expanduser()
    blob = subprocess.run(["git", "-C", str(market), "show", f"{prov['commit']}:{prov['path']}"], capture_output=True)
    if blob.returncode != 0:
        v.unk("MARKETPLACE_UNAVAILABLE", f"{market} holds no {prov['commit'][:12]}:{prov['path']}")
    elif sha256(blob.stdout) != prov["sha256"]:
        v.refuse("VALIDATOR_NOT_BYTE_IDENTICAL", f"marketplace {prov['commit'][:12]}:{prov['path']} sha256 {sha256(blob.stdout)}")
    elif run(["git", "-C", str(market), "merge-base", "--is-ancestor", prov["commit"], f"refs/remotes/origin/{prov['ref']}"], market).returncode != 0:
        v.refuse("VALIDATOR_UNPUBLISHED", f"{prov['commit'][:12]} is not on origin/{prov['ref']}")
    else:
        v.line(f"OK validator {prov['path']} = ggen-marketplace {prov['commit'][:12]} (published on origin/{prov['ref']}), sha256 {got[:16]}")
    return local


def r_receipts(root: Path) -> list[tuple[str, dict]]:
    out = []
    for rel in git(root, "ls-files", "--", f"{SUBJ['receipts_dir']}/*.json", f"{SUBJ['receipts_dir']}/**/*.json").splitlines():
        try:
            doc = json.loads((root / rel).read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if isinstance(doc, dict) and R_KEYS <= set(doc):
            out.append((rel, doc))
    return out


def m_imported_receipts(root: Path, v: Verdict) -> int:
    validator = validator_identity(root, v)
    if validator is None:
        return v.close("validator not admitted")
    receipts = r_receipts(root)
    if not receipts:
        v.refuse("NO_RECEIPTS", f"no R-shape receipt under {SUBJ['receipts_dir']}: nothing validated carries no bits")
    head = git(root, "rev-parse", "HEAD")
    for rel, doc in receipts:
        p = run([sys.executable, str(validator), rel, "--contract", "dfcm_fleet_v1"], root)
        if p.returncode != 0:
            v.refuse("RECEIPT_INVALID", f"{rel}: {(p.stdout + p.stderr).strip().splitlines()[-3:]}")
            continue
        ident = doc.get("identity", {})
        repo, sha = str(ident.get("repo", "")), str(ident.get("subject_sha", ""))
        own = repo == SUBJ["repository"] or (repo.startswith("/") and Path(repo).resolve() == root.resolve())
        if not own:
            v.line(f"OK {rel}: dfcm_fleet_v1 valid; subject {repo}@{sha[:12]} is foreign to this history (not bound here)")
            continue
        if run(["git", "-C", str(root), "merge-base", "--is-ancestor", sha, head], root).returncode != 0:
            v.refuse("RECEIPT_SUBJECT_FOREIGN", f"{rel}: identity.subject_sha {sha!r} is not a commit at or before HEAD")
            continue
        v.line(f"OK {rel}: dfcm_fleet_v1 valid; standing {doc['standing'].get('value')} at {sha[:12]} (ancestor of HEAD)")
    crowns = tomllib.loads((root / SDIR / SUBJ["imported_crown_render"]).read_text(encoding="utf-8"))
    n = crowns.get("imported_crowns", {}).get("crown_count", 0)
    v.line(f"imported Semantic Manufacturing crowns in the release graph: {n} (the STOP and gate receipts are lifted "
           f"by CE23-3 and judged by pack gate 090 + member chatman-stop; 0 until STOP=true)")
    return v.close(f"{len(receipts)} release receipts validated, {n} imported crowns")


# ----------------------------------------------------------------------------------------------------
# ci-dispositions and exact-head-ci


def court_facts(root: Path) -> dict:
    """Typed dispositions and local members of the release court, read from release.ttl."""
    import rdflib  # noqa: PLC0415
    g = release_graph(root)
    er, ce9 = rdflib.Namespace(ER), rdflib.Namespace(CE9)
    typed, local = {}, {}
    for d in g.subjects(rdflib.RDF.type, er.CheckDisposition):
        key = (str(g.value(d, er.checkWorkflow) or ""), str(g.value(d, er.checkName) or ""))
        typed[key] = {"iri": str(d), "class": str(g.value(d, er.failureClass)).rsplit("#", 1)[-1],
                      "boundary": str(g.value(d, er.checkBoundary)).rsplit("#", 1)[-1]}
    for gate in g.subjects(ce9.reproducesCheck, None):
        key = (str(g.value(gate, ce9.checkWorkflow) or ""), str(g.value(gate, ce9.reproducesCheck)))
        local[key] = {"gate": str(g.value(gate, er.gateName)), "job": str(g.value(gate, ce9.checkJob) or ""),
                      "command": str(g.value(gate, er.command) or "")}
    return {"typed": typed, "local": local}


def disposition_law(index: dict, typed: dict, local: dict, rendered: list[str] | None) -> list[tuple[str, str]]:
    """Pure law: every check of the universe `index` ({(workflow, check): row}) has at most one
    declared disposition, every declaration names a check the head carries, and a local member's
    command is the runner over exactly that job. Returns (code, text) refusals."""
    refused = []
    if rendered is not None and rendered != sorted({n for (_, n) in typed}):
        refused.append(("TYPED_RENDER_DRIFT", f"{SUBJ['typed_checks']} {rendered} != the graph's typed names"))
    for key in sorted(typed):
        if key not in index:
            refused.append(("STALE_TYPED_CHECK", f"typed {key[1]!r} ({key[0]}) is not a check the head carries: a "
                                                 f"disposition of nothing hides nothing and is refused"))
    for key, m in sorted(local.items()):
        row = index.get(key)
        want = f"{PINS['ci']['local_member_prefix']}{key[0]} {m['job']}"
        if row is None or row["job"] != m["job"]:
            refused.append(("MEMBER_NOT_A_CHECK", f"member {m['gate']} reproduces {key[1]!r} ({key[0]}#{m['job']}), "
                                                  f"which the head does not carry"))
        elif not (m["command"] == want or m["command"].startswith(want + " --skip-step ")):
            refused.append(("MEMBER_COMMAND_MISMATCH", f"member {m['gate']} runs {m['command']!r}, not {want!r}"))
        if key in typed:
            refused.append(("DOUBLE_DISPOSITION", f"{key[1]!r} ({key[0]}) is both typed and a local member"))
    names: dict[str, list[str]] = {}
    for (wf, name) in index:
        names.setdefault(name, []).append(wf)
    for (wf, name) in sorted(typed):
        others = [w for w in names.get(name, []) if w != wf and (w, name) not in typed]
        if others:
            refused.append(("TYPED_NAME_AMBIGUOUS", f"typed name {name!r} ({wf}) also names untyped checks of {others}: "
                                                    f"typed-checks.txt would hide their failures"))
    return refused


def m_ci_dispositions(root: Path, v: Verdict) -> int:
    u = ci_checks.universe(root, SUBJ["base_commit"], "HEAD")
    facts = court_facts(root)
    typed, local = facts["typed"], facts["local"]
    index = {(r["workflow"], r["check"]): r for r in u["checks"]}
    rendered = (root / SDIR / SUBJ["typed_checks"]).read_text(encoding="utf-8").splitlines()
    for code, text in disposition_law(index, typed, local, rendered):
        v.refuse(code, text)
    counts = {"local": 0, "typed": 0, "exact-head": 0}
    for key, row in sorted(index.items()):
        kind = "local" if key in local else "typed" if key in typed else "exact-head"
        counts[kind] += 1
        how = (f"local member {local[key]['gate']}" if kind == "local"
               else f"typed {typed[key]['class']}/{typed[key]['boundary']}" if kind == "typed"
               else "judged by its check-run at the exact head")
        flag = f" uncertain={row['uncertain']}" if row["uncertain"] else ""
        v.line(f"{key[0].split('/')[-1]}#{row['job']} {key[1]!r} events={row['events']}{flag}: {how}")
    return v.close(f"universe={len(index)} checks over {u['workflows']} workflows (changed_files={u['changed_files']}, "
                   f"truncated={u['truncated']}): {counts}")


def judge_checkruns(runs: list[dict], universe: list[dict], typed: dict, local: dict, passing: set[str]) -> tuple[list, list, list]:
    """Pure law over observed check-runs (each {name, workflow, status, conclusion, id}): returns (refused,
    unknown, lines). The newest run per (workflow, name) decides."""
    refused, unknown, lines = [], [], []
    latest: dict[tuple[str, str], dict] = {}
    for r in sorted(runs, key=lambda r: r.get("id", 0)):
        latest[(r.get("workflow") or "", r["name"])] = r
    typed_names = {n for (_, n) in typed}
    for key, r in sorted(latest.items()):
        if r.get("status") != "completed":
            unknown.append(("EXACT_HEAD_CI_PENDING", f"{key[1]!r} ({key[0]}) is {r.get('status')}"))
            continue
        if r.get("conclusion") in passing:
            continue
        if key in typed or (not key[0] and key[1] in typed_names):
            lines.append(f"typed {key[1]!r} ({key[0]}) concluded {r.get('conclusion')}")
            continue
        refused.append(("UNTYPED_FAILURE", f"{key[1]!r} ({key[0] or 'workflow unknown'}) concluded {r.get('conclusion')} "
                                           f"and has no typed disposition"))
    for key, m in sorted(local.items()):
        r = latest.get(key)
        if r is None:
            unknown.append(("MEMBER_CHECK_MISSING", f"local member {m['gate']} ({key[1]!r}) has no check-run at the head"))
        elif r.get("status") == "completed" and r.get("conclusion") != "success":
            refused.append(("LOCAL_CI_DISAGREE", f"local member {m['gate']} passed locally but {key[1]!r} concluded {r.get('conclusion')}"))
    for row in universe:
        key = (row["workflow"], row["check"])
        if "pull_request" in row["events"] and key not in latest and key not in typed and key not in local:
            unknown.append(("EXACT_HEAD_CHECK_MISSING", f"{key[1]!r} ({key[0]}) fires on the release pull request but has no check-run yet"))
    return refused, unknown, lines


def observe_checkruns(repo: str, sha: str) -> tuple[list[dict] | None, str]:
    if shutil.which("gh") is None:
        return None, "gh is not on PATH"
    c = run(["gh", "api", f"repos/{repo}/commits/{sha}", "--jq", ".sha"], Path.cwd(), timeout=120)
    if c.returncode != 0 or c.stdout.strip() != sha:
        return None, f"{repo}@{sha[:12]} is not published on GitHub (gh api exit {c.returncode})"
    runs = run(["gh", "api", "--paginate", f"repos/{repo}/actions/runs?head_sha={sha}&per_page=100",
                "--jq", ".workflow_runs[] | [.id, .path] | @tsv"], Path.cwd(), timeout=300)
    paths = dict(line.split("\t", 1) for line in runs.stdout.splitlines() if "\t" in line)
    cr = run(["gh", "api", "--paginate", f"repos/{repo}/commits/{sha}/check-runs?per_page=100",
              "--jq", ".check_runs[] | {id, name, status, conclusion, run: (.details_url | capture(\"runs/(?<r>[0-9]+)\").r // null)} | @json"],
             Path.cwd(), timeout=300)
    if runs.returncode != 0 or cr.returncode != 0:
        return None, f"gh api check-runs exit {cr.returncode}, runs exit {runs.returncode}"
    out = []
    for line in cr.stdout.splitlines():
        r = json.loads(line)
        r["workflow"] = paths.get(str(r.get("run")), "")
        out.append(r)
    return out, "ok"


def m_exact_head_ci(root: Path, v: Verdict) -> int:
    head = git(root, "rev-parse", "HEAD")
    runs, why = observe_checkruns(SUBJ["repository"], head)
    if runs is None:
        v.unk("EXACT_HEAD_UNPUBLISHED", f"{why}: exact-head CI cannot be observed before the driver pushes this head")
        return v.close(f"head={head}")
    if not runs:
        v.unk("EXACT_HEAD_CI_UNOBSERVED", f"{SUBJ['repository']}@{head[:12]} has no check-run (no release pull request or push run yet)")
        return v.close(f"head={head}")
    u = ci_checks.universe(root, SUBJ["base_commit"], "HEAD")
    facts = court_facts(root)
    refused, unknown, lines = judge_checkruns(runs, u["checks"], facts["typed"], facts["local"], set(PINS["ci"]["passing_conclusions"]))
    for text in lines:
        v.line(text)
    for code, text in refused:
        v.refuse(code, text)
    for code, text in unknown:
        v.unk(code, text)
    return v.close(f"head={head} check_runs={len(runs)}")


# ----------------------------------------------------------------------------------------------------
# replay and chatman-stop


def goal_gates(root: Path) -> dict[str, str]:
    import rdflib  # noqa: PLC0415
    g = rdflib.Graph().parse(root / SDIR / SUBJ["goal"], format="turtle")
    q = f"""PREFIX sj: <{SJ}> PREFIX dcterms: <{DCT}>
      SELECT ?id ?cmd WHERE {{ ?c a sj:GoalCheckpoint ; dcterms:identifier ?id ; sj:courtCommand ?cmd ;
                                  sj:checkpointOf <{SUBJ['goal_root']}> . }}"""
    return {str(r.id): str(r.cmd) for r in g.query(q)}


GATE_TOKEN = re.compile(r"\bce:(CE23-[0-9]+(?:-[A-Za-z]+)?)")
WO_TOKEN = re.compile(r"\bWO-([0-9A-Fa-f]{16})\b")


def projected_receipts(root: Path) -> list[dict]:
    """The root court's projection of the release's gate receipts (receipts_dir/*.json in the R shape):
    the gates a receipt covers are its file stem (when it names a CE23 gate) and every ce:<gate> token of
    identity.gate; the work orders it covers are the WO-<16 hex> tokens of identity.work_orders."""
    out = []
    for rel, doc in r_receipts(root):
        if Path(rel).parent.as_posix() != SUBJ["receipts_dir"]:
            continue
        ident = doc["identity"]
        gates = set(GATE_TOKEN.findall(str(ident.get("gate", ""))))
        if re.fullmatch(r"CE23-[0-9]+(?:-[A-Za-z]+)?", Path(rel).stem):
            gates.add(Path(rel).stem)
        orders = {m.lower() for m in WO_TOKEN.findall(" ".join(map(str, ident.get("work_orders") or [])))}
        out.append({"rel": rel, "standing": str(doc.get("standing", {}).get("value", "")), "gates": sorted(gates),
                    "orders": sorted(orders), "doc": doc})
    return out


def receipt_gates(root: Path) -> dict[str, list[str]]:
    """Gate id -> the ALIVE receipts that cover it."""
    covered: dict[str, list[str]] = {}
    for r in projected_receipts(root):
        if r["standing"] == "ALIVE":
            for gate in r["gates"]:
                covered.setdefault(gate, []).append(r["rel"])
    return covered


def court_process(root: Path, cmd: str) -> subprocess.CompletedProcess:
    return run(["sh", "-c", cmd], root, timeout=1200)


def record_court(gate: str, cmd: str, p: subprocess.CompletedProcess, v: Verdict) -> str:
    tail = [ln for ln in (p.stdout + p.stderr).strip().splitlines() if not ln.startswith("OK ")][-3:]
    print(f"  COURT_RUN {gate}: {cmd} -> exit {p.returncode}", flush=True)
    if p.returncode == 0:
        v.line(f"OK {gate}: exit 0 ({(p.stdout.strip().splitlines() or [''])[-1][:160]})")
        return "ALIVE"
    if p.returncode == 75:
        v.unk(f"COURT_UNKNOWN:{gate}", f"{cmd} exit 75: {tail}")
        return "UNKNOWN"
    v.refuse(f"COURT_REFUSED:{gate}", f"{cmd} exit {p.returncode}: {tail}")
    return "REFUSED"


def m_replay(root: Path, v: Verdict) -> int:
    for surface, (out, locked) in GGEN_SURFACES.items():
        committed = committed_render(root, surface, out, locked)
        again, why = cold_render(root, surface, out, locked, "replay-second-location")
        if again is None:
            v.refuse("RENDER_REPLAY_REFUSED", f"{surface}: {why}")
        elif again != committed:
            v.refuse("RENDER_NOT_DETERMINISTIC", f"{surface}: a cold render from a second scratch location differs from the "
                                                 f"committed bytes: {sorted(k for k in set(again) | set(committed) if again.get(k) != committed.get(k))[:5]}")
        else:
            v.line(f"OK {surface}: a cold render from a second scratch location replays the committed {len(again)} files byte for byte")
    gates = goal_gates(root)
    exclude = PINS["stop"]["exclude"]
    todo = []
    for gate, rels in sorted(receipt_gates(root).items()):
        if gate not in gates or gate in exclude:
            v.line(f"skip {rels}: {gate} is {'excluded' if gate in exclude else 'not a court gate of the goal root'}")
            continue
        todo.append(gate)
    # The receipted gate courts are independent read-only courts over the same committed head, each with
    # its own scratch; they run concurrently so the root court stays within one bounded run.
    from concurrent.futures import ThreadPoolExecutor  # noqa: PLC0415
    with ThreadPoolExecutor(max_workers=max(1, len(todo))) as pool:
        results = dict(zip(todo, pool.map(lambda g: (g, court_process(root, gates[g])), todo)))
    for gate in todo:
        record_court(gate, gates[gate], results[gate][1], v)
    return v.close(f"{len(todo)} receipted gate courts replayed at HEAD")


def m_chatman_stop(root: Path, v: Verdict) -> int:
    """CHATMAN_STOP: the goal root's own sj:stopQuery (goal.ttl), evaluated with rdflib over goal.ttl, the
    compiled CE23 orders and the admitted gate receipts projected as sj:Receipt nodes. The query is read
    from the graph, never re-typed here. CE23-9 (this court) and CE23-10 (the root receipt rendered from
    this court's observation) enter provisionally ALIVE: their standing is this court's own conjunction,
    so STOP here means every other term holds; CE-REL re-evaluates the query with their real receipts."""
    import rdflib  # noqa: PLC0415
    from rdflib import RDF, Literal, URIRef  # noqa: PLC0415
    sj, dct = rdflib.Namespace(SJ), rdflib.Namespace(DCT)
    g = rdflib.Graph().parse(root / SDIR / SUBJ["goal"], format="turtle")
    for orders in sorted((root / SDIR / "sjira" / "compiled").glob("*/orders.ttl")):
        g.parse(orders, format="turtle")
    goal_root = URIRef(SUBJ["goal_root"])
    query = g.value(goal_root, sj.stopQuery)
    if query is None:
        v.refuse("STOP_QUERY_ABSENT", f"{SUBJ['goal']} declares no sj:stopQuery on {goal_root}")
        return v.close("CHATMAN_STOP=unknown")
    ids = {str(g.value(c, dct.identifier)): c for c in g.subjects(RDF.type, sj.GoalCheckpoint)}
    under = {gid for gid, c in ids.items() if goal_root in set(g.transitive_objects(c, sj.checkpointOf)) and c != goal_root}
    tag = {gid for gid in under if gid == "CE23-11"}
    order_iri = {str(o).rsplit("#", 1)[-1].lower().removeprefix("wo-"): o for o in g.subjects(RDF.type, sj.WorkOrder)}
    validator, head = HERE / "unified_receipt_validator.py", git(root, "rev-parse", "HEAD")
    projected: dict[str, list[str]] = {}
    for r in projected_receipts(root):
        p = run([sys.executable, str(validator), r["rel"], "--contract", "dfcm_fleet_v1"], root)
        sha = str(r["doc"]["identity"].get("subject_sha", ""))
        if p.returncode != 0 or run(["git", "-C", str(root), "merge-base", "--is-ancestor", sha, head], root).returncode != 0:
            v.line(f"not projected {r['rel']}: not admitted (validator exit {p.returncode} or subject {sha[:12]} not at or before HEAD)")
            continue
        node = URIRef(f"urn:ce23-9:receipt:{r['rel']}")
        g.add((node, RDF.type, sj.Receipt))
        g.add((node, sj.standing, Literal(r["standing"])))
        for gid in r["gates"]:
            if gid in ids:
                g.add((ids[gid], sj.receipt, node))
                projected.setdefault(gid, []).append(f"{r['standing']}:{r['rel']}")
        for wo in r["orders"]:
            if wo in order_iri:
                g.add((order_iri[wo], sj.receipt, node))
    for gid, why in sorted(PINS["stop"]["exclude"].items()):
        if gid in tag or gid not in ids:
            continue
        node = URIRef(f"urn:ce23-9:provisional:{gid}")
        g.add((node, RDF.type, sj.Receipt))
        g.add((node, sj.standing, Literal("ALIVE")))
        g.add((ids[gid], sj.receipt, node))
        v.line(f"PROVISIONAL {gid} ALIVE: {why}")
    stop = bool(g.query(str(query)).askAnswer)
    crown = sorted(under - tag)
    missing, refused_gates = [], []
    for gid in crown:
        standings = [str(g.value(r, sj.standing)) for r in g.objects(ids[gid], sj.receipt)]
        if "ALIVE" in standings:
            continue
        (refused_gates if any(s.startswith(("BLOCKED", "REFUSED")) for s in standings) else missing).append(gid)
    open_orders = [o for o in g.subjects(RDF.type, sj.WorkOrder)
                   if goal_root in set(g.transitive_objects(o, sj.checkpointOf))
                   and not any(str(g.value(c, dct.identifier)) in tag for c in g.objects(o, sj.checkpointOf))
                   and (o, sj.boundaryClass, sj.Successor) not in g
                   and not any(str(g.value(r, sj.standing) or "").startswith(("ALIVE", "BLOCKED", "UNSUPPORTED", "REFUSED"))
                               for r in g.objects(o, sj.receipt))]
    v.line(f"crown gates {crown}; admitted receipts projected onto {sorted(projected)}")
    for gid in refused_gates:
        v.refuse(f"GATE_RECEIPT_NOT_ALIVE:{gid}", f"{gid} carries only non-ALIVE terminal receipts {projected.get(gid)}")
    for gid in missing:
        v.unk(f"NO_ALIVE_RECEIPT:{gid}", f"{gid} has no admitted ALIVE gate receipt ({gates_court(root, ids, gid, g)})")
    if open_orders:
        v.unk("ORDERS_OPEN", f"{len(open_orders)} CE23 work orders under the goal root have no terminal receipt and are not "
                             f"Successor, e.g. {sorted(str(o).rsplit('#', 1)[-1] for o in open_orders)[:4]}")
    if stop != (not missing and not refused_gates and not open_orders):
        v.refuse("STOP_QUERY_DISAGREES", f"the goal's sj:stopQuery answered {stop} while the member's own reading found "
                                         f"missing={missing} refused={refused_gates} open_orders={len(open_orders)}")
    acceptance(root, v)
    crowns = tomllib.loads((root / SDIR / SUBJ["imported_crown_render"]).read_text(encoding="utf-8"))
    v.line(f"imported Semantic Manufacturing crowns rendered (pack gate 090 admitted): {crowns.get('imported_crowns', {}).get('crown_count', 0)}")
    return v.close(f"CHATMAN_STOP={'true' if stop else 'false'} (goal sj:stopQuery; CE23-9 and CE23-10 provisional)")


def gates_court(root: Path, ids: dict, gid: str, g) -> str:
    cmd = str(g.value(ids[gid], rdflib_ns(SJ).courtCommand) or "")
    script = root / cmd.split()[-1] if cmd else None
    if script and script.is_file() and "machinery lands in a generated CE23 lane" in script.read_text(encoding="utf-8"):
        return f"its court {cmd} is the CE-INTAKE stub (exit 75): machinery absent"
    return f"court {cmd or 'none'}"


def rdflib_ns(ns: str):
    import rdflib  # noqa: PLC0415
    return rdflib.Namespace(ns)


def acceptance(root: Path, v: Verdict) -> None:
    """The operator edge: GC23-12 successor acceptance committed in the acceptance component at its commit."""
    import rdflib  # noqa: PLC0415
    comp = PINS["stop"]["acceptance_component"]
    g = release_graph(root)
    er = rdflib.Namespace(ER)
    sha = next((str(g.value(c, er.commitSha)) for c in g.subjects(er.componentId, rdflib.Literal(comp))), "")
    repo = Path(os.environ.get(f"CE23_REPO_{comp.upper()}") or (Path.home() / comp)).expanduser()
    if run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}^{{commit}}"], root).returncode != 0:
        v.unk("ACCEPTANCE_UNOBSERVABLE", f"{repo} holds no {comp} component commit {sha[:12]}")
    elif run(["git", "-C", str(repo), "cat-file", "-e", f"{sha}:{PINS['stop']['acceptance_path']}"], root).returncode != 0:
        v.unk("OPERATOR_ACCEPTANCE_ABSENT", f"GC23-12 successor acceptance ({PINS['stop']['acceptance_path']}) is absent at the "
                                            f"{comp} component commit {sha[:12]}: operator-only edge, STOP=false until the operator commits it")
    else:
        v.line(f"OK operator acceptance present at {comp}@{sha[:12]}:{PINS['stop']['acceptance_path']}")


MEMBERS = {
    "subject-clean": m_subject_clean,
    "projection-drift": m_projection_drift,
    "manifest-refs": m_manifest_refs,
    "imported-receipts": m_imported_receipts,
    "ci-dispositions": m_ci_dispositions,
    "replay": m_replay,
    "exact-head-ci": m_exact_head_ci,
    "chatman-stop": m_chatman_stop,
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("member", choices=sorted(MEMBERS))
    ap.add_argument("--root", type=Path)
    a = ap.parse_args(argv)
    root = (a.root or Path(subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip() or ".")).resolve()
    v = Verdict(a.member)
    print(f"MEMBER {a.member} root={root}", flush=True)
    try:
        return MEMBERS[a.member](root, v)
    except ModuleNotFoundError as exc:
        v.unk("TOOL_MISSING", f"python module {exc.name} is not importable")
        return v.close("not judged")
    except RuntimeError as exc:
        v.refuse("SUBJECT_UNREADABLE", str(exc))
        return v.close("not judged")


if __name__ == "__main__":
    raise SystemExit(main())
