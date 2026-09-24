#!/usr/bin/env python3
"""CE23-7 court: version-fence the Chatman tooling (release/v26.9.23/sjira/goal.ttl ce:CE23-7).

Proposition: verify_release, the portfolio survey and planner, the standing verifier and
the West projection can explicitly target release/v26.9.23 and never silently default to
release/v26.9.1; targeting v26.9.1 stays byte-identical and release/v26.9.1 byte-untouched.
Falsifier (goal.ttl ce:CE23-7-falsifier): the court exits 0 while a Chatman tool asked for
release/v26.9.23 reads release/v26.9.1.

Every clause runs the real tools as subprocesses on real files (no mocks). A PEP 578 audit
hook (audit_run.py) records every path each v26.9.23-targeted run opens; any open under a
release/v26.9.1/ directory is the falsifier witnessed. Clauses:

  F1 predecessor   release/v26.9.1 is byte-untouched (git tree / file digest pin)
  F2 identity      each tool targeting v26.9.1 emits the pre-fence bytes: pinned digests
                   (while the inputs hash to their pins) and/or the differential against
                   the pre-fence tools materialized from fence.base_commit
  F3 pointer       each tool's default equals its explicit --release <catalog pointer line>
  F4 line          in a synthesized two-line tree (pointer flipped, and pointer kept with
                   an explicit --release v26.9.23) every tool succeeds bound to 26.9.23 and
                   opens nothing under release/v26.9.1/
  F5 falsifiers    must refuse, typed: a v26.9.1 manifest under release/v26.9.23 (version-path
                   law), --release/--manifest conflicts, a cross-line companion input, a West
                   projection sourced from another line, an invalid line
  F6 subject       on the judged subject itself every tool run with --release v26.9.23 either
                   succeeds bound to 26.9.23 or refuses typed, never reading release/v26.9.1
  F7 literals      no fenced tool names the predecessor line; every other scripts/**/*.py that
                   does carries a typed fence.toml ledger row (none stale)
  F8 unit          python3 -m unittest discover -s tests: OK, Ran >= fence.unittest_floor

The survey reads GitHub; a release court must be deterministic and offline, so the survey
runs unmodified against a local stdlib HTTP server (127.0.0.1, ephemeral port) that answers
the four GitHub REST shapes it uses from the targeted manifest. That server is the one test
double here, and only because the real collaborator is a remote network service.

Subprocesses run under a no-LLM environment: a fresh HOME, a PATH of python3's and git's
directories plus /usr/bin:/bin (UNKNOWN when any holds claude or zcode), PYTHONUSERBASE,
LANG and PYTHONDONTWRITEBYTECODE=1 only.

    python3 release/v26.9.23/courts/ce23_7/court.py [--measure-base]

Exit: 0 ALIVE; 1 REFUSED (typed REFUSED[<code>] lines: a counterexample was witnessed);
75 UNKNOWN (typed UNKNOWN[<code>] lines: environment or baseline machinery absent).
--measure-base prints the base_commit tools' v26.9.1 input/output digests (the pins).
"""

from __future__ import annotations

import hashlib
import http.server
import json
import os
import re
import shutil
import site
import subprocess
import sys
import tempfile
import threading
import tomllib
import urllib.parse
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
AUDIT_RUN = HERE / "audit_run.py"
FENCE = tomllib.loads((HERE / "fence.toml").read_text(encoding="utf-8"))["fence"]
DOC = tomllib.loads((HERE / "fence.toml").read_text(encoding="utf-8"))
TARGET = FENCE["target"]  # v26.9.23
PRED = FENCE["predecessor"]  # v26.9.1
TARGET_VERSION = TARGET[1:]
PRED_VERSION = PRED[1:]
TOKEN = re.compile(FENCE["token"])
OBSERVED_AT = "2026-09-23T00:00:00Z"
LINE_INPUTS = ("manifest.toml", "fleet-policy.toml", "fanout-bootstrap.toml", "constitutional-role-crosswalk.toml")
WEST_INPUTS = ("catalog", "west.yml", "west", ".gitmodules", "west-commands.yml")


class Verdicts:
    def __init__(self) -> None:
        self.refused: list[str] = []
        self.unknown: list[str] = []

    def ok(self, clause: str, detail: str) -> None:
        print(f"OK {clause}: {detail}", flush=True)

    def refuse(self, code: str, clause: str, detail: str) -> None:
        line = f"REFUSED[{code}] {clause}: {detail}"
        self.refused.append(line)
        print(line, flush=True)

    def unknown_(self, code: str, clause: str, detail: str) -> None:
        line = f"UNKNOWN[{code}] {clause}: {detail}"
        self.unknown.append(line)
        print(line, flush=True)


V = Verdicts()


