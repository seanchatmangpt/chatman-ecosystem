from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

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
                    "artifact_digest": d1,
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


if __name__ == "__main__":
    unittest.main()
