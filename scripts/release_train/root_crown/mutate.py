"""Mutation harness for the root crown (stdlib only; in-process; no child processes).

Two kinds of mutant, both judged by the real courts:

* **source** mutants: one anchored edit to one court source file (``anchor`` must occur
  exactly once, else ``REFUSED:ANCHOR_DRIFT``, exit 2). The edit is applied inside a
  ``TemporaryDirectory`` copy of ``COPY_PATHS``; the named killer test modules are then run
  in-process (``unittest``) against the copy, with ``sys.modules``/``sys.path``/cwd isolated
  and restored. The mutant is *killed* when at least one killer test fails or errors.
* **data** mutants: ``build(env)`` feeds the unmodified courts a mutated input and a clean
  control; the mutant is *killed* when the court emits the ``expected`` token on the mutated
  input and does not emit it on the control (anti-vacuity).

Before any mutant runs, the whole suite ``TEST_DIR`` must be green on the pristine copy,
else ``REFUSED:BASELINE_RED`` (exit 2): a red baseline cannot kill anything lawfully.
``ROOT_CROWN_SUBJECT_TREE`` is removed from the environment for the whole run so the
report does not depend on whether a tag subject happens to be materialized.

Output: ``{schema, baseline, mutants{name:{kind,killed,detail,...}}, all_killed, survivors}``.
Exit 0 every mutant killed, 1 a survivor, 2 refusal (ANCHOR_DRIFT, BASELINE_RED,
MUTATION_REPORT_DRIFT, usage). ``--write-report`` writes the canonical report;
``--check-report`` recomputes it and refuses any byte difference.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import importlib
import io
import json
import os
import shutil
import sys
import tempfile
import unittest
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterator

REPO = Path(__file__).resolve().parents[3]
RELEASE = "v26.9.25"
SCHEMA_REPORT = "https://chatman.dev/root-crown/hardening/mutation-report/v1"
REPORT = f"release/{RELEASE}/hardening/inputs/mutation-report.json"
TEST_DIR = "tests/release_train/root_crown"
COPY_PATHS = (
    "scripts",
    TEST_DIR,
    "release/v26.9.24",
    f"release/{RELEASE}",
    f"docs/jira/{RELEASE}",
)
SUBJECT_ENV = "ROOT_CROWN_SUBJECT_TREE"
# Harness refusals (typed per RFC-0004 §39 + Chatman broken_term).
HARNESS_CODES = {
    "ANCHOR_DRIFT": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "BASELINE_RED": ("VERIFICATION_FAILURE", "admission_vacuous"),
    "MUTATION_REPORT_DRIFT": ("EVIDENCE_FAILURE", "R_missing_replay"),
}
MAX_DETAIL_TESTS = 6


class HarnessRefusal(Exception):
    def __init__(self, code: str, detail: str) -> None:
        super().__init__(f"REFUSED:{code}:{detail}")
        self.code = code
        self.detail = detail

    def as_dict(self) -> dict[str, Any]:
        cls, term = HARNESS_CODES[self.code]
        return {"refusal": str(self), "code": self.code, "failure_class": cls, "broken_term": term}


@dataclass(frozen=True)
class SourceMutant:
    name: str
    file: str
    anchor: str
    replacement: str
    killers: tuple[str, ...]
    rule: str = ""


@dataclass(frozen=True)
class DataMutant:
    name: str
    build: Callable[["Env"], tuple[list[str], list[str]]]  # (control emitted, mutant emitted)
    expected: str
    rule: str = ""


@dataclass
class Env:
    """Modules of the pristine copy, imported inside the isolation context."""

    root: Path
    modules: dict[str, Any] = field(default_factory=dict)

    def __getattr__(self, name: str) -> Any:
        try:
            return self.modules[name]
        except KeyError as exc:
            raise AttributeError(name) from exc


# ------------------------------------------------------------------ isolation


def _tops(paths: tuple[str, ...]) -> set[str]:
    return {p.split("/")[0] for p in paths}


@contextmanager
def isolated(copy_root: Path, test_dir: Path, tops: set[str]) -> Iterator[None]:
    """Import only from ``copy_root``; restore modules, path, cwd, env and bytecode flag."""

    def owned(name: str) -> bool:
        return name.split(".")[0] in tops or name == "_support" or name.startswith("test_")

    def foreign(entry: str) -> bool:
        base = Path(entry or ".").resolve()
        return any((base / top).exists() for top in tops)

    saved_modules = {k: v for k, v in sys.modules.items() if owned(k)}
    saved_path = list(sys.path)
    saved_cwd = os.getcwd()
    saved_bytecode = sys.dont_write_bytecode
    saved_env = os.environ.pop(SUBJECT_ENV, None)
    sink = io.StringIO()  # courts and CLI tests print; the report is the only output
    for name in saved_modules:
        del sys.modules[name]
    sys.path[:] = [str(test_dir), str(copy_root)] + [p for p in saved_path if not foreign(p)]
    sys.dont_write_bytecode = True
    os.chdir(copy_root)
    importlib.invalidate_caches()
    try:
        with redirect_stdout(sink), redirect_stderr(sink):
            yield
    finally:
        for name in [k for k in sys.modules if owned(k)]:
            del sys.modules[name]
        sys.modules.update(saved_modules)
        sys.path[:] = saved_path
        os.chdir(saved_cwd)
        sys.dont_write_bytecode = saved_bytecode
        if saved_env is not None:
            os.environ[SUBJECT_ENV] = saved_env
        importlib.invalidate_caches()


def _copy(root: Path, dest: Path, paths: tuple[str, ...]) -> None:
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for rel in paths:
        src = root / rel
        if src.is_dir():
            shutil.copytree(src, dest / rel, ignore=ignore, symlinks=True)
        elif src.is_file():
            (dest / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dest / rel)


def _run_tests(suite: unittest.TestSuite) -> dict[str, Any]:
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=0).run(suite)
    failed = sorted({t.id() for t, _ in result.failures + result.errors})
    return {
        "tests_run": result.testsRun,
        "failures": len(result.failures),
        "errors": len(result.errors),
        "skipped": len(result.skipped),
        "ok": result.wasSuccessful(),
        "failed_tests": failed,
    }


def _discover(test_dir: Path) -> unittest.TestSuite:
    return unittest.TestLoader().discover(str(test_dir), pattern="test_*.py", top_level_dir=str(test_dir))


def _load(modules: tuple[str, ...]) -> unittest.TestSuite:
    loader = unittest.TestLoader()
    return unittest.TestSuite(loader.loadTestsFromName(m) for m in modules)


def anchor_refusals(root: Path, mutants: tuple[SourceMutant, ...]) -> list[str]:
    out = []
    for m in mutants:
        path = root / m.file
        count = path.read_text(encoding="utf-8").count(m.anchor) if path.is_file() else -1
        if count != 1:
            out.append(f"{m.name}:{m.file}:anchor-count={count}")
    return out


# ------------------------------------------------------------------ run


def run(
    root: Path = REPO,
    *,
    paths: tuple[str, ...] = COPY_PATHS,
    test_dir: str = TEST_DIR,
    source: tuple[SourceMutant, ...] | None = None,
    data: tuple[DataMutant, ...] | None = None,
    env_modules: tuple[str, ...] = (),
) -> dict[str, Any]:
    """Run every mutant against a temp copy of ``root``; raise HarnessRefusal on refusal."""
    source = SOURCE_MUTANTS if source is None else source
    data = DATA_MUTANTS if data is None else data
    names = [m.name for m in source] + [m.name for m in data]
    if len(set(names)) != len(names):
        raise HarnessRefusal("ANCHOR_DRIFT", "duplicate mutant names")
    drift = anchor_refusals(root, source)
    if drift:
        raise HarnessRefusal("ANCHOR_DRIFT", ",".join(drift))
    tops = _tops(paths)
    mutants: dict[str, dict[str, Any]] = {}
    with tempfile.TemporaryDirectory(prefix="root-crown-mutate-") as tmp:
        copy_root = Path(tmp).resolve()
        _copy(root, copy_root, paths)
        # The report never judges itself: the copy's baseline is the same with or without it.
        (copy_root / REPORT).unlink(missing_ok=True)
        tests = copy_root / test_dir
        with isolated(copy_root, tests, tops):
            baseline = _run_tests(_discover(tests))
        if not baseline["ok"]:
            raise HarnessRefusal("BASELINE_RED", ",".join(baseline["failed_tests"][:MAX_DETAIL_TESTS]))
        for m in source:
            target = copy_root / m.file
            original = target.read_bytes()
            text = original.decode("utf-8")
            target.write_text(text.replace(m.anchor, m.replacement, 1), encoding="utf-8")
            try:
                with isolated(copy_root, tests, tops):
                    outcome = _run_tests(_load(m.killers))
            finally:
                target.write_bytes(original)
            killed = not outcome["ok"]
            failed = outcome["failed_tests"]
            detail = (
                f"killed by {len(failed)} test(s): " + ",".join(failed[:MAX_DETAIL_TESTS])
                if killed
                else f"SURVIVED: {outcome['tests_run']} killer test(s) green"
            )
            mutants[m.name] = {
                "kind": "source",
                "file": m.file,
                "rule": m.rule,
                "killers": list(m.killers),
                "killed": killed,
                "detail": detail,
            }
        if data:
            with isolated(copy_root, tests, tops):
                env = Env(copy_root)
                for mod in ("_support",) + DATA_ENV_MODULES + env_modules:
                    env.modules[mod.rsplit(".", 1)[-1]] = importlib.import_module(mod)
                for dm in data:
                    try:
                        control, emitted = dm.build(env)
                        hit = any(dm.expected in s for s in emitted)
                        leak = any(dm.expected in s for s in control)
                        killed = hit and not leak
                        detail = (
                            f"court emitted {dm.expected!r}; control clean"
                            if killed
                            else f"SURVIVED: mutant_emitted={hit} control_emitted={leak}"
                        )
                    except Exception as exc:  # noqa: BLE001 — a crashing court is a survivor, typed
                        killed, detail = False, f"SURVIVED: court raised {type(exc).__name__}"
                    mutants[dm.name] = {"kind": "data", "rule": dm.rule, "expected": dm.expected, "killed": killed, "detail": detail}
    survivors = sorted(n for n, v in mutants.items() if not v["killed"])
    files = sorted({m.file for m in source})
    return {
        "GENERATED": "scripts/release_train/root_crown/mutate.py -- do not edit; run --write-report",
        "schema": SCHEMA_REPORT,
        "release": RELEASE,
        "source_digests": {f: "sha256:" + hashlib.sha256((root / f).read_bytes()).hexdigest() for f in files},
        "baseline": {k: v for k, v in baseline.items() if k != "failed_tests"},
        "mutants": dict(sorted(mutants.items())),
        "total": len(mutants),
        "killed": len(mutants) - len(survivors),
        "all_killed": not survivors,
        "survivors": survivors,
        "authority": "NONE",
    }


def dump(report: dict[str, Any]) -> bytes:
    return (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8")


# ------------------------------------------------------------------ source mutants

EVIDENCE = "scripts/release_train/root_crown/evidence.py"
CROWN = "scripts/release_train/root_crown/crown.py"
POSTTAG = "scripts/release_train/root_crown/posttag.py"
CHAIN = "scripts/release_train/root_crown/chain.py"
REPLAY = "scripts/release_train/root_crown/replay.py"
GITOBJ = "scripts/release_train/root_crown/gitobj.py"
POLICY = "scripts/release_train/root_crown/policy.py"
BINDING = "scripts/release_train/root_crown/binding.py"
MODEL = "scripts/release_train/root_crown/model.py"

T_TYPED = "test_typed_terminal"
T_ALIGN = "test_terminal_alignment"
T_CROWN = "test_crown"
T_FALS = "test_falsifiers"
T_POST = "test_post_tag"
T_CHAIN = "test_chain"
T_REPLAY = "test_replay"
T_GITOBJ = "test_gitobj"
T_POLICY = "test_policy"
T_BINDING = "test_binding"

SOURCE_MUTANTS: tuple[SourceMutant, ...] = (
    # --- the five audit survivors (each killed by a new test in test_typed_terminal) ---------
    SourceMutant(
        "owner_off",
        EVIDENCE,
        '    if not (isinstance(owner, str) and owner.strip()):\n        gaps.append("owner")',
        '    if False:\n        gaps.append("owner")',
        (T_TYPED,),
        "BLOCKED_WITHOUT_TYPE(missing=owner)",
    ),
    SourceMutant(
        "successor_off",
        EVIDENCE,
        '            gaps.append("successor")',
        "            pass",
        (T_TYPED,),
        "BLOCKED_WITHOUT_TYPE(missing=successor)",
    ),
    SourceMutant(
        "type_off",
        EVIDENCE,
        '    if not str(type_text).strip():\n        gaps.append("type")',
        '    if False:\n        gaps.append("type")',
        (T_TYPED,),
        "BLOCKED_WITHOUT_TYPE(missing=type)",
    ),
    SourceMutant(
        "terminal_accepts_partial",
        EVIDENCE,
        "    if standing in SUCCESS_TERMINAL and policy_row.admits(standing):",
        '    if standing in SUCCESS_TERMINAL | {"PARTIAL_ALIVE"}:',
        (T_TYPED,),
        "AC-15 PARTIAL_ALIVE is not terminal (ARTIFACT_BLOCKED)",
    ),
    SourceMutant(
        "typed_terminal_blocked_as_capability",
        EVIDENCE,
        "    if standing in TYPED_TERMINAL and policy_row.admits(standing):",
        "    if standing in NON_TERMINAL_IMPL or (standing in TYPED_TERMINAL and policy_row.admits(standing)):",
        (T_TYPED,),
        "AC-15 typed PLANNED is not a terminal disposition (ARTIFACT_BLOCKED)",
    ),
    # --- rebuilt mutants ---------------------------------------------------------------------
    SourceMutant(
        "broken_term_off",
        EVIDENCE,
        "    if not terms & set(BROKEN_TERMS):",
        "    if False:",
        (T_ALIGN, T_TYPED),
        "BLOCKED_WITHOUT_TYPE(missing=broken_term)",
    ),
    SourceMutant(
        "failure_class_off",
        EVIDENCE,
        "    if not classes & set(FAILURE_CLASSES):",
        "    if False:",
        (T_ALIGN, T_TYPED),
        "BLOCKED_WITHOUT_TYPE(missing=failure_class)",
    ),
    SourceMutant(
        "required_unknown_off",
        EVIDENCE,
        '    if standing == "UNKNOWN" and req.required:',
        "    if False:",
        (T_ALIGN, T_CROWN),
        "REQUIRED_UNKNOWN",
    ),
    SourceMutant(
        "untyped_closure_accepted",
        EVIDENCE,
        '    if untyped:\n        return REFUSED("SUBJECT_NOT_TERMINAL"',
        '    if False:\n        return REFUSED("SUBJECT_NOT_TERMINAL"',
        (T_ALIGN,),
        "SUBJECT_NOT_TERMINAL(untyped)",
    ),
    SourceMutant(
        "non_terminal_impl_accepted",
        EVIDENCE,
        '            if label == "impl" and state in NON_TERMINAL_IMPL:',
        "            if False:",
        (T_ALIGN,),
        "CLOSURE_PARTIAL",
    ),
    SourceMutant(
        "lineage_bad_accepted",
        EVIDENCE,
        '    if status in LINEAGE_BAD:\n        return REFUSED("ARTIFACT_SUBJECT_SPLIT"',
        '    if False:\n        return REFUSED("ARTIFACT_SUBJECT_SPLIT"',
        (T_ALIGN, T_CROWN),
        "ARTIFACT_SUBJECT_SPLIT",
    ),
    SourceMutant(
        "crown_sha_split_off",
        CROWN,
        '    if mode == "PRE_TAG" and root_obs.get("head_sha") and root_obs["head_sha"] != crown_sha:',
        "    if False:",
        (T_CROWN, T_POST),
        "CROWN_SHA_SPLIT",
    ),
    SourceMutant(
        "tag_split_off",
        EVIDENCE,
        '    if tag["sha"] != ctx.crown_sha:',
        "    if False:",
        (T_CROWN, T_FALS, T_POST),
        "TAG_SHA_SPLIT",
    ),
    SourceMutant(
        "chain_digest_unchecked",
        CROWN,
        '        if not verify_receipt(previous) or previous.get("release") != release_dir.name:',
        "        if False:",
        (T_CROWN, "test_loop"),
        "RECEIPT_CHAIN_BROKEN(previous digest)",
    ),
    # --- one disable-mutant per PR-1 / crown rule ----------------------------------------------
    SourceMutant(
        "tag_object_digest_off",
        GITOBJ,
        "            if actual != sha:",
        "            if False:",
        (T_GITOBJ, T_POST),
        "TAG_OBJECT_DIGEST_MISMATCH",
    ),
    SourceMutant(
        "tag_mutated_off",
        POSTTAG,
        '        elif tag.get("object_sha") != record["tag"]["object_sha"]:',
        "        elif False:",
        (T_POST,),
        "TAG_MUTATED(object)",
    ),
    SourceMutant(
        "tag_deleted_off",
        POSTTAG,
        '        if tag.get("sha") is None:\n            refusals.append(',
        "        if False:\n            refusals.append(",
        (T_POST,),
        "TAG_MUTATED(deleted)",
    ),
    SourceMutant(
        "tag_binding_mutated_off",
        POSTTAG,
        '            if tag.get("sha") is None or (tag.get("object_sha") not in (None, record["tag"]["object_sha"])):',
        '            if tag.get("sha") is None:',
        (T_POST,),
        "TAG_MUTATED(post-tag binding)",
    ),
    SourceMutant(
        "tag_subject_split_off",
        POSTTAG,
        '        if tag.get("sha") != record["subject"]["commit_sha"]:\n            refusals.append(',
        "        if False:\n            refusals.append(",
        (T_POST,),
        "TAG_SUBJECT_SPLIT",
    ),
    SourceMutant(
        "tag_binding_subject_split_off",
        POSTTAG,
        '            if tag.get("sha") != record["subject"]["commit_sha"]:\n                return REFUSED',
        "            if False:\n                return REFUSED",
        (T_POST,),
        "TAG_SUBJECT_SPLIT(post-tag binding)",
    ),
    SourceMutant(
        "record_section_unchecked",
        POSTTAG,
        "        if record.get(section) != recomputed.get(section):",
        "        if False:",
        (T_TYPED, T_POST),
        "TAG_RECEIPT_SPLIT/TAG_SUBJECT_SPLIT(record vs raw objects)",
    ),
    SourceMutant(
        "historical_receipt_digest_off",
        POSTTAG,
        '    if crown.receipt_digest_of(receipt) != ref["receipt_digest"]:',
        "    if False:",
        (T_TYPED, T_POST),
        "TAG_RECEIPT_SPLIT(historical)",
    ),
    SourceMutant(
        "subject_tree_off",
        POSTTAG,
        "        if actual != expected:",
        "        if False:",
        (T_POST, T_TYPED),
        "SUBJECT_TREE_MISMATCH",
    ),
    SourceMutant(
        "historical_observation_split_off",
        POSTTAG,
        '    if observed_digest != receipt.get("observations_digest"):',
        "    if False:",
        (T_POST,),
        "HISTORICAL_OBSERVATION_SPLIT",
    ),
    SourceMutant(
        "payload_mutated_off",
        POSTTAG,
        '    if actual != payload["tree_sha"]:',
        "    if False:",
        (T_POST,),
        "PAYLOAD_MUTATED_POST_TAG",
    ),
    SourceMutant(
        "replay_diverged_off",
        REPLAY,
        "        if got != expected_digest:",
        "        if False:",
        (T_REPLAY,),
        "REPLAY_DIVERGED",
    ),
    SourceMutant(
        "parent_digest_off",
        CHAIN,
        '        if recomputed != receipt.get("receipt_digest") or recomputed != entry.get("receipt_digest"):',
        "        if False:",
        (T_CHAIN,),
        "RECEIPT_CHAIN_BROKEN:PARENT_DIGEST",
    ),
    SourceMutant(
        "parent_refused_off",
        CHAIN,
        '    if parent.get("standing") == "REFUSED":',
        "    if False:",
        (T_CHAIN,),
        "RECEIPT_CHAIN_BROKEN:PARENT_REFUSED",
    ),
    SourceMutant(
        "parent_untyped_blocked_off",
        CHAIN,
        '    elif parent.get("standing") == "BLOCKED" and _untyped(parent):',
        "    elif False:",
        (T_CHAIN,),
        "RECEIPT_CHAIN_BROKEN:PARENT_UNTYPED_BLOCKED",
    ),
    SourceMutant(
        "parent_not_ancestor_off",
        CHAIN,
        '    elif parent.get("crown_sha") not in ancestry:',
        "    elif False:",
        (T_CHAIN,),
        "RECEIPT_CHAIN_BROKEN:PARENT_NOT_ANCESTOR",
    ),
    SourceMutant(
        "verifier_crashed_off",
        CROWN,
        "    except Exception as exc:  # noqa: BLE001 — containment is the point",
        "    except ArithmeticError as exc:  # mutant: containment narrowed",
        (T_CROWN,),
        "VERIFIER_CRASHED",
    ),
    SourceMutant(
        "gitobj_exec_bit_off",
        GITOBJ,
        "            mode = MODE_EXEC if st.st_mode & stat.S_IXUSR else MODE_FILE",
        "            mode = MODE_FILE",
        (T_GITOBJ,),
        "git tree mode 100755",
    ),
    SourceMutant(
        "blocked_without_type_off",
        CROWN,
        '        if state.state in {"BLOCKED", "UNKNOWN"} and (not state.code or state.code not in FAILURE_CLASS):',
        "        if False:",
        (T_CROWN,),
        "BLOCKED_WITHOUT_TYPE(crown)",
    ),
    SourceMutant(
        "f09_type_off",
        EVIDENCE,
        '        return _typed_terminal(req, ctx, data, is_local, standing, (inline_type, inline_term), f09_row, "RFC §55")',
        '        return PASS(f"typed blocker {data.get(\'type\')} (RFC §55)", data.get("subject_sha"))',
        (T_FALS, T_ALIGN),
        "BLOCKED_WITHOUT_TYPE(F-09)",
    ),
    SourceMutant(
        "worktree_stale_off",
        EVIDENCE,
        "    if now - seen > WORKTREE_FRESHNESS:",
        "    if False:",
        (T_TYPED, T_CROWN),
        "OBSERVATION_STALE(AC-09)",
    ),
    # --- PR-3 terminality policy + owner rule: one disable-mutant per rule ---------------------
    SourceMutant(
        "policy_admission_ignored",
        EVIDENCE,
        "    if standing in TYPED_TERMINAL and policy_row.admits(standing):",
        "    if standing in TYPED_TERMINAL:",
        (T_ALIGN,),
        "capability ACs admit ALIVE only (ARTIFACT_BLOCKED)",
    ),
    SourceMutant(
        "f09_required_unknown_off",
        EVIDENCE,
        '    if req.required and standing == "UNKNOWN":',
        "    if False:",
        (T_ALIGN,),
        "REQUIRED_UNKNOWN(F-09)",
    ),
    SourceMutant(
        "f09_policy_ignored",
        EVIDENCE,
        "    if standing in TYPED_TERMINAL and f09_row.admits(standing):",
        "    if standing in TYPED_TERMINAL:",
        (T_ALIGN,),
        "F-09 admits BLOCKED/UNSUPPORTED only (ARTIFACT_BLOCKED)",
    ),
    SourceMutant(
        "closure_policy_ignored",
        EVIDENCE,
        "                if not policy_row.admits(state):",
        "                if False:",
        (T_ALIGN,),
        "CLOSURE_PARTIAL(not-admitted-by-policy)",
    ),
    SourceMutant(
        "receipt_policy_refusal_dropped",
        EVIDENCE,
        "    if refusal is not None:\n        return refusal\n    assert policy_row is not None\n    data, blocker",
        "    if False:\n        return refusal\n    assert policy_row is not None\n    data, blocker",
        (T_POLICY,),
        "TERMINALITY_POLICY_MISSING / ACCEPTANCE_DRIFT (receipt_artifact)",
    ),
    SourceMutant(
        "closure_owner_split_off",
        EVIDENCE,
        '    if splits:\n        return REFUSED("OWNER_SPLIT"',
        '    if False:\n        return REFUSED("OWNER_SPLIT"',
        (T_POLICY,),
        "OWNER_SPLIT(closure row)",
    ),
    SourceMutant(
        "owner_split_off",
        EVIDENCE,
        "        if wrong:\n",
        "        if False:\n",
        (T_POLICY, T_TYPED),
        "OWNER_SPLIT(receipt)",
    ),
    SourceMutant(
        "owner_container_default_off",
        EVIDENCE,
        '        return container, "container", None',
        '        return None, "absent", None',
        (T_POLICY, T_TYPED),
        "owner_source=container",
    ),
    SourceMutant(
        "bound_detail_says_alive",
        EVIDENCE,
        '    return _admitted(ctx, bound, f"{req.evidence_locator} {standing} at {subject} ({status})", subject)',
        '    return _admitted(ctx, bound, f"{req.evidence_locator} ALIVE at {subject} ({status})", subject)',
        (T_ALIGN, T_POLICY),
        "_bound detail names the receipt standing",
    ),
    SourceMutant(
        "crown_policy_validation_off",
        CROWN,
        "    refusals += ctx.policy_refusals()",
        "    pass",
        (T_POLICY,),
        "POLICY_COVERAGE_GAP(crown, non-consulting requirement)",
    ),
    SourceMutant(
        "policy_release_unchecked",
        POLICY,
        '    if doc.get("release") != release:',
        "    if False:",
        (T_POLICY,),
        "TERMINALITY_POLICY_MISSING(other release)",
    ),
    SourceMutant(
        "acceptance_drift_off",
        POLICY,
        "    if sha256_text(acceptance) != row.acceptance_sha256:",
        "    if False:",
        (T_POLICY,),
        "ACCEPTANCE_DRIFT",
    ),
    SourceMutant(
        "relaxation_phrase_unchecked",
        POLICY,
        "        elif row.rfc_phrase not in section:",
        "        elif False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(phrase not in anchor)",
    ),
    SourceMutant(
        "relaxation_own_line_unchecked",
        POLICY,
        "        elif (line := own_line(rid, row.rfc_anchor, section)) is not None and row.rfc_phrase not in line:",
        "        elif False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(borrowed phrase)",
    ),
    SourceMutant(
        "relaxation_marker_off",
        POLICY,
        "        if not any(marker in row.rfc_phrase for marker in RELAXATION_MARKERS):",
        "        if False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(no terminality marker)",
    ),
    SourceMutant(
        "relaxation_ceiling_off",
        POLICY,
        '        if row.standing_ceiling != "TERMINAL":',
        "        if False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(ceiling ALIVE)",
    ),
    SourceMutant(
        "success_ceiling_off",
        POLICY,
        '    elif row.standing_ceiling != "ALIVE":',
        "    elif False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(success row ceiling)",
    ),
    SourceMutant(
        "rfc_import_digest_off",
        POLICY,
        "        if text_sha != policy.rfc_import_sha256 or (import_sha256 is not None and import_sha256 != text_sha):",
        "        if False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(rfc import digest)",
    ),
    SourceMutant(
        "non_terminal_state_admitted",
        POLICY,
        "    if foreign:",
        "    if False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(non-terminal state)",
    ),
    SourceMutant(
        "missing_row_unreported",
        POLICY,
        '            refusals.append(f"REFUSED:POLICY_COVERAGE_GAP:{req[\'id\']}:no-policy-row")',
        "            pass",
        (T_POLICY,),
        "POLICY_COVERAGE_GAP(no row)",
    ),
    SourceMutant(
        "duplicate_row_admitted",
        POLICY,
        "    if len(raws) != 1:",
        "    if not raws:",
        (T_POLICY,),
        "POLICY_COVERAGE_GAP(duplicate row)",
    ),
    SourceMutant(
        "shared_grounding_admitted",
        POLICY,
        "        if len(cited_by) > 1:",
        "        if False:",
        (T_POLICY,),
        "POLICY_RELAXATION_UNGROUNDED(one grounding, several relaxations)",
    ),
    # --- evidence binding (PR-4): one disable-mutant per binding rule + the wiring sites
    SourceMutant(
        "binding_not_durable_admitted",
        BINDING,
        "    if not is_durable(binding.evidence_locator):",
        "    if False:",
        (T_BINDING,),
        "EVIDENCE_NOT_DURABLE",
    ),
    SourceMutant(
        "binding_mutable_subject_admitted",
        BINDING,
        "        if not (isinstance(value, str) and HEX40.fullmatch(value)):",
        "        if False:",
        (T_BINDING,),
        "EVIDENCE_SUBJECT_MUTABLE",
    ),
    SourceMutant(
        "binding_container_claims_subject_admitted",
        BINDING,
        "        if subject == container or (foreign and subject == crown_sha):",
        "        if False:",
        (T_BINDING,),
        "EVIDENCE_CONTAINER_CLAIMS_SUBJECT",
    ),
    SourceMutant(
        "binding_split_admitted",
        BINDING,
        "    if status in LINEAGE_BAD:",
        "    if False:",
        (T_BINDING,),
        "EVIDENCE_SUBJECT_SPLIT",
    ),
    SourceMutant(
        "binding_lineage_missing_admitted",
        BINDING,
        '    if status not in LINEAGE_OK or proof.get("delta_paths") is None:',
        "    if False:",
        (T_BINDING, T_POST),
        "EVIDENCE_LINEAGE_MISSING",
    ),
    SourceMutant(
        "binding_misclaim_admitted",
        BINDING,
        '    if proof.get("delta_class") != computed:',
        "    if False:",
        (T_BINDING,),
        "EVIDENCE_DELTA_MISCLAIMED",
    ),
    SourceMutant(
        "binding_unbounded_inherited",
        BINDING,
        '    if computed == "UNBOUNDED":',
        "    if False:",
        (T_BINDING, T_POST, T_POLICY),
        "EVIDENCE_DELTA_UNBOUNDED",
    ),
    SourceMutant(
        "binding_content_digest_unchecked",
        BINDING,
        "    if content is not None and binding.evidence_digest != sha256_tag(content):",
        "    if False:",
        (T_BINDING,),
        "EVIDENCE_DIGEST_MISMATCH(bytes)",
    ),
    SourceMutant(
        "binding_self_digest_unchecked",
        BINDING,
        "    if binding.binding_digest != binding.computed_digest():",
        "    if False:",
        (T_BINDING,),
        "EVIDENCE_DIGEST_MISMATCH(binding)",
    ),
    SourceMutant(
        "binding_traversal_admitted",
        BINDING,
        '    if any(s in ("", ".", "..") for s in segments):',
        "    if False:",
        (T_BINDING,),
        "classify_delta(traversal)",
    ),
    SourceMutant(
        "binding_deny_extension_ignored",
        BINDING,
        '    if any(lowered.endswith(ext) for ext in allowlist.get("deny_extensions", [])):',
        "    if False:",
        (T_BINDING,),
        "classify_delta(deny_extensions)",
    ),
    SourceMutant(
        "binding_deny_segment_ignored",
        BINDING,
        '    if set(segments) & set(allowlist.get("deny_segments", [])):',
        "    if False:",
        (T_BINDING,),
        "classify_delta(deny_segments)",
    ),
    SourceMutant(
        "binding_glob_star_crosses_segments",
        BINDING,
        '            out.append("[^/]*")',
        '            out.append(".*")',
        (T_BINDING,),
        "classify_delta(* is one segment)",
    ),
    SourceMutant(
        "binding_admission_bypassed",
        EVIDENCE,
        "    refusal = binding.admit(bound, crown_sha=ctx.crown_sha, root_repository=ctx.container_repo, allowlist=ctx.allowlist)",
        "    refusal = None",
        (T_BINDING, T_POST, T_POLICY),
        "admit wired into every PASS",
    ),
    SourceMutant(
        "binding_remote_delta_dropped",
        EVIDENCE,
        '        delta_paths=observed.get("subject_delta_paths"),',
        "        delta_paths=[],",
        (T_BINDING, T_POST, T_POLICY),
        "observed delta reaches the binding",
    ),
    SourceMutant(
        "binding_new_head_exemption_widened",
        CROWN,
        '            in_tree = bound is not None and bound.kind == "IN_TREE_DERIVED" and state.subject_sha == crown_sha',
        "            in_tree = state.subject_sha == crown_sha",
        (T_BINDING,),
        "NEW_HEAD exemption only for IN_TREE_DERIVED",
    ),
    SourceMutant(
        "binding_dropped_from_receipt",
        MODEL,
        '            "binding": None if self.binding is None else self.binding.as_dict(),',
        '            "binding": None,',
        (T_BINDING, T_POST),
        "ReqState.binding in as_dict v2",
    ),
    SourceMutant(
        "binding_post_tag_deltas_ignored",
        POSTTAG,
        "        with_deltas(observations, hardening)",
        "        observations",
        (T_POST,),
        "committed delta observations reach the current evaluation",
    ),
)


# ------------------------------------------------------------------ data mutants (§4 mission list)

DATA_ENV_MODULES = (
    "scripts.release_train.root_crown.crown",
    "scripts.release_train.root_crown.evidence",
    "scripts.release_train.root_crown.posttag",
    "scripts.release_train.root_crown.replay",
    "scripts.release_train.root_crown.model",
    "scripts.release_train.root_crown.policy",
    "scripts.release_train.root_crown.binding",
    "scripts.release_train.release_closure_court.court",
)
TAG_OBJECT = "337e839937c247de4ee58b744c8b8e43950d18e3"
TAG_COMMIT = "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"
HIST_RUN = "receipts/run-36161744816"
PREV_RUN = "receipts/run-36160116076"
TYPED = "AUTHORITY_FAILURE:operator-repo-rename;R_missing_authority"


def _state(s: Any) -> list[str]:
    return [f"{s.state}:{s.code}:{s.detail}"]


def _verdict(v: Any) -> list[str]:
    return list(v.refusals) + [f"{r['state']}:{r['code']}:{r['id']}" for r in v.remaining]


def _alive(env: Env) -> tuple[Any, dict[str, Any]]:
    tree = env._support.alive_tree()
    return tree, env._support.alive_observations(tree)


def _req(tree: Any, rid: str) -> Any:
    return next(r for r in tree.inputs().requirements if r.id == rid)


def _ctx(env: Env, tree: Any, obs: dict[str, Any]) -> Any:
    return env.evidence.Context(
        root=tree.root, release_dir=tree.release_dir, observations=obs, crown_sha=env._support.CROWN_SHA, inputs=tree.inputs()
    )


def _remote_eval(env: Env, rid: str, **fields: Any) -> tuple[list[str], list[str]]:
    tree, obs = _alive(env)
    try:
        req = _req(tree, rid)
        control = _state(env.evidence.EVALUATORS[req.evidence_kind](req, _ctx(env, tree, obs)))
        mutated = copy.deepcopy(obs)
        artifact = mutated["artifacts"][req.evidence_locator]["json"]
        for key, value in fields.items():
            if value is None:
                artifact.pop(key, None)
            else:
                artifact[key] = value
        return control, _state(env.evidence.EVALUATORS[req.evidence_kind](req, _ctx(env, tree, mutated)))
    finally:
        tree.cleanup()


def _crown_eval(env: Env, mutate: Callable[[Any, dict[str, Any]], None]) -> tuple[list[str], list[str]]:
    tree, obs = _alive(env)
    try:
        control = _verdict(env.crown.evaluate(tree.release_dir, obs, None, env._support.CROWN_SHA, root=tree.root))
        mutated = copy.deepcopy(obs)
        mutate(tree, mutated)
        return control, _verdict(env.crown.evaluate(tree.release_dir, mutated, None, env._support.CROWN_SHA, root=tree.root))
    finally:
        tree.cleanup()


def dm_terminal_blocker_without_type(env: Env) -> tuple[list[str], list[str]]:
    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        loc = _req(tree, "AC-15").evidence_locator
        obs["artifacts"][loc]["json"].update(standing="BLOCKED")

    return _crown_eval(env, mutate)


def dm_terminal_blocker_without_reason(env: Env) -> tuple[list[str], list[str]]:
    return _remote_eval(env, "AC-15", standing="BLOCKED", type="operator-repo-rename")


def dm_terminal_blocker_without_owner(env: Env) -> tuple[list[str], list[str]]:
    """A typed disposition with no owner at all (no explicit owner, no container repository).

    Since PR-3 a receipt's container repository is its owner, so every real locator yields
    one; the typing court still names an absent owner.
    """

    def gaps(owner: Any) -> list[str]:
        return ["missing=" + "+".join(env.evidence.typing_gaps({}, "BLOCKED", type_text=TYPED, owner=owner))]

    return gaps("seanchatmangpt/zoela"), gaps(None)


def dm_terminal_blocker_foreign_owner(env: Env) -> tuple[list[str], list[str]]:
    """A terminal receipt in zoela claiming xaas as its owner (owner != container)."""

    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        loc = _req(tree, "AC-15").evidence_locator
        obs["artifacts"][loc]["json"].update(standing="BLOCKED", type=TYPED, owner="seanchatmangpt/xaas")

    return _crown_eval(env, mutate)


def dm_f09_superseded_as_blocker(env: Env) -> tuple[list[str], list[str]]:
    """RFC §55 admits a typed blocker, not a SUPERSEDED disposition, for the cloud runtime."""

    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        loc = _req(tree, "F-09").evidence_locator
        obs["artifacts"][loc]["json"].update(standing="SUPERSEDED", type=TYPED, successor="f" * 40)

    return _crown_eval(env, mutate)


def _crown_policy(env: Env, edit: Callable[[Any, dict[str, Any]], None]) -> tuple[list[str], list[str]]:
    """Crown over the ALIVE tree with the committed policy (control) and an edited copy (mutant)."""
    tree, obs = _alive(env)
    committed = json.loads(
        (env.root / "scripts/release_train/root_crown/policy" / RELEASE / "terminality.json").read_text(encoding="utf-8")
    )
    try:
        with tempfile.TemporaryDirectory() as tmp:
            control_root, mutant_root = Path(tmp) / "control", Path(tmp) / "mutant"
            env._support.dump(control_root / RELEASE / "terminality.json", committed)
            control = _verdict(
                env.crown.evaluate(
                    tree.release_dir, obs, None, env._support.CROWN_SHA, root=tree.root, policy_root=control_root
                )
            )
            doc = copy.deepcopy(committed)
            edit(tree, doc)
            if doc:
                env._support.dump(mutant_root / RELEASE / "terminality.json", doc)
            mutated = _verdict(
                env.crown.evaluate(
                    tree.release_dir, obs, None, env._support.CROWN_SHA, root=tree.root, policy_root=mutant_root
                )
            )
            return control, mutated
    finally:
        tree.cleanup()


def dm_policy_missing(env: Env) -> tuple[list[str], list[str]]:
    return _crown_policy(env, lambda tree, doc: doc.clear())


def dm_policy_coverage_gap(env: Env) -> tuple[list[str], list[str]]:
    def edit(tree: Any, doc: dict[str, Any]) -> None:
        doc["rows"] = [r for r in doc["rows"] if r["id"] != "F-09"]

    return _crown_policy(env, edit)


def dm_relaxation_ungrounded(env: Env) -> tuple[list[str], list[str]]:
    """AC-07 (a capability court) relaxed to admit a typed BLOCKED, grounded by its own line."""

    def edit(tree: Any, doc: dict[str, Any]) -> None:
        row = next(r for r in doc["rows"] if r["id"] == "AC-07")
        row.update(allowed_terminal_states=["ALIVE", "BLOCKED"], standing_ceiling="TERMINAL")

    return _crown_policy(env, edit)


def dm_acceptance_drift(env: Env) -> tuple[list[str], list[str]]:
    """AC-15's acceptance text restated without moving the policy."""

    def edit(tree: Any, doc: dict[str, Any]) -> None:
        path = tree.release_dir / "requirements.json"
        reqs = json.loads(path.read_text(encoding="utf-8"))
        next(r for r in reqs["requirements"] if r["id"] == "AC-15")["acceptance"] += " (restated)"
        env._support.dump(path, reqs)

    return _crown_policy(env, edit)


