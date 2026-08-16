"""Chicago-style tests for scripts/rebrand_portfolio.py.

These tests exercise real, unmocked logic: the real `portfolio_context`
generator, the real `parse_error` decoder, and the real `process_repository`
decision function against real `Result` state.

`process_repository` calls out to the real GitHub REST API for the
branch/PR-mutating paths (creating branches, opening draft PRs). A real
GitHub API call is the "genuinely infeasible in-process" exception under the
project's Chicago-testing rule: it is a paid, rate-limited, credentialed,
side-effecting third-party API that would create real branches/PRs on real
repositories if exercised in CI. Per that rule's guidance, this suite instead
exercises `process_repository` only along the early-return paths that need no
network access at all (`REFUSED`/`UNSUPPORTED` classification from real
repository metadata), and separately exercises the pure functions
(`portfolio_context`, `parse_error`) with zero doubles. No
`unittest.mock`/`Mock`/`patch`/`monkeypatch` is used anywhere in this file.
"""

from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "rebrand_portfolio", ROOT / "scripts" / "rebrand_portfolio.py"
)
rebrand_portfolio = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = rebrand_portfolio
SPEC.loader.exec_module(rebrand_portfolio)


class PortfolioContextTest(unittest.TestCase):
    def test_contains_repository_name_and_boundary_language(self) -> None:
        content = rebrand_portfolio.portfolio_context("seanchatmangpt/example-repo")
        self.assertIn("`seanchatmangpt/example-repo`", content)
        self.assertIn("Forward Deployment Portfolio Context", content)
        self.assertIn("does **not** assert", content)
        self.assertIn("A = μ(O*)", content)

    def test_is_deterministic_for_the_same_repository(self) -> None:
        first = rebrand_portfolio.portfolio_context("seanchatmangpt/repo-a")
        second = rebrand_portfolio.portfolio_context("seanchatmangpt/repo-a")
        self.assertEqual(first, second)


class ParseErrorTest(unittest.TestCase):
    def test_decodes_json_error_payload(self) -> None:
        error = RuntimeError('{"status": 404, "url": "https://api.github.com/x"}')
        decoded = rebrand_portfolio.parse_error(error)
        self.assertEqual(decoded["status"], 404)
        self.assertEqual(decoded["url"], "https://api.github.com/x")

    def test_falls_back_to_error_string_for_non_json_payload(self) -> None:
        error = RuntimeError("connection reset")
        decoded = rebrand_portfolio.parse_error(error)
        self.assertEqual(decoded, {"error": "connection reset"})


class ProcessRepositoryEarlyReturnTest(unittest.TestCase):
    """Exercises the real decision function on real repository metadata,
    along the paths that require no network I/O (archived, empty, and
    no-push-authority repositories are refused/unsupported before any API
    call is made)."""

    def test_refuses_archived_repository(self) -> None:
        metadata = {
            "name": "archived-repo",
            "full_name": "seanchatmangpt/archived-repo",
            "default_branch": "main",
            "archived": True,
            "size": 42,
            "permissions": {"push": True},
        }
        result = rebrand_portfolio.process_repository(
            api=None,  # unreachable: refused before any API use
            owner="seanchatmangpt",
            metadata=metadata,
            campaign_branch="brand/x",
            file_path="FORWARD_DEPLOYMENT.md",
            dry_run=False,
        )
        self.assertEqual(result.state, "REFUSED")
        self.assertEqual(result.reason, "ARCHIVED")
        self.assertEqual(result.repository, "seanchatmangpt/archived-repo")

    def test_marks_empty_repository_unsupported(self) -> None:
        metadata = {
            "name": "empty-repo",
            "full_name": "seanchatmangpt/empty-repo",
            "default_branch": "main",
            "archived": False,
            "size": 0,
            "permissions": {"push": True},
        }
        result = rebrand_portfolio.process_repository(
            api=None,
            owner="seanchatmangpt",
            metadata=metadata,
            campaign_branch="brand/x",
            file_path="FORWARD_DEPLOYMENT.md",
            dry_run=False,
        )
        self.assertEqual(result.state, "UNSUPPORTED")
        self.assertEqual(result.reason, "NO_BASE_COMMIT")

    def test_refuses_repository_without_push_authority(self) -> None:
        metadata = {
            "name": "readonly-repo",
            "full_name": "seanchatmangpt/readonly-repo",
            "default_branch": "main",
            "archived": False,
            "size": 10,
            "permissions": {"push": False},
        }
        result = rebrand_portfolio.process_repository(
            api=None,
            owner="seanchatmangpt",
            metadata=metadata,
            campaign_branch="brand/x",
            file_path="FORWARD_DEPLOYMENT.md",
            dry_run=False,
        )
        self.assertEqual(result.state, "REFUSED")
        self.assertEqual(result.reason, "NO_PUSH_AUTHORITY")

    def test_dry_run_reports_candidate_without_touching_the_api(self) -> None:
        metadata = {
            "name": "candidate-repo",
            "full_name": "seanchatmangpt/candidate-repo",
            "default_branch": "main",
            "archived": False,
            "size": 10,
            "permissions": {"push": True},
        }
        result = rebrand_portfolio.process_repository(
            api=None,
            owner="seanchatmangpt",
            metadata=metadata,
            campaign_branch="brand/x",
            file_path="FORWARD_DEPLOYMENT.md",
            dry_run=True,
        )
        self.assertEqual(result.state, "CANDIDATE")
        self.assertEqual(result.reason, "DRY_RUN")


if __name__ == "__main__":
    unittest.main()
