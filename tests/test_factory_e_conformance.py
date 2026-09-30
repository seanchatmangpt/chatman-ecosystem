import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).parents[1]
spec = importlib.util.spec_from_file_location("fe", ROOT / "scripts" / "factory_e_conformance.py")
fe = importlib.util.module_from_spec(spec); spec.loader.exec_module(fe)
FX = ROOT / "tests" / "fixtures" / "factory_e"
NOW = "2026-09-30T12:00:00Z"


def load(name):
    return json.loads((FX / f"{name}.json").read_text())


class PositiveTests(unittest.TestCase):
    def test_positive_fixtures_conform(self):
        for n in ("positive_partial", "positive_alive_independent", "positive_fibo", "positive_extended"):
            with self.subTest(n):
                self.assertTrue(fe.check(load(n), now=NOW)["conformant"])


class NegativeTests(unittest.TestCase):
    CASES = {
        "neg_schema_invalid": "SCHEMA_INVALID",
        "neg_missing_law": "MISSING_LAW",
        "neg_duplicate_law": "DUPLICATE_LAW",
        "neg_foreign_subject": "STALE_OR_FOREIGN_SUBJECT",
        "neg_alive_without_execution": "ALIVE_WITHOUT_EXECUTION",
        "neg_self_certified": "SELF_CERTIFIED",
        "neg_hidden_semantics": "HIDDEN_SEMANTICS",
        "neg_do_unauthorized": "CONSEQUENCE_UNAUTHORIZED",
        "neg_actuating_replay": "ACTUATING_REPLAY",
        "neg_profile_override": "PROFILE_WEAKENS_CORE",
        "neg_expired_horizon": "EVIDENCE_HORIZON_EXPIRED",
        "neg_negative_value": "NEGATIVE_VALUE_CHANGE",
        "neg_chesterton": "CHESTERTON_VIOLATION",
        "neg_vacuous_court": "VACUOUS_COURT",
        "neg_violation_observed": "VIOLATION_OBSERVED",
        "neg_unhardened": "UNHARDENED_FAILURE",
        "neg_hardening_escape": "UNHARDENED_FAILURE",
        "neg_chicago_disjunctive": "CHICAGO_NOT_CONJUNCTIVE",
        "neg_external_unqualified": "EXTERNAL_NOT_REQUALIFIED",
        "neg_external_unpinned": "SCHEMA_INVALID",
        "neg_artifact_unobserved": "SCHEMA_INVALID",
    }

    def test_each_negative_gets_its_typed_refusal(self):
        for n, code in self.CASES.items():
            with self.subTest(n):
                with self.assertRaises(fe.Refusal) as cm:
                    fe.check(load(n), now=NOW)
                self.assertEqual(cm.exception.code, code)

    def test_fibo_term_without_fibo_owner_refused(self):
        d = load("positive_fibo")
        d["terms"][-1]["owner"] = "acme/other"
        with self.assertRaises(fe.Refusal) as cm:
            fe.check(d, now=NOW)
        self.assertEqual(cm.exception.code, "HIDDEN_SEMANTICS")


class ReferenceMapTests(unittest.TestCase):
    def test_reference_map_is_evidence_not_dependency(self):
        ref = json.loads((ROOT / "docs" / "rfc" / "v26.9.29-factory-e-reference-map.json").read_text())
        src = (ROOT / "scripts" / "factory_e_conformance.py").read_text()
        for e in ref["references"]:
            self.assertEqual(e["role"], "reference_evidence")
            self.assertEqual(e["standing"], "UNKNOWN")
            self.assertNotIn("sha", e)
            self.assertNotIn(e["repo"].split("/")[1], src)


class RunnerTests(unittest.TestCase):
    def test_runner_is_non_mutating(self):
        before = (FX / "positive_partial.json").read_bytes()
        self.assertEqual(fe.main(["x", str(FX / "positive_partial.json")]), 0)
        self.assertEqual(fe.main(["x", str(FX / "neg_missing_law.json")]), 1)
        self.assertEqual(before, (FX / "positive_partial.json").read_bytes())

    def test_schema_law_ids_match_runner_core(self):
        s = json.loads(fe.SCHEMA.read_text())
        self.assertEqual(s["$defs"]["law"]["properties"]["id"]["enum"], fe.CORE)


if __name__ == "__main__":
    unittest.main()
