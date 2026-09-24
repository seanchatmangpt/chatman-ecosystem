"""CE23-9 exact-head root court: the CI check universe, the local CI job runner, the exact-head and
disposition laws and the judge's handling of the generated court, on real repositories and real bytes.

Chicago style: synthetic workflows live in real git repositories created in temporary directories and
are read through the court's own functions (release/v26.9.23/courts/ce23_9/ci_checks.py, ci_job.py run
as a real subprocess); the exact-head CI law runs over the committed real check-runs of base c59596f5
(fixtures/checkruns-c59596f5.json, captured with gh api); the judge runs a court rendered by the real
ggen from the vendored chatman-ecosystem-release-pack template with three members (ALIVE, UNKNOWN,
REFUSED); the receipt validator is read from the real pinned ggen-marketplace blob (a named skip where
the canonical marketplace checkout is absent), and its pin typing (published / publication pending /
off the line / unobserved) is judged on real git repositories. No collaborator is replaced. The whole
court is `sh release/v26.9.23/courts/CE23-9.sh`.
"""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURT_DIR = ROOT / "release" / "v26.9.23" / "courts" / "ce23_9"
PACK = ROOT / "release" / "v26.9.23" / "vendor" / "ggen-marketplace" / "packs" / "chatman-ecosystem-release-pack"


def load(name: str):
    spec = importlib.util.spec_from_file_location(f"ce23_9_{name}", COURT_DIR / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[f"ce23_9_{name}"] = module
    spec.loader.exec_module(module)
    return module


ci_checks = load("ci_checks")
try:
    import rdflib  # noqa: F401
    import yaml  # noqa: F401
    HAVE_LIBS = True
except ImportError:
    HAVE_LIBS = False
members = load("members") if HAVE_LIBS else None


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True, text=True).stdout.strip()


