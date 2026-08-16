from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("verify_portfolio", ROOT / "scripts" / "verify_portfolio.py")
verify_portfolio = importlib.util.module_from_spec(SPEC)
assert SPEC.loader is not None
sys.modules[SPEC.name] = verify_portfolio
SPEC.loader.exec_module(verify_portfolio)


class PortfolioControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = verify_portfolio.load(ROOT / "release" / "v26.9.1" / "fleet-policy.toml")
        self.manifest = verify_portfolio.load(ROOT / "release" / "v26.9.1" / "manifest.toml")
        self.candidates = verify_portfolio.load(ROOT / "release" / "v26.9.1" / "candidates.toml")

    def test_policy_and_candidates_are_admitted(self) -> None:
        self.assertEqual([], verify_portfolio.validate(self.policy, self.manifest, self.candidates))

    def test_unknown_owned_repo_defaults_out_of_release(self) -> None:
        self.assertEqual("OUT_OF_RELEASE", verify_portfolio.classify(self.policy, "seanchatmangpt/future-repo"))

    def test_capstone_classifies_crown(self) -> None:
        self.assertEqual("CROWN", verify_portfolio.classify(self.policy, "seanchatmangpt/fdegym"))

    def test_candidate_cannot_overclaim_release_standing(self) -> None:
        candidate = copy.deepcopy(self.candidates)
        candidate["candidates"][0]["release_standing"] = "ALIVE"
        codes = {finding["code"] for finding in verify_portfolio.validate(self.policy, self.manifest, candidate)}
        self.assertIn("CANDIDATE_RELEASE_STANDING_OVERCLAIM", codes)

    def test_release_repo_cannot_move_to_adapter(self) -> None:
        policy = copy.deepcopy(self.policy)
        repo = "seanchatmangpt/ggen"
        policy["dispositions"]["required"].remove(repo)
        policy["dispositions"]["adapter"].append(repo)
        codes = {finding["code"] for finding in verify_portfolio.validate(policy, self.manifest, self.candidates)}
        self.assertIn("FLEET_RELEASE_CLOSURE_MISMATCH", codes)

    def test_repository_count_is_constrained_by_pagination_not_a_historical_literal(self) -> None:
        policy = copy.deepcopy(self.policy)
        policy["fleet"]["observed_owned_repository_count"] = 401
        codes = {finding["code"] for finding in verify_portfolio.validate(policy, self.manifest, self.candidates)}
        self.assertIn("FLEET_OBSERVED_COUNT_PAGINATION_MISMATCH", codes)

    def test_current_355_repository_observation_is_pagination_consistent(self) -> None:
        self.assertEqual(355, self.policy["fleet"]["observed_owned_repository_count"])
        self.assertEqual([], verify_portfolio.validate_pagination_evidence(self.policy["fleet"]))


if __name__ == "__main__":
    unittest.main()
