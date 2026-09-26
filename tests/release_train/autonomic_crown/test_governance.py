"""observe_governance parsing (pure functions over real API response shapes; no network)."""

from __future__ import annotations

import unittest

from scripts.observe_governance import parse_branch, parse_environment
from scripts.release_train.autonomic_crown.standing import authority_of


class GovernanceTest(unittest.TestCase):
    def test_parse_branch(self):
        self.assertEqual(parse_branch({"name": "main", "protected": True}), {"protected": True})
        self.assertEqual(parse_branch({"name": "main", "protected": False}), {"protected": False})
        self.assertEqual(parse_branch({"name": "main"}), {"protected": False})

    def test_parse_environment(self):
        env = {
            "name": "release-crown",
            "protection_rules": [
                {"id": 1, "type": "wait_timer", "wait_timer": 0},
                {"id": 2, "type": "required_reviewers", "reviewers": [{"type": "User", "reviewer": {"login": "op"}}]},
            ],
            "deployment_branch_policy": {"protected_branches": True, "custom_branch_policies": False},
        }
        self.assertEqual(parse_environment(env), {"present": True, "reviewers": 1, "protected_branches": True})
        self.assertEqual(
            parse_environment({"name": "release-crown", "protection_rules": [], "deployment_branch_policy": None}),
            {"present": True, "reviewers": 0, "protected_branches": False},
        )
        self.assertEqual(parse_environment(None), {"present": False, "reviewers": 0, "protected_branches": False})

    def test_observed_shapes_drive_authority(self):
        today = {
            "main": parse_branch({"protected": False}),
            "environments": {"release-crown": parse_environment({"protection_rules": []})},
        }
        self.assertEqual(authority_of(today, [])[0], "WAITING_EXTERNAL_AUTHORITY")
        unobserved = {
            "main": {"protected": None, "unobserved": 0},
            "environments": {"release-crown": {"unobserved": 0}},
        }
        self.assertEqual(authority_of(unobserved, [])[0], "WAITING_EXTERNAL_AUTHORITY")


if __name__ == "__main__":
    unittest.main()