# ---------------------------------------------------------------- environment
def no_llm_env(home: Path) -> dict[str, str]:
    dirs: list[str] = []
    for tool in ("python3", "git"):
        found = shutil.which(tool)
        if not found:
            raise SystemExit(f"UNKNOWN[TOOL_MISSING] env: {tool} not on PATH")
        parent = str(Path(found).parent)
        if parent not in dirs:
            dirs.append(parent)
    dirs += ["/usr/bin", "/bin"]
    for directory in dirs:
        for llm in ("claude", "zcode"):
            if os.access(os.path.join(directory, llm), os.X_OK):
                raise SystemExit(f"UNKNOWN[LLM_ON_PATH] env: {directory} holds {llm}; no no-LLM PATH")
    home.mkdir(parents=True, exist_ok=True)
    return {
        "HOME": str(home),
        "PATH": ":".join(dirs),
        "LANG": os.environ.get("LANG", "en_US.UTF-8"),
        "PYTHONUSERBASE": site.getuserbase(),
        "PYTHONDONTWRITEBYTECODE": "1",
    }


ENV: dict[str, str] = {}


def run(cmd: list[str], cwd: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, cwd=cwd, env=ENV, capture_output=True, text=True, timeout=600)


def tool(script: str, args: list[str], cwd: Path, log: Path | None = None, root: Path = ROOT) -> subprocess.CompletedProcess[str]:
    path = str(root / script)
    if log is None:
        return run([sys.executable, path, *args], cwd)
    return run([sys.executable, str(AUDIT_RUN), str(log), path, *args], cwd)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def inputs_digest(root: Path, paths: list[str]) -> str | None:
    h = hashlib.sha256()
    for rel in paths:
        path = root / rel
        if not path.is_file():
            return None
        h.update(f"{sha(path.read_bytes())}  {rel}\n".encode())
    return h.hexdigest()


def tree_files_digest(directory: Path, rel_base: Path) -> str:
    lines = []
    for path in sorted(directory.rglob("*")):
        if path.is_file() and "__pycache__" not in path.parts:
            lines.append(f"{sha(path.read_bytes())}  {path.relative_to(rel_base).as_posix()}\n")
    return sha("".join(lines).encode())


def opened_under(log: Path, directory: Path) -> list[str]:
    prefix = os.path.realpath(directory) + os.sep
    if not log.exists():
        return []
    return sorted({line for line in log.read_text(encoding="utf-8").splitlines() if line.startswith(prefix)})


def probe_fired(log: Path, script: Path) -> bool:
    return log.exists() and os.path.realpath(script) in log.read_text(encoding="utf-8").splitlines()


def git(*args: str) -> subprocess.CompletedProcess[str]:
    return run(["git", "-C", str(ROOT), *args], ROOT)


# ---------------------------------------------------------- GitHub fixture
class GitHubFixture(http.server.ThreadingHTTPServer):
    """Answers the survey's four GitHub REST shapes from one manifest (see module doc)."""

    daemon_threads = True

    def __init__(self) -> None:
        super().__init__(("127.0.0.1", 0), _FixtureHandler)
        self.owner = "seanchatmangpt"
        self.repos: list[dict[str, Any]] = []
        self.shas: dict[str, str] = {}
        threading.Thread(target=self.serve_forever, daemon=True).start()

    @property
    def url(self) -> str:
        return f"http://127.0.0.1:{self.server_address[1]}"

    def load(self, manifest: Path) -> None:
        data = tomllib.loads(manifest.read_text(encoding="utf-8"))
        repos = sorted({str(c["repository"]) for c in data.get("components", [])})
        self.shas = {str(c["repository"]): str(c.get("sha", "")) for c in data.get("components", [])}
        self.repos = [
            {
                "full_name": repo,
                "owner": {"login": repo.split("/", 1)[0]},
                "private": False,
                "visibility": "public",
                "archived": False,
                "fork": False,
                "default_branch": "main",
                "updated_at": OBSERVED_AT,
            }
            for repo in repos
        ]


class _FixtureHandler(http.server.BaseHTTPRequestHandler):
    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002 - BaseHTTPRequestHandler signature
        return

    def _send(self, status: int, body: Any) -> None:
        payload = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_GET(self) -> None:  # noqa: N802
        fixture = self.server
        assert isinstance(fixture, GitHubFixture)
        parsed = urllib.parse.urlparse(self.path)
        query = urllib.parse.parse_qs(parsed.query)
        if re.fullmatch(r"/users/[^/]+/repos", parsed.path):
            page = int(query.get("page", ["1"])[0])
            self._send(200, fixture.repos if page == 1 else [])
        elif parsed.path == "/search/issues":
            self._send(200, {"total_count": 0, "items": []})
        elif match := re.fullmatch(r"/repos/([^/]+)/([^/]+)/commits/(.+)", parsed.path):
            repo = f"{urllib.parse.unquote(match[1])}/{urllib.parse.unquote(match[2])}"
            found = fixture.shas.get(repo)
            if found:
                self._send(200, {"sha": found, "html_url": f"https://github.com/{repo}/commit/{found}"})
            else:
                self._send(404, {"message": "Not Found"})
        else:
            self._send(404, {"message": "Not Found"})


FIXTURE: GitHubFixture | None = None


