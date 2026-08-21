from __future__ import annotations

import copy
import unittest
import urllib.parse
from datetime import datetime, timezone

from scripts.reconcile_portfolio_activity import (
    CensusError,
    GitHubClient,
    Window,
    build_census,
    inclusive_search_bounds,
    verify_receipt,
)


class FakeClient:
    def __init__(self, repos, prs, evidence=None):
        self.repos = repos
        self.prs = prs
        self.evidence = evidence or {
            "root_reported_total_count": len(prs),
            "retrieved_count": len(prs),
            "retrieved_unique_count": len(prs),
            "deduplicated_count": 0,
            "search_cap": 1000,
            "partition_strategy": "fake",
            "partition_count": 1,
            "max_partition_total": len(prs),
            "incomplete_results": False,
            "partitions": [],
        }

    def list_public_owner_repositories(self, owner):
        return copy.deepcopy(self.repos)

    def search_updated_pull_requests(self, owner, since, until):
        return copy.deepcopy(self.prs), copy.deepcopy(self.evidence)


class ScriptedSearchClient(GitHubClient):
    """Search fake keyed by decoded updated range; supports pagination."""

    def __init__(self, rows_by_range, totals_by_range=None, incomplete_ranges=None):
        super().__init__(token=None)
        self.rows_by_range = rows_by_range
        self.totals_by_range = totals_by_range or {
            key: len(rows) for key, rows in rows_by_range.items()
        }
        self.incomplete_ranges = set(incomplete_ranges or [])
        self.calls = []

    def _request(self, path):
        parsed = urllib.parse.urlparse(path)
        params = urllib.parse.parse_qs(parsed.query)
        q = params["q"][0]
        page = int(params.get("page", ["1"])[0])
        marker = q.split("updated:", 1)[1]
        self.calls.append((marker, page))
        rows = self.rows_by_range.get(marker, [])
        total = self.totals_by_range.get(marker, len(rows))
        start = (page - 1) * 100
        end = start + 100
        return {
            "total_count": total,
            "incomplete_results": marker in self.incomplete_ranges,
            "items": copy.deepcopy(rows[start:end]),
        }


