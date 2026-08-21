import hashlib
import unittest

import scripts.reconcile_ci_outcomes as m


def receipt(payload):
    digest = hashlib.sha256(m.canonical_bytes(payload)).hexdigest()
    return {**payload, "receipt": {"algorithm": "sha256", "observation_digest": digest}}


def activity(repos=None):
    repos = repos or ["seanchatmangpt/a", "seanchatmangpt/b"]
    return receipt({
        "schema": "chatman.portfolio-activity-census/2",
        "owner": "seanchatmangpt",
        "window": {"since": "2026-08-15T00:00:00Z", "until": "2026-08-22T00:00:00Z"},
        "reconciliation": {"union_repositories": repos},
    })


class Fake:
    def __init__(self, rows):
        self.rows = rows

    def list_workflow_runs(self, repo, since, until):
        return list(self.rows.get(repo, []))


def run(i, at, status="completed", conclusion="success", name="CI"):
    return {
        "id": i,
        "created_at": at,
        "status": status,
        "conclusion": conclusion,
        "name": name,
        "event": "pull_request",
        "head_sha": "a" * 40,
    }


class Tests(unittest.TestCase):
    def test_reconciles_ci_and_no_ci_repositories(self):
        rows = {
            "seanchatmangpt/a": [
                run(1, "2026-08-16T00:00:00Z"),
                run(2, "2026-08-17T00:00:00Z", conclusion="failure"),
            ],
            "seanchatmangpt/b": [],
        }
        result = m.build_ci_census(Fake(rows), activity())
        self.assertEqual(1, result["summary"]["repositories_with_observed_ci_runs"])
        self.assertEqual(1, result["summary"]["repositories_without_observed_ci_runs"])
        self.assertEqual(1, result["summary"]["repositories_with_failure_like_outcomes"])
        self.assertEqual(2, result["summary"]["observed_run_count"])
        self.assertEqual(0.5, result["summary"]["ci_observation_coverage"])
        self.assertTrue(m.verify_receipt(result))

    def test_half_open_window_excludes_until(self):
        rows = {
            "seanchatmangpt/a": [
                run(1, "2026-08-15T00:00:00Z"),
                run(2, "2026-08-22T00:00:00Z"),
            ],
            "seanchatmangpt/b": [],
        }
        result = m.build_ci_census(Fake(rows), activity())
        self.assertEqual(1, result["summary"]["observed_run_count"])

    def test_pending_is_not_success(self):
        rows = {
            "seanchatmangpt/a": [
                run(1, "2026-08-16T00:00:00Z", status="in_progress", conclusion=None)
            ],
            "seanchatmangpt/b": [],
        }
        result = m.build_ci_census(Fake(rows), activity())
        self.assertEqual(1, result["summary"]["pending_run_count"])
        self.assertEqual(0, result["summary"]["completed_run_count"])
        self.assertEqual(1, result["summary"]["conclusion_counts"]["STATUS:in_progress"])

    def test_tampered_activity_receipt_refused(self):
        subject = activity()
        subject["owner"] = "other"
        with self.assertRaisesRegex(m.CIOutcomeError, "ACTIVITY_CENSUS_RECEIPT"):
            m.build_ci_census(Fake({}), subject)

    def test_foreign_repo_refused(self):
        with self.assertRaisesRegex(m.CIOutcomeError, "ACTIVITY_REPOSITORY_OUT_OF_SCOPE"):
            m.build_ci_census(Fake({}), activity(["other/a"]))

    def test_duplicate_run_identity_deduplicated(self):
        row = run(1, "2026-08-16T00:00:00Z")
        result = m.build_ci_census(
            Fake({"seanchatmangpt/a": [row, dict(row)], "seanchatmangpt/b": []}),
            activity(),
        )
        self.assertEqual(1, result["summary"]["observed_run_count"])
        self.assertEqual(1, result["repositories"][0]["duplicate_rows"])

    def test_missing_run_identity_refused(self):
        bad = run(1, "2026-08-16T00:00:00Z")
        bad.pop("id")
        with self.assertRaisesRegex(m.CIOutcomeError, "CI_RUN_IDENTITY_MISSING"):
            m.build_ci_census(
                Fake({"seanchatmangpt/a": [bad], "seanchatmangpt/b": []}),
                activity(),
            )

    def test_tampered_output_receipt_fails_replay(self):
        result = m.build_ci_census(
            Fake({"seanchatmangpt/a": [], "seanchatmangpt/b": []}), activity()
        )
        result["summary"]["observed_run_count"] = 99
        self.assertFalse(m.verify_receipt(result))


if __name__ == "__main__":
    unittest.main()