def survey(args: list[str], cwd: Path, out: Path, manifest: Path, log: Path | None = None,
           root: Path = ROOT) -> subprocess.CompletedProcess[str]:
    assert FIXTURE is not None
    FIXTURE.load(manifest)
    return tool("scripts/survey_portfolio.py",
                [*args, "--api-url", FIXTURE.url, "--observed-at", OBSERVED_AT, "--output-dir", str(out)],
                cwd, log, root)


def outputs_digest(out: Path) -> str:
    return sha((out / "SHA256SUMS").read_bytes()) if (out / "SHA256SUMS").is_file() else "absent"


# ------------------------------------------------------------ fixtures
def copy_west_surface(tree: Path) -> None:
    for name in WEST_INPUTS:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, tree / name, dirs_exist_ok=True)
        elif src.is_file():
            shutil.copy2(src, tree / name)


def substitute(text: str, pattern: str, repl: str, what: str) -> str:
    new, count = re.subn(pattern, repl, text, count=1, flags=re.M)
    if count != 1:
        raise FixtureError(f"{what}: anchor {pattern!r} not found once")
    return new


class FixtureError(RuntimeError):
    pass


def synth_line(tree: Path, *, flip: bool, with_predecessor: bool = True) -> Path:
    """A two-line tree: release/v26.9.1 copied, release/v26.9.23 derived from it."""
    copy_west_surface(tree)
    pred_dir, target_dir = tree / "release" / PRED, tree / "release" / TARGET
    target_dir.mkdir(parents=True)
    if with_predecessor:
        pred_dir.mkdir(parents=True)
    for name in LINE_INPUTS:
        text = (ROOT / "release" / PRED / name).read_text(encoding="utf-8")
        if with_predecessor:
            (pred_dir / name).write_text(text, encoding="utf-8")
        if name in ("manifest.toml", "constitutional-role-crosswalk.toml"):
            text = substitute(text, rf'^version = "{re.escape(PRED_VERSION)}"$', f'version = "{TARGET_VERSION}"', name)
        elif name == "fanout-bootstrap.toml":
            text = substitute(text, rf'^release = "{re.escape(PRED_VERSION)}"$', f'release = "{TARGET_VERSION}"', name)
        (target_dir / name).write_text(text, encoding="utf-8")
    if flip:
        catalog = tree / "catalog" / "west.toml"
        catalog.write_text(substitute(
            catalog.read_text(encoding="utf-8"),
            rf'^release_manifest = "release/{re.escape(PRED)}/manifest.toml"$',
            f'release_manifest = "release/{TARGET}/manifest.toml"', "catalog/west.toml"), encoding="utf-8")
        for west_file in [tree / "west.yml", *sorted((tree / "west").glob("*.yml"))]:
            text = west_file.read_text(encoding="utf-8")
            west_file.write_text(text.replace(f"source: release/{PRED}/manifest.toml",
                                              f"source: release/{TARGET}/manifest.toml"), encoding="utf-8")
    return tree


# ------------------------------------------------------------- clauses
def f1_predecessor() -> None:
    probe = git("rev-parse", "--is-inside-work-tree")
    if probe.returncode == 0 and probe.stdout.strip() == "true":
        tree = git("rev-parse", f"HEAD:release/{PRED}")
        if tree.returncode != 0:
            V.refuse("PREDECESSOR_ABSENT", "F1", f"HEAD has no release/{PRED}")
        elif tree.stdout.strip() != FENCE["predecessor_tree"]:
            V.refuse("PREDECESSOR_TOUCHED", "F1", f"release/{PRED} tree {tree.stdout.strip()} != {FENCE['predecessor_tree']}")
        else:
            V.ok("F1", f"release/{PRED} git tree {tree.stdout.strip()} at HEAD")
    digest = tree_files_digest(ROOT / "release" / PRED, ROOT)
    if digest != FENCE["predecessor_files_sha256"]:
        V.refuse("PREDECESSOR_TOUCHED", "F1", f"release/{PRED} file digest {digest} != pin")
    else:
        V.ok("F1", f"release/{PRED} file digest {digest[:16]} (minus __pycache__)")


def base_tools(dest: Path) -> bool:
    commit = FENCE["base_commit"]
    if git("cat-file", "-e", f"{commit}^{{commit}}").returncode != 0:
        return False
    for script in ("verify_release", "plan_completion", "survey_portfolio", "verify_standing_evidence", "verify_west_workspace"):
        shown = run(["git", "-C", str(ROOT), "show", f"{commit}:scripts/{script}.py"], ROOT)
        if shown.returncode != 0:
            return False
        (dest / "scripts").mkdir(parents=True, exist_ok=True)
        (dest / "scripts" / f"{script}.py").write_text(shown.stdout, encoding="utf-8")
    return True


def pred_file(name: str) -> str:
    return f"release/{PRED}/{name}"


def west_projection_line(root: Path) -> set[str]:
    sources: set[str] = set()
    for west_file in [root / "west.yml", *sorted((root / "west").glob("*.yml"))]:
        sources |= set(re.findall(r"source: release/(v[0-9.]+)/manifest\.toml", west_file.read_text(encoding="utf-8")))
    return sources