def pr(i, updated, repo="seanchatmangpt/repo"):
    return {
        "id": i,
        "node_id": f"PR_{i}",
        "url": f"https://api.github.com/repos/{repo}/issues/{i}",
        "repository_url": f"https://api.github.com/repos/{repo}",
        "updated_at": updated,
    }


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
                    "id": 1,
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
        self.assertEqual(
            result["reconciliation"]["union_repositories"],
            ["seanchatmangpt/in"],
        )

    def test_receipt_rejects_tampered_sensor_result(self):
        result = build_census(
            FakeClient(
                repos=[
                    {
                        "full_name": "seanchatmangpt/a",
                        "pushed_at": "2026-08-20T00:00:00Z",
                    }
                ],
                prs=[],
            ),
            owner="seanchatmangpt",
            window=self.window,
        )
        result["reconciliation"]["union_repository_count"] = 999
        self.assertFalse(verify_receipt(result))

    def test_malformed_rows_do_not_become_activity(self):
        client = FakeClient(
            repos=[
                {
                    "full_name": "other/repo",
                    "pushed_at": "2026-08-20T00:00:00Z",
                },
                {"full_name": "seanchatmangpt/no-time"},
            ],
            prs=[
                {
                    "id": 1,
                    "repository_url": "garbage",
                    "updated_at": "2026-08-20T00:00:00Z",
                },
                {
                    "id": 2,
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
        self.assertGreater(
            result["sensors"]["updated_pull_request"]["malformed_rows"], 0
        )

    def test_search_cap_is_partitioned_and_fully_recovered(self):
        since = datetime(2026, 8, 21, 0, 0, 0, tzinfo=timezone.utc)
        until = datetime(2026, 8, 21, 0, 0, 4, tzinfo=timezone.utc)
        root = "2026-08-21T00:00:00Z..2026-08-21T00:00:03Z"
        left = "2026-08-21T00:00:00Z..2026-08-21T00:00:01Z"
        right = "2026-08-21T00:00:02Z..2026-08-21T00:00:03Z"
        left_rows = [pr(i, "2026-08-21T00:00:00Z") for i in range(1, 601)]
        right_rows = [pr(i, "2026-08-21T00:00:02Z") for i in range(601, 1002)]
        client = ScriptedSearchClient(
            {root: [], left: left_rows, right: right_rows},
            totals_by_range={root: 1001, left: 600, right: 401},
        )
        rows, evidence = client.search_updated_pull_requests(
            "seanchatmangpt", since, until
        )
        self.assertEqual(len(rows), 1001)
        self.assertEqual(evidence["root_reported_total_count"], 1001)
        self.assertEqual(evidence["partition_count"], 2)
        self.assertEqual(evidence["max_partition_total"], 600)
        self.assertEqual(evidence["deduplicated_count"], 0)

    def test_one_second_over_cap_fails_closed(self):
        since = datetime(2026, 8, 21, 0, 0, 0, tzinfo=timezone.utc)
        until = datetime(2026, 8, 21, 0, 0, 1, tzinfo=timezone.utc)
        marker = "2026-08-21T00:00:00Z..2026-08-21T00:00:00Z"
        client = ScriptedSearchClient(
            {marker: []}, totals_by_range={marker: 1001}
        )
        with self.assertRaisesRegex(CensusError, r"PR_SEARCH_PARTITION_CAP"):
            client.search_updated_pull_requests("seanchatmangpt", since, until)

    def test_partition_deduplicates_stable_identity(self):
        since = datetime(2026, 8, 21, 0, 0, 0, tzinfo=timezone.utc)
        until = datetime(2026, 8, 21, 0, 0, 4, tzinfo=timezone.utc)
        root = "2026-08-21T00:00:00Z..2026-08-21T00:00:03Z"
        left = "2026-08-21T00:00:00Z..2026-08-21T00:00:01Z"
        right = "2026-08-21T00:00:02Z..2026-08-21T00:00:03Z"
        duplicate = pr(7, "2026-08-21T00:00:02Z")
        client = ScriptedSearchClient(
            {root: [], left: [duplicate], right: [duplicate]},
            totals_by_range={root: 1001, left: 1, right: 1},
        )
        rows, evidence = client.search_updated_pull_requests(
            "seanchatmangpt", since, until
        )
        self.assertEqual(len(rows), 1)
        self.assertEqual(evidence["deduplicated_count"], 1)

    def test_incomplete_partition_refuses(self):
        since = datetime(2026, 8, 21, 0, 0, 0, tzinfo=timezone.utc)
        until = datetime(2026, 8, 21, 0, 0, 4, tzinfo=timezone.utc)
        root = "2026-08-21T00:00:00Z..2026-08-21T00:00:03Z"
        left = "2026-08-21T00:00:00Z..2026-08-21T00:00:01Z"
        right = "2026-08-21T00:00:02Z..2026-08-21T00:00:03Z"
        client = ScriptedSearchClient(
            {root: [], left: [], right: []},
            totals_by_range={root: 1001, left: 0, right: 0},
            incomplete_ranges={left},
        )
        with self.assertRaisesRegex(CensusError, r"PR_SEARCH_INCOMPLETE_RESULTS"):
            client.search_updated_pull_requests("seanchatmangpt", since, until)

    def test_exact_search_bounds_preserve_half_open_seconds(self):
        start, end = inclusive_search_bounds(
            datetime(2026, 8, 21, 0, 0, 0, 500000, tzinfo=timezone.utc),
            datetime(2026, 8, 21, 0, 0, 2, 0, tzinfo=timezone.utc),
        )
        self.assertEqual(start.isoformat(), "2026-08-21T00:00:00+00:00")
        self.assertEqual(end.isoformat(), "2026-08-21T00:00:01+00:00")


if __name__ == "__main__":
    unittest.main()