def dm_success_replaced_by_blocker(env: Env) -> tuple[list[str], list[str]]:
    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        loc = _req(tree, "AC-07").evidence_locator
        obs["artifacts"][loc]["json"].update(
            standing="BLOCKED", type="lane:court-unharvested;R_missing_consequence;EVIDENCE_FAILURE"
        )

    return _crown_eval(env, mutate)


def dm_subject_container_conflation(env: Env) -> tuple[list[str], list[str]]:
    """Evidence for a remote producer stamped with the container (crown) commit."""

    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        loc = _req(tree, "AC-07").evidence_locator
        obs["artifacts"][loc]["json"]["subject_sha"] = env._support.CROWN_SHA
        obs["artifacts"][loc]["subject_compare"] = "diverged"

    return _crown_eval(env, mutate)


def dm_stale_observation(env: Env) -> tuple[list[str], list[str]]:
    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        obs["local_worktrees"]["observed_at"] = "2026-09-24T12:59:59Z"  # 24h before observed_at

    return _crown_eval(env, mutate)


def _post_tag(env: Env) -> tuple[Any, Path, dict[str, Any]]:
    tree = env._support.committed_tree()
    hardening = tree.release_dir / "hardening"
    shutil.copytree(env.root / f"release/{RELEASE}/hardening", hardening)
    return tree, hardening, env.posttag.load_record(hardening)