def identity_runs(work: Path) -> dict[str, dict[str, Any]]:
    """The v26.9.1 identity runs: new tool (explicit --release) and pre-fence argv."""
    m, f, b, c = pred_file("manifest.toml"), pred_file("fleet-policy.toml"), pred_file("fanout-bootstrap.toml"), pred_file("constitutional-role-crosswalk.toml")
    west_root = work / "west-root"
    copy_west_surface(west_root)
    (west_root / "release" / PRED).mkdir(parents=True)
    shutil.copy2(ROOT / m, west_root / m)
    catalog = west_root / "catalog" / "west.toml"
    catalog.write_text(re.sub(r'(?m)^release_manifest = ".*"$', f'release_manifest = "{m}"', catalog.read_text(encoding="utf-8"), count=1), encoding="utf-8")
    return {
        "verify_release": {"script": "scripts/verify_release.py", "new": ["--release", PRED], "base": ["--manifest", m]},
        "plan_release_only": {"script": "scripts/plan_completion.py", "new": ["--release", PRED, "--release-only"],
                              "base": ["--manifest", m, "--fleet", f, "--bootstrap", b, "--release-only"]},
        "plan_full": {"script": "scripts/plan_completion.py", "new": ["--release", PRED],
                      "base": ["--manifest", m, "--fleet", f, "--bootstrap", b]},
        "verify_standing_evidence": {"script": "scripts/verify_standing_evidence.py", "new": ["--release", PRED], "base": ["--manifest", m]},
        "verify_west_workspace": {"script": "scripts/verify_west_workspace.py", "new": ["--json", "--root", str(ROOT), "--release", PRED],
                                  "base": ["--json", "--root", str(west_root)],
                                  "new_diff": ["--json", "--root", str(west_root), "--release", PRED]},
        "survey_portfolio": {"survey": True, "new": ["--release", PRED], "base": ["--manifest", m, "--fleet", f, "--crosswalk", c]},
    }


def run_output(spec: dict[str, Any], argv: list[str], root: Path, out: Path) -> tuple[int, bytes]:
    if spec.get("survey"):
        proc = survey(argv, ROOT, out, ROOT / pred_file("manifest.toml"), root=root)
        return proc.returncode, outputs_digest(out).encode()
    proc = tool(spec["script"], argv, ROOT, root=root)
    return proc.returncode, proc.stdout.encode()


def f2_identity(work: Path, measure: bool = False) -> None:
    runs = identity_runs(work)
    base = work / "base"
    have_base = base_tools(base)
    pins = {row["id"]: row for row in DOC.get("baseline", [])}
    for bid, spec in runs.items():
        witnessed: list[str] = []
        pin = pins.get(bid)
        if measure:
            if not have_base:
                raise SystemExit(f"UNKNOWN[BASE_ABSENT] measure: {FENCE['base_commit']} not in this repository")
            code, out = run_output(spec, spec["base"], base, work / f"m-{bid}")
            value = out.decode() if spec.get("survey") else sha(out)
            print(f"{bid}: inputs_sha256={inputs_digest(ROOT, pin['inputs']) if pin else '-'} output_sha256={value} exit={code}")
            continue
        if pin and bid == "verify_west_workspace" and west_projection_line(ROOT) != {PRED}:
            V.ok("F2", f"{bid}: N/A, the West projection at the subject is sourced from {sorted(west_projection_line(ROOT))}")
            continue
        if pin and pin["output_sha256"] != "PIN" and inputs_digest(ROOT, pin["inputs"]) == pin["inputs_sha256"]:
            code, out = run_output(spec, spec["new"], ROOT, work / f"n-{bid}")
            got = out.decode() if spec.get("survey") else sha(out)
            if code != 0 or got != pin["output_sha256"]:
                V.refuse("V26_9_1_OUTPUT_CHANGED", "F2", f"{bid} --release {PRED}: exit {code}, output {got[:16]} != pin {pin['output_sha256'][:16]}")
                continue
            witnessed.append(f"pin {got[:16]}")
        if have_base:
            base_code, base_out = run_output(spec, spec["base"], base, work / f"b-{bid}")
            new_code, new_out = run_output(spec, spec.get("new_diff", spec["new"]), ROOT, work / f"d-{bid}")
            if (base_code, base_out) != (new_code, new_out):
                V.refuse("V26_9_1_OUTPUT_CHANGED", "F2", f"{bid}: pre-fence exit {base_code} vs fenced exit {new_code}, outputs differ")
                continue
            witnessed.append(f"differential vs {FENCE['base_commit'][:12]} exit {new_code}")
        if witnessed:
            V.ok("F2", f"{bid} --release {PRED} byte-identical ({'; '.join(witnessed)})")
        else:
            V.unknown_("BASELINE_STALE", "F2", f"{bid}: inputs moved off their pin and {FENCE['base_commit'][:12]} is not in this repository")


