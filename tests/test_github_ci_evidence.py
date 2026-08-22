import unittest
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parents[1] / "scripts"))
import github_ci_evidence as m

SHA = "a" * 40


def run(i, name, status="completed", conclusion="success", sha=SHA):
    return {
        "id": i,
        "name": name,
        "event": "pull_request",
        "head_sha": sha,
        "status": status,
        "conclusion": conclusion,
        "html_url": f"https://example/{i}",
    }


class GithubCiEvidenceTests(unittest.TestCase):
    def test_all_success_is_partial_alive_ci_only(self):
        doc = m.manufacture("o/r", SHA, {"workflow_runs": [run(2, "B"), run(1, "A")]})
        self.assertEqual(doc["standing"], "PARTIAL_ALIVE")
        self.assertEqual(doc["counts"], {"PASS": 2, "FAIL": 0, "PENDING": 0})
        m.verify_receipt(doc)

    def test_failure_is_build_broken(self):
        doc = m.manufacture("o/r", SHA, {"workflow_runs": [run(1, "A", conclusion="failure")]})
        self.assertEqual(doc["standing"], "BUILD_BROKEN")

    def test_pending_never_false_positive(self):
        doc = m.manufacture("o/r", SHA, {"workflow_runs": [run(1, "A", status="in_progress", conclusion=None)]})
        self.assertEqual(doc["standing"], "UNKNOWN")

    def test_empty_never_claims_success(self):
        doc = m.manufacture("o/r", SHA, {"workflow_runs": []})
        self.assertEqual(doc["standing"], "UNKNOWN")

    def test_stale_head_refuses(self):
        with self.assertRaisesRegex(m.Refusal, "expected="):
            m.manufacture("o/r", SHA, {"workflow_runs": [run(1, "A", sha="b" * 40)]})

    def test_tamper_breaks_replay(self):
        doc = m.manufacture("o/r", SHA, {"workflow_runs": [run(1, "A")]})
        doc["runs"][0]["standing"] = "FAIL"
        with self.assertRaises(m.Refusal):
            m.verify_receipt(doc)

    def test_deterministic_order_and_receipt(self):
        first = m.manufacture("o/r", SHA, {"workflow_runs": [run(2, "B"), run(1, "A")]})
        second = m.manufacture("o/r", SHA, {"workflow_runs": [run(1, "A"), run(2, "B")]})
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