def _local_tag(**fields: Any) -> dict[str, Any]:
    return {"name": RELEASE, "sha": TAG_COMMIT, "object_sha": TAG_OBJECT, "object_type": "tag", "source": "local-git"} | fields


def dm_expired_current_as_historical(env: Env) -> tuple[list[str], list[str]]:
    tree, hardening, record = _post_tag(env)
    try:
        control = env.posttag.historical_standing(record, hardening, None, tree.root)["refusals"]
        path = hardening / HIST_RUN / "observations.json"
        obs = json.loads(path.read_text(encoding="utf-8"))
        obs["observed_at"] = "2026-09-25T16:36:09Z"  # a fresh current observation substituted for history
        path.write_text(json.dumps(obs), encoding="utf-8")
        return control, env.posttag.historical_standing(record, hardening, None, tree.root)["refusals"]
    finally:
        tree.cleanup()


def _tag_codes(env: Env, tag: dict[str, Any]) -> tuple[list[str], list[str]]:
    tree, hardening, record = _post_tag(env)
    try:
        control, _ = env.posttag.verify_tag_subject(record, hardening, [_local_tag()])
        mutated, _ = env.posttag.verify_tag_subject(record, hardening, [tag])
        return control, mutated
    finally:
        tree.cleanup()


def dm_mutable_tag(env: Env) -> tuple[list[str], list[str]]:
    return _tag_codes(env, _local_tag(object_sha="e" * 40))