def pointer_line(root: Path) -> str | None:
    policy = tomllib.loads((root / "catalog" / "west.toml").read_text(encoding="utf-8"))
    match = re.fullmatch(r"release/(v[0-9]+\.[0-9]+\.[0-9]+)/manifest\.toml", str(policy.get("boundaries", {}).get("release_manifest", "")))
    return match[1] if match else None


def f3_pointer(work: Path) -> None:
    line = pointer_line(ROOT)
    if line is None:
        V.refuse("POINTER_UNDECLARED", "F3", "catalog/west.toml [boundaries].release_manifest is not release/vYY.M.D/manifest.toml")
        return
    cases = [
        ("verify_release", "scripts/verify_release.py", []),
        ("plan_completion", "scripts/plan_completion.py", []),
        ("verify_standing_evidence", "scripts/verify_standing_evidence.py", []),
        ("verify_west_workspace", "scripts/verify_west_workspace.py", ["--json"]),
        ("release_line", "scripts/release_line.py", []),
    ]
    for tid, script, extra in cases:
        default = tool(script, extra, ROOT)
        explicit = tool(script, [*extra, "--release", line], ROOT)
        if (default.returncode, default.stdout, default.stderr) != (explicit.returncode, explicit.stdout, explicit.stderr):
            V.refuse("DEFAULT_NOT_DECLARED_LINE", "F3", f"{tid}: default differs from --release {line}")
        else:
            V.ok("F3", f"{tid}: default == --release {line} (exit {default.returncode})")
    manifest = ROOT / "release" / line / "manifest.toml"
    if manifest.is_file():
        d = survey([], ROOT, work / "f3-default", manifest)
        e = survey(["--release", line], ROOT, work / "f3-explicit", manifest)
        same = (d.returncode, outputs_digest(work / "f3-default")) == (e.returncode, outputs_digest(work / "f3-explicit"))
        (V.ok("F3", f"survey_portfolio: default == --release {line} (exit {d.returncode})") if same
         else V.refuse("DEFAULT_NOT_DECLARED_LINE", "F3", f"survey_portfolio: default differs from --release {line}"))


def check_bound(tid: str, clause: str, proc: subprocess.CompletedProcess[str], log: Path, tree: Path,
                script: str, out: Path | None = None) -> bool:
    silent = opened_under(log, tree / "release" / PRED)
    if not probe_fired(log, ROOT / script):
        V.unknown_("PROBE_SILENT", clause, f"{tid}: the audit hook recorded no open of {script}")
        return False
    if silent:
        V.refuse("SILENT_V26_9_1_READ", clause, f"{tid} targeting {TARGET} opened {silent[0]}")
        return False
    if proc.returncode != 0:
        V.refuse("TARGET_RUN_FAILED", clause, f"{tid}: exit {proc.returncode}: {(proc.stderr or proc.stdout).strip()[-300:]}")
        return False
    if not opened_under(log, tree / "release" / TARGET):
        V.refuse("TARGET_NOT_READ", clause, f"{tid}: opened nothing under release/{TARGET}")
        return False
    try:
        if tid == "verify_release":
            report = json.loads(proc.stdout)
            assert report["release"] == TARGET_VERSION and report["findings"] == [], report["findings"]
        elif tid.startswith("plan_completion"):
            plan = json.loads(proc.stdout)
            branches = [p["branch"] for p in plan["packets"] if p.get("branch")]
            assert plan["release"] == TARGET_VERSION, plan["release"]
            assert branches and all(b.startswith(f"agent/{TARGET}-") for b in branches), [b for b in branches if not b.startswith(f"agent/{TARGET}-")][:3]
        elif tid == "verify_west_workspace":
            assert json.loads(proc.stdout)["release_component_count"] > 0
        elif tid == "verify_standing_evidence":
            assert json.loads(proc.stdout)["schema"] == "chatman-ecosystem.standing-evidence/1"
        elif tid == "survey_portfolio":
            assert out is not None
            report = (out / "REPORT.md").read_text(encoding="utf-8")
            census = (out / "REPO_CENSUS.csv").read_text(encoding="utf-8")
            scope = "REQUIRED_" + TARGET.upper().replace(".", "_")
            assert f"- {TARGET} required components:" in report, "report label"
            assert scope in census and not TOKEN.search(census), "census scope"
    except (AssertionError, KeyError, ValueError) as exc:
        V.refuse("OUTPUT_NOT_BOUND", clause, f"{tid}: output not bound to {TARGET_VERSION}: {exc}")
        return False
    return True


