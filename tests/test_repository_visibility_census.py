import copy
import unittest
from datetime import datetime, timezone

from scripts.repository_visibility_census import (
    GitHubVisibilityClient,
    VisibilityError,
    Window,
    build_census,
    verify_receipt,
)


class FakeSensor:
    def __init__(self, rows, scope):
        self.rows = rows
        self.scope = scope

    def owner_repositories(self, owner):
        return copy.deepcopy(self.rows), copy.deepcopy(self.scope)


class ScriptedClient(GitHubVisibilityClient):
    def __init__(self, token, responses):
        super().__init__(token=token)
        self.responses = responses
        self.calls = []

    def _request(self, path):
        self.calls.append(path)
        for prefix, payload in self.responses:
            if path.startswith(prefix):
                return copy.deepcopy(payload)
        raise AssertionError(f"unexpected request: {path}")


class VisibilityCensusTests(unittest.TestCase):
    def setUp(self):
        self.window = Window(
            since=datetime(2026, 8, 15, 0, 0, tzinfo=timezone.utc),
            until=datetime(2026, 8, 22, 0, 0, tzinfo=timezone.utc),
        )

    def test_authenticated_scope_preserves_private_active_repository(self):
        sensor = FakeSensor(
            [
                {"full_name": "seanchatmangpt/public", "private": False, "pushed_at": "2026-08-21T01:00:00Z"},
                {"full_name": "seanchatmangpt/private", "private": True, "pushed_at": "2026-08-21T02:00:00Z"},
            ],
            {
                "visibility_scope": "AUTHENTICATED_OWNER",
                "authenticated_owner": "seanchatmangpt",
                "private_repository_visibility": "AVAILABLE_TO_TOKEN",
            },
        )
        result = build_census(sensor, owner="seanchatmangpt", window=self.window)
        self.assertEqual(result["standing"], "PARTIAL_ALIVE")
        self.assertEqual(result["measurement"]["active_repository_count"], 2)
        self.assertEqual(result["measurement"]["active_private_repository_count"], 1)
        self.assertTrue(verify_receipt(result))

    def test_stale_push_is_not_false_positive(self):
        sensor = FakeSensor(
            [{"full_name": "seanchatmangpt/stale", "private": True, "pushed_at": "2026-08-14T23:59:59Z"}],
            {
                "visibility_scope": "AUTHENTICATED_OWNER",
                "authenticated_owner": "seanchatmangpt",
                "private_repository_visibility": "AVAILABLE_TO_TOKEN",
            },
        )
        result = build_census(sensor, owner="seanchatmangpt", window=self.window)
        self.assertEqual(result["measurement"]["active_repository_count"], 0)

    def test_until_boundary_is_excluded(self):
        sensor = FakeSensor(
            [{"full_name": "seanchatmangpt/boundary", "private": False, "pushed_at": "2026-08-22T00:00:00Z"}],
            {
                "visibility_scope": "PUBLIC_ONLY",
                "authenticated_owner": None,
                "private_repository_visibility": "UNAVAILABLE",
            },
        )
        result = build_census(sensor, owner="seanchatmangpt", window=self.window)
        self.assertEqual(result["measurement"]["active_repository_count"], 0)
        self.assertEqual(result["standing"], "OBSERVED")

    def test_receipt_rejects_tampering(self):
        sensor = FakeSensor(
            [{"full_name": "seanchatmangpt/a", "private": False, "pushed_at": "2026-08-21T01:00:00Z"}],
            {
                "visibility_scope": "PUBLIC_ONLY",
                "authenticated_owner": None,
                "private_repository_visibility": "UNAVAILABLE",
            },
        )
        result = build_census(sensor, owner="seanchatmangpt", window=self.window)
        result["measurement"]["active_repository_count"] = 99
        self.assertFalse(verify_receipt(result))

    def test_authenticated_owner_mismatch_refuses(self):
        client = ScriptedClient(token="secret", responses=[("/user", {"login": "someone-else"})])
        with self.assertRaisesRegex(VisibilityError, r"REFUSED\[AUTHENTICATED_OWNER_MISMATCH\]"):
            client.owner_repositories("seanchatmangpt")
        self.assertEqual(client.calls, ["/user"])

    def test_authenticated_path_uses_owner_affiliation_and_includes_private(self):
        client = ScriptedClient(
            token="secret",
            responses=[
                ("/user/repos?", [{"full_name": "seanchatmangpt/private", "private": True, "pushed_at": "2026-08-21T02:00:00Z"}]),
                ("/user", {"login": "seanchatmangpt"}),
            ],
        )
        rows, scope = client.owner_repositories("seanchatmangpt")
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["private"])
        self.assertEqual(scope["visibility_scope"], "AUTHENTICATED_OWNER")
        self.assertTrue(any("affiliation=owner" in call for call in client.calls))

    def test_public_fallback_does_not_claim_private_visibility(self):
        client = ScriptedClient(
            token=None,
            responses=[("/users/seanchatmangpt/repos?", [])],
        )
        rows, scope = client.owner_repositories("seanchatmangpt")
        self.assertEqual(rows, [])
        self.assertEqual(scope["visibility_scope"], "PUBLIC_ONLY")
        self.assertEqual(scope["private_repository_visibility"], "UNAVAILABLE")


if __name__ == "__main__":
    unittest.main()
