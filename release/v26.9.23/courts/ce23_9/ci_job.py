#!/usr/bin/env python3
"""Run one GitHub Actions job's `run:` steps locally at the exact head (CE23-9 root court, local CI members).

A local member of the CE23-9 root court reproduces an existing chatman CI check instead of trusting a
copy of its commands: this runner reads the job from the committed workflow file of the head
(`git show HEAD:<workflow>`, never the working tree) and executes its `run:` steps in order, in the
checkout (the court root), exactly as a hosted runner would run them after `actions/checkout` of the
candidate SHA. What differs from a hosted runner is explicit, never silent:

  * `uses:` steps (checkout, toolchain setup, caches, artifact upload/download) are not executed; each
    prints `CI_JOB_SKIP_USES`. The checkout is the court root at HEAD; toolchains are the local pinned
    ones (rust-toolchain.toml, python3), recorded by the court's probes.
  * `${{ ... }}` expressions are evaluated over a fixed pull_request context: github.sha and
    github.event.pull_request.head.sha = HEAD, github.event_name = 'pull_request', github.repository,
    github.workspace, github.ref = 'refs/pull/0/merge', runner.os/temp, env.* (workflow, job, step
    env and GITHUB_ENV writes), literals, ==, !=, &&, ||, ! and parentheses. Anything else
    (secrets.*, github.token, steps.*.outputs, functions other than success()/always()/failure()) makes
    that step UNSUPPORTED: the job is not locally reproducible and the runner exits 3.
  * `--skip-step NAME` omits a named step; every skip is printed and is part of the gate command, so it
    is hashed into the court input.
  * PYTHONDONTWRITEBYTECODE=1 is set (tracked release/v26.9.1/qlever/__pycache__ bytecode must not
    churn), and after the job the checkout must still be clean (`git status --porcelain
    --untracked-files=no`): a step that mutates a tracked file refuses the member.

Shells follow GitHub: default `bash -e {0}`, `shell: bash` -> `bash --noprofile --norc -eo pipefail {0}`,
`sh` -> `sh -e {0}`, `python` -> `python3 {0}`. working-directory (step or defaults.run) and the job's
timeout-minutes (default 20) apply.

  ci_job.py <workflow path> <job id> [--skip-step NAME ...] [--root DIR]
Exit: 0 every executed step passed; 1 a step failed (CI_JOB_STEP_FAILED) or the job mutated the
checkout; 3 not locally reproducible (UNSUPPORTED[...] line); 2 usage (unknown workflow/job); 75 a step
failed while GitHub's API refused its reads with the rate limit (CI_JOB_STEP_RATE_LIMITED: an
infrastructure edge, not a verdict on the subject; unauthenticated reads allow 60 per hour per address).
"""
from __future__ import annotations

import argparse
import os
import platform
import re
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

sys.dont_write_bytecode = True

REPOSITORY = "seanchatmangpt/chatman-ecosystem"
EXPR = re.compile(r"\$\{\{(.*?)\}\}", re.S)
TOKEN = re.compile(r"\s*(?:(?P<str>'(?:[^']|'')*')|(?P<op>==|!=|&&|\|\||!|\(|\))|(?P<num>-?\d+(?:\.\d+)?)"
                   r"|(?P<id>[A-Za-z_][A-Za-z0-9_.\-]*(?:\(\))?))")


class Unsupported(Exception):
    pass


class Ctx:
    def __init__(self, root: Path, head: str, env: dict[str, str]):
        self.root, self.head, self.env, self.failed = root, head, env, False

    def lookup(self, name: str):
        fixed = {
            "github.sha": self.head,
            "github.event.pull_request.head.sha": self.head,
            "github.event_name": "pull_request",
            "github.repository": REPOSITORY,
            "github.workspace": str(self.root),
            "github.ref": "refs/pull/0/merge",
            "github.head_ref": "release/v26.9.23-int",
            "github.base_ref": "main",
            "runner.os": {"Darwin": "macOS", "Linux": "Linux"}.get(platform.system(), platform.system()),
            "runner.temp": tempfile.gettempdir(),
        }
        if name in fixed:
            return fixed[name]
        if name.startswith("env."):
            return self.env.get(name[4:], "")
        if name == "success()":
            return not self.failed
        if name == "failure()":
            return self.failed
        if name in ("always()", "true"):
            return True
        if name in ("false", "null"):
            return False if name == "false" else None
        raise Unsupported(f"expression context '{name}'")


