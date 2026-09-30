from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
COURT_PATH = ROOT / "scripts" / "release_train" / "universal_laws_court.py"
VECTORS_PATH = ROOT / "tests" / "universal-laws" / "vectors.json"
SCHEMA_PATH = ROOT / "schemas" / "universal-laws" / "conformance.schema.json"
ONTOLOGY_PATH = ROOT / "ontology" / "universal-laws" / "universal-laws.ttl"

_spec = importlib.util.spec_from_file_location("universal_laws_court", COURT_PATH)
assert _spec and _spec.loader
court = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(court)


class UniversalLawsCourtTest(unittest.TestCase):
    def test_portable_vectors_match_expected_results(self) -> None:
        receipt, code = court.run(str(VECTORS_PATH))
        self.assertEqual(0, code)
        self.assertEqual("ALIVE", receipt["standing"])
        self.assertEqual("NONE", receipt["authority"])
        self.assertEqual(14, receipt["cases"])
        self.assertEqual(14, receipt["attempts_observed"])
        self.assertEqual([], receipt["mismatches"])

    def test_positive_control_is_not_vacuous(self) -> None:
        document = json.loads(VECTORS_PATH.read_text(encoding="utf-8"))
        positive = next(
            item for item in document["cases"] if item["id"] == "qualified-equivalence"
        )
        result = court.evaluate_case(positive)
        self.assertTrue(result.attempt_observed)
        self.assertFalse(result.violation_observed)
        self.assertEqual("ADMISSIBLE", result.result)

    def test_unknown_law_fails_closed_to_unknown(self) -> None:
        result = court.evaluate_case({"id": "future-law", "law": "L99"})
        self.assertEqual("UNKNOWN", result.result)
        self.assertTrue(result.attempt_observed)

    def test_negative_value_is_below_null(self) -> None:
        result = court.evaluate_case(
            {
                "id": "negative",
                "law": "NULL",
                "candidate_value": -0.01,
                "null_value": 0,
                "adopted": True,
            }
        )
        self.assertEqual("REFUSED", result.result)

    def test_machine_schema_is_authority_free(self) -> None:
        schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
        self.assertEqual("NONE", schema["properties"]["authority"]["const"])
        self.assertEqual(
            ["UQ0", "UQ1", "UQ2", "UQ3", "UQ4", "UQ5", "UQ6", "UQ7"],
            schema["properties"]["level"]["enum"],
        )

    def test_ontology_declares_every_normative_law(self) -> None:
        text = ONTOLOGY_PATH.read_text(encoding="utf-8")
        for law in [f"L{i}" for i in range(1, 13)] + ["NULL"]:
            self.assertIn(f"ul:{law} a ul:Law", text)


if __name__ == "__main__":
    unittest.main()
