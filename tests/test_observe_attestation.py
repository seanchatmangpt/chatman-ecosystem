"""observe_attestation.py (outside the court): lane verification, typed errors, no raise.

The GitHub API is replaced by an in-process fixture implementing the same contract
(path -> JSON object, RuntimeError on a missing route) because the real API is a network
side channel the unit gate must not depend on; the live observation is committed as
release/v26.9.25/hardening/inputs/attestation-observations.json. The receipt bytes are read
by the real durable_locator Resolver from a real temporary git repository.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))
from scripts import observe_attestation as oa  # noqa: E402
from scripts.durable_locator import durable_locator as dl  # noqa: E402

HEAD = "b" * 40


class FixtureApi:
    """A dict-backed GitHub API: a real, simple implementation of the api(path) contract."""

    def __init__(self, routes):
        self.routes = routes

    def __call__(self, path):
        if path not in self.routes:
            raise RuntimeError(f"gh api {path}: exit 1: HTTP 404")
        return self.routes[path]


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, check=True, text=True
    )
    return out.stdout.strip()


class RealRepo:
    def __init__(self, slug: str) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.root = Path(self._tmp.name)
        self.repo = self.root / slug.split("/")[1]
        self.repo.mkdir()
        git(self.repo, "init", "-q")
        git(self.repo, "remote", "add", "origin", f"https://github.com/{slug}.git")
        (self.repo / "receipt.json").write_text('{"standing": "ALIVE"}\n')
        git(self.repo, "add", "receipt.json")
        git(
            self.repo,
            "-c",
            "user.name=t",
            "-c",
            "user.email=t@t",
            "commit",
            "-q",
            "-m",
            "r",
        )
        self.sha = git(self.repo, "rev-parse", "HEAD")

    def close(self) -> None:
        self._tmp.cleanup()


def lane(sha: str, merge: str | None = None, receipt: str | None = None) -> dict:
    return {
        "id": "L1",
        "repository": "o/r",
        "pr": 7,
        "head_sha": "c" * 40,
        "merge_sha": merge or sha,
        "receipt_locator": receipt or f"git:o/r@{sha}:receipt.json",
    }


class ObserveAttestationTest(unittest.TestCase):
    def test_classify_merge(self):
        self.assertEqual(oa.classify_merge("identical"), "ON_DEFAULT")
        self.assertEqual(oa.classify_merge("ahead"), "ON_DEFAULT")
        self.assertEqual(oa.classify_merge("behind"), "NOT_ON_DEFAULT")
        self.assertEqual(oa.classify_merge("diverged"), "NOT_ON_DEFAULT")
        self.assertEqual(oa.classify_merge(None), "UNKNOWN")

    def test_merged_lane_with_receipt_bytes(self):
        repo = RealRepo("o/r")
        try:
            api = FixtureApi(
                {
                    "repos/o/r": {"default_branch": "master"},
                    "repos/o/r/commits/master": {"sha": HEAD},
                    "repos/o/r/pulls/7": {
                        "merged": True,
                        "state": "closed",
                        "head": {"sha": "c" * 40},
                        "merge_commit_sha": repo.sha,
                    },
                    f"repos/o/r/compare/{repo.sha}...{HEAD}": {"status": "ahead"},
                }
            )
            out = oa.observe_lane(
                api, dl.Resolver(repo.root, allow_network=False), lane(repo.sha)
            )
        finally:
            repo.close()
        self.assertEqual(
            (out["default_branch"], out["pr_state"], out["merge_on_default"]),
            ("master", "MERGED", "ON_DEFAULT"),
        )
        self.assertEqual(out["pr_merge_commit"], repo.sha)
        self.assertEqual(
            out["receipt"]["sha256"],
            hashlib.sha256(b'{"standing": "ALIVE"}\n').hexdigest(),
        )

    def test_attacker_owner_receipt_is_refused_not_read_from_the_canonical_checkout(
        self,
    ):
        repo = RealRepo("o/r")
        try:
            api = FixtureApi(
                {
                    "repos/o/r": {"default_branch": "main"},
                    "repos/o/r/commits/main": {"sha": HEAD},
                }
            )
            out = oa.observe_lane(
                api,
                dl.Resolver(repo.root, allow_network=False),
                lane(repo.sha, receipt=f"git:attacker/r@{repo.sha}:receipt.json"),
            )
        finally:
            repo.close()
        self.assertEqual(out["receipt"]["error"], "REFUSED[OWNER_MISMATCH]")
        self.assertEqual(out["merge_on_default"], "UNKNOWN")
        self.assertIn("pr_error", out)

    def test_scratch_receipt_locator_is_refused(self):
        api = FixtureApi(
            {
                "repos/o/r": {"default_branch": "main"},
                "repos/o/r/commits/main": {"sha": HEAD},
            }
        )
        with tempfile.TemporaryDirectory() as tmp:
            out = oa.observe_lane(
                api,
                dl.Resolver(Path(tmp), allow_network=False),
                lane("d" * 40, receipt="/private/tmp/x/receipt.json"),
            )
        self.assertEqual(out["receipt"]["error"], "REFUSED[SCRATCH_LOCATOR]")

    def test_unreachable_repository_is_a_typed_error(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = oa.observe_lane(
                FixtureApi({}),
                dl.Resolver(Path(tmp), allow_network=False),
                lane("d" * 40),
            )
        self.assertTrue(out["error"].startswith("RuntimeError:gh api repos/o/r"))


if __name__ == "__main__":
    unittest.main()