def line_runs(tree: Path, work: Path, tag: str, explicit: bool) -> None:
    flag = ["--release", TARGET] if explicit else []
    cases = [
        ("verify_release", "scripts/verify_release.py", flag),
        ("plan_completion", "scripts/plan_completion.py", flag),
        ("plan_completion --release-only", "scripts/plan_completion.py", [*flag, "--release-only"]),
        ("verify_standing_evidence", "scripts/verify_standing_evidence.py", flag),
        ("verify_west_workspace", "scripts/verify_west_workspace.py", ["--json", "--root", str(tree), *flag]),
    ]
    for tid, script, argv in cases:
        log = work / f"{tag}-{tid.replace(' ', '')}.opens"
        proc = tool(script, argv, tree, log)
        if check_bound(tid, "F4", proc, log, tree, script):
            V.ok("F4", f"{tag}: {tid} {' '.join(flag) or '(default)'} bound to {TARGET_VERSION}, nothing opened under release/{PRED}")
    log, out = work / f"{tag}-survey.opens", work / f"{tag}-survey"
    proc = survey(flag, tree, out, tree / "release" / TARGET / "manifest.toml", log)
    if check_bound("survey_portfolio", "F4", proc, log, tree, "scripts/survey_portfolio.py", out):
        V.ok("F4", f"{tag}: survey_portfolio {' '.join(flag) or '(default)'} bound to {TARGET_VERSION}, nothing opened under release/{PRED}")


def f4_line(work: Path) -> None:
    flipped = synth_line(work / "line-flipped", flip=True)
    kept = synth_line(work / "line-kept", flip=False)
    line_runs(flipped, work, "pointer->v26.9.23", explicit=False)
    line_runs(flipped, work, "pointer->v26.9.23+flag", explicit=True)
    # West stays out of the kept-pointer tree: its projection there is sourced from v26.9.1 (F5d).
    flag = ["--release", TARGET]
    for tid, script, argv in [
        ("verify_release", "scripts/verify_release.py", flag),
        ("plan_completion", "scripts/plan_completion.py", flag),
        ("verify_standing_evidence", "scripts/verify_standing_evidence.py", flag),
    ]:
        log = work / f"kept-{tid}.opens"
        proc = tool(script, argv, kept, log)
        if check_bound(tid, "F4", proc, log, kept, script):
            V.ok("F4", f"pointer->{PRED}: {tid} --release {TARGET} bound to {TARGET_VERSION}, nothing opened under release/{PRED}")
    log, out = work / "kept-survey.opens", work / "kept-survey"
    proc = survey(flag, kept, out, kept / "release" / TARGET / "manifest.toml", log)
    if check_bound("survey_portfolio", "F4", proc, log, kept, "scripts/survey_portfolio.py", out):
        V.ok("F4", f"pointer->{PRED}: survey_portfolio --release {TARGET} bound to {TARGET_VERSION}, nothing opened under release/{PRED}")
    # Default and explicit agree on the flipped tree (the pointer is the only default).
    for tid, script, extra in [("verify_release", "scripts/verify_release.py", []),
                               ("plan_completion", "scripts/plan_completion.py", []),
                               ("verify_west_workspace", "scripts/verify_west_workspace.py", ["--json", "--root", str(flipped)])]:
        a, b = tool(script, extra, flipped), tool(script, [*extra, "--release", TARGET], flipped)
        if (a.returncode, a.stdout) != (b.returncode, b.stdout):
            V.refuse("DEFAULT_NOT_DECLARED_LINE", "F4", f"{tid}: flipped-pointer default differs from --release {TARGET}")
    # The tools need no predecessor at all once the pointer names v26.9.23.
    alone = synth_line(work / "line-alone", flip=True, with_predecessor=False)
    for tid, script, argv in [("verify_release", "scripts/verify_release.py", []),
                              ("plan_completion", "scripts/plan_completion.py", []),
                              ("verify_standing_evidence", "scripts/verify_standing_evidence.py", []),
                              ("verify_west_workspace", "scripts/verify_west_workspace.py", ["--json", "--root", str(alone)])]:
        proc = tool(script, argv, alone)
        if proc.returncode != 0:
            V.refuse("PREDECESSOR_REQUIRED", "F4", f"{tid}: fails without release/{PRED}: {(proc.stderr or proc.stdout).strip()[-200:]}")
        else:
            V.ok("F4", f"no release/{PRED} in the tree: {tid} (default) exit 0")


def expect_refusal(clause: str, tid: str, proc: subprocess.CompletedProcess[str], exit_code: int, marker: str) -> None:
    text = proc.stdout + proc.stderr
    if proc.returncode == exit_code and marker in text:
        V.ok(clause, f"{tid} refused: exit {exit_code}, {marker}")
    else:
        V.refuse("FALSIFIER_ADMITTED", clause, f"{tid}: expected exit {exit_code} with {marker}, got exit {proc.returncode}: {text.strip()[-240:]}")


