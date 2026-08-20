from __future__ import annotations

import copy
import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify_pending_branch_bundle.py"
spec = importlib.util.spec_from_file_location("verify_pending_branch_bundle", SCRIPT)
assert spec is not None and spec.loader is not None
mod = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod
spec.loader.exec_module(mod)


class PendingBranchBundleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data = mod.load_bundle(ROOT / "release" / "v26.9.1" / "pending-branches.toml")

    def assert_refused(self, data: dict, code: str) -> None:
        with self.assertRaises(mod.Refusal) as ctx:
            mod.validate(data)
        self.assertEqual(str(ctx.exception), code)

    def test_current_bundle_is_closed_and_observed(self) -> None:
        receipt = mod.validate(self.data)
        self.assertEqual(receipt["standing"], "OBSERVED")
        self.assertEqual(receipt["repository_count"], 3)
        self.assertEqual(receipt["branch_count"], 17)
        self.assertEqual(receipt["integration_count"], 3)
        self.assertEqual(
            receipt["per_repository"],
            {
                "seanchatmangpt/autofde-lab": 9,
                "seanchatmangpt/gymact": 5,
                "seanchatmangpt/mfw": 3,
            },
        )

    def test_authority_escalation_is_refused(self) -> None:
        mutated = copy.deepcopy(self.data)
        mutated["bundle"]["merge_authority"] = True
        self.assert_refused(mutated, "REFUSED:AUTHORITY_ESCALATION:merge_authority")

    def test_duplicate_pr_is_refused(self) -> None:
        mutated = copy.deepcopy(self.data)
        duplicate = copy.deepcopy(mutated["branch"][0])
        duplicate["ref"] = "agent/duplicate-ref"
        duplicate["sha"] = "0" * 40
        mutated["branch"].append(duplicate)
        mutated["bundle"]["branch_count"] += 1
        self.assert_refused(mutated, "REFUSED:DUPLICATE_PR:seanchatmangpt/autofde-lab#79")

    def test_invalid_sha_is_refused(self) -> None:
        mutated = copy.deepcopy(self.data)
        mutated["branch"][0]["sha"] = "not-a-sha"
        self.assert_refused(mutated, "REFUSED:INVALID_SHA:seanchatmangpt/autofde-lab#79")

    def test_integration_identity_drift_is_refused(self) -> None:
        mutated = copy.deepcopy(self.data)
        mutated["branch"][0]["sha"] = "0" * 40
        self.assert_refused(mutated, "REFUSED:INTEGRATION_IDENTITY_DRIFT:seanchatmangpt/autofde-lab#79")

    def test_integration_role_cannot_be_erased(self) -> None:
        mutated = copy.deepcopy(self.data)
        mutated["branch"][0]["role"] = "SOURCE"
        self.assert_refused(mutated, "REFUSED:INTEGRATION_ROLE_DRIFT:seanchatmangpt/autofde-lab#79")


if __name__ == "__main__":
    unittest.main()
