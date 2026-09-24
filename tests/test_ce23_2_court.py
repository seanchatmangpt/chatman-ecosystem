"""CE23-2 court: the legacy-role crosswalk clauses, judged on real files and real repositories.

Chicago style: every case runs the court's own clause functions
(release/v26.9.23/courts/ce23_2/court.py) over real bytes: the committed predecessor manifest
blob, the committed render and imports of release/v26.9.23 copied into a temporary directory and
then edited, real rdflib parsing, and (ObserverCase) the real observer over the canonical xaas
checkout. No collaborator is replaced. The whole subject (ggen renders, pack gates, the
18-mutant corpus) is judged by `sh release/v26.9.23/courts/CE23-2.sh`, not here; these cases
cover refusal codes that corpus does not reach.
"""

from __future__ import annotations

import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COURT_DIR = ROOT / "release" / "v26.9.23" / "courts" / "ce23_2"
SPEC = importlib.util.spec_from_file_location("ce23_2_court", COURT_DIR / "court.py")
assert SPEC is not None and SPEC.loader is not None
court = importlib.util.module_from_spec(SPEC)
sys.modules["ce23_2_court"] = court
SPEC.loader.exec_module(court)
SUB = ROOT / court.SDIR


def base_manifest() -> bytes | None:
    proc = subprocess.run(["git", "-C", str(ROOT), "cat-file", "blob", f"{court.SUBJ['base_commit']}:{court.PRED_MANIFEST}"],
                          capture_output=True)
    return proc.stdout if proc.returncode == 0 else None


class SubjectCopy(unittest.TestCase):
    """A temporary copy of the subject's inputs and render (release.ttl, ggen.toml, imports/, out/)."""

    def setUp(self) -> None:
        try:
            import rdflib  # noqa: F401, PLC0415
        except ImportError:
            self.skipTest("rdflib absent")
        data = base_manifest()
        if data is None:
            self.skipTest(f"this checkout holds no base commit {court.SUBJ['base_commit']}")
        self.pred, problem = court.role_function(data)
        self.assertIsNotNone(self.pred, problem)
        self.tmp = tempfile.TemporaryDirectory(prefix="ce23-2-test.")
        self.addCleanup(self.tmp.cleanup)
        self.sub = Path(self.tmp.name) / "sub"
        self.sub.mkdir()
        for rel in ("release.ttl", "ggen.toml"):
            shutil.copy2(SUB / rel, self.sub / rel)
        for rel in ("imports", "out", "sjira/compiled"):
            shutil.copytree(SUB / rel, self.sub / rel)

    def edit(self, rel: str, old: str, new: str, count: int = 1) -> None:
        path = self.sub / rel
        text = path.read_text(encoding="utf-8")
        self.assertIn(old, text)
        path.write_text(text.replace(old, new, count), encoding="utf-8")

    def append(self, rel: str, text: str) -> None:
        with (self.sub / rel).open("a", encoding="utf-8") as f:
            f.write(text)


class PredecessorCase(unittest.TestCase):
    def test_committed_manifest_is_a_function_of_16_roles(self) -> None:
        data = base_manifest()
        if data is None:
            self.skipTest("no base commit")
        pred, problem = court.role_function(data)
        self.assertEqual(problem, "")
        self.assertEqual(len(pred["roles"]), 16)
        self.assertEqual(pred["by_role"]["formal-proof"]["id"], "mfact")

    def test_role_with_two_components_is_ambiguous(self) -> None:
        data = base_manifest()
        if data is None:
            self.skipTest("no base commit")
        text = data.decode("utf-8") + '\n[[components]]\nid = "mfact-2"\nrepository = "seanchatmangpt/mfact-2"\nrole = "formal-proof"\n'
        pred, problem = court.role_function(text.encode())
        self.assertIsNone(pred)
        self.assertIn("formal-proof", problem)

    def test_duplicated_required_role_is_ambiguous(self) -> None:
        data = base_manifest()
        if data is None:
            self.skipTest("no base commit")
        pred, problem = court.role_function(data.replace(b'  "capstone",\n', b'  "capstone",\n  "capstone",\n'))
        self.assertIsNone(pred)
        self.assertIn("16 distinct", problem)


