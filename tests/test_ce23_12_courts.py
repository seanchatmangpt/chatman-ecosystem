"""CE23-12 courts and the in-repo nonllm-class-qualification-pack, judged on real bytes.

Chicago style: every case runs the real code (release/v26.9.23/bench/pack/scripts/*.py and
release/v26.9.23/courts/ce23_12/court.py) over the committed design graph, generated tables and
projections, or over copies of them edited in a temporary directory; the statistics are
cross-checked against scipy's own Beta quantile; the end-to-end case runs the real court script as
a subprocess on a real synthetic git repository. No collaborator is replaced. The full subject
(ggen renders, the 31-artifact corpus on five instruments, the MSA measurements, the anti-vacuity
repositories) is judged by `sh release/v26.9.23/courts/CE23-12.sh`, not here.
"""

from __future__ import annotations

import importlib.util
import json
import shutil
import site
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
BENCH = ROOT / "release" / "v26.9.23" / "bench"
SCRIPTS = BENCH / "pack" / "scripts"
COURT = ROOT / "release" / "v26.9.23" / "courts" / "ce23_12"


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


sys.path.insert(0, str(SCRIPTS))
kernel = load("t_evidence_tiers", SCRIPTS / "evidence_tiers.py")
doe = load("t_doe_verify", SCRIPTS / "doe_verify.py")
native = load("t_native_predicates", SCRIPTS / "native_predicates.py")
verify = load("t_verify", SCRIPTS / "verify.py")
court = load("t_ce23_12_court", COURT / "court.py")


class KernelCase(unittest.TestCase):
    def test_zero_defect_bounds_match_the_operator_table(self) -> None:
        self.assertEqual(kernel.round6(kernel.upper_bound(30, 0, 0.95)), "0.095034")
        self.assertEqual(kernel.round6(kernel.upper_bound(100, 0, 0.95)), "0.029513")
        self.assertEqual(kernel.round6(kernel.upper_bound(300, 0, 0.95)), "0.009936")
        self.assertEqual(kernel.round6(kernel.upper_bound(3000, 0, 0.95)), "0.000998")
        self.assertEqual(kernel.upper_bound(0, 0, 0.95), 1.0)

    def test_bounds_agree_with_scipy_beta_quantile(self) -> None:
        try:
            from scipy.stats import beta  # noqa: PLC0415
        except ImportError:
            self.skipTest("scipy absent")
        for n in (5, 30, 31, 59, 100, 300):
            for x in (1, 2, 5):
                if x < n:
                    self.assertAlmostEqual(kernel.upper_bound(n, x, 0.95), float(beta.ppf(0.95, x + 1, n - x)), delta=1e-9)

    def test_yield_sizes_follow_the_closed_form(self) -> None:
        self.assertEqual(kernel.min_n_for_lower_bound(0.05, 0.95, 0.95), 59)
        self.assertEqual(kernel.min_n_for_lower_bound(0.05, 0.90, 0.95), 29)
        self.assertEqual(kernel.min_n_zero_defect(0.05, 0.10), 29)
        self.assertEqual(kernel.min_n_zero_defect(0.05, 0.001), 2995)

    def test_committed_tables_equal_a_fresh_computation(self) -> None:
        k = kernel.Kernel(BENCH)
        tiers, bounds, _ = k.render()
        self.assertEqual((BENCH / "generated/evidence-tiers.ttl").read_text(encoding="utf-8"), tiers)
        self.assertEqual((BENCH / "generated/bound-table.ttl").read_text(encoding="utf-8"), bounds)


class DoeCase(unittest.TestCase):
    def setUp(self) -> None:
        self.design = json.loads((BENCH / "out/doe/design-matrix.json").read_text(encoding="utf-8"))

    def test_committed_design_is_resolution_iv(self) -> None:
        a = doe.analyse(self.design)
        self.assertEqual(a["resolution"], 4)
        self.assertEqual(a["defining_relation"], "I=ABCE=ADEF=BCDF")
        self.assertTrue(a["balanced"] and a["orthogonal"])
        self.assertEqual(a["runs"], 16)

    def test_toolchain_generated_by_cold_and_concurrency_drops_to_resolution_iii(self) -> None:
        for run in self.design["runs"]:
            run["coded"]["E"] = run["coded"]["A"] * run["coded"]["B"]
        self.assertEqual(doe.analyse(self.design)["resolution"], 3)

    def test_os_factor_never_in_a_run(self) -> None:
        self.assertNotIn("OS", {f["factor"] for f in self.design["factors"]})
        self.assertIn("OS", {n["factor"] for n in self.design["not_varied"]})


