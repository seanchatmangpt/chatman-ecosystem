"""CLI exit codes follow standing: 0 ALIVE, 3 typed BLOCKED, 2 REFUSED."""

from __future__ import annotations

import copy
import json
import unittest

from _support import CROWN_SHA, alive_observations, alive_tree, dump

from scripts.release_train.root_crown.__main__ import main


class CliTest(unittest.TestCase):
    def setUp(self):
        self.tree = alive_tree()
        self.obs = alive_observations(self.tree)

    def tearDown(self):
        self.tree.cleanup()

    def run_cli(self, obs, previous=None, head_sha=CROWN_SHA, extra=()):
        root = self.tree.root
        dump(root / "obs.json", obs)
        argv = [
            "--release",
            "v26.9.25",
            "--root",
            str(root),
            "--observations",
            str(root / "obs.json"),
            "--crown-sha",
            CROWN_SHA,
            "--out",
            str(root / "out/receipt.json"),
            "--tag-decision",
            str(root / "out/tag-decision.json"),
        ]
        if previous is not None:
            argv += ["--previous", str(previous)]
        if head_sha is not None:
            argv += ["--head-sha", head_sha]
        return main(argv + list(extra))

    def decision(self):
        return json.loads((self.tree.root / "out/tag-decision.json").read_text())

    def test_head_sha_is_real_not_the_crown_sha(self):
        """__main__ used to pass crown_sha as head_sha, making SHA_MISMATCH vacuous."""
        self.assertEqual(self.run_cli(self.obs, head_sha="d" * 40), 0)
        self.assertEqual(self.decision()["decision"], "ILLEGAL")
        self.assertIn(f"TAG_ILLEGAL:SHA_MISMATCH:head={'d' * 40}:crown={CROWN_SHA}", self.decision()["reasons"])
        self.assertEqual(self.run_cli(self.obs, head_sha=None), 0)
        self.assertEqual(self.decision()["decision"], "ILLEGAL", "absent --head-sha must fail closed")

    def test_pre_tag_receipt_is_schema_v2_and_verifies(self):
        from scripts.release_train.root_crown.crown import verify_receipt

        self.assertEqual(self.run_cli(self.obs, extra=["--mode", "PRE_TAG"]), 0)
        receipt = json.loads((self.tree.root / "out/receipt.json").read_text())
        self.assertEqual(receipt["schema"], "https://chatman.dev/root-crown/receipt/v2")
        self.assertEqual((receipt["mode"], receipt["attestation_head_sha"]), ("PRE_TAG", CROWN_SHA))
        self.assertEqual(receipt["subject"]["commit_sha"], CROWN_SHA)
        self.assertIsNone(receipt["historical"])
        self.assertTrue(verify_receipt(receipt))
        self.assertTrue(verify_receipt(receipt["current"]["core"]), "v1 core receipts still verify")
        tampered = dict(receipt, standing="BLOCKED")
        self.assertFalse(verify_receipt(tampered))

    def test_post_tag_requested_without_record_is_typed_blocked(self):
        self.assertEqual(self.run_cli(self.obs, extra=["--mode", "POST_TAG"]), 3)
        receipt = json.loads((self.tree.root / "out/receipt.json").read_text())
        self.assertEqual(receipt["mode"], "POST_TAG")
        self.assertIn("TAG_UNRECORDED", {b["code"] for b in receipt["blockers"]})
        self.assertEqual(self.decision()["decision"], "NOT_APPLICABLE:POST_TAG")

    def test_absent_observation_file_is_typed_blocked_not_a_crash(self):
        root = self.tree.root
        argv = [
            "--release", "v26.9.25", "--root", str(root), "--observations", str(root / "absent.json"),
            "--crown-sha", CROWN_SHA, "--head-sha", CROWN_SHA, "--out", str(root / "out/receipt.json"),
        ]  # fmt: skip
        self.assertEqual(main(argv), 3)

    def test_alive_exit_0_and_legal_tag_decision(self):
        self.assertEqual(self.run_cli(self.obs), 0)
        decision = json.loads((self.tree.root / "out/tag-decision.json").read_text())
        self.assertEqual(decision["decision"], "LEGAL")

    def test_typed_blocked_exit_3(self):
        obs = copy.deepcopy(self.obs)
        obs["environment"]["cold"] = False
        self.assertEqual(self.run_cli(obs), 3)
        receipt = json.loads((self.tree.root / "out/receipt.json").read_text())
        self.assertEqual(receipt["requirements"]["AC-12"]["code"], "NOT_COLD")
        self.assertEqual(receipt["current"]["core"]["requirements"]["AC-12"]["code"], "NOT_COLD")
        decision = json.loads((self.tree.root / "out/tag-decision.json").read_text())
        self.assertEqual(decision["decision"], "ILLEGAL")

    def test_refused_exit_2(self):
        obs = copy.deepcopy(self.obs)
        obs["tag"]["sha"] = "d" * 40
        self.assertEqual(self.run_cli(obs), 2)

    def test_missing_previous_file_is_genesis_and_existing_one_chains(self):
        self.assertEqual(self.run_cli(self.obs, previous=self.tree.root / "absent.json"), 0)
        first = json.loads((self.tree.root / "out/receipt.json").read_text())
        self.assertTrue(first["genesis"])
        dump(self.tree.root / "prev.json", first)
        self.assertEqual(self.run_cli(self.obs, previous=self.tree.root / "prev.json"), 0)
        second = json.loads((self.tree.root / "out/receipt.json").read_text())
        self.assertEqual(second["previous_receipt_digest"], first["receipt_digest"])


if __name__ == "__main__":
    unittest.main()