class Repo(unittest.TestCase):
    """A real git repository: `base` commit, then `write` + `commit` build the head."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-9-test.")
        self.addCleanup(self.tmp.cleanup)
        self.repo = Path(self.tmp.name) / "repo"
        self.repo.mkdir()
        git(self.repo, "init", "-q", "-b", "main")
        git(self.repo, "config", "user.email", "court@example.invalid")
        git(self.repo, "config", "user.name", "court")
        self.write("README.md", "base\n")
        self.base = self.commit("base")

    def write(self, rel: str, text: str) -> None:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def commit(self, msg: str) -> str:
        git(self.repo, "add", "-A")
        git(self.repo, "commit", "-q", "-m", msg)
        return git(self.repo, "rev-parse", "HEAD")


@unittest.skipUnless(HAVE_LIBS, "PyYAML and rdflib are court dependencies")
class UniverseCase(Repo):
    def test_trigger_semantics(self) -> None:
        self.write(".github/workflows/docs.yml", "name: docs\non:\n  pull_request:\n    paths: ['docs/**']\n"
                   "  push:\n    branches: [main]\n    paths: ['docs/**']\njobs:\n  build:\n    name: Build docs\n"
                   "    runs-on: ubuntu-latest\n    steps: [{run: 'true'}]\n")
        self.write(".github/workflows/other-base.yml", "on:\n  pull_request:\n    branches: [develop]\n"
                   "jobs:\n  x:\n    runs-on: ubuntu-latest\n    steps: [{run: 'true'}]\n")
        self.write(".github/workflows/sched.yml", "on:\n  schedule: [{cron: '1 1 * * *'}]\njobs:\n  obs:\n"
                   "    name: Observe ${{ matrix.repo }}\n    strategy:\n      matrix:\n        repo: [a/b, c/d]\n"
                   "    runs-on: ubuntu-latest\n    steps: [{run: 'true'}]\n")
        self.write(".github/workflows/negated.yml", "on:\n  pull_request:\n    paths: ['docs/**', '!docs/ignored.md']\n"
                   "jobs:\n  n:\n    runs-on: ubuntu-latest\n    steps: [{run: 'true'}]\n")
        self.write(".github/workflows/ignore.yml", "on:\n  pull_request:\n    paths-ignore: ['docs/**', '.github/**']\n"
                   "jobs:\n  i:\n    runs-on: ubuntu-latest\n    steps: [{run: 'true'}]\n")
        self.write(".github/workflows/dispatch.yml", "on: workflow_dispatch\njobs:\n  d:\n    runs-on: ubuntu-latest\n"
                   "    steps: [{run: 'true'}]\n")
        self.write("docs/ignored.md", "x\n")
        self.commit("head")
        u = ci_checks.universe(self.repo, self.base, "HEAD")
        got = {(r["workflow"].split("/")[-1], r["check"]): r["events"] for r in u["checks"]}
        self.assertEqual(got, {
            ("docs.yml", "Build docs"): ["pull_request", "push"],
            ("sched.yml", "Observe a/b"): ["schedule"],
            ("sched.yml", "Observe c/d"): ["schedule"],
        })
        self.assertFalse(u["truncated"])

    def test_300_file_window_is_uncertain_not_dropped(self) -> None:
        self.write(".github/workflows/late.yml", "on:\n  pull_request:\n    paths: ['zz/**']\njobs:\n  l:\n"
                   "    runs-on: ubuntu-latest\n    steps: [{run: 'true'}]\n")
        for i in range(300):
            self.write(f"aa/f{i:03d}.txt", "x\n")
        self.write("zz/late.txt", "x\n")
        self.commit("head")
        u = ci_checks.universe(self.repo, self.base, "HEAD")
        row = next(r for r in u["checks"] if r["workflow"].endswith("late.yml"))
        self.assertTrue(u["truncated"])
        self.assertEqual((row["events"], row["uncertain"]), ([], ["pull_request"]))

    def test_glob_semantics(self) -> None:
        self.assertTrue(ci_checks.glob_regex("docs/*.md").match("docs/a.md"))
        self.assertFalse(ci_checks.glob_regex("docs/*.md").match("docs/x/a.md"))
        self.assertTrue(ci_checks.glob_regex("docs/**").match("docs/x/y/a.md"))
        self.assertTrue(ci_checks.glob_regex("*.jsx?").match("page.js"))
        self.assertTrue(ci_checks.glob_regex("*.jsx?").match("page.jsx"))
        self.assertFalse(ci_checks.glob_regex("*.jsx?").match("page.jsxx"))


@unittest.skipUnless(HAVE_LIBS, "PyYAML is a court dependency")
class CiJobCase(Repo):
    def job(self, body: str, *extra: str) -> subprocess.CompletedProcess:
        self.write(".github/workflows/w.yml", body)
        self.commit("workflow")
        return subprocess.run([sys.executable, str(COURT_DIR / "ci_job.py"), ".github/workflows/w.yml", "j", *extra],
                              cwd=self.repo, capture_output=True, text=True, env=dict(os.environ, PYTHONDONTWRITEBYTECODE="1"))

    def test_runs_steps_at_head_with_context_and_env_file(self) -> None:
        p = self.job("env:\n  SUBJECT: ${{ github.event.pull_request.head.sha || github.sha }}\njobs:\n  j:\n    steps:\n"
                     "      - uses: actions/checkout@v4\n"
                     "      - run: echo \"FOO=bar\" >> \"$GITHUB_ENV\"\n"
                     "      - run: test \"$FOO\" = bar && test \"$SUBJECT\" = \"$(git rev-parse HEAD)\" && echo \"subject=$SUBJECT\"\n"
                     "      - name: produce an artifact\n        run: echo x > artifact.json\n")
        head = git(self.repo, "rev-parse", "HEAD")
        self.assertEqual(p.returncode, 0, p.stdout + p.stderr)
        self.assertIn("CI_JOB_SKIP_USES step=1", p.stdout)
        self.assertIn(f"subject={head}", p.stdout)
        self.assertIn("CI_JOB_BYPRODUCT_REMOVED artifact.json", p.stdout)
        self.assertFalse((self.repo / "artifact.json").exists())
        self.assertIn(f"CI_JOB_PASS .github/workflows/w.yml#j head={head}", p.stdout)

    def test_failing_step_refuses(self) -> None:
        p = self.job("jobs:\n  j:\n    steps:\n      - name: fails\n        run: exit 3\n      - run: echo never\n")
        self.assertEqual(p.returncode, 1)
        self.assertIn("CI_JOB_STEP_FAILED step=1 name='fails' exit=3", p.stdout)
        self.assertNotIn("never", p.stdout)

    def test_secret_expression_is_unsupported_not_guessed(self) -> None:
        p = self.job("jobs:\n  j:\n    steps:\n      - run: echo ${{ secrets.TOKEN }}\n")
        self.assertEqual(p.returncode, 3)
        self.assertIn("UNSUPPORTED[EXPRESSION]", p.stdout)

    def test_tracked_mutation_refuses(self) -> None:
        p = self.job("jobs:\n  j:\n    steps:\n      - run: echo changed >> README.md\n")
        self.assertEqual(p.returncode, 1)
        self.assertIn("CI_JOB_MUTATED_CHECKOUT", p.stdout)

    def test_skip_step_must_name_a_step_and_is_printed(self) -> None:
        body = "jobs:\n  j:\n    steps:\n      - name: slow\n        run: exit 9\n      - run: 'true'\n"
        self.assertEqual(self.job(body, "--skip-step", "nope").returncode, 2)
        p = subprocess.run([sys.executable, str(COURT_DIR / "ci_job.py"), ".github/workflows/w.yml", "j", "--skip-step", "slow"],
                           cwd=self.repo, capture_output=True, text=True)
        self.assertEqual(p.returncode, 0, p.stdout)
        self.assertIn("CI_JOB_SKIP_DECLARED step=1 name='slow'", p.stdout)

    def test_github_rate_limit_is_an_infrastructure_edge_not_a_verdict(self) -> None:
        p = self.job("jobs:\n  j:\n    steps:\n      - name: refs\n        run: |\n          echo 'HTTP Error 403: rate limit exceeded'\n          exit 2\n")
        self.assertEqual(p.returncode, 75)
        self.assertIn("CI_JOB_STEP_RATE_LIMITED step=1 name='refs' exit=2", p.stdout)
        q = self.job("jobs:\n  j:\n    steps:\n      - name: refs\n        run: |\n          echo 'HTTP Error 404: not found'\n          exit 2\n")
        self.assertEqual(q.returncode, 1)

    def test_invalid_workflow_yaml_is_a_typed_usage_error(self) -> None:
        p = self.job("jobs:\n  j:\n    steps:\n      - run: echo a: b: c\n")
        self.assertEqual(p.returncode, 2)
        self.assertIn("is not valid YAML at HEAD", p.stdout)
        self.assertNotIn("Traceback", p.stdout + p.stderr)

    def test_job_if_false_in_pull_request_context(self) -> None:
        p = self.job("jobs:\n  j:\n    if: github.event_name == 'push'\n    steps:\n      - run: exit 1\n")
        self.assertEqual(p.returncode, 0)
        self.assertIn("CI_JOB_SKIPPED", p.stdout)


@unittest.skipUnless(HAVE_LIBS, "PyYAML and rdflib are court dependencies")
class ValidatorPinCase(Repo):
    """The receipt validator is never committed: it is the pinned marketplace blob, read at run time."""

    PATH = "packs/p/generated/validator.py"

    def market(self, body: bytes = b"print('validator')\n") -> tuple[str, str]:
        """This case's repository as a marketplace: base, then `line` holding the validator at PATH."""
        (self.repo / self.PATH).parent.mkdir(parents=True, exist_ok=True)
        (self.repo / self.PATH).write_bytes(body)
        pinned = self.commit("validator")
        return pinned, members.sha256(body)

    def pin(self, commit: str, digest: str) -> dict:
        return {"commit": commit, "path": self.PATH, "sha256": digest, "ref": "line"}

    def materialize(self, pin: dict) -> tuple[Path | None, list]:
        dest = Path(self.tmp.name) / f"dest-{len(os.listdir(self.tmp.name))}"
        return members.materialize_validator(dest, pin, self.repo)

    def refs(self, remote: str | None, local: str | None) -> None:
        for ref, sha in (("refs/remotes/origin/line", remote), ("refs/heads/line", local)):
            if sha:
                git(self.repo, "update-ref", ref, sha)

    def test_published_pin_is_admitted_and_written(self) -> None:
        pinned, digest = self.market()
        self.refs(pinned, pinned)
        path, findings = self.materialize(self.pin(pinned, digest))
        self.assertEqual([k for k, _, _ in findings], ["OK"], findings)
        self.assertIsNotNone(path)
        self.assertEqual(members.sha256(path.read_bytes()), digest)

    def test_pending_publication_is_an_edge_not_a_counterexample(self) -> None:
        pinned, digest = self.market()
        self.refs(self.base, pinned)  # the line fast-forwards the published ref: only a push is missing
        path, findings = self.materialize(self.pin(pinned, digest))
        self.assertEqual([(k, c) for k, c, _ in findings], [("UNKNOWN", "VALIDATOR_PUBLICATION_PENDING")])
        self.assertIsNotNone(path)

    def test_pin_off_the_line_is_refused(self) -> None:
        pinned, digest = self.market()
        git(self.repo, "checkout", "-q", "-b", "other", self.base)
        self.write("x.txt", "diverged\n")
        sibling = self.commit("diverged published line")
        self.refs(sibling, pinned)  # the local line cannot fast-forward the published ref
        _, findings = self.materialize(self.pin(pinned, digest))
        self.assertEqual([(k, c) for k, c, _ in findings], [("REFUSED", "VALIDATOR_OFF_REF")])
        self.assertIn("diverged", findings[0][2])
        self.refs(self.base, self.base)  # neither the published ref nor the local line holds the pin
        _, findings = self.materialize(self.pin(pinned, digest))
        self.assertEqual([(k, c) for k, c, _ in findings], [("REFUSED", "VALIDATOR_OFF_REF")])

    def test_unobserved_ref_absent_commit_and_digest_mismatch(self) -> None:
        pinned, digest = self.market()
        _, findings = self.materialize(self.pin(pinned, digest))
        self.assertEqual([(k, c) for k, c, _ in findings], [("UNKNOWN", "MARKETPLACE_REF_UNOBSERVED")])
        path, findings = self.materialize(self.pin("0" * 40, digest))
        self.assertEqual(([(k, c) for k, c, _ in findings], path), ([("UNKNOWN", "MARKETPLACE_UNAVAILABLE")], None))
        self.refs(pinned, pinned)
        path, findings = self.materialize(self.pin(pinned, "f" * 64))
        self.assertEqual(([(k, c) for k, c, _ in findings], path), ([("REFUSED", "VALIDATOR_NOT_BYTE_IDENTICAL")], None))

    def test_real_pin_reads_the_published_marketplace_blob(self) -> None:
        pin = members.PINS["validator"]
        path, findings = members.materialize_validator(Path(self.tmp.name) / "real", pin)
        if path is None and findings[0][1] == "MARKETPLACE_UNAVAILABLE":
            self.skipTest(f"canonical ggen-marketplace checkout absent: {findings[0][2]}")
        self.assertIsNotNone(path)
        self.assertEqual(members.sha256(path.read_bytes()), pin["sha256"])
        self.assertNotIn("REFUSED", [k for k, _, _ in findings], findings)
        # no copy is committed: the court's files are the ones root.toml names, and none is a validator
        committed = git(ROOT, "ls-files", "--", "release/v26.9.23").splitlines()
        self.assertEqual([f for f in committed if f.endswith("unified_receipt_validator.py")], [])

    def test_judging_court_names_no_shadow_tree_path(self) -> None:
        needles = (str(Path.home() / "wt") + "/", "~/" + "wt/", "$HOME/" + "wt/")
        for rel in members.SUBJ["court_files"]:
            data = subprocess.run(["git", "-C", str(ROOT), "show", f"HEAD:{rel}"], capture_output=True).stdout
            self.assertTrue(data, rel)
            self.assertEqual([n for n in needles if n.encode() in data], [], rel)