def dm_tag_not_subject(env: Env) -> tuple[list[str], list[str]]:
    return _tag_codes(env, _local_tag(sha="d" * 40))


def dm_payload_mutated_post_tag(env: Env) -> tuple[list[str], list[str]]:
    tree, hardening, record = _post_tag(env)
    try:
        control = env.posttag.payload_refusals(tree.root, record)
        allow = tree.release_dir / "worktrees-allow.json"
        allow.write_bytes(allow.read_bytes() + b"\n")
        return control, env.posttag.payload_refusals(tree.root, record)
    finally:
        tree.cleanup()


def dm_replay_mismatch(env: Env) -> tuple[list[str], list[str]]:
    """Two replays of the same inputs agree (control); a substituted observation diverges."""
    hardening = env.root / f"release/{RELEASE}/hardening"
    obs = json.loads((hardening / HIST_RUN / "observations.json").read_text(encoding="utf-8"))
    prev = json.loads((hardening / PREV_RUN / "crown-receipt.json").read_text(encoding="utf-8"))
    first = env.replay.replay(env.root, RELEASE, obs, prev, TAG_COMMIT, "sha256:" + "0" * 64)
    expected = str(first.receipt_digest)
    control = env.replay.replay(env.root, RELEASE, obs, prev, TAG_COMMIT, expected)
    substituted = dict(obs, observed_at="2026-09-25T16:36:09Z")
    mutated = env.replay.replay(env.root, RELEASE, substituted, prev, TAG_COMMIT, expected)
    return [str(control.refusal())], [str(mutated.refusal())]


