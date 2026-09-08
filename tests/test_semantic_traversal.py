from __future__ import annotations

import copy
from pathlib import Path
import sys
import tomllib
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from verify_semantic_traversal import manufacture_receipt, verify_document, verify_receipt  # noqa: E402


class SemanticTraversalContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.contract_path = ROOT / "catalog" / "semantic-traversal.toml"
        with cls.contract_path.open("rb") as handle:
            cls.canonical = tomllib.load(handle)

    def document(self) -> dict:
        return copy.deepcopy(self.canonical)

    def test_canonical_contract_is_admitted(self) -> None:
        self.assertEqual([], verify_document(self.document()))

    def test_correspondence_drift_refuses(self) -> None:
        document = self.document()
        document["correspondence"]["stages"].remove("admission")
        self.assertIn("REFUSED:CORRESPONDENCE_DRIFT", verify_document(document))

    def test_duplicate_metric_refuses(self) -> None:
        document = self.document()
        document["metric"].append(copy.deepcopy(document["metric"][0]))
        self.assertTrue(
            any(finding.startswith("REFUSED:DUPLICATE_METRIC:") for finding in verify_document(document))
        )

    def test_missing_invariant_refuses(self) -> None:
        document = self.document()
        document["invariant"] = [
            item for item in document["invariant"] if item["id"] != "GENERATED_IS_PROJECTION"
        ]
        self.assertIn(
            "REFUSED:MISSING_INVARIANT:GENERATED_IS_PROJECTION",
            verify_document(document),
        )

    def test_derived_formula_drift_refuses(self) -> None:
        document = self.document()
        document["derived_metric"][0]["formula"] = "semantic_fact_count / interpretation_count"
        self.assertIn(
            "REFUSED:DERIVED_FORMULA_DRIFT:mean_semantic_traversal",
            verify_document(document),
        )

    def test_zero_denominator_must_remain_unknown(self) -> None:
        document = self.document()
        document["derived_metric"][0]["zero_denominator"] = "0"
        self.assertIn(
            "REFUSED:ZERO_DENOMINATOR_NOT_UNKNOWN:mean_semantic_traversal",
            verify_document(document),
        )

    def test_do_without_broker_refuses(self) -> None:
        document = self.document()
        actuation = next(route for route in document["route"] if route["id"] == "actuation")
        actuation["broker_required"] = False
        self.assertIn("REFUSED:AMBIENT_DO:actuation", verify_document(document))

    def test_route_owner_drift_refuses(self) -> None:
        document = self.document()
        manufacture = next(route for route in document["route"] if route["id"] == "manufacture")
        manufacture["owner"] = "repository:chatman-ecosystem"
        self.assertIn("REFUSED:ROUTE_OWNER_DRIFT:manufacture", verify_document(document))

    def test_exact_subject_receipt_replays(self) -> None:
        receipt = manufacture_receipt(self.contract_path, "a" * 40)
        self.assertEqual([], verify_receipt(receipt, self.contract_path, "a" * 40))

    def test_receipt_exact_subject_drift_refuses(self) -> None:
        receipt = manufacture_receipt(self.contract_path, "a" * 40)
        self.assertIn(
            "REFUSED:RECEIPT_EXACT_SUBJECT_DRIFT",
            verify_receipt(receipt, self.contract_path, "b" * 40),
        )

    def test_receipt_tamper_refuses(self) -> None:
        receipt = manufacture_receipt(self.contract_path, "a" * 40)
        receipt["exclusions"][0] = "cross-repository runtime traversal claimed"
        findings = verify_receipt(receipt, self.contract_path, "a" * 40)
        self.assertIn("REFUSED:RECEIPT_EXCLUSIONS_DRIFT", findings)
        self.assertIn("REFUSED:RECEIPT_INTEGRITY", findings)


if __name__ == "__main__":
    unittest.main()
