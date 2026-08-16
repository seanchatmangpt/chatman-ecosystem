from __future__ import annotations

import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("survey_portfolio", ROOT / "scripts" / "survey_portfolio.py")
survey_portfolio = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = survey_portfolio
SPEC.loader.exec_module(survey_portfolio)


class FakeClient:
    def __init__(self, *, complete: bool = True, omit_required: bool = False) -> None:
        self.complete = complete
        self.repos = [
            {
                "full_name": "seanchatmangpt/chatman-ecosystem",
                "owner": {"login": "seanchatmangpt"},
                "private": False,
                "archived": False,
                "fork": False,
                "default_branch": "main",
                "updated_at": "2026-08-15T23:00:00Z",
            },
            {
                "full_name": "seanchatmangpt/ggen",
                "owner": {"login": "seanchatmangpt"},
                "private": False,
                "archived": False,
                "fork": False,
                "default_branch": "main",
                "updated_at": "2026-08-15T23:01:00Z",
            },
            {
                "full_name": "seanchatmangpt/gymact",
                "owner": {"login": "seanchatmangpt"},
                "private": False,
                "archived": False,
                "fork": False,
                "default_branch": "main",
                "updated_at": "2026-08-15T23:02:00Z",
            },
            {
                "full_name": "seanchatmangpt/ggen-legacy",
                "owner": {"login": "seanchatmangpt"},
                "private": False,
                "archived": False,
                "fork": False,
                "default_branch": "main",
                "updated_at": "2026-08-15T23:03:00Z",
            },
            {
                "full_name": "seanchatmangpt/random-repo",
                "owner": {"login": "seanchatmangpt"},
                "private": False,
                "archived": False,
                "fork": False,
                "default_branch": "main",
                "updated_at": "2026-08-15T23:04:00Z",
            },
        ]
        if omit_required:
            self.repos = [repo for repo in self.repos if repo["full_name"] != "seanchatmangpt/gymact"]

    def list_owned_repositories(self, owner: str):
        assert owner == "seanchatmangpt"
        return self.repos, {
            "inventory_mode": "authenticated-owner" if self.complete else "public-owner",
            "inventory_complete": self.complete,
            "inventory_standing": "ALIVE" if self.complete else "PARTIAL_ALIVE",
            "page_size": 100,
            "nonempty_pages": 1,
            "next_page_empty": True,
            "observed_owned_repository_count": len(self.repos),
        }

    def list_open_pull_requests(self, owner: str):
        return [
            {
                "repository_url": "https://api.github.com/repos/seanchatmangpt/chatman-ecosystem",
                "number": 11,
                "title": "docs: freeze constitution",
                "html_url": "https://github.com/seanchatmangpt/chatman-ecosystem/pull/11",
                "draft": True,
                "updated_at": "2026-08-15T23:10:00Z",
            },
            {
                "repository_url": "https://api.github.com/repos/seanchatmangpt/random-repo",
                "number": 1,
                "title": "irrelevant",
                "html_url": "https://github.com/seanchatmangpt/random-repo/pull/1",
                "draft": False,
                "updated_at": "2026-08-15T23:11:00Z",
            },
        ]

    def list_open_issues(self, owner: str):
        return [
            {
                "repository_url": "https://api.github.com/repos/seanchatmangpt/ggen",
                "number": 99,
                "title": "required repo issue",
                "html_url": "https://github.com/seanchatmangpt/ggen/issues/99",
            },
            {
                "repository_url": "https://api.github.com/repos/seanchatmangpt/random-repo",
                "number": 2,
                "title": "outside required set",
                "html_url": "https://github.com/seanchatmangpt/random-repo/issues/2",
            },
        ]

    def resolve_ref(self, repository: str, ref: str):
        if repository == "seanchatmangpt/ggen":
            return {"sha": "b" * 40}
        if repository == "seanchatmangpt/gymact":
            return {"sha": "c" * 40}
        raise survey_portfolio.SurveyError(f"unobserved {repository}@{ref}")


class PortfolioSurveyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manifest = {
            "release": {"version": "26.9.1"},
            "components": [
                {
                    "id": "ggen",
                    "repository": "seanchatmangpt/ggen",
                    "ref": "main",
                    "sha": "a" * 40,
                    "role": "manufacture",
                    "standing": "UNKNOWN",
                    "disposition": "REQUIRED",
                    "required": True,
                    "depends_on": [],
                },
                {
                    "id": "gymact",
                    "repository": "seanchatmangpt/gymact",
                    "ref": "main",
                    "sha": "c" * 40,
                    "role": "actuation",
                    "standing": "BLOCKED",
                    "blocker": "EXTERNAL",
                    "disposition": "REQUIRED",
                    "required": True,
                    "depends_on": ["ggen"],
                },
            ],
        }
        self.fleet = {
            "fleet": {
                "owner": "seanchatmangpt",
                "observed_owned_repository_count": 4,
                "nonempty_pages": 1,
                "page_size": 100,
                "next_page_empty": True,
                "default_disposition": "OUT_OF_RELEASE",
                "composition_root": "seanchatmangpt/chatman-ecosystem",
            },
            "dispositions": {
                "crown": [],
                "required": ["seanchatmangpt/ggen", "seanchatmangpt/gymact"],
                "adapter": [],
                "bench_gym": [],
                "source_archaeology": ["seanchatmangpt/ggen-legacy"],
                "explicit_out_of_release": [],
            },
        }
        self.crosswalk, findings = survey_portfolio.load_crosswalk(
            ROOT / "release" / "v26.9.1" / "constitutional-role-crosswalk.toml"
        )
        self.assertEqual([], findings)

    def build(self, client=None):
        return survey_portfolio.build_survey(
            client or FakeClient(),
            owner="seanchatmangpt",
            manifest=self.manifest,
            fleet=self.fleet,
            crosswalk=self.crosswalk,
            observed_at="2026-08-15T19:14:00-07:00",
        )

    def test_actuation_release_role_does_not_grant_actuate(self) -> None:
        mapping = self.crosswalk["actuation"]
        self.assertEqual("Construct", mapping["primary"])
        self.assertIn("ProduceEvidence", mapping["capabilities"])
        self.assertNotEqual("Actuate", mapping["primary"])
        self.assertIn("NO_AMBIENT_DO", mapping["authority_ceiling"])

    def test_build_survey_separates_portfolio_release_and_support(self) -> None:
        survey = self.build()
        self.assertEqual(5, survey["summary"]["owned_repository_count"])
        self.assertEqual(2, survey["summary"]["required_component_count"])
        self.assertEqual(1, survey["summary"]["open_core_pr_count"])
        self.assertEqual(1, survey["summary"]["open_required_issue_count"])
        self.assertEqual(1, survey["summary"]["scope_counts"]["ROOT"])
        self.assertEqual(2, survey["summary"]["scope_counts"]["REQUIRED_V26_9_1"])
        self.assertEqual(1, survey["summary"]["scope_counts"]["CONSTITUTIONAL_SUPPORT"])
        self.assertEqual(1, survey["summary"]["scope_counts"]["UNMAPPED"])
        self.assertTrue(survey["summary"]["inventory_complete"])

    def test_ref_drift_is_observed_not_promoted(self) -> None:
        survey = self.build()
        ggen = next(row for row in survey["required_components"] if row["id"] == "ggen")
        self.assertEqual("true", ggen["ref_drift"])
        self.assertEqual("UNKNOWN", ggen["standing"])
        codes = {finding["code"] for finding in survey["findings"]}
        self.assertIn("REQUIRED_REF_DRIFT", codes)
        self.assertIn("PORTFOLIO_COUNT_DRIFT", codes)

    def test_public_partial_inventory_never_turns_absence_into_blocking_fact(self) -> None:
        survey = self.build(FakeClient(complete=False, omit_required=True))
        by_code = {finding["code"]: finding for finding in survey["findings"]}
        self.assertEqual("PARTIAL_ALIVE", survey["summary"]["inventory_standing"])
        self.assertFalse(survey["summary"]["inventory_complete"])
        self.assertEqual("WARN", by_code["REQUIRED_REPOSITORY_UNOBSERVED_PARTIAL_INVENTORY"]["severity"])
        self.assertNotIn("REQUIRED_REPOSITORY_UNOBSERVED", by_code)
        self.assertIn("INVENTORY_AUTHORITY_PARTIAL", by_code)

    def test_complete_inventory_makes_required_absence_blocking(self) -> None:
        survey = self.build(FakeClient(complete=True, omit_required=True))
        by_code = {finding["code"]: finding for finding in survey["findings"]}
        self.assertEqual("BLOCKING", by_code["REQUIRED_REPOSITORY_UNOBSERVED"]["severity"])
        self.assertNotIn("REQUIRED_REPOSITORY_UNOBSERVED_PARTIAL_INVENTORY", by_code)

    def test_missing_release_role_mapping_is_blocking(self) -> None:
        broken = dict(self.crosswalk)
        broken.pop("manufacture")
        findings = survey_portfolio.validate_crosswalk(self.manifest, broken)
        self.assertTrue(any(f.code == "RELEASE_ROLE_UNMAPPED" and f.severity == "BLOCKING" for f in findings))

    def test_actuate_crosswalk_requires_brce_exclusive(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / "bad.toml"
            path.write_text(
                "[[crosswalk]]\nrelease_role='bad'\nprimary='Actuate'\ncapabilities=[]\nauthority_ceiling='BAD'\n",
                encoding="utf-8",
            )
            _, findings = survey_portfolio.load_crosswalk(path)
            self.assertIn("CROSSWALK_AMBIENT_ACTUATION", {finding.code for finding in findings})

    def test_outputs_are_receipted_and_replayable(self) -> None:
        survey = self.build()
        with tempfile.TemporaryDirectory() as first, tempfile.TemporaryDirectory() as second:
            survey_portfolio.write_outputs(survey, Path(first))
            survey_portfolio.write_outputs(survey, Path(second))
            names = sorted(path.name for path in Path(first).iterdir())
            self.assertIn("SHA256SUMS", names)
            self.assertIn("REPORT.md", names)
            self.assertIn("REPO_CENSUS.csv", names)
            for name in names:
                self.assertEqual((Path(first) / name).read_bytes(), (Path(second) / name).read_bytes())
            payload = json.loads((Path(first) / "FINDINGS.json").read_text(encoding="utf-8"))
            self.assertEqual("2026-08-15T19:14:00-07:00", payload["observed_at"])


class GitHubPaginationTests(unittest.TestCase):
    def test_public_owner_inventory_requires_empty_terminator_and_is_partial(self) -> None:
        class Client(survey_portfolio.GitHubClient):
            def __init__(self):
                super().__init__(inventory_mode="public-owner")
                self.calls = []

            def _request_json(self, path_or_url):
                from urllib.parse import parse_qs, urlparse
                self.calls.append(path_or_url)
                page = parse_qs(urlparse(path_or_url).query).get("page", [""])[0]
                if page == "1":
                    return [{"full_name": "seanchatmangpt/a", "owner": {"login": "seanchatmangpt"}}]
                return []

        client = Client()
        repos, evidence = client.list_owned_repositories("seanchatmangpt")
        self.assertEqual(1, len(repos))
        self.assertEqual(1, evidence["nonempty_pages"])
        self.assertTrue(evidence["next_page_empty"])
        self.assertFalse(evidence["inventory_complete"])
        self.assertEqual("PARTIAL_ALIVE", evidence["inventory_standing"])
        self.assertEqual(2, len(client.calls))

    def test_authenticated_owner_inventory_is_complete(self) -> None:
        class Client(survey_portfolio.GitHubClient):
            def __init__(self):
                super().__init__(token="fixture", inventory_mode="authenticated-owner")

            def _request_json(self, path_or_url):
                from urllib.parse import parse_qs, urlparse
                page = parse_qs(urlparse(path_or_url).query).get("page", [""])[0]
                if page == "1":
                    return [{"full_name": "seanchatmangpt/a", "owner": {"login": "seanchatmangpt"}}]
                return []

        _, evidence = Client().list_owned_repositories("seanchatmangpt")
        self.assertTrue(evidence["inventory_complete"])
        self.assertEqual("ALIVE", evidence["inventory_standing"])


if __name__ == "__main__":
    unittest.main()
