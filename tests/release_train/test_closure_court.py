from __future__ import annotations

import copy
import unittest

from scripts.release_train.closure_court import evaluate

A = "a" * 40
B = "b" * 40


def row() -> dict:
    return {
        "subject_id": "S1",
        "repository": "o/r",
        "sha": A,
        "artifact": "docs/spec.md",
        "spec_standing": "FINAL_SPEC",
        "impl_standing": "PLANNED",
        "authority_ceiling": "NONE",
        "authority_claimed": "NONE",
        "courts": [],
        "distribution": {"state": "NOT_APPLICABLE"},
    }


def closure() -> dict:
    return {
        "release": "v26.9.24",
        "normative_ledger": {"repository": "engineering-standards", "sha": B},
        "transient_heads": [{"sha": "c" * 40}],
        "subjects": [row()],
    }


class ClosureCourtTest(unittest.TestCase):
    def test_clean_terminal_subject_is_alive(self) -> None:
        self.assertEqual(evaluate(closure())["standing"], "ALIVE")

    def test_blocked_distribution_is_typed_partial_alive(self) -> None:
        data = closure()
        data["subjects"][0]["distribution"] = {
            "state": "BLOCKED",
            "type": "release-train-in-flight",
        }
        out = evaluate(data)
        self.assertEqual(out["standing"], "PARTIAL_ALIVE")
        self.assertEqual(
            out["remaining"],
            ["S1:distribution:BLOCKED(release-train-in-flight)"],
        )

    def test_duplicate_subject_refuses(self) -> None:
        data = closure()
        data["subjects"].append(copy.deepcopy(data["subjects"][0]))
        self.assertEqual(evaluate(data)["standing"], "REFUSED")

    def test_missing_exact_sha_refuses(self) -> None:
        data = closure()
        data["subjects"][0]["sha"] = "deadbeef"
        self.assertEqual(evaluate(data)["standing"], "REFUSED")

    def test_alive_requires_exact_pass(self) -> None:
        data = closure()
        data["subjects"][0]["impl_standing"] = "ALIVE"
        self.assertEqual(evaluate(data)["standing"], "REFUSED")
        data["subjects"][0]["courts"] = [{"name": "court", "result": "PASS", "sha": A}]
        self.assertEqual(evaluate(data)["standing"], "ALIVE")

    def test_court_subject_split_refuses(self) -> None:
        data = closure()
        data["subjects"][0]["courts"] = [{"name": "court", "result": "PASS", "sha": B}]
        self.assertEqual(evaluate(data)["standing"], "REFUSED")

    def test_authority_escalation_refuses(self) -> None:
        data = closure()
        data["subjects"][0]["authority_claimed"] = "DO"
        self.assertEqual(evaluate(data)["standing"], "REFUSED")

    def test_transient_pin_refuses(self) -> None:
        data = closure()
        data["subjects"][0]["pins"] = [{"sha": "c" * 40}]
        self.assertEqual(evaluate(data)["standing"], "REFUSED")

    def test_distribution_must_bind_same_sha(self) -> None:
        data = closure()
        data["subjects"][0]["distribution"] = {"state": "TAGGED", "sha": B, "ref": "v26.9.24"}
        self.assertEqual(evaluate(data)["standing"], "REFUSED")

    def test_superseded_requires_exact_successor(self) -> None:
        data = closure()
        data["subjects"][0]["spec_standing"] = "SUPERSEDED"
        self.assertEqual(evaluate(data)["standing"], "REFUSED")
        data["subjects"][0]["successor"] = {"repository": "o/r", "sha": B}
        self.assertEqual(evaluate(data)["standing"], "ALIVE")


if __name__ == "__main__":
    unittest.main()
