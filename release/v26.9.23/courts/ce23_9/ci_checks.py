#!/usr/bin/env python3
"""Static CI check universe of an exact chatman-ecosystem head (CE23-9 root court, member ci-dispositions).

Which GitHub check runs does the exact head carry?  Read from the committed workflow files of the head
(`git show <head>:.github/workflows/*.yml`, never the working tree) and from the file list of the release
pull request (`git diff --name-only <base> <head>`), with GitHub's documented trigger semantics:

  pull_request   the release PR targets main: fires when `branches` (base branch) admits main and the
                 PR's changed files pass `paths` / `paths-ignore`;
  push           after the merge to main: fires when `branches` admits main and the same changed files
                 pass `paths` / `paths-ignore` (the merge brings exactly the PR's files);
  schedule       runs on main after the merge (every scheduled workflow is an existing main check).

workflow_dispatch / workflow_call / other events never run by themselves and contribute no check.
Filter patterns follow the GitHub cheat sheet: `*` is any run of characters except `/`, `**` any run of
characters, `?` makes the preceding character optional, `+` repeats it, `[...]` is a class, and a
leading `!` negates (in `paths` the last matching pattern decides).  A job's check name is its `name`
(`${{ matrix.K }}` expanded over a static matrix), otherwise its id, with GitHub's " (v1, v2)" suffix for
an unnamed matrix job.  GitHub evaluates path filters over at most the first 300 changed files; with more,
`truncated` is set and a path-filtered workflow that matches only beyond the first 300 files in diff order
is reported as `uncertain` (the caller types it, never drops it).

Output (JSON, sorted, no clock or absolute path): one row per (workflow, job, check name) with the events
that fire it.  Stdlib + PyYAML only (PyYAML absent -> exit 75, UNKNOWN).

  ci_checks.py [--root DIR] --base SHA [--head REV]      (exit 0; 75 tool missing; 2 usage/git error)
"""
from __future__ import annotations

import argparse
import itertools
import json
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True

MAIN = "main"
PATH_FILTER_LIMIT = 300
MATRIX_EXPR = re.compile(r"\$\{\{\s*matrix\.([A-Za-z0-9_-]+)\s*\}\}")


def glob_regex(pattern: str) -> re.Pattern[str]:
    """GitHub filter pattern -> anchored regex (cheat sheet semantics, see module docstring)."""
    out: list[str] = []
    i = 0
    while i < len(pattern):
        c = pattern[i]
        if c == "*":
            if pattern[i:i + 2] == "**":
                out.append(".*")
                i += 2
                continue
            out.append("[^/]*")
        elif c == "?":
            if out:
                out[-1] = f"(?:{out[-1]})?"
        elif c == "+":
            if out:
                out[-1] = f"(?:{out[-1]})+"
        elif c == "[":
            j = pattern.find("]", i + 1)
            if j == -1:
                out.append(re.escape(c))
            else:
                out.append("[" + pattern[i + 1:j].replace("\\", "\\\\") + "]")
                i = j
        else:
            out.append(re.escape(c))
        i += 1
    return re.compile("".join(out) + r"\Z")


def ordered_match(patterns: list[str], value: str) -> bool:
    """Last matching pattern decides; a `!pattern` match excludes."""
    verdict = False
    for p in patterns:
        neg = p.startswith("!")
        if glob_regex(p[1:] if neg else p).match(value):
            verdict = not neg
    return verdict


def as_list(v) -> list[str]:
    if v is None:
        return []
    if isinstance(v, str):
        return [v]
    return [str(x) for x in v]


def branch_admits(spec: dict, branch: str) -> bool:
    inc, exc = as_list(spec.get("branches")), as_list(spec.get("branches-ignore"))
    if inc:
        return ordered_match(inc, branch)
    if exc:
        return not ordered_match(exc, branch)
    return True


def paths_fire(spec: dict, files: list[str]) -> tuple[bool, bool]:
    """(fires, uncertain) for one event spec over the changed files (GitHub's 300-file window)."""
    inc, exc = as_list(spec.get("paths")), as_list(spec.get("paths-ignore"))
    if not inc and not exc:
        return True, False
    window, beyond = files[:PATH_FILTER_LIMIT], files[PATH_FILTER_LIMIT:]

    def hit(fs: list[str]) -> bool:
        if inc:
            return any(ordered_match(inc, f) for f in fs)
        return any(not ordered_match(exc, f) for f in fs)

    if hit(window):
        return True, False
    return False, bool(beyond) and hit(beyond)


