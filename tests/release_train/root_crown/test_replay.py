"""Isolated tag-time replay.

The exact-replay test needs the real tag subject (``git archive 68bacd8d release scripts
docs/jira/v26.9.25``), materialized outside the court because the court is subprocess-free;
its directory is passed as ``ROOT_CROWN_SUBJECT_TREE`` (the root-crown workflow's Subject
step sets it). Without it that test is a named skip, never a substitute. The isolation
tests use a real, tiny subject package written to disk (a genuine ``evaluate`` with a
fixed receipt), not a mock.
"""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

from _support import REPO, RELEASE

from scripts.release_train.root_crown import crown as head_crown
from scripts.release_train.root_crown import gitobj, replay

SUBJECT = Path(os.environ.get("ROOT_CROWN_SUBJECT_TREE", "/nonexistent-subject"))
HARDENING = REPO / "release" / RELEASE / "hardening"
TAG_COMMIT = "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"
TAG_DIGEST = "sha256:2323f877bca4d3fdca217ace53e7501f7978ed66e4afbdd39904e1f1cda0fa0c"

FAKE_CROWN = """
from types import SimpleNamespace

def evaluate(release_dir, observations, previous, crown_sha, root=None):
    marker = observations.get("marker", "none")
    return SimpleNamespace(standing="ALIVE", receipt={"receipt_digest": "sha256:" + marker})
"""


def historical_inputs():
    obs = json.loads((HARDENING / "receipts/run-36161744816/observations.json").read_text())
    prev = json.loads((HARDENING / "receipts/run-36160116076/crown-receipt.json").read_text())
    return obs, prev


def fake_subject(root: Path) -> Path:
    pkg = root / "scripts/release_train/root_crown"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "crown.py").write_text(FAKE_CROWN)
    (root / "release" / RELEASE).mkdir(parents=True)
    return root


class IsolationTest(unittest.TestCase):
    def test_subject_code_runs_and_caller_modules_are_restored(self):
        before = sys.modules["scripts.release_train.root_crown.crown"]
        path_before = list(sys.path)
        with tempfile.TemporaryDirectory() as tmp:
            subject = fake_subject(Path(tmp))
            result = replay.replay(subject, RELEASE, {"marker": "abc"}, None, "c" * 40, "sha256:abc")
            self.assertEqual((result.exact, result.receipt_digest), (True, "sha256:abc"))
            self.assertEqual(list(subject.rglob("__pycache__")), [], "replay must not write into the subject")
        self.assertIs(sys.modules["scripts.release_train.root_crown.crown"], before)
        self.assertIs(head_crown.evaluate, before.evaluate)
        self.assertEqual(sys.path, path_before)

    def test_divergent_digest_is_typed_replay_diverged(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = replay.replay(fake_subject(Path(tmp)), RELEASE, {"marker": "abc"}, None, "c" * 40, "sha256:xyz")
        self.assertFalse(result.exact)
        self.assertTrue(result.refusal().startswith("BLOCKED:REPLAY_DIVERGED:replayed=sha256:abc"))

    def test_subject_without_code_diverges_instead_of_importing_head_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            (Path(tmp) / "release" / RELEASE).mkdir(parents=True)
            result = replay.replay(Path(tmp), RELEASE, {}, None, "c" * 40, TAG_DIGEST)
        self.assertFalse(result.exact)
        self.assertIn("REPLAY_DIVERGED", result.refusal())
        self.assertIn("ModuleNotFoundError", result.detail)


@unittest.skipUnless((SUBJECT / "scripts").is_dir(), "ROOT_CROWN_SUBJECT_TREE (git archive of 68bacd8d) not provided")
class ExactReplayTest(unittest.TestCase):
    def test_tag_time_crown_reproduces_2323f877(self):
        obs, prev = historical_inputs()
        tree_before = gitobj.tree_sha_of_dir(SUBJECT / "scripts")
        result = replay.replay(SUBJECT, RELEASE, obs, prev, TAG_COMMIT, TAG_DIGEST)
        self.assertTrue(result.exact, result.detail)
        self.assertEqual((result.receipt_digest, result.standing), (TAG_DIGEST, "ALIVE"))
        self.assertEqual(gitobj.tree_sha_of_dir(SUBJECT / "scripts"), tree_before)

    def test_substituted_observation_diverges(self):
        obs, prev = historical_inputs()
        obs["observed_at"] = "2026-09-25T16:36:09Z"
        result = replay.replay(SUBJECT, RELEASE, obs, prev, TAG_COMMIT, TAG_DIGEST)
        self.assertFalse(result.exact)
        self.assertIn("REPLAY_DIVERGED", result.refusal())


if __name__ == "__main__":
    unittest.main()
