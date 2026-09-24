"""CE23-1 court: the release-subject falsifier and the predecessor fence, judged on real repositories.

Chicago style: every case builds a real git repository in a temporary directory (release/v26.9.1
materialized with `git archive` from this checkout's pinned base commit) and judges it with the
court's own judge() (release/v26.9.23/courts/ce23_1/court.py), running the real git and tar. No
collaborator is replaced. The full subject (ggen render, vendored pack, imports, verify_release,
the 23-mutant corpus) is judged by `sh release/v26.9.23/courts/CE23-1.sh`, not here.
"""

from __future__ import annotations

import importlib.util
import sys
import tempfile
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURT_DIR = ROOT / "release" / "v26.9.23" / "courts" / "ce23_1"
SPEC = importlib.util.spec_from_file_location("ce23_1_court", COURT_DIR / "court.py")
assert SPEC is not None and SPEC.loader is not None
court = importlib.util.module_from_spec(SPEC)
sys.modules["ce23_1_court"] = court
SPEC.loader.exec_module(court)


class SubjectCase(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-1-test.")
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        try:
            self.env = court.Env(tmp / "home")
        except court.Environment as exc:
            self.skipTest(f"court environment absent: {exc}")
        base_commit = court.SUBJ["base_commit"]
        if self.env.git_(ROOT, "cat-file", "-e", f"{base_commit}^{{commit}}").returncode != 0:
            self.skipTest(f"this checkout holds no base commit {base_commit}")
        self.repo = tmp / "repo"
        self.repo.mkdir()
        self.assertEqual(self.env.git_(self.repo, "init", "-q", "-b", "main").returncode, 0)
        self.env.archive(ROOT, base_commit, [court.PRED_DIR], self.repo)
        self.base = self.env.commit_all(self.repo, "base")
        self.work = tmp / "work"

    def judge(self) -> court.Verdict:
        return court.judge(self.repo, self.base, self.env, self.work)

    def test_no_subject_is_refused_while_predecessor_holds(self) -> None:
        self.env.commit_all(self.repo, "head without a v26.9.23 subject")
        v = self.judge()
        self.assertIn("SUBJECT_ABSENT", v.refused)
        self.assertNotIn("PREDECESSOR_CHANGED", v.refused)
        self.assertTrue(any(line.startswith("OK P1:") for line in v.lines), v.lines)
        self.assertFalse(v.alive)

    def test_predecessor_change_is_refused(self) -> None:
        (self.repo / court.PRED_DIR / "manifest.toml").write_text("[release]\nversion = \"26.9.1\"\n", encoding="utf-8")
        self.env.commit_all(self.repo, "head that rewrites the v26.9.1 manifest")
        v = self.judge()
        self.assertIn("PREDECESSOR_CHANGED", v.refused)
        refusal = next(line for line in v.lines if line.startswith("REFUSED[PREDECESSOR_CHANGED] P1"))
        self.assertIn("release/v26.9.1/manifest.toml", refusal)

    def test_uncommitted_predecessor_edit_is_refused(self) -> None:
        self.env.commit_all(self.repo, "head")
        with (self.repo / court.PRED_DIR / "fleet-policy.toml").open("a", encoding="utf-8") as f:
            f.write("# uncommitted\n")
        self.assertIn("PREDECESSOR_DIRTY", self.judge().refused)

    def test_orphan_base_is_refused(self) -> None:
        self.env.commit_all(self.repo, "head")
        v = court.judge(self.repo, "0" * 40, self.env, self.work)
        self.assertIn("BASE_NOT_ANCESTOR", v.refused)


class ClauseCase(unittest.TestCase):
    """A4 (closed-world ggen.toml), A5 (no symlink beyond the line pointers) and C1 (the judging
    court is the head's) on a small real repository judged from git objects; no ggen run."""

    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-1-clause.")
        self.addCleanup(self.tmp.cleanup)
        tmp = Path(self.tmp.name)
        try:
            self.env = court.Env(tmp / "home")
        except court.Environment as exc:
            self.skipTest(f"court environment absent: {exc}")
        self.outside = tmp / "outside"
        self.outside.mkdir()
        self.repo = tmp / "repo"
        self.repo.mkdir()
        self.assertEqual(self.env.git_(self.repo, "init", "-q", "-b", "main").returncode, 0)
        sub = self.sub = self.repo / court.SDIR
        pack = f"{court.SUBJ['vendor_dir']}/packs/p"
        for rel, text in {
            "release.ttl": "# release facts\n",
            "templates/.gitkeep": "",
            court.SUBJ["classification_import"]: "# classification bytes\n",
            f"{pack}/pack.toml": "[pack]\nname = \"p\"\n",
            "out/manifest.toml": "[release]\n",
            "out/constitutional-role-crosswalk.toml": "[constitutional]\n",
            "ggen.toml": ('[project]\nname = "t"\n\n[ontology]\nsource = "release.ttl"\n\n[templates]\ndir = "templates"\n\n'
                          f'[packs]\np = {{ path = "{pack}", lock = true, extra_ontologies = '
                          f'["{court.SUBJ["classification_import"]}"] }}\n'),
        }.items():
            (sub / rel).parent.mkdir(parents=True, exist_ok=True)
            (sub / rel).write_text(text, encoding="utf-8")
        for name, target in court.SUBJ["line_pointers"].items():
            (sub / name).symlink_to(target)
        for rel, data in court.COURT_BYTES.items():
            assert data is not None
            (self.repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (self.repo / rel).write_bytes(data)

    def judged(self) -> court.Verdict:
        head = self.env.commit_all(self.repo, "head")
        v = court.Verdict()
        court.config_law(v, self.repo, head, self.env)
        court.self_contained(v, self.repo, head, self.env)
        court.court_identity(v, self.repo, head, self.env)
        return v

    def refusal(self, v: court.Verdict, prefix: str) -> str:
        for line in v.lines:
            if line.startswith(prefix):
                return line
        self.fail(f"no {prefix!r} line in {v.lines}")

    def test_contained_closed_world_subject_under_its_committed_court_is_admitted(self) -> None:
        v = self.judged()
        self.assertTrue(v.alive, v.lines)
        self.assertEqual([line.split(":")[0] for line in v.lines], ["OK A4", "OK A5", "OK C1"])

    def test_import_as_absolute_symlink_to_identical_bytes_is_refused(self) -> None:
        f = self.sub / court.SUBJ["classification_import"]
        (self.outside / f.name).write_bytes(f.read_bytes())
        f.unlink()
        f.symlink_to(self.outside / f.name)
        v = self.judged()
        a5 = self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A5")
        self.assertIn(f"{court.SDIR}/{court.SUBJ['classification_import']} (120000 symlink) -> {self.outside}", a5)
        self.assertNotIn(f"{court.SDIR}/manifest.toml (", a5)  # the pinned line pointers stay admitted
        a4 = self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A4")
        self.assertIn(f"{court.SUBJ['classification_import']!r} is ['120000', 'blob']", a4)

    def test_config_key_outside_the_judged_schema_is_refused(self) -> None:
        with (self.sub / "ggen.toml").open("a", encoding="utf-8") as fh:
            fh.write("\n[law]\nreflexive = true\n")
        v = self.judged()
        self.assertEqual(v.refused, ["CONFIG_UNJUDGED"], v.lines)
        self.assertIn("law.reflexive", self.refusal(v, "REFUSED[CONFIG_UNJUDGED] A4"))

    def test_read_path_not_committed_in_the_subject_is_refused(self) -> None:
        text = (self.sub / "ggen.toml").read_text(encoding="utf-8")
        (self.sub / "ggen.toml").write_text(text.replace("extra_ontologies = [", 'extra_ontologies = ["imports/absent.ttl", '),
                                            encoding="utf-8")
        v = self.judged()
        self.assertIn("imports/absent.ttl", self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A4"))
        self.assertIn("not committed", self.refusal(v, "REFUSED[SUBJECT_NOT_INDEPENDENT] A4"))

    def test_committed_pins_other_than_the_judging_court_are_refused(self) -> None:
        with (self.repo / court.SDIR / "courts/ce23_1/subject.toml").open("a", encoding="utf-8") as fh:
            fh.write("# re-pinned\n")
        v = self.judged()
        self.assertEqual(v.refused, ["COURT_NOT_AT_HEAD"], v.lines)
        self.assertIn("courts/ce23_1/subject.toml (differs", self.refusal(v, "REFUSED[COURT_NOT_AT_HEAD] C1"))


class RenderCase(unittest.TestCase):
    def test_committed_render_binds_the_classification_to_the_xaas_component(self) -> None:
        manifest = ROOT / court.SDIR / "manifest.toml"
        if not manifest.is_file():
            self.skipTest(f"{manifest} absent")
        doc = tomllib.loads(manifest.read_text(encoding="utf-8"))
        match = court.SOURCE_RE.match(doc["release"]["classification_source"])
        self.assertIsNotNone(match, doc["release"]["classification_source"])
        pinned = {c["repository"]: c["sha"] for c in doc["components"] if c["required"] is True}
        self.assertEqual(pinned.get(match["repo"]), match["sha"])
        data = (ROOT / court.SDIR / court.SUBJ["classification_import"]).read_bytes()
        self.assertEqual(court.sha256(data), match["digest"])


if __name__ == "__main__":
    unittest.main()