def evaluate(text: str, ctx: Ctx):
    tokens, pos = [], 0
    text = text.strip()
    while pos < len(text):
        m = TOKEN.match(text, pos)
        if not m or m.end() == pos:
            raise Unsupported(f"expression syntax '{text}'")
        pos = m.end()
        for kind in ("str", "op", "num", "id"):
            if m.group(kind) is not None:
                tokens.append((kind, m.group(kind)))
                break
    i = 0

    def peek():
        return tokens[i] if i < len(tokens) else (None, None)

    def take():
        nonlocal i
        i += 1
        return tokens[i - 1]

    def primary():
        kind, val = take()
        if kind == "str":
            return val[1:-1].replace("''", "'")
        if kind == "num":
            return float(val)
        if kind == "id":
            return ctx.lookup(val)
        if val == "(":
            v = disj()
            if take()[1] != ")":
                raise Unsupported(f"expression syntax '{text}'")
            return v
        if val == "!":
            return not truthy(primary())
        raise Unsupported(f"expression syntax '{text}'")

    def comparison():
        left = primary()
        while peek()[1] in ("==", "!="):
            op = take()[1]
            right = primary()
            eq = str(left).lower() == str(right).lower() if isinstance(left, str) and isinstance(right, str) else left == right
            left = eq if op == "==" else not eq
        return left

    def conj():
        left = comparison()
        while peek()[1] == "&&":
            take()
            right = comparison()
            left = right if truthy(left) else left
        return left

    def disj():
        left = conj()
        while peek()[1] == "||":
            take()
            right = conj()
            left = left if truthy(left) else right
        return left

    value = disj()
    if i != len(tokens):
        raise Unsupported(f"expression syntax '{text}'")
    return value


def truthy(v) -> bool:
    return v not in (None, False, "", 0, 0.0)


def render(value, ctx: Ctx) -> str:
    def sub(m: re.Match) -> str:
        v = evaluate(m.group(1), ctx)
        return "" if v is None else ("true" if v is True else "false" if v is False else str(v))
    return EXPR.sub(sub, str(value))


def condition(expr, ctx: Ctx) -> bool:
    if expr is None:
        return not ctx.failed
    text = str(expr).strip()
    m = EXPR.fullmatch(text)
    return truthy(evaluate(m.group(1) if m else text, ctx))


def shell_argv(shell: str | None, script: Path) -> list[str]:
    if shell in (None, ""):
        return ["bash", "-e", str(script)]
    if shell == "bash":
        return ["bash", "--noprofile", "--norc", "-eo", "pipefail", str(script)]
    if shell == "sh":
        return ["sh", "-e", str(script)]
    if shell == "python":
        return ["python3", str(script)]
    if "{0}" in shell:
        return [part.replace("{0}", str(script)) for part in shell.split()]
    raise Unsupported(f"shell '{shell}'")


def read_env_file(path: Path) -> dict[str, str]:
    out: dict[str, str] = {}
    lines = path.read_text(encoding="utf-8").splitlines() if path.exists() else []
    k = 0
    while k < len(lines):
        line = lines[k]
        if "<<" in line and "=" not in line.split("<<", 1)[0]:
            key, delim = line.split("<<", 1)
            body = []
            k += 1
            while k < len(lines) and lines[k] != delim:
                body.append(lines[k])
                k += 1
            out[key] = "\n".join(body)
        elif "=" in line:
            key, val = line.split("=", 1)
            out[key] = val
        k += 1
    return out


RATE_LIMITED = re.compile(r"HTTP Error 403: rate limit exceeded|API rate limit exceeded")


def tee(argv_: list[str], cwd: Path, env: dict, timeout: int) -> tuple[int, str]:
    """Run one step, streaming its combined output and keeping the last 64 KiB for classification."""
    tail = ""
    with subprocess.Popen(argv_, cwd=cwd, env=env, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                          errors="replace") as proc:
        watchdog = threading.Timer(timeout, proc.kill)
        watchdog.start()
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                sys.stdout.write(line)
                tail = (tail + line)[-65536:]
            rc = proc.wait()
        finally:
            timed_out = not watchdog.is_alive()
            watchdog.cancel()
    return (124 if timed_out and rc != 0 else rc), tail


def untracked(root: Path) -> set[str]:
    out = subprocess.run(["git", "-C", str(root), "ls-files", "--others", "--exclude-standard", "-z"],
                         capture_output=True, text=True).stdout
    return {p for p in out.split("\0") if p}