class TotalityCase(SubjectCopy):
    XW = court.PATHS["crosswalk_toml"]

    def judge(self) -> court.Verdict:
        v = court.Verdict()
        court.totality(v, self.sub, self.pred)
        return v

    def test_committed_render_is_total(self) -> None:
        v = self.judge()
        self.assertTrue(v.alive, v.lines)
        self.assertTrue(any("16/16 roles" in line for line in v.lines), v.lines)

    def test_duplicated_row_is_refused(self) -> None:
        text = (self.sub / self.XW).read_text(encoding="utf-8")
        start = text.index('[[role]]\nlegacy_role = "formal-proof"')
        end = text.index("[[role]]", start + 1)
        self.append(self.XW, "\n" + text[start:end])
        self.assertIn("ROLE_DUPLICATED", self.judge().refused)

    def test_foreign_row_is_refused(self) -> None:
        self.append(self.XW, '\n[[role]]\nlegacy_role = "invented-role"\nboundary = "SUCCESSOR"\nreason = "x"\n'
                             'derived_by = "rule:x"\ndecided_by = ""\n')
        self.assertIn("ROLE_FOREIGN", self.judge().refused)

    def test_altered_legacy_sha_is_refused(self) -> None:
        sha = self.pred["by_role"]["formal-proof"]["sha"]
        self.edit(self.XW, f'legacy_sha = "{sha}"', f'legacy_sha = "{"0" * 40}"')
        v = self.judge()
        self.assertIn("LEGACY_TOPOLOGY_ALTERED", v.refused)
        self.assertTrue(any("formal-proof" in line for line in v.lines if line.startswith("REFUSED")))

    def test_untyped_boundary_is_refused(self) -> None:
        self.edit(self.XW, 'boundary = "SUCCESSOR"', 'boundary = "UNCLASSIFIED"')
        self.assertIn("BOUNDARY_UNTYPED", self.judge().refused)

    def test_double_provenance_is_refused(self) -> None:
        self.edit(self.XW, 'decided_by = ""', 'decided_by = "operator"')
        self.assertIn("PROVENANCE_MISSING", self.judge().refused)

    def test_empty_reason_is_refused(self) -> None:
        self.edit(self.XW, 'reason = "fleet classification row for gymact has class Successor"', 'reason = ""')
        self.assertIn("PROVENANCE_MISSING", self.judge().refused)


class RuleCase(SubjectCopy):
    REFS = court.PATHS["court_references_import"]
    CLS = court.PATHS["classification_import"]

    def judge(self) -> court.Verdict:
        v = court.Verdict()
        rows = court.totality(court.Verdict(), self.sub, self.pred)
        court.rule(v, self.sub, self.pred, rows)
        return v

    def test_committed_inputs_derive_every_row(self) -> None:
        v = self.judge()
        self.assertTrue(v.alive, v.lines)

    def test_court_executed_unclassified_role_is_undecidable(self) -> None:
        self.append(self.REFS, '<https://example.invalid/court.sh> er:courtReferencesComponent "seanchatmangpt/mfact" .\n')
        v = self.judge()
        self.assertIn("ROLE_UNDECIDABLE", v.refused)
        self.assertTrue(any("formal-proof" in line for line in v.lines if "ROLE_UNDECIDABLE" in line))

    def test_basename_collision_is_ambiguous(self) -> None:
        self.append(self.CLS, "\n<https://example.invalid/fleet-ggen-2> a sj:FleetClassification ;\n"
                              '    dcterms:identifier "ggen" ;\n    sj:fleetClass sj:Refused .\n')
        v = self.judge()
        self.assertIn("CLASSIFICATION_AMBIGUOUS", v.refused)
        self.assertIn("CLASSIFICATION_NOT_PINNED", v.refused)


class DecisionCase(SubjectCopy):
    def test_no_decision_is_admitted_and_none_exists(self) -> None:
        v = court.Verdict()
        court.decisions(v, self.sub, court.totality(court.Verdict(), self.sub, self.pred))
        self.assertTrue(v.alive, v.lines)

    def test_decision_in_the_graph_alone_is_refused(self) -> None:
        self.append("release.ttl", "\nr23:decision-research a er:RoleDisposition ;\n    er:legacyRole \"research\" ;\n"
                                   "    er:boundary er:ROLE_BLOCKED ;\n    er:decidedBy \"operator\" ;\n"
                                   "    er:reason \"test\" .\n")
        v = court.Verdict()
        court.decisions(v, self.sub, court.totality(court.Verdict(), self.sub, self.pred))
        self.assertIn("DECISION_UNADMITTED", v.refused)
        self.assertTrue(any("research" in line for line in v.lines if line.startswith("REFUSED")))


class ObserverCase(unittest.TestCase):
    """The observer is deterministic and the committed import is its output (canonical xaas checkout)."""

    def test_observation_reproduces_the_committed_import(self) -> None:
        try:
            import rdflib  # noqa: F401, PLC0415
        except ImportError:
            self.skipTest("rdflib absent")
        spec = importlib.util.spec_from_file_location("ce23_2_observer", COURT_DIR / "observe_court_refs.py")
        assert spec is not None and spec.loader is not None
        observer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(observer)
        xaas = court.repo_for("xaas")
        try:
            first = observer.observe(SUB, xaas)
        except observer.ObservationError as exc:
            self.skipTest(f"observation inputs absent: {exc}")
        second = observer.observe(SUB, xaas)
        self.assertEqual(first, second)
        self.assertEqual(first.encode("utf-8"), (SUB / court.PATHS["court_references_import"]).read_bytes())
        self.assertNotIn(str(Path.home()), first)
        self.assertIn('er:courtReferencesComponent "seanchatmangpt/ggen_igniter", "seanchatmangpt/xaas"', first)
        self.assertIn("#   seanchatmangpt/mfact: []", first)


if __name__ == "__main__":
    unittest.main()