class InstrumentCase(unittest.TestCase):
    """The fast instruments (native evaluator, SPARQL on pyoxigraph) over the committed design."""

    @classmethod
    def setUpClass(cls) -> None:
        try:
            import pyoxigraph  # noqa: F401, PLC0415
            import rdflib  # noqa: PLC0415
        except ImportError:
            raise unittest.SkipTest("rdflib or pyoxigraph absent")
        cls.base = verify.load_union(BENCH)
        cls.inst = verify.Instruments(BENCH, rdflib.Graph().parse(BENCH / "design.ttl", format="turtle"))
        cls.corpus = {a.id: a for a in verify.load_corpus(COURT / "mutations.toml")}

    def judge(self, art_id: str):
        g = self.corpus[art_id].apply(self.base)
        return self.inst.native(g), self.inst.sparql_oxigraph(g)

    def test_committed_design_admitted(self) -> None:
        (a1, laws1, _), (a2, laws2, _) = self.judge("G0")
        self.assertTrue(a1, laws1)
        self.assertTrue(a2, laws2)

    def test_lawful_discovery_tuple_admitted(self) -> None:
        (a1, _, d1), (a2, _, d2) = self.judge("G1")
        self.assertTrue(a1, d1)
        self.assertTrue(a2, d2)

    def test_overclaim_refused_under_standing(self) -> None:
        for mid in ("M2", "M3", "M4", "M5", "M6", "M10", "M25"):
            (a1, laws1, _), (a2, laws2, _) = self.judge(mid)
            self.assertFalse(a1, mid)
            self.assertIn("STANDING", laws1, mid)
            self.assertFalse(a2, mid)
            self.assertIn("STANDING", laws2, mid)

    def test_os_column_refused_under_factor(self) -> None:
        (a1, laws1, _), (a2, laws2, _) = self.judge("M7")
        self.assertEqual((a1, a2), (False, False))
        self.assertIn("FACTOR", laws1)
        self.assertIn("FACTOR", laws2)

    def test_every_removal_pattern_matches(self) -> None:
        for art in self.corpus.values():
            art.apply(self.base)  # raises ValueError on a vacuous (matching-nothing) removal

    def test_native_split_law_sees_a_patch_id_leak(self) -> None:
        g = self.corpus["M13"].apply(self.base)
        self.assertTrue(native.law_split(g))


class ReceiptAdmissionCase(unittest.TestCase):
    classes = ["class-a", "class-b"]

    def receipt(self) -> dict:
        return {
            "identity": {"subject_sha": "a" * 40, "bench_tree": "b" * 40, "conjunct": "BenchmarkDesign"},
            "standing": {"value": "ALIVE"},
            "non_llm_operational": {c: {"standing": "UNKNOWN", "n": 0} for c in self.classes},
            "environment": {"os_factor": "UNSUPPORTED", "statement": court.PINS["statement"]["os_ceiling"]},
        }

    def admit(self, r: dict) -> list[str]:
        return court.admit_receipt(r, "BenchmarkDesign", "a" * 40, "b" * 40, self.classes)

    def test_exact_head_receipt_admitted(self) -> None:
        self.assertEqual(self.admit(self.receipt()), [])

    def test_stale_subject_refused(self) -> None:
        r = self.receipt()
        r["identity"]["subject_sha"] = "c" * 40
        self.assertIn("stale_receipt:subject_sha", self.admit(r))

    def test_operational_claim_refused(self) -> None:
        r = self.receipt()
        r["non_llm_operational"]["class-a"] = {"standing": "NON_LLM_OPERATIONAL_ALIVE", "n": 30}
        self.assertIn("operational_claimed:class-a", self.admit(r))

    def test_varied_os_refused(self) -> None:
        r = self.receipt()
        r["environment"]["os_factor"] = "VARIED"
        self.assertIn("os_ceiling_unstated", self.admit(r))

    def test_kappa_undefined_without_both_classes(self) -> None:
        self.assertIsNone(court.cohen_kappa([True, True], [True, True]))
        self.assertEqual(court.cohen_kappa([True, False, True], [True, False, True]), 1.0)


class EndToEndCase(unittest.TestCase):
    """The real GeneratedQualificationPlan court on a synthetic git repository whose design holds a
    hand-written work order: the court must exit 1 with REFUSED[handwritten_work_order]."""

    def test_handwritten_order_refused_by_the_court(self) -> None:
        if shutil.which("ggen") is None:
            self.skipTest("ggen absent")
        tmp = tempfile.TemporaryDirectory(prefix="ce23-12-e2e.")
        self.addCleanup(tmp.cleanup)
        repo = Path(tmp.name) / "repo"
        repo.mkdir()
        archive = subprocess.run(["git", "-C", str(ROOT), "archive", "HEAD", "release/v26.9.23/bench", "release/v26.9.23/sjira",
                                  "release/v26.9.23/courts"], capture_output=True, check=True).stdout
        subprocess.run(["tar", "-x", "-C", str(repo)], input=archive, check=True)
        design = repo / "release/v26.9.23/bench/design.ttl"
        design.write_text(design.read_text(encoding="utf-8") + "\nce23:hand-order a sj:WorkOrder .\n", encoding="utf-8")
        for cmd in (["init", "-q"], ["-c", "user.email=t@local", "-c", "user.name=t", "commit", "-q", "--allow-empty", "-m", "base"],
                    ["add", "-A"], ["-c", "user.email=t@local", "-c", "user.name=t", "commit", "-q", "-m", "mutant"]):
            subprocess.run(["git", "-C", str(repo), *cmd], check=True, capture_output=True)
        proc = subprocess.run([sys.executable, str(COURT / "court.py"), "gqp", "--root", str(repo), "--no-av"],
                              capture_output=True, text=True, timeout=1200,
                              env={"PATH": f"{Path(sys.executable).parent}:{Path(shutil.which('ggen')).resolve().parent}:/usr/bin:/bin",
                                   "HOME": str(Path.home()), "PYTHONDONTWRITEBYTECODE": "1",
                                   "PYTHONUSERBASE": site.getuserbase(), "LANG": "en_US.UTF-8"})
        if proc.returncode == 75 and "REFUSED[" not in proc.stdout:
            self.skipTest("the court typed an absent tool UNKNOWN: " + proc.stdout.strip().splitlines()[0])
        self.assertEqual(proc.returncode, 1, proc.stdout[-2000:])
        self.assertIn("REFUSED[handwritten_work_order] A4", proc.stdout)


if __name__ == "__main__":
    unittest.main()