def _artifact_eval(env: Env, rid: str, edit: Callable[[dict[str, Any], dict[str, Any]], None]) -> tuple[list[str], list[str]]:
    """Crown over the ALIVE tree; ``edit(artifact_entry, receipt_json)`` breaks one producer receipt."""

    def mutate(tree: Any, obs: dict[str, Any]) -> None:
        art = obs["artifacts"][_req(tree, rid).evidence_locator]
        edit(art, art["json"])

    return _crown_eval(env, mutate)


AUTOFDE_FALSIFIER = "scripts/release_tlc_court_receipt.py"  # beb7bc2d frontier falsifier


def dm_delta_unbounded(env: Env) -> tuple[list[str], list[str]]:
    return _artifact_eval(env, "AC-07", lambda art, data: art["subject_delta_paths"].append(AUTOFDE_FALSIFIER))


def dm_delta_unobserved(env: Env) -> tuple[list[str], list[str]]:
    return _artifact_eval(env, "AC-07", lambda art, data: art.pop("subject_delta_paths"))


def dm_delta_misclaimed(env: Env) -> tuple[list[str], list[str]]:
    def edit(art: dict[str, Any], data: dict[str, Any]) -> None:
        art["subject_delta_paths"].append(AUTOFDE_FALSIFIER)
        data["subject_delta_class"] = "RECEIPT_ONLY"  # the receipt-only claim the delta refutes

    return _artifact_eval(env, "AC-07", edit)