def tests_shim(root: Path, scratch: Path, env: dict[str, str]) -> str | None:
    """A hosted runner's python3 has no top-level `tests` package; some hosts do (a stray regular
    package in site-packages). A regular package anywhere on sys.path beats the repository's tests/
    namespace directory, so `python3 -m unittest tests.x` fails on such a host for a reason that is not
    the subject's. When (and only when) that shadow is observed, write a scratch `tests` package whose
    __path__ is the repository's tests/ and return the shadowing file (printed as CI_JOB_HOST_SHIM)."""
    if not (root / "tests").is_dir() or (root / "tests" / "__init__.py").exists():
        return None
    probe = subprocess.run(["python3", "-c", "import tests,sys;sys.stdout.write(getattr(tests,'__file__','') or '')"],
                           cwd=scratch, env=env, capture_output=True, text=True)
    found = probe.stdout.strip()
    if probe.returncode != 0 or not found or Path(found).resolve().is_relative_to(root):
        return None
    pkg = scratch / "shim" / "tests"
    pkg.mkdir(parents=True, exist_ok=True)
    (pkg / "__init__.py").write_text(f"__path__ = [{str(root / 'tests')!r}]\n", encoding="utf-8")
    return found


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("workflow")
    ap.add_argument("job")
    ap.add_argument("--skip-step", action="append", default=[])
    ap.add_argument("--root", type=Path, default=Path("."))
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(line_buffering=True)
    try:
        import yaml  # noqa: PLC0415
    except ImportError:
        print("UNSUPPORTED[TOOL_MISSING] ci_job: PyYAML is not importable")
        return 3
    root = a.root.resolve()
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True).stdout.strip()
    blob = subprocess.run(["git", "-C", str(root), "show", f"HEAD:{a.workflow}"], capture_output=True, text=True)
    if blob.returncode != 0 or not re.fullmatch(r"[0-9a-f]{40}", head):
        print(f"CI_JOB_USAGE {a.workflow} is not committed at HEAD {head}")
        return 2
    try:
        doc = yaml.safe_load(blob.stdout) or {}
    except yaml.YAMLError as exc:
        print(f"CI_JOB_USAGE {a.workflow} is not valid YAML at HEAD: {str(exc).splitlines()[0]}")
        return 2
    job = (doc.get("jobs") or {}).get(a.job)
    if not isinstance(job, dict):
        print(f"CI_JOB_USAGE {a.workflow} has no job {a.job}")
        return 2
    if "uses" in job:
        print(f"UNSUPPORTED[REUSABLE_WORKFLOW] {a.workflow}#{a.job} calls {job['uses']}")
        return 3
    known = {str(s.get("name")) for s in job.get("steps") or [] if isinstance(s, dict) and s.get("name")}
    unknown_skips = sorted(set(a.skip_step) - known)
    if unknown_skips:
        print(f"CI_JOB_USAGE --skip-step names no step of {a.workflow}#{a.job}: {unknown_skips}")
        return 2
    scratch = Path(tempfile.mkdtemp(prefix="ce23-9-ci-job."))
    files = {k: scratch / k.lower() for k in ("GITHUB_OUTPUT", "GITHUB_ENV", "GITHUB_PATH", "GITHUB_STEP_SUMMARY")}
    for f in files.values():
        f.touch()
    base_env = {k: v for k, v in os.environ.items()}
    base_env.update({"PYTHONDONTWRITEBYTECODE": "1", "CI": "true", "GITHUB_WORKSPACE": str(root),
                     "GITHUB_SHA": head, "GITHUB_REPOSITORY": REPOSITORY, "GITHUB_EVENT_NAME": "pull_request",
                     "RUNNER_TEMP": str(scratch)})
    base_env.update({k: str(v) for k, v in files.items()})
    shim = tests_shim(root, scratch, base_env)
    if shim:
        base_env["PYTHONPATH"] = os.pathsep.join([str(scratch / "shim")] + [p for p in [base_env.get("PYTHONPATH", "")] if p])
        print(f"CI_JOB_HOST_SHIM the host's python3 resolves `tests` to {shim}, which shadows the repository's "
              f"tests/ namespace directory (`python3 -m unittest tests.<module>` cannot import it); PYTHONPATH "
              f"leads with a scratch tests package whose __path__ is {root / 'tests'}")
    ctx = Ctx(root, head, dict(base_env))
    timeout = int(job.get("timeout-minutes") or 20) * 60
    defaults_wd = ((doc.get("defaults") or {}).get("run") or {}).get("working-directory")
    defaults_wd = ((job.get("defaults") or {}).get("run") or {}).get("working-directory", defaults_wd)
    try:
        for scope in (doc.get("env") or {}, job.get("env") or {}):
            for k, v in scope.items():
                ctx.env[k] = render(v, ctx)
        if not condition(job.get("if"), ctx):
            print(f"CI_JOB_SKIPPED {a.workflow}#{a.job}: job if is false in the pull_request context")
            return 0
    except Unsupported as exc:
        print(f"UNSUPPORTED[EXPRESSION] {a.workflow}#{a.job} job env/if: {exc}")
        return 3
    before = untracked(root)
    print(f"CI_JOB {a.workflow}#{a.job} name={job.get('name', a.job)!r} head={head} steps={len(job.get('steps') or [])}")
    try:
        rc = run_steps(a, job, ctx, scratch, files, defaults_wd, timeout, root)
    finally:
        for rel in sorted(untracked(root) - before):
            # A hosted runner discards its workspace; files the job itself created (receipts it uploads
            # as artifacts, e.g. gall-crown.yml's gall-receipt.json) must not leak into later members.
            (root / rel).unlink(missing_ok=True)
            print(f"CI_JOB_BYPRODUCT_REMOVED {rel}")
    dirty = subprocess.run(["git", "-C", str(root), "status", "--porcelain", "--untracked-files=no"],
                           capture_output=True, text=True).stdout.strip()
    if dirty:
        print(f"CI_JOB_MUTATED_CHECKOUT {a.workflow}#{a.job}: {dirty.splitlines()[:5]}")
        return 1
    if rc == 0:
        print(f"CI_JOB_PASS {a.workflow}#{a.job} head={head}")
    return rc


