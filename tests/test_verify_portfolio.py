from __future__ import annotations

import copy
import sys
import tomllib
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from verify_portfolio import classify, validate, validate_pagination_evidence  # noqa: E402


def load(path: Path) -> dict:
    with path.open("rb") as handle:
        return tomllib.load(handle)


class VerifyPortfolioTests(unittest.TestCase):
    def setUp(self) -> None:
        base = ROOT / "release" / "v26.9.1"
        self.policy = load(base / "fleet-policy.toml")
        self.manifest = load(base / "manifest.toml")
        self.candidates = load(base / "candidates.toml")

    def test_current_release_state_is_clean(self) -> None:
        self.assertEqual(validate(self.policy, self.manifest, self.candidates), [])

    def test_classify_composition_root_is_crown(self) -> None:
        root = self.policy["fleet"]["composition_root"]
        self.assertEqual(classify(self.policy, root), "CROWN")

    def test_classify_required_repository(self) -> None:
        repo = self.policy["dispositions"]["required"][0]
        self.assertEqual(classify(self.policy, repo), "REQUIRED")

    def test_classify_unknown_repository_falls_back_to_default(self) -> None:
        result = classify(self.policy, "seanchatmangpt/definitely-not-in-any-list")
        self.assertEqual(result, self.policy["fleet"]["default_disposition"])
        self.assertEqual(result, "OUT_OF_RELEASE")

    def test_pagination_evidence_valid_when_count_in_range(self) -> None:
        fleet = {
            "observed_owned_repository_count": 355,
            "nonempty_pages": 4,
            "page_size": 100,
            "next_page_empty": True,
        }
        self.assertEqual(validate_pagination_evidence(fleet), [])

    def test_pagination_evidence_flags_count_below_page_floor(self) -> None:
        fleet = {
            "observed_owned_repository_count": 250,
            "nonempty_pages": 4,
            "page_size": 100,
            "next_page_empty": True,
        }
        findings = validate_pagination_evidence(fleet)
        codes = {f["code"] for f in findings}
        self.assertIn("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH", codes)

    def test_pagination_evidence_flags_missing_terminator(self) -> None:
        fleet = {
            "observed_owned_repository_count": 355,
            "nonempty_pages": 4,
            "page_size": 100,
            "next_page_empty": False,
        }
        findings = validate_pagination_evidence(fleet)
        codes = {f["code"] for f in findings}
        self.assertIn("FLEET_PAGINATION_TERMINATOR_INVALID", codes)

    def test_pagination_evidence_flags_invalid_types(self) -> None:
        fleet = {
            "observed_owned_repository_count": "many",
            "nonempty_pages": 0,
            "page_size": -1,
            "next_page_empty": None,
        }
        findings = validate_pagination_evidence(fleet)
        codes = {f["code"] for f in findings}
        self.assertIn("FLEET_OBSERVED_COUNT_INVALID", codes)
        self.assertIn("FLEET_NONEMPTY_PAGES_INVALID", codes)
        self.assertIn("FLEET_PAGE_SIZE_INVALID", codes)
        self.assertIn("FLEET_PAGINATION_TERMINATOR_INVALID", codes)
        # Range check is skipped once type findings already exist.
        self.assertNotIn("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH", codes)

    def test_repository_in_two_dispositions_is_flagged(self) -> None:
        policy = copy.deepcopy(self.policy)
        dupe = policy["dispositions"]["required"][0]
        policy["dispositions"]["adapter"].append(dupe)
        findings = validate(policy, self.manifest, self.candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("FLEET_REPOSITORY_MULTI_DISPOSITION", codes)

    def test_repository_outside_owner_namespace_is_flagged(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["dispositions"]["required"].append("someoneelse/rogue-repo")
        findings = validate(policy, self.manifest, self.candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("FLEET_REPOSITORY_OWNER_INVALID", codes)

    def test_candidate_sha_equal_to_admitted_sha_is_flagged_not_distinct(self) -> None:
        candidates = copy.deepcopy(self.candidates)
        first = candidates["candidates"][0]
        component_id = first["component"]
        admitted_sha = next(
            c["sha"] for c in self.manifest["components"] if c["id"] == component_id
        )
        first["candidate_sha"] = admitted_sha
        findings = validate(self.policy, self.manifest, candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("CANDIDATE_NOT_DISTINCT", codes)

    def test_candidate_for_unadmitted_component_is_flagged(self) -> None:
        candidates = copy.deepcopy(self.candidates)
        candidates["candidates"][0]["component"] = "not-a-real-component"
        findings = validate(self.policy, self.manifest, candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("CANDIDATE_COMPONENT_NOT_ADMITTED", codes)

    def test_duplicate_candidate_component_is_flagged(self) -> None:
        candidates = copy.deepcopy(self.candidates)
        candidates["candidates"].append(dict(candidates["candidates"][0]))
        findings = validate(self.policy, self.manifest, candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("CANDIDATE_DUPLICATE_COMPONENT", codes)

    def test_candidate_release_standing_overclaim_is_flagged(self) -> None:
        candidates = copy.deepcopy(self.candidates)
        candidates["candidates"][0]["release_standing"] = "ALIVE"
        findings = validate(self.policy, self.manifest, candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("CANDIDATE_RELEASE_STANDING_OVERCLAIM", codes)

    def test_default_disposition_not_fail_safe_is_flagged(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["fleet"]["default_release_blocking"] = True
        findings = validate(policy, self.manifest, self.candidates)
        codes = {f["code"] for f in findings}
        self.assertIn("FLEET_DEFAULT_NOT_FAIL_SAFE", codes)


if __name__ == "__main__":
    unittest.main()