def f5_falsifiers(work: Path) -> None:
    kept = synth_line(work / "fals-kept", flip=False)
    wrong = work / "fals-version" / "release" / TARGET
    wrong.mkdir(parents=True)
    shutil.copy2(ROOT / pred_file("manifest.toml"), wrong / "manifest.toml")
    proc = tool("scripts/verify_release.py", ["--manifest", str(wrong / "manifest.toml")], ROOT)
    try:
        findings = json.loads(proc.stdout)["findings"]
    except (ValueError, KeyError):
        findings = []
    if proc.returncode == 2 and any("VERSION" in f["code"] and TARGET_VERSION in f["detail"] for f in findings):
        V.ok("F5a", f"a {PRED} manifest under release/{TARGET} refused: {[f['code'] for f in findings if 'VERSION' in f['code']]}")
    else:
        V.refuse("FALSIFIER_ADMITTED", "F5a", f"a {PRED} manifest under release/{TARGET}: exit {proc.returncode}, findings {findings}")
    unbound = work / "fals-unbound"
    unbound.mkdir()
    shutil.copy2(ROOT / pred_file("manifest.toml"), unbound / "manifest.toml")
    expect_refusal("F5a", "verify_release (unbound manifest)",
                   tool("scripts/verify_release.py", ["--manifest", str(unbound / "manifest.toml")], ROOT), 2, "ECOSYSTEM_VERSION_PATH_UNBOUND")
    conflict = ["--release", TARGET, "--manifest", pred_file("manifest.toml")]
    for tid, script in [("verify_release", "scripts/verify_release.py"), ("plan_completion", "scripts/plan_completion.py"),
                        ("verify_standing_evidence", "scripts/verify_standing_evidence.py")]:
        expect_refusal("F5b", tid, tool(script, conflict, kept), 2, "RELEASE_TARGET_CONFLICT")
    expect_refusal("F5b", "survey_portfolio", survey(conflict, kept, work / "fals-survey", kept / pred_file("manifest.toml")), 2, "RELEASE_TARGET_CONFLICT")
    expect_refusal("F5b", "verify_west_workspace",
                   tool("scripts/verify_west_workspace.py", ["--json", "--root", str(kept), "--release", TARGET, "--release-manifest", pred_file("manifest.toml")], kept),
                   2, "RELEASE_TARGET_CONFLICT")
    expect_refusal("F5c", "plan_completion (cross-line fleet)",
                   tool("scripts/plan_completion.py", ["--manifest", f"release/{TARGET}/manifest.toml", "--fleet", pred_file("fleet-policy.toml")], kept),
                   2, "RELEASE_TARGET_CONFLICT")
    expect_refusal("F5c", "survey_portfolio (cross-line crosswalk)",
                   survey(["--manifest", f"release/{TARGET}/manifest.toml", "--crosswalk", pred_file("constitutional-role-crosswalk.toml")],
                          kept, work / "fals-survey2", kept / "release" / TARGET / "manifest.toml"),
                   2, "RELEASE_TARGET_CONFLICT")
    expect_refusal("F5d", "verify_west_workspace (projection sourced from v26.9.1)",
                   tool("scripts/verify_west_workspace.py", ["--json", "--root", str(kept), "--release", TARGET], kept),
                   1, "REFUSED:WEST_RELEASE_SOURCE_MISMATCH")
    expect_refusal("F5e", "release_line (invalid line)", tool("scripts/release_line.py", ["--release", "v26.13.1"], ROOT), 2, "RELEASE_LINE_INVALID")


def f6_subject(work: Path) -> None:
    flag = ["--release", TARGET]
    cases = [
        ("verify_release", "scripts/verify_release.py", flag, None),
        ("plan_completion", "scripts/plan_completion.py", flag, None),
        ("verify_standing_evidence", "scripts/verify_standing_evidence.py", flag, None),
        ("verify_west_workspace", "scripts/verify_west_workspace.py", ["--json", *flag], None),
        ("survey_portfolio", "scripts/survey_portfolio.py", flag, work / "subject-survey"),
    ]
    manifest = ROOT / "release" / TARGET / "manifest.toml"
    for tid, script, argv, out in cases:
        log = work / f"subject-{tid}.opens"
        if out is not None:
            proc = survey(argv, ROOT, out, manifest if manifest.is_file() else ROOT / pred_file("manifest.toml"), log)
        else:
            proc = tool(script, argv, ROOT, log)
        text = (proc.stdout + proc.stderr).strip()
        silent = opened_under(log, ROOT / "release" / PRED)
        if not probe_fired(log, ROOT / script):
            V.unknown_("PROBE_SILENT", "F6", f"{tid}: the audit hook recorded no open of {script}")
        elif silent:
            V.refuse("SILENT_V26_9_1_READ", "F6", f"{tid} --release {TARGET} at the subject opened {silent[0]}")
        elif proc.returncode == 0:
            if check_bound(tid, "F6", proc, log, ROOT, script, out):
                V.ok("F6", f"{tid} --release {TARGET} at the subject: exit 0 bound to {TARGET_VERSION}")
        elif missing := re.search(rf"RELEASE_INPUT_MISSING:release/{re.escape(TARGET)}/[^ \n]+", text):
            V.ok("F6", f"{tid} --release {TARGET} at the subject: typed {missing[0]}")
        elif tid == "verify_west_workspace" and (west := re.search(r"REFUSED:WEST_[A-Z_]+", text)):
            V.ok("F6", f"{tid} --release {TARGET} at the subject: typed {west[0]}")
        elif tid == "verify_release" and proc.returncode == 2 and text.startswith("{"):
            report = json.loads(proc.stdout)
            codes = sorted({f["code"] for f in report["findings"]})
            if report["release"] == TARGET_VERSION and not any("VERSION" in code for code in codes):
                V.ok("F6", f"{tid} --release {TARGET} at the subject: bound to {TARGET_VERSION}, typed findings {codes}")
            else:
                V.refuse("OUTPUT_NOT_BOUND", "F6", f"{tid}: release {report['release']}, findings {codes}")
        else:
            V.refuse("UNTYPED_FAILURE", "F6", f"{tid} --release {TARGET} at the subject: exit {proc.returncode}: {text[-300:]}")


