import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path

MODULE_PATH = Path(__file__).parents[1] / "scripts" / "verify_ci_subject.py"
spec = importlib.util.spec_from_file_location("verify_ci_subject", MODULE_PATH)
subject = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(subject)

HEAD = "a" * 40
MERGE = "b" * 40


class VerifyCiSubjectTests(unittest.TestCase):
    def pr_event(self):
        return {"pull_request": {"head": {"sha": HEAD}}}

    def test_pr_head_is_admitted_exact_subject(self):
        receipt = subject.build_receipt(event_name="pull_request", event=self.pr_event(), fallback_sha=MERGE, actual_sha=HEAD)
        self.assertEqual(receipt["expected_sha"], HEAD)
        self.assertEqual(receipt["expected_source"], "pull_request.head.sha")
        self.assertTrue(subject.verify_receipt(receipt))

    def test_synthetic_pr_merge_sha_is_refused(self):
        with self.assertRaisesRegex(subject.SubjectError, r"REFUSED\[SUBJECT_SHA_MISMATCH\]"):
            subject.build_receipt(event_name="pull_request", event=self.pr_event(), fallback_sha=MERGE, actual_sha=MERGE)

    def test_missing_pr_head_is_refused(self):
        with self.assertRaisesRegex(subject.SubjectError, r"REFUSED\[MISSING_PULL_REQUEST_HEAD\]"):
            subject.build_receipt(event_name="pull_request", event={"pull_request": {}}, fallback_sha=HEAD, actual_sha=HEAD)

    def test_non_pr_event_uses_fallback_sha(self):
        receipt = subject.build_receipt(event_name="workflow_dispatch", event={}, fallback_sha=HEAD, actual_sha=HEAD)
        self.assertEqual(receipt["expected_source"], "github.sha")
        self.assertTrue(subject.verify_receipt(receipt))

    def test_tampered_receipt_fails_replay(self):
        receipt = subject.build_receipt(event_name="pull_request", event=self.pr_event(), fallback_sha=MERGE, actual_sha=HEAD)
        tampered = copy.deepcopy(receipt)
        tampered["actual_sha"] = MERGE
        self.assertFalse(subject.verify_receipt(tampered))

    def test_cli_replay_round_trip(self):
        receipt = subject.build_receipt(event_name="pull_request", event=self.pr_event(), fallback_sha=MERGE, actual_sha=HEAD)
        with tempfile.TemporaryDirectory() as td:
            path = Path(td) / "receipt.json"
            path.write_text(json.dumps(receipt), encoding="utf-8")
            self.assertEqual(subject.main(["--replay", str(path)]), 0)


if __name__ == "__main__":
    unittest.main()