def dm_receipt_names_its_container(env: Env) -> tuple[list[str], list[str]]:
    return _artifact_eval(env, "AC-07", lambda art, data: data.update(subject_sha=art["head_sha"]))


def dm_mutable_subject(env: Env) -> tuple[list[str], list[str]]:
    return _artifact_eval(env, "AC-07", lambda art, data: data.update(subject_sha="master"))


def dm_evidence_not_durable(env: Env) -> tuple[list[str], list[str]]:
    """A PASS court under durable/v1 citing a scratch path (the tag-time closure's form)."""
    closure = json.loads((env.root / f"release/{RELEASE}/closure.json").read_text(encoding="utf-8"))
    index = json.loads((env.root / f"release/{RELEASE}/hardening/evidence/INDEX.json").read_text(encoding="utf-8"))
    bound = env.court.bind_index(closure, index)
    control = list(env.court.evaluate(bound, env.root).refusals)
    court = bound["subjects"][9]["courts"][0]
    court["evidence_locator"] = court["evidence"]  # scratchpad/v26925/lanes/... (not durable)
    return [r for r in control if ":AFFIDAVIT:" in r], list(env.court.evaluate(bound, env.root).refusals)


def dm_evidence_digest_mismatch(env: Env) -> tuple[list[str], list[str]]:
    """The E1 affidavit court output with one byte flipped: the recorded output_sha256 no longer recomputes."""
    closure = json.loads((env.root / f"release/{RELEASE}/closure.json").read_text(encoding="utf-8"))
    index = json.loads((env.root / f"release/{RELEASE}/hardening/evidence/INDEX.json").read_text(encoding="utf-8"))
    bound = env.court.bind_index(closure, index)
    control = list(env.court.evaluate(bound, env.root).refusals)
    rel = f"release/{RELEASE}/hardening/evidence"
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(env.root / rel, Path(tmp) / rel)
        target = next((Path(tmp) / rel / "courts/affidavit").glob("*/court.out"))
        data = bytearray(target.read_bytes())
        data[0] ^= 1
        target.write_bytes(bytes(data))
        return control, list(env.court.evaluate(bound, Path(tmp)).refusals)


