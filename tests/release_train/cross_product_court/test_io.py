from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.release_train.cross_product_court.__main__ import run
from scripts.release_train.cross_product_court.io import (
    load_case,
    receipt_dict,
)


class CrossProductIoTests(unittest.TestCase):
    def test_json_case_round_trip_and_receipt(self) -> None:
        tla_sha = "1" * 40
        ocel_sha = "4" * 40
        d1 = "sha256:" + "2" * 64
        d2 = "sha256:" + "3" * 64
        d3 = "sha256:" + "5" * 64
        payload = {
            "case_id": "XPROD-JSON",
            "semantic_subject_id": "urn:chatman:xprod:test",
            "subjects": [
                {
                    "repository": "seanchatmangpt/autofde-lab",
                    "subject_sha": tla_sha,
                },
                {
                    "repository": "seanchatmangpt/gymact",
                    "subject_sha": ocel_sha,
                },
            ],
            "required_formalisms": ["TLA+", "OCEL2"],
            "evidence": [
                {
                    "evidence_id": "tla-1",
                    "repository": "seanchatmangpt/autofde-lab",
                    "subject_sha": tla_sha,
                    "formalism": "TLA+",
                    "claim_id": "trace-safe",
                    "artifact_digest": d1,
                    "validator": "tlc2.TLC",
                    "validator_digest": d2,
                    "result": "PASS",
                },
                {
                    "evidence_id": "ocel-1",
                    "repository": "seanchatmangpt/gymact",
                    "subject_sha": ocel_sha,
                    "formalism": "OCEL2",
                    "claim_id": "trace-safe",
                    "artifact_digest": d3,
                    "validator": "ocel-validator",
                    "validator_digest": d2,
                    "result": "PASS",
                },
            ],
            "relations": [
                {
                    "relation_id": "OCELxTLA",
                    "left": "OCEL2",
                    "right": "TLA+",
                    "claim_id": "trace-safe",
                }
            ],
            "mutants": [],
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            case = load_case(path)
            receipt = receipt_dict(case)
        self.assertEqual(receipt["standing"], "ALIVE")
        self.assertEqual(receipt["authority"], "NONE")
        self.assertEqual(len(receipt["subject_bindings"]), 2)
        self.assertTrue(
            receipt["receipt_digest"].startswith("sha256:")
        )

    def test_authority_do_case_is_a_typed_refusal_not_a_crash(self) -> None:
        sha = "1" * 40
        payload = {
            "case_id": "XPROD-DO",
            "semantic_subject_id": "urn:chatman:xprod:test-do",
            "subjects": [
                {"repository": "seanchatmangpt/autofde-lab", "subject_sha": sha}
            ],
            "required_formalisms": ["TLA+"],
            "evidence": [
                {
                    "evidence_id": "tla-do",
                    "repository": "seanchatmangpt/autofde-lab",
                    "subject_sha": sha,
                    "formalism": "TLA+",
                    "claim_id": "trace-safe",
                    "artifact_digest": "sha256:" + "2" * 64,
                    "validator": "tlc2.TLC",
                    "validator_digest": "sha256:" + "3" * 64,
                    "result": "PASS",
                    "authority": "DO",
                }
            ],
        }
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            data, code = run(str(path))
        self.assertEqual(code, 2)
        self.assertEqual(data["standing"], "REFUSED")
        self.assertEqual(data["authority"], "NONE")
        self.assertEqual(
            data["refusals"],
            [
                "REFUSED:INADMISSIBLE_CASE:"
                "cross-product evidence projections carry no authority"
            ],
        )

    def test_missing_field_is_a_typed_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "case.json"
            path.write_text(json.dumps({"case_id": "x"}), encoding="utf-8")
            data, code = run(str(path))
        self.assertEqual(code, 2)
        self.assertTrue(
            data["refusals"][0].startswith(
                "REFUSED:INADMISSIBLE_CASE:missing field"
            )
        )


if __name__ == "__main__":
    unittest.main()
