from __future__ import annotations

import copy
import unittest
from datetime import datetime, timezone

from scripts.reconcile_portfolio_activity import (
    CensusError,
    Window,
    build_census,
    verify_receipt,
)


class FakeClient:
    def __init__(self, repos, prs, evidence=None):
        self.repos = repos
        self.prs = prs
        self.evidence = evidence or {
            "reported_total_count": len(prs),
            "retrieved_count": len(prs),
            "search_cap": 1000,
            "incomplete_results": False,
        }

    def list_public_owner_repositories(self, owner):
        return copy.deepcopy(self.repos)

    def search_updated_pull_requests(self, owner, since, until):
        return copy.deepcopy(self.prs), copy.deepcopy(self.evidence)


class RefusingClient(FakeClient):
    def search_updated_pull_requests(self, owner, since, until):
        raise CensusError("REFUSED[PR_SEARCH_CAP] total_count=1001")


class CensusTests(unittest.TestCase):
    def setUp(self):
        self.window = Window(
            datetime(2026, 8, 15, tzinfo=timezone.utc),
            datetime(2026, 8, 22, tzinfo=timezone.utc),
        )

    def test_pr_only_repository_is_preserved_in_union(self):
        client = FakeClient(
            repos=[
                {
                    "full_name": "seanchatmangpt/gymact",
                    "pushed_at": "2026-08-21T12:00:00Z",
                },
                {
                    "full_name": "seanchatmangpt/ash_r2ml",
                    "pushed_at": "2026-08-01T12:00:00Z",
                },
            ],
            prs=[
                {
                    "repository_url": "https://api.github.com/repos/seanchatmangpt/ash_r2ml",
                    "updated_at": "2026-08-21T18:00:00Z",
                }
            ],
        )
        result = build_census(client, owner="seanchatmangpt", window=self.window)
        self.assertEqual(
            result["reconciliation"]["union_repositories"],
            ["seanchatmangpt/ash_r2ml", "seanchatmangpt/gymact"],
        )
        self.assertEqual(
            result["reconciliation"]["pr_only_repositories"],
            ["seanchatmangpt/ash_r2ml"],
        )
        self.assertFalse(result["reconciliation"]["single_sensor_complete_activity_claim"])
        self.assertTrue(verify_receipt(result))

    def test_exact_half_open_window_excludes_until_boundary(self):
        client = FakeClient(
            repos=[
                {
                    "full_name": "seanchatmangpt/in",
                    "pushed_at": "2026-08-15T00:00:00Z",
                },
                {
                    "full_name": "seanchatmangpt/out",
                    "pushed_at": "2026-08-22T00:00:00Z",
                },
            ],
            prs=[],
        )
        result = build_census(client, owner="seanchatmangpt", window=self.window)
        self.assertEqual(result["reconciliation"]["union_repositories"], ["seanchatmangpt/in"])

    def test_receipt_rejects_tampered_sensor_result(self):
        result = build_census(
            FakeClient(
                repos=[{"full_name": "seanchatmangpt/a", "pushed_at": "2026-08-20T00:00:00Z"}],
                prs=[],
            ),
            owner="seanchatmangpt",
            window=self.window,
        )
        result["reconciliation"]["union_repository_count"] = 999
        self.assertFalse(verify_receipt(result))

    def test_pr_search_cap_refusal_propagates(self):
        with self.assertRaisesRegex(CensusError, r"REFUSED\[PR_SEARCH_CAP\]"):
            build_census(
                RefusingClient([], []),
                owner="seanchatmangpt",
                window=self.window,
            )

    def test_malformed_rows_do_not_become_activity(self):
        client = FakeClient(
            repos=[
                {"full_name": "other/repo", "pushed_at": "2026-08-20T00:00:00Z"},
                {"full_name": "seanchatmangpt/no-time"},
            ],
            prs=[
                {"repository_url": "garbage", "updated_at": "2026-08-20T00:00:00Z"},
                {
                    "repository_url": "https://api.github.com/repos/other/repo",
                    "updated_at": "2026-08-20T00:00:00Z",
                },
            ],
        )
        result = build_census(client, owner="seanchatmangpt", window=self.window)
        self.assertEqual(result["reconciliation"]["union_repository_count"], 0)
        self.assertGreater(result["sensors"]["public_owner_repository_push"]["malformed_rows"], 0)
        self.assertGreater(result["sensors"]["updated_pull_request"]["malformed_rows"], 0)


if __name__ == "__main__":
    unittest.main()