def f7_literals() -> None:
    fenced = [row["script"] for row in DOC["tool"]]
    for script in fenced:
        hits = [f"{script}:{n}" for n, line in enumerate((ROOT / script).read_text(encoding="utf-8").splitlines(), 1) if TOKEN.search(line)]
        if hits:
            V.refuse("FENCED_TOOL_NAMES_PREDECESSOR", "F7", ", ".join(hits))
    ledger = {row["path"]: row for row in DOC.get("ledger", [])}
    for row in ledger.values():
        if not all(row.get(k) for k in ("disposition", "owner", "reason")) or row["disposition"] not in {"SUCCESSOR", "CHESTERTON_FENCE", "PREDECESSOR_LAW"}:
            V.refuse("LEDGER_ROW_UNTYPED", "F7", row["path"])
    binding = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "scripts").rglob("*.py")
        if "__pycache__" not in path.parts and TOKEN.search(path.read_text(encoding="utf-8", errors="replace"))
    }
    for path in sorted(binding - set(ledger) - set(fenced)):
        V.refuse("UNLEDGERED_V26_9_1_BINDING", "F7", f"{path} names {PRED} with no fence.toml ledger row")
    for path in sorted(set(ledger) - binding):
        V.refuse("STALE_LEDGER_ROW", "F7", f"{path} no longer names {PRED}; remove its ledger row")
    if not any(line.startswith("REFUSED") and " F7:" in line for line in V.refused):
        V.ok("F7", f"{len(fenced)} fenced tools name no {PRED}; {len(binding)} other bindings, all ledgered")


def f8_unit() -> None:
    if git("rev-parse", "--is-inside-work-tree").returncode != 0:
        V.unknown_("NOT_A_CHECKOUT", "F8", "the suite needs a git checkout (tests call git rev-parse HEAD)")
        return
    proc = run([sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_*.py"], ROOT)
    text = proc.stdout + proc.stderr
    ran = re.search(r"^Ran (\d+) tests?", text, re.M)
    count = int(ran[1]) if ran else 0
    if proc.returncode == 0 and re.search(r"^OK", text, re.M) and count >= FENCE["unittest_floor"]:
        V.ok("F8", f"unittest Ran {count} (floor {FENCE['unittest_floor']}) OK")
    else:
        tail = [line for line in text.splitlines() if re.match(r"^(FAIL|ERROR|FAILED|Ran)", line)]
        V.refuse("UNIT_SUITE", "F8", f"exit {proc.returncode}, Ran {count} (floor {FENCE['unittest_floor']}): {tail[:6]}")


def main(argv: list[str]) -> int:
    global ENV, FIXTURE
    measure = "--measure-base" in argv
    with tempfile.TemporaryDirectory(prefix="ce23-7-court.") as scratch:
        work = Path(scratch)
        try:
            ENV = no_llm_env(work / "home")
        except SystemExit as exc:
            print(str(exc))
            print("CE23-7 UNKNOWN")
            return 75
        for module in ("yaml", "west"):
            probe = run([sys.executable, "-c", f"import {module}"], ROOT)
            if probe.returncode != 0:
                print(f"UNKNOWN[MODULE_MISSING] env: python3 cannot import {module}")
                print("CE23-7 UNKNOWN")
                return 75
        FIXTURE = GitHubFixture()
        try:
            head = git("rev-parse", "HEAD")
            print(f"CE23-7 court: subject {head.stdout.strip() if head.returncode == 0 else 'unknown (no git)'} at {ROOT}", flush=True)
            if measure:
                f2_identity(work / "measure", measure=True)
                return 0
            for clause in (f1_predecessor, f7_literals):
                clause()
            for name, clause in (("F2", f2_identity), ("F3", f3_pointer), ("F4", f4_line), ("F5", f5_falsifiers), ("F6", f6_subject)):
                sub = work / name
                sub.mkdir()
                try:
                    clause(sub)
                except FixtureError as exc:
                    V.unknown_("FIXTURE_UNBUILDABLE", name, str(exc))
            f8_unit()
        finally:
            FIXTURE.shutdown()
            FIXTURE.server_close()
    if V.refused:
        print(f"CE23-7 REFUSED ({len(V.refused)} counterexample(s))")
        return 1
    if V.unknown:
        print(f"CE23-7 UNKNOWN ({len(V.unknown)} clause(s) unwitnessed)")
        return 75
    print("CE23-7 ALIVE")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