@unittest.skipUnless(HAVE_LIBS, "PyYAML and rdflib are court dependencies")
class LawCase(unittest.TestCase):
    def test_exact_head_law_on_the_real_base_checkruns(self) -> None:
        fixture = json.loads((COURT_DIR / "fixtures" / "checkruns-c59596f5.json").read_text(encoding="utf-8"))
        facts = members.court_facts(ROOT)
        refused, _, lines = members.judge_checkruns(fixture["check_runs"], [], facts["typed"], facts["local"], {"success", "skipped", "neutral"})
        names = {text.split("'")[1] for _, text in refused}
        self.assertEqual(names, {"Fast constitutional gates", "S0-S3 exact-head crown",
                                 "Full behavior and negative fixtures", "Cold-cache correctness"})
        self.assertTrue(any("'survey'" in line for line in lines))

    def test_untyped_failure_pending_and_missing(self) -> None:
        typed = {("w.yml", "known bad"): {}}
        local = {("w.yml", "mine"): {"gate": "g"}}
        runs = [{"id": 1, "name": "known bad", "workflow": "w.yml", "status": "completed", "conclusion": "failure"},
                {"id": 2, "name": "new bad", "workflow": "w.yml", "status": "completed", "conclusion": "failure"},
                {"id": 3, "name": "slow", "workflow": "w.yml", "status": "in_progress", "conclusion": None}]
        universe = [{"workflow": "w.yml", "check": "expected", "events": ["pull_request"]}]
        refused, unknown, _ = members.judge_checkruns(runs, universe, typed, local, {"success"})
        self.assertEqual([c for c, _ in refused], ["UNTYPED_FAILURE"])
        self.assertEqual(sorted(c for c, _ in unknown), ["EXACT_HEAD_CHECK_MISSING", "EXACT_HEAD_CI_PENDING", "MEMBER_CHECK_MISSING"])
        # the newest run of a check decides: a rerun that succeeded clears the older failure
        runs.append({"id": 4, "name": "new bad", "workflow": "w.yml", "status": "completed", "conclusion": "success"})
        refused, _, _ = members.judge_checkruns(runs, universe, typed, local, {"success"})
        self.assertEqual(refused, [])

    def test_receipt_projection_names_gates_and_orders(self) -> None:
        projected = {r["rel"]: r for r in members.projected_receipts(ROOT)}
        ce23_12 = projected["receipts/v26.9.23/CE23-12.json"]
        self.assertEqual(ce23_12["gates"], ["CE23-12", "CE23-12-BenchmarkDesign", "CE23-12-GeneratedQualificationPlan",
                                            "CE23-12-MSAContract"])
        self.assertIn("10d3712c7e428097", projected["receipts/v26.9.23/CE23-2.json"]["orders"])
        self.assertEqual(projected["receipts/v26.9.23/CE23-0.json"]["gates"], ["CE23-0"])
        self.assertNotIn("receipts/v26.9.23/CE23-12.gate/court-receipt-CE23-12.json", projected)

    def test_disposition_law(self) -> None:
        prefix = members.PINS["ci"]["local_member_prefix"]
        index = {("w.yml", "a"): {"job": "ja"}, ("w.yml", "b"): {"job": "jb"}, ("v.yml", "b"): {"job": "jb"}}
        local = {("w.yml", "a"): {"gate": "ga", "job": "ja", "command": f"{prefix}w.yml ja"}}
        self.assertEqual(members.disposition_law(index, {}, local, None), [])
        codes = lambda typed, loc: sorted(c for c, _ in members.disposition_law(index, typed, loc, None))  # noqa: E731
        self.assertEqual(codes({("w.yml", "gone"): {}}, local), ["STALE_TYPED_CHECK"])
        self.assertEqual(codes({("w.yml", "b"): {}}, local), ["TYPED_NAME_AMBIGUOUS"])
        self.assertEqual(codes({("w.yml", "a"): {}}, local), ["DOUBLE_DISPOSITION"])
        bad = {("w.yml", "a"): {"gate": "ga", "job": "ja", "command": f"{prefix}w.yml jb"}}
        self.assertEqual(codes({}, bad), ["MEMBER_COMMAND_MISMATCH"])
        skip = {("w.yml", "a"): {"gate": "ga", "job": "ja", "command": f"{prefix}w.yml ja --skip-step 'x'"}}
        self.assertEqual(codes({}, skip), [])


