"""Observer (outside the court): default branch read, never hardcoded; typed errors, no raise.

The GitHub API is replaced by an in-process fixture implementing the same fetch contract
(url -> JSON object, HTTPError on 404) because the real API is a network side channel
the unit gate must not depend on; the live observer run is recorded separately by the
root-crown workflow receipt.
"""

from __future__ import annotations

import base64
import io
import json
import sys
import unittest
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import observe_release_heads as obs  # noqa: E402

API = obs.API
PIN = "a" * 40
HEAD = "b" * 40


class FixtureApi:
    """A dict-backed GitHub API: a real, simple implementation of the fetch contract."""

    def __init__(self, routes):
        self.routes = routes
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        if url not in self.routes:
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, io.BytesIO(b""))
        return self.routes[url]


def content(value):
    return {"content": base64.b64encode(json.dumps(value).encode()).decode(), "sha": "c" * 40}


class ObserverTest(unittest.TestCase):
    def test_master_default_branch_is_honored(self):
        api = FixtureApi(
            {
                f"{API}/repos/o/autofde-lab": {"default_branch": "master", "visibility": "public"},
                f"{API}/repos/o/autofde-lab/commits/master": {"sha": HEAD},
                f"{API}/repos/o/autofde-lab/compare/{PIN}...{HEAD}": {"status": "ahead"},
            }
        )
        out = obs.observe_repo(api, "o/autofde-lab", PIN)
        self.assertEqual((out["default_branch"], out["head_sha"], out["compare_status"]), ("master", HEAD, "ahead"))
        self.assertFalse(any("/commits/main" in c for c in api.calls))

    def test_unreachable_repo_is_a_typed_error_not_an_exception(self):
        out = obs.observe_repo(FixtureApi({}), "o/private", PIN)
        self.assertEqual(out["error"], "HTTP404")
        self.assertNotIn("head_sha", out)

    def test_artifact_subject_lineage_is_observed(self):
        receipt = {"standing": "ALIVE", "subject_sha": PIN}
        api = FixtureApi(
            {
                f"{API}/repos/o/r/contents/release/v26.9.25/receipts/x.json?ref={HEAD}": content(receipt),
                f"{API}/repos/o/r/compare/{PIN}...{HEAD}": {"status": "ahead"},
            }
        )
        out = obs.observe_artifact(api, "o/r:release/v26.9.25/receipts/x.json", {"head_sha": HEAD})
        self.assertEqual(out["json"], receipt)
        self.assertEqual(out["subject_compare"], "ahead")
        missing = obs.observe_artifact(api, "o/r:absent.json", {"head_sha": HEAD})
        self.assertEqual(missing["error"], "HTTP404")

    def test_absent_tag_is_null_and_annotated_tag_is_dereferenced(self):
        self.assertEqual(obs.observe_tag(FixtureApi({}), "o/r", "v26.9.25"), {"name": "v26.9.25", "sha": None})
        api = FixtureApi(
            {
                f"{API}/repos/o/r/git/ref/tags/v26.9.25": {"object": {"type": "tag", "sha": "d" * 40}},
                f"{API}/repos/o/r/git/tags/{'d' * 40}": {"object": {"sha": HEAD}},
            }
        )
        self.assertEqual(obs.observe_tag(api, "o/r", "v26.9.25")["sha"], HEAD)

    def test_local_topology_receipt_projects_violations(self):
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "TOPOLOGY-RECEIPT.json"
            path.write_text(
                json.dumps(
                    {
                        "m_term": {
                            "observed_at": "2026-09-25T07:00:00Z",
                            "holds": False,
                            "unauthorized_worktrees": 1,
                            "violations": [{"repo_id": "unibit", "path": "/x", "class": "ORPHAN_WORKTREE"}],
                        }
                    }
                )
            )
            local = obs.observe_local_worktrees(str(Path(tmp) / "TOPOLOGY-RECEIPT*.json"))
        self.assertEqual(
            local["worktrees"], [{"repo": "unibit", "path": "/x", "class": "ORPHAN_WORKTREE", "blocked": None}]
        )
        self.assertEqual(local["observed_at"], "2026-09-25T07:00:00Z")
        self.assertFalse(local["holds"])


if __name__ == "__main__":
    unittest.main()