DATA_MUTANTS: tuple[DataMutant, ...] = (
    DataMutant("dm_terminal_blocker_without_type", dm_terminal_blocker_without_type, "REFUSED:BLOCKED_WITHOUT_TYPE:AC-15", "BLOCKED_WITHOUT_TYPE"),
    DataMutant(
        "dm_terminal_blocker_without_reason",
        dm_terminal_blocker_without_reason,
        "missing=broken_term+failure_class",
        "BLOCKED_WITHOUT_TYPE",
    ),
    DataMutant("dm_terminal_blocker_without_owner", dm_terminal_blocker_without_owner, "missing=owner", "BLOCKED_WITHOUT_TYPE"),
    DataMutant(
        "dm_terminal_blocker_foreign_owner", dm_terminal_blocker_foreign_owner, "REFUSED:OWNER_SPLIT:AC-15", "OWNER_SPLIT"
    ),
    DataMutant(
        "dm_f09_superseded_as_blocker", dm_f09_superseded_as_blocker, "BLOCKED:ARTIFACT_BLOCKED:F-09", "ARTIFACT_BLOCKED"
    ),
    DataMutant("dm_policy_missing", dm_policy_missing, "REFUSED:TERMINALITY_POLICY_MISSING", "TERMINALITY_POLICY_MISSING"),
    DataMutant("dm_policy_coverage_gap", dm_policy_coverage_gap, "REFUSED:POLICY_COVERAGE_GAP:F-09", "POLICY_COVERAGE_GAP"),
    DataMutant(
        "dm_relaxation_ungrounded",
        dm_relaxation_ungrounded,
        "REFUSED:POLICY_RELAXATION_UNGROUNDED:AC-07",
        "POLICY_RELAXATION_UNGROUNDED",
    ),
    DataMutant("dm_acceptance_drift", dm_acceptance_drift, "REFUSED:ACCEPTANCE_DRIFT:AC-15", "ACCEPTANCE_DRIFT"),
    DataMutant("dm_success_replaced_by_blocker", dm_success_replaced_by_blocker, "BLOCKED:ARTIFACT_BLOCKED:AC-07", "ARTIFACT_BLOCKED"),
    DataMutant(
        "dm_subject_container_conflation",
        dm_subject_container_conflation,
        "REFUSED:ARTIFACT_SUBJECT_SPLIT:AC-07",
        "ARTIFACT_SUBJECT_SPLIT",
    ),
    DataMutant("dm_stale_observation", dm_stale_observation, "BLOCKED:OBSERVATION_STALE:AC-09", "OBSERVATION_STALE"),
    DataMutant(
        "dm_expired_current_as_historical",
        dm_expired_current_as_historical,
        "REFUSED:HISTORICAL_OBSERVATION_SPLIT",
        "HISTORICAL_OBSERVATION_SPLIT",
    ),
    DataMutant("dm_mutable_tag", dm_mutable_tag, "REFUSED:TAG_MUTATED", "TAG_MUTATED"),
    DataMutant("dm_tag_not_subject", dm_tag_not_subject, "REFUSED:TAG_SUBJECT_SPLIT", "TAG_SUBJECT_SPLIT"),
    DataMutant(
        "dm_payload_mutated_post_tag",
        dm_payload_mutated_post_tag,
        "REFUSED:PAYLOAD_MUTATED_POST_TAG",
        "PAYLOAD_MUTATED_POST_TAG",
    ),
    DataMutant("dm_replay_mismatch", dm_replay_mismatch, "BLOCKED:REPLAY_DIVERGED", "REPLAY_DIVERGED"),
    DataMutant("dm_delta_unbounded", dm_delta_unbounded, "BLOCKED:EVIDENCE_DELTA_UNBOUNDED:AC-07", "EVIDENCE_DELTA_UNBOUNDED"),
    DataMutant("dm_delta_unobserved", dm_delta_unobserved, "REFUSED:EVIDENCE_LINEAGE_MISSING:AC-07", "EVIDENCE_LINEAGE_MISSING"),
    DataMutant("dm_delta_misclaimed", dm_delta_misclaimed, "REFUSED:EVIDENCE_DELTA_MISCLAIMED:AC-07", "EVIDENCE_DELTA_MISCLAIMED"),
    DataMutant(
        "dm_receipt_names_its_container",
        dm_receipt_names_its_container,
        "REFUSED:EVIDENCE_CONTAINER_CLAIMS_SUBJECT:AC-07",
        "EVIDENCE_CONTAINER_CLAIMS_SUBJECT",
    ),
    DataMutant("dm_mutable_subject", dm_mutable_subject, "REFUSED:EVIDENCE_SUBJECT_MUTABLE:AC-07", "EVIDENCE_SUBJECT_MUTABLE"),
    DataMutant(
        "dm_evidence_not_durable",
        dm_evidence_not_durable,
        "REFUSED:EVIDENCE_NOT_DURABLE:AFFIDAVIT:affidavit:brce_court",
        "EVIDENCE_NOT_DURABLE",
    ),
    DataMutant(
        "dm_evidence_digest_mismatch",
        dm_evidence_digest_mismatch,
        "REFUSED:EVIDENCE_DIGEST_MISMATCH:AFFIDAVIT",
        "EVIDENCE_DIGEST_MISMATCH",
    ),
)