def triggers(doc: dict) -> dict:
    on = doc.get(True, doc.get("on"))
    if isinstance(on, str):
        return {on: {}}
    if isinstance(on, list):
        return {str(k): {} for k in on}
    if isinstance(on, dict):
        return {str(k): (v if isinstance(v, dict) else {}) for k, v in on.items()}
    return {}


def matrix_rows(job: dict) -> list[dict]:
    strategy = job.get("strategy") if isinstance(job.get("strategy"), dict) else {}
    matrix = strategy.get("matrix") if isinstance(strategy.get("matrix"), dict) else None
    if not matrix:
        return []
    axes = {k: v for k, v in matrix.items() if k not in ("include", "exclude") and isinstance(v, list)}
    rows = [dict(zip(axes, combo)) for combo in itertools.product(*axes.values())] if axes else []
    for ex in matrix.get("exclude") or []:
        if isinstance(ex, dict):
            rows = [r for r in rows if not all(r.get(k) == v for k, v in ex.items())]
    for inc in matrix.get("include") or []:
        if isinstance(inc, dict):
            rows.append(dict(inc))
    return rows


def check_names(job_id: str, job: dict) -> list[str]:
    name = job.get("name")
    rows = matrix_rows(job)
    if not rows:
        return [str(name) if name is not None else job_id]
    names = []
    for row in rows:
        if name is not None:
            names.append(MATRIX_EXPR.sub(lambda m: str(row.get(m.group(1), m.group(0))), str(name)))
        else:
            names.append(f"{job_id} ({', '.join(str(v) for v in row.values())})")
    return names


def git(root: Path, *args: str) -> str:
    p = subprocess.run(["git", "-C", str(root), *args], capture_output=True, text=True)
    if p.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)}: {p.stderr.strip()}")
    return p.stdout


def universe(root: Path, base: str, head: str) -> dict:
    import yaml  # noqa: PLC0415 (a court dependency: ModuleNotFoundError is typed UNKNOWN by the caller)
    files = [f for f in git(root, "diff", "--name-only", base, head).splitlines() if f]
    listing = git(root, "ls-tree", "--name-only", f"{head}:.github/workflows").splitlines()
    rows, workflows = [], 0
    for leaf in sorted(listing):
        if not leaf.endswith((".yml", ".yaml")):
            continue
        path = f".github/workflows/{leaf}"
        try:
            doc = yaml.safe_load(git(root, "show", f"{head}:{path}")) or {}
        except yaml.YAMLError as exc:
            raise RuntimeError(f"{path} is not valid YAML at {head}: {str(exc).splitlines()[0]}") from exc
        workflows += 1
        on = triggers(doc)
        events, uncertain = [], []
        for ev in ("pull_request", "push"):
            if ev in on and branch_admits(on[ev], MAIN):
                fires, unsure = paths_fire(on[ev], files)
                if fires:
                    events.append(ev)
                elif unsure:
                    uncertain.append(ev)
        if "schedule" in on:
            events.append("schedule")
        if not events and not uncertain:
            continue
        for job_id, job in (doc.get("jobs") or {}).items():
            if not isinstance(job, dict):
                continue
            for name in check_names(str(job_id), job):
                rows.append({"workflow": path, "job": str(job_id), "check": name,
                             "events": sorted(events), "uncertain": sorted(uncertain),
                             "workflow_name": str(doc.get("name") or path)})
    rows.sort(key=lambda r: (r["check"], r["workflow"], r["job"]))
    return {"base": base, "head": git(root, "rev-parse", head).strip(), "changed_files": len(files),
            "truncated": len(files) > PATH_FILTER_LIMIT, "workflows": workflows, "checks": rows}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--root", type=Path, default=Path("."))
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    a = ap.parse_args(argv)
    try:
        u = universe(a.root, a.base, a.head)
    except ModuleNotFoundError as exc:
        print(f"UNKNOWN[TOOL_MISSING] ci_checks: python module {exc.name} is not importable", file=sys.stderr)
        return 75
    except RuntimeError as exc:
        print(f"ci_checks: {exc}", file=sys.stderr)
        return 2
    json.dump(u, sys.stdout, indent=1, sort_keys=True)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
