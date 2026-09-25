"""hardening.py: TAG-SUBJECT.json, receipts/chain.json and replay-receipt.json are
deterministic projections of committed bytes (+ the materialized tag subject)."""

from __future__ import annotations

import json
import os
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import REPO, RELEASE

from scripts.release_train.root_crown import chain, hardening

HARDENING = REPO / "release" / RELEASE / "hardening"
SUBJECT = Path(os.environ.get("ROOT_CROWN_SUBJECT_TREE", "/nonexistent-subject"))
REPOSITORY = "seanchatmangpt/chatman-ecosystem"


def dump(value) -> bytes:
    return (json.dumps(value, indent=2, sort_keys=True) + "\n").encode()


@unittest.skipUnless((HARDENING / hardening.TAG_SUBJECT).is_file(), "hardening projection not committed")
class HardeningProjectionTest(unittest.TestCase):
    def test_committed_tag_subject_and_chain_are_current_and_deterministic(self):
        first = dump(hardening.project_tag_subject(HARDENING, RELEASE, REPOSITORY))
        second = dump(hardening.project_tag_subject(HARDENING, RELEASE, REPOSITORY))
        self.assertEqual(first, second)
        self.assertEqual((HARDENING / hardening.TAG_SUBJECT).read_bytes(), first)
        self.assertEqual((HARDENING / chain.CHAIN_FILE).read_bytes(), dump(chain.project(HARDENING, RELEASE)))
        record = json.loads(first)
        self.assertEqual(record["GENERATED"], hardening.GENERATED)
        self.assertEqual(record["tag"]["object_sha"], "337e839937c247de4ee58b744c8b8e43950d18e3")
        self.assertEqual(record["payload"]["tree_sha"], "a01b914de2e4b3503dc2126ce233654af764c362")

    def test_projection_carries_no_machine_local_path(self):
        for name in (hardening.TAG_SUBJECT, chain.CHAIN_FILE, hardening.REPLAY_RECEIPT):
            text = (HARDENING / name).read_text()
            with self.subTest(name=name):
                for marker in ("/Users/", "/tmp/", "/private/", "~/", "/home/"):
                    self.assertNotIn(marker, text)

    def test_check_refuses_a_hand_edit(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "hardening"
            shutil.copytree(HARDENING, copy)
            rendered = {
                hardening.TAG_SUBJECT: dump(hardening.project_tag_subject(copy, RELEASE, REPOSITORY)),
                chain.CHAIN_FILE: dump(chain.project(copy, RELEASE)),
            }
            self.assertEqual(hardening.check(copy, rendered), [])
            path = copy / hardening.TAG_SUBJECT
            path.write_text(path.read_text().replace('"approval_run": "36161744816"', '"approval_run": "1"'))
            drift = hardening.check(copy, rendered)
        self.assertEqual(len(drift), 1)
        self.assertTrue(drift[0].startswith("REFUSED:PROJECTION_DRIFT:") and drift[0].endswith(hardening.TAG_SUBJECT))

    def test_two_tag_objects_for_one_release_are_refused(self):
        with tempfile.TemporaryDirectory() as tmp:
            copy = Path(tmp) / "hardening"
            shutil.copytree(HARDENING, copy)
            from scripts.release_train.root_crown import gitobj

            body = (copy / hardening.OBJECTS / "337e839937c247de4ee58b744c8b8e43950d18e3.tag.raw").read_bytes()
            other = body.replace(b"approval run", b"approval  run")
            (copy / hardening.OBJECTS / f"{gitobj.object_sha('tag', other)}.tag.raw").write_bytes(other)
            with self.assertRaises(hardening.HardeningError) as ctx:
                hardening.project_tag_subject(copy, RELEASE, REPOSITORY)
        self.assertIn("TAG_UNRECORDED", str(ctx.exception))

    @unittest.skipUnless(
        (SUBJECT / "scripts").is_dir(), "ROOT_CROWN_SUBJECT_TREE (git archive of 68bacd8d) not provided"
    )
    def test_replay_receipt_is_current(self):
        rendered = hardening.outputs(HARDENING, RELEASE, REPOSITORY, SUBJECT, REPO)
        self.assertEqual(hardening.check(HARDENING, rendered), [])
        replay = json.loads(rendered[hardening.REPLAY_RECEIPT])
        self.assertTrue(replay["historical"]["replay"]["exact"])
        self.assertEqual(replay["historical"]["replay_standing"], "HISTORICAL_RELEASE_REPLAY_EXACT")


if __name__ == "__main__":
    unittest.main()
