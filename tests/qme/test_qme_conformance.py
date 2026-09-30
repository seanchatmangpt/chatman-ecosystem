import importlib.util
import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODULE = ROOT / "conformance" / "qme-1" / "qme_conformance.py"
FIXTURES = ROOT / "conformance" / "qme-1" / "fixtures"

spec = importlib.util.spec_from_file_location("qme_conformance", MODULE)
qme = importlib.util.module_from_spec(spec)
spec.loader.exec_module(qme)

REQUIRED_REFUSALS = {
    "EXACT_SUBJECT",
    "MXINF",
    "REPLAY_ACTUATES",
    "SELF_OBSERVED_DO",
    "VACUOUS_COURT",
    "VIOLATION_OBSERVED",
    "HIDDEN_SEMANTICS",
    "AUTHORITY_PROMOTION",
    "HIDDEN_GENERATION",
    "NEGATIVE_SUBJECT",
    "GUARD_RETIREMENT_UNGROUNDED",
    "EXTERNAL_AUTHORITY_PROMOTION",
    "NEGATIVE_VALUE_PROMOTED",
    "CANONICAL_OWNER_MISSING",
    "FALSIFIERS_MISSING",
}


class QMEConformanceTest(unittest.TestCase):
    def load(self, name):
        with (FIXTURES / name).open(encoding="utf-8") as handle:
            return json.load(handle)

    def test_valid_core_has_no_semantic_refusals(self):
        self.assertEqual(qme.court(self.load("valid-core.json")), [])

    def test_every_fixture_has_exact_expected_semantic_result(self):
        for path in sorted(FIXTURES.glob("*.json")):
            with self.subTest(path=path.name):
                record = self.load(path.name)
                self.assertEqual(
                    qme.court(record),
                    sorted(record.get("_expected_errors", [])),
                )

    def test_every_fixture_carries_the_required_schema_surface(self):
        with (ROOT / "schemas" / "qme-1" / "conformance.schema.json").open(
            encoding="utf-8"
        ) as handle:
            schema = json.load(handle)
        required = set(schema["required"])
        for path in FIXTURES.glob("*.json"):
            with self.subTest(path=path.name):
                self.assertTrue(required.issubset(self.load(path.name)))

    def test_every_semantic_refusal_has_a_killer_fixture(self):
        covered = set()
        for path in FIXTURES.glob("*.json"):
            covered.update(self.load(path.name).get("_expected_errors", []))
        self.assertEqual(REQUIRED_REFUSALS, covered)


if __name__ == "__main__":
    unittest.main()