def run_steps(a, job: dict, ctx: Ctx, scratch: Path, files: dict, defaults_wd, timeout: int, root: Path) -> int:
    for n, step in enumerate(job.get("steps") or [], 1):
        label = step.get("name") or step.get("uses") or (str(step.get("run", "")).strip().splitlines() or [""])[0]
        if step.get("name") in a.skip_step:
            print(f"CI_JOB_SKIP_DECLARED step={n} name={label!r}")
            continue
        if "uses" in step:
            print(f"CI_JOB_SKIP_USES step={n} uses={step['uses']}")
            continue
        try:
            if not condition(step.get("if"), ctx):
                print(f"CI_JOB_SKIP_IF step={n} name={label!r}")
                continue
            env = dict(ctx.env)
            for k, v in (step.get("env") or {}).items():
                env[k] = render(v, ctx)
            script = render(step.get("run", ""), ctx)
            wd = render(step.get("working-directory") or defaults_wd or ".", ctx)
            argv_ = shell_argv(step.get("shell"), scratch / f"step-{n}.sh")
        except Unsupported as exc:
            print(f"UNSUPPORTED[EXPRESSION] {a.workflow}#{a.job} step={n} name={label!r}: {exc}")
            return 3
        (scratch / f"step-{n}.sh").write_text(script + "\n", encoding="utf-8")
        cwd = (root / wd).resolve()
        print(f"CI_JOB_STEP step={n} name={label!r} cwd={os.path.relpath(cwd, root)}", flush=True)
        rc, tail = tee(argv_, cwd, env, timeout)
        extra_path = files["GITHUB_PATH"].read_text(encoding="utf-8").split()
        if extra_path:
            ctx.env["PATH"] = os.pathsep.join(extra_path + [ctx.env.get("PATH", "")])
        ctx.env.update(read_env_file(files["GITHUB_ENV"]))
        if rc != 0:
            ctx.failed = True
            if RATE_LIMITED.search(tail):
                print(f"CI_JOB_STEP_RATE_LIMITED step={n} name={label!r} exit={rc}: the step's GitHub API reads were "
                      f"refused by the API rate limit (infrastructure edge; export GITHUB_TOKEN or GH_TOKEN, or rerun "
                      f"after the limit resets); the job is not judged")
                return 75
            print(f"CI_JOB_STEP_FAILED step={n} name={label!r} exit={rc}")
            return 1
        print(f"CI_JOB_STEP_PASS step={n} name={label!r}")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
