"""CE23-1 court: the release-subject falsifier and the predecessor fence, judged on real repositories.

Chicago style: every case builds a real git repository in a temporary directory (release/v26.9.1
materialized with `git archive` from this checkout's pinned base commit) and judges it with the
court's own judge() (release/v26.9.23/courts/ce23_1/court.py), running the real git and tar. No
collaborator is replaced. The full subject (ggen render, vendored pack, imports, verify_release,
the 17-mutant corpus) is judged by `sh release/v26.9.23/courts/CE23-1.sh`, not here.
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