# ------------------------------------------------------------------ CLI


def emit(report: dict[str, Any], root: Path, *, write: bool = False, check: bool = False) -> int:
    """Write or check ``REPORT`` under ``root``, print the report; return the exit code."""
    rendered = dump(report)
    path = root / REPORT
    if write:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(rendered)
    elif check and (not path.is_file() or path.read_bytes() != rendered):
        refusal = HarnessRefusal("MUTATION_REPORT_DRIFT", f"{REPORT} does not recompute; run --write-report")
        print(json.dumps(refusal.as_dict(), sort_keys=True))
        sys.stdout.write(rendered.decode("utf-8"))
        return 2
    sys.stdout.write(rendered.decode("utf-8"))
    return 0 if report["all_killed"] else 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python3 -m scripts.release_train.root_crown.mutate")
    parser.add_argument("--root", type=Path, default=REPO)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--write-report", action="store_true", help=f"write {REPORT}")
    mode.add_argument("--check-report", action="store_true", help=f"recompute and compare to {REPORT}")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    try:
        report = run(root)
    except HarnessRefusal as refusal:
        print(json.dumps(refusal.as_dict(), sort_keys=True))
        return 2
    return emit(report, root, write=args.write_report, check=args.check_report)


if __name__ == "__main__":
    raise SystemExit(main())
