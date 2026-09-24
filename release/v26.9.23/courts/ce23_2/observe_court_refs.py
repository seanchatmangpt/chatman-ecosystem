#!/usr/bin/env python3
"""Observe which GC-26.9.23 court scripts execute which repository checkout (CE23-2 input).

Writes release/v26.9.23/imports/court-references.ttl: the er:courtReferencesComponent facts
the vendored chatman-ecosystem-release-pack's disposition rule and gates 070/080 read. It is an
observation, never a decision:

  * the governing courts are `docs/sjira/v26.9.23/courts/*.sh` of seanchatmangpt/xaas at the
    commit of the release's required xaas component (release.ttl er:commitSha), read with
    `git archive` from the canonical xaas checkout (read-only; CE23_REPO_XAAS, default ~/xaas);
  * the probe is xaas's own `scripts/sjira/fleet_matrix.py court_references()` at that same
    commit (imported from the archive, never from a working tree), called with
    {"name": <basename>, "path": None}: a script references a repository when it names
    `$<NAME>_DIR`, `${<NAME>_DIR`, `~/<name>`, `$HOME/<name>` or `${HOME}/<name>`;
    it is unioned with a home-agnostic absolute checkout path `/(Users|home)/<user>/<name>`
    so the observation is the same on every machine;
  * the probed repositories are every er:legacyRepository of imports/legacy-v26.9.1.ttl (the
    predecessor's components) plus every er:repository of release.ttl's er:Component rows.

Every probed repository is listed in the header with its hits (an empty hit list is a recorded
negative observation). The output has no clock and no local path: the same commit and graph give
the same bytes, so the CE23-2 court re-runs this script and compares with `cmp` semantics.

Handwritten residue (HANDWRITTEN.md row): no pack lifts court-script references into RDF.

    observe_court_refs.py --subject release/v26.9.23 [--xaas-repo PATH] > imports/court-references.ttl

Exit: 0 written; 2 an input is absent or the xaas commit is not in the checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ER = "http://seanchatmangpt.github.io/packs/chatman-ecosystem-release#"
COURTS_REPOSITORY = "seanchatmangpt/xaas"
COURTS_PATH = "docs/sjira/v26.9.23/courts"
MATRIX_PATH = "scripts/sjira/fleet_matrix.py"
LEGACY_IMPORT = "imports/legacy-v26.9.1.ttl"
SHA40 = re.compile(r"^[0-9a-f]{40}$")


class ObservationError(Exception):
    """An input of the observation is absent: nothing is observed."""


def subject_graph(subject: Path) -> tuple[list[str], dict[str, str]]:
    """(predecessor component repositories, {release component repository: commit})."""
    from rdflib import RDF, Graph, Namespace  # noqa: PLC0415

    er = Namespace(ER)
    g = Graph()
    g.parse(subject / "release.ttl", format="turtle")
    g.parse(subject / LEGACY_IMPORT, format="turtle")
    legacy = sorted({str(o) for o in g.objects(None, er.legacyRepository)})
    comps: dict[str, str] = {}
    for c in g.subjects(RDF.type, er.Component):
        repo = g.value(c, er.repository)
        if repo is not None:
            comps[str(repo)] = str(g.value(c, er.commitSha) or "")
    return legacy, comps


def archive(repo: Path, sha: str, paths: list[str], dest: Path) -> None:
    blob = subprocess.run(["git", "--no-optional-locks", "-C", str(repo), "archive", "--format=tar", sha, "--", *paths],
                          capture_output=True)
    if blob.returncode != 0:
        raise ObservationError(f"git archive {sha} in {repo}: {blob.stderr.decode(errors='replace').strip()[-240:]}")
    tar = subprocess.run(["tar", "-x", "-f", "-", "-C", str(dest)], input=blob.stdout, capture_output=True)
    if tar.returncode != 0:
        raise ObservationError(f"tar -x: {tar.stderr.decode(errors='replace').strip()[-240:]}")


def observe(subject: Path, xaas_repo: Path) -> str:
    """Return the Turtle bytes (as text) of the court-reference observation for `subject`."""
    for rel in ("release.ttl", LEGACY_IMPORT):
        if not (subject / rel).is_file():
            raise ObservationError(f"{subject / rel} absent")
    legacy, comps = subject_graph(subject)
    sha = comps.get(COURTS_REPOSITORY, "")
    if not SHA40.match(sha):
        raise ObservationError(f"release.ttl names no 40-hex er:commitSha for a {COURTS_REPOSITORY} component")
    probe = subprocess.run(["git", "--no-optional-locks", "-C", str(xaas_repo), "cat-file", "-e", f"{sha}^{{commit}}"],
                           capture_output=True)
    if probe.returncode != 0:
        raise ObservationError(f"{xaas_repo} holds no commit {sha}")
    repos = sorted(set(legacy) | set(comps))
    with tempfile.TemporaryDirectory(prefix="ce23-2-courtrefs.") as tmp:
        root = Path(tmp)
        archive(xaas_repo, sha, [MATRIX_PATH, COURTS_PATH], root)
        spec = importlib.util.spec_from_file_location("ce23_2_fleet_matrix", root / MATRIX_PATH)
        if spec is None or spec.loader is None:
            raise ObservationError(f"{MATRIX_PATH} at {sha} is not importable")
        matrix = importlib.util.module_from_spec(spec)
        sys.dont_write_bytecode = True
        spec.loader.exec_module(matrix)
        courts = root / COURTS_PATH
        scripts = sorted(p.name for p in courts.glob("*.sh"))
        hits: dict[str, list[str]] = {}
        for slug in repos:
            name = slug.rsplit("/", 1)[-1]
            found = set(matrix.court_references(str(courts), {"name": name, "path": None}))
            absolute = re.compile(r"/(?:Users|home)/[A-Za-z0-9_.-]+/" + re.escape(name) + r"(?![A-Za-z0-9_.-])")
            for script in scripts:
                if absolute.search((courts / script).read_text(encoding="utf-8", errors="replace")):
                    found.add(script)
            hits[slug] = sorted(found)
    base = f"https://github.com/{COURTS_REPOSITORY}/blob/{sha}/{COURTS_PATH}/"
    by_script: dict[str, list[str]] = {}
    for slug, names in hits.items():
        for script in names:
            by_script.setdefault(script, []).append(slug)
    q = lambda s: '"' + s.replace("\\", "\\\\").replace('"', '\\"') + '"'  # noqa: E731
    out = [
        f"@prefix er: <{ER}> .",
        "",
        "# GENERATED by release/v26.9.23/courts/ce23_2/observe_court_refs.py (CE23-2); do not hand-edit.",
        f"# Observation, not a decision: fleet_matrix.court_references() of {COURTS_REPOSITORY}@{sha}",
        f"# ({MATRIX_PATH} at that commit, read-only; path None, unioned with a home-agnostic",
        f"# absolute checkout path) over the {len(scripts)} court scripts {COURTS_PATH}/*.sh at that",
        f"# commit, for {len(repos)} repositories: the {len(legacy)} components of the predecessor release",
        f"# ({LEGACY_IMPORT}) and the {len(comps)} components of release.ttl.",
        f"# Court scripts: {', '.join(scripts)}",
        "# Probed repositories (court scripts that execute the checkout):",
    ]
    out += [f"#   {slug}: [{', '.join(hits[slug])}]" for slug in repos]
    for script in sorted(by_script):
        objs = ", ".join(q(s) for s in sorted(by_script[script]))
        out.append(f"<{base}{script}> er:courtReferencesComponent {objs} .")
    return "\n".join(out) + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--subject", type=Path, required=True, help="the release sub-project (release/v26.9.23)")
    parser.add_argument("--xaas-repo", type=Path,
                        default=Path(os.environ.get("CE23_REPO_XAAS") or (Path.home() / "xaas")).expanduser())
    args = parser.parse_args(argv)
    try:
        sys.stdout.write(observe(args.subject, args.xaas_repo))
    except ObservationError as exc:
        print(f"UNKNOWN[OBSERVATION_INPUT_ABSENT] {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