@unittest.skipUnless(HAVE_LIBS and shutil.which("ggen"), "ggen, PyYAML and rdflib render and judge the court")
class GeneratedCourtCase(unittest.TestCase):
    """A court rendered by the real ggen from the vendored pack template, with three members."""

    def test_judge_types_each_member_and_continues_after_the_stop(self) -> None:
        tmp = tempfile.TemporaryDirectory(prefix="ce23-9-court-test.")
        self.addCleanup(tmp.cleanup)
        pack = Path(tmp.name) / "pack"
        shutil.copytree(PACK, pack)
        consumer = pack / "qualification" / "consumer-v26.9.23"
        release = consumer / "release.ttl"
        text = release.read_text(encoding="utf-8")
        start = text.index("q23:gate-explicit-runner a er:Gate ;")
        end = text.index("q23:probe-subject a er:Probe ;")
        gates = ("q23:gate-explicit-runner a er:Gate ;\n    er:gateOrder 1 ;\n    er:gateName \"alive\" ;\n"
                 "    er:command \"echo 'MEMBER_ALIVE alive ok'\" .\n\n"
                 "q23:gate-imports-recheck a er:Gate ;\n    er:gateOrder 2 ;\n    er:gateName \"edge\" ;\n"
                 "    er:command \"echo 'MEMBER_UNKNOWN[EDGE] edge operator'; exit 75\" .\n\n"
                 "q23:gate-crosswalk-total a er:Gate ;\n    er:gateOrder 3 ;\n    er:gateName \"bad\" ;\n"
                 "    er:command \"echo 'MEMBER_REFUSED[BAD] bad counterexample'; exit 1\" .\n\n")
        release.write_text(text[:start] + gates + text[end:], encoding="utf-8")
        (consumer / "observed.ttl").write_text("", encoding="utf-8")
        shutil.rmtree(consumer / "out", ignore_errors=True)
        sync = subprocess.run(["ggen", "sync", "run"], cwd=consumer, capture_output=True, text=True)
        self.assertEqual(sync.returncode, 0, sync.stderr[-800:])
        git(pack, "init", "-q")  # the court's subject probe is `git rev-parse HEAD`
        git(pack, "-c", "user.email=court@example.invalid", "-c", "user.name=court", "add", "-A")
        git(pack, "-c", "user.email=court@example.invalid", "-c", "user.name=court", "commit", "-q", "-m", "court test subject")
        court = load("court")
        script = consumer / "out" / "scripts" / "crown_v26_9_23.sh"
        rendered = court.rendered_gates(script)
        self.assertEqual([(g["order"], g["name"]) for g in rendered], [(1, "alive"), (2, "edge"), (3, "bad")])
        judge = court.Judge()
        with redirect_stdout(io.StringIO()) as out:
            table = court.k_run_court(consumer, script, rendered, dict(os.environ), judge)
        self.assertEqual([(r["name"], r["verdict"], r["source"]) for r in table],
                         [("alive", "ALIVE", "court"), ("edge", "UNKNOWN", "court"), ("bad", "REFUSED", "continued")])
        self.assertIn("COURT_STOPPED order=2 name=edge", out.getvalue())
        self.assertEqual((judge.refused, judge.unknown), (["MEMBER:bad"], ["MEMBER:edge"]))
        # the court's own R receipt of that run is valid under the pinned generated validator
        receipt = Path(tmp.name) / "court-receipt.json"
        court.write_receipt(receipt, ROOT, git(ROOT, "rev-parse", "HEAD"), "REFUSED", table, judge, 0.0)
        validator, findings = members.materialize_validator(Path(tmp.name) / "validator")
        if validator is None:
            self.skipTest(f"receipt validator not readable from the canonical marketplace checkout: {findings}")
        check = subprocess.run([sys.executable, str(validator), str(receipt),
                                "--contract", "dfcm_fleet_v1"], capture_output=True, text=True)
        self.assertEqual(check.returncode, 0, check.stdout + check.stderr)
        self.assertEqual(json.loads(receipt.read_text())["standing"]["broken_term"], "mu_on_O")


if __name__ == "__main__":
    unittest.main()
