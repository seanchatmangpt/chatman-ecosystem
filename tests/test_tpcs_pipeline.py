from __future__ import annotations

import importlib.util
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("tpcs_pipeline", ROOT / "scripts" / "tpcs_pipeline.py")
assert SPEC is not None and SPEC.loader is not None
mod = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = mod
SPEC.loader.exec_module(mod)


class ToyotaCodeProductionSystemTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.cfg = mod.load_config()

    def test_config_preserves_pull_and_zero_unreceipted_actuation(self) -> None:
        mod.validate_config(self.cfg)
        self.assertEqual(self.cfg["mode"], "pull")
        self.assertTrue(self.cfg["zero_unreceipted_actuation"])
        self.assertFalse(self.cfg["acceptance_mutation_authority"])

    def test_stage_order_is_fixed(self) -> None:
        self.assertEqual(
            [stage["id"] for stage in self.cfg["stage"]],
            ["observe", "admit", "construct", "verify", "receipt", "replay", "standing"],
        )

    def test_good_construct_reaches_alive_with_receipt(self) -> None:
        item = mod.WorkItem("a" * 40, "python3 -m unittest", "CONSTRUCT")
        result = mod.run(item, self.cfg)
        self.assertEqual(result["standing"], "ALIVE")
        self.assertRegex(result["sha256"], r"^[0-9a-f]{64}$")
        self.assertTrue(result["replay_match"])

    def assert_refused(self, item, expected: str) -> None:
        with self.assertRaises(mod.Refusal) as ctx:
            mod.run(item, self.cfg)
        self.assertEqual(str(ctx.exception), expected)

    def test_invalid_subject_is_refused(self) -> None:
        self.assert_refused(mod.WorkItem("HEAD", "x", "SELECT"), "REFUSED_INVALID_SUBJECT")

    def test_acceptance_mutation_is_refused(self) -> None:
        self.assert_refused(
            mod.WorkItem("b" * 40, "x", "CONSTRUCT", acceptance_mutated=True),
            "REFUSED_ACCEPTANCE_MUTATION",
        )

    def test_unreceipted_do_is_refused(self) -> None:
        self.assert_refused(
            mod.WorkItem("c" * 40, "x", "DO", actuation_receipted=False),
            "REFUSED_UNRECEIPTED_ACTUATION",
        )

    def test_replay_mismatch_is_refused(self) -> None:
        self.assert_refused(
            mod.WorkItem("d" * 40, "x", "SELECT", replay_match=False),
            "REFUSED_REPLAY_MISMATCH",
        )

    def test_wip_limit_is_fail_closed(self) -> None:
        stage = next(stage for stage in self.cfg["stage"] if stage["id"] == "construct")
        with self.assertRaises(mod.Refusal) as ctx:
            mod.enforce_wip(stage, stage["wip_limit"] + 1, self.cfg)
        self.assertEqual(str(ctx.exception), "REFUSED_WIP_LIMIT")


if __name__ == "__main__":
    unittest.main()
