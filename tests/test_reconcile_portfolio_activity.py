from __future__ import annotations

import copy
import unittest
from datetime import date, datetime, timedelta, timezone

from scripts.reconcile_portfolio_activity import (
    CensusError,
    SearchSlice,
    Window,
    build_census,
    collect_partitioned_pr_search,
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
        self.assertGreater(
            result["sensors"]["public_owner_repository_push"]["malformed_rows"], 0
        )
        self.assertGreater(result["sensors"]["updated_pull_request"]["malformed_rows"], 0)


class PartitionedSearchTests(unittest.TestCase):
    def test_under_cap_preserves_previous_single_query_path(self):
        rows = [{"id": 1}, {"id": 2}]

        def fetch(search_slice):
            self.assertIsNone(search_slice)
            return copy.deepcopy(rows), 2, False

        result, evidence = collect_partitioned_pr_search(
            fetch,
            created_floor=date(2008, 1, 1),
            created_ceiling=date(2026, 8, 22),
        )
        self.assertEqual(result, rows)
        self.assertFalse(evidence["cap_triggered"])
        self.assertEqual(evidence["partition_strategy"], "none")

    def test_cap_uses_disjoint_creation_date_partitions_and_recovers_all_rows(self):
        calls = []

        def fetch(search_slice):
            calls.append(search_slice)
            if search_slice is None:
                return [{"id": 999}], 1200, False
            is_root = (
                search_slice.created_since == date(2008, 1, 1)
                and search_slice.created_until == date(2026, 1, 1)
            )
            if is_root:
                return [{"id": 999}], 1200, False
            if search_slice.created_until.year <= 2017:
                return [{"id": i} for i in range(1, 701)], 700, False
            return [{"id": i} for i in range(701, 1201)], 500, False

        rows, evidence = collect_partitioned_pr_search(
            fetch,
            created_floor=date(2008, 1, 1),
            created_ceiling=date(2026, 1, 1),
        )
        self.assertEqual(len(rows), 1200)
        self.assertTrue(evidence["cap_triggered"])
        self.assertEqual(evidence["partition_strategy"], "created_date_recursive")
        self.assertEqual(evidence["leaf_partition_count"], 2)
        self.assertEqual(evidence["duplicate_count"], 0)
        self.assertEqual(len(calls), 4)

    def test_single_day_over_cap_refuses_instead_of_sampling(self):
        def fetch(search_slice):
            if search_slice is None:
                return [], 1500, False
            return [], 1500, False

        with self.assertRaisesRegex(
            CensusError, r"REFUSED\[PR_SEARCH_UNSPLITTABLE_DAY_CAP\]"
        ):
            collect_partitioned_pr_search(
                fetch,
                created_floor=date(2026, 8, 22),
                created_ceiling=date(2026, 8, 22),
            )

    def test_partition_incomplete_results_refuses(self):
        def fetch(search_slice):
            if search_slice is None:
                return [], 1100, False
            return [], 10, True

        with self.assertRaisesRegex(CensusError, r"REFUSED\[PR_SEARCH_INCOMPLETE_RESULTS\]"):
            collect_partitioned_pr_search(
                fetch,
                created_floor=date(2008, 1, 1),
                created_ceiling=date(2026, 8, 22),
            )

    def test_missing_exact_pr_identity_refuses_deduplication(self):
        def fetch(search_slice):
            if search_slice is None:
                return [], 1100, False
            is_root = (
                search_slice.created_since == date(2008, 1, 1)
                and search_slice.created_until == date(2026, 1, 1)
            )
            if is_root:
                return [], 1100, False
            if search_slice.created_until.year <= 2017:
                return [{"id": i} for i in range(600)], 600, False
            return [{"repository_url": "https://api.github.com/repos/seanchatmangpt/x"}], 1, False

        with self.assertRaisesRegex(CensusError, r"REFUSED\[PR_SEARCH_RESULT_IDENTITY_MISSING\]"):
            collect_partitioned_pr_search(
                fetch,
                created_floor=date(2008, 1, 1),
                created_ceiling=date(2026, 1, 1),
            )

    def test_search_slice_is_disjoint_at_midpoint(self):
        left, right = SearchSlice(date(2026, 1, 1), date(2026, 1, 10)).split()
        self.assertEqual(left.created_until + timedelta(days=1), right.created_since)


if __name__ == "__main__":
    unittest.main()
