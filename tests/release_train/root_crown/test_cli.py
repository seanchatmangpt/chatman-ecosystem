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

    def run_cli(self, obs, previous=None):
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
        return main(argv)

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
