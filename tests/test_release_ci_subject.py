from __future__ import annotations

import copy
import unittest

from scripts.verify_release_ci_subject import SubjectRefusal, manufacture, replay


A = "a" * 40
B = "b" * 40


class ReleaseCiSubjectTest(unittest.TestCase):
    def test_exact_subject_manufactures_replayable_receipt(self) -> None:
        receipt = manufacture(A, A, "pull_request", "pull_request.head.sha")
        self.assertEqual(replay(receipt), receipt)
        self.assertEqual(receipt["standing"], "VERIFIED")
        self.assertEqual(receipt["expected_sha"], A)

    def test_receipt_is_deterministic(self) -> None:
        first = manufacture(A, A, "pull_request", "pull_request.head.sha")
        second = manufacture(A, A, "pull_request", "pull_request.head.sha")
        self.assertEqual(first, second)

    def test_synthetic_or_stale_subject_is_refused(self) -> None:
        with self.assertRaisesRegex(SubjectRefusal, "SUBJECT_SHA_MISMATCH"):
            manufacture(A, B, "pull_request", "pull_request.head.sha")

    def test_malformed_sha_is_refused(self) -> None:
        with self.assertRaisesRegex(SubjectRefusal, "SUBJECT_SHA_INVALID"):
            manufacture("main", "main", "push", "github.sha")

    def test_tampered_receipt_is_refused(self) -> None:
        receipt = manufacture(A, A, "pull_request", "pull_request.head.sha")
        altered = copy.deepcopy(receipt)
        altered["actual_sha"] = B
        with self.assertRaisesRegex(SubjectRefusal, "SUBJECT_RECEIPT_TAMPERED"):
            replay(altered)

    def test_unverified_receipt_is_refused_even_with_recomputed_shape(self) -> None:
        receipt = manufacture(A, A, "pull_request", "pull_request.head.sha")
        receipt["standing"] = "UNKNOWN"
        with self.assertRaisesRegex(SubjectRefusal, "SUBJECT_RECEIPT_TAMPERED"):
            replay(receipt)


if __name__ == "__main__":
    unittest.main()
