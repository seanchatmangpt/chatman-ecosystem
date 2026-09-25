"""Receipt chain read from git: the parent is the committed chain head; every breach is a
typed RECEIPT_CHAIN_BROKEN token. Real committed receipts, copied and mutated on disk."""

from __future__ import annotations

import json
import shutil
import tempfile
import unittest
from pathlib import Path

from _support import REPO, RELEASE

from scripts.release_train.root_crown import chain, crown
from scripts.release_train.root_crown.model import CHAIN_TOKENS

HARDENING = REPO / "release" / RELEASE / "hardening"
TAG_COMMIT = "68bacd8dcc9ae12e4e97727a284c14abdc7520c5"
HEAD_DIGEST = "sha256:7e7e9c80c3cd4649d9e00039d2336c8b5ff477b53227332dd4b445de3c2cc856"


def tokens(result: chain.ChainResult) -> set[str]:
    return {r.split(":")[2] for r in result.refusals if r.startswith("REFUSED:RECEIPT_CHAIN_BROKEN:")}


@unittest.skipUnless((HARDENING / chain.CHAIN_FILE).is_file(), "hardening chain not committed")
class ChainTest(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self._tmp.name) / "hardening"
        shutil.copytree(HARDENING, self.dir)

    def tearDown(self):
        self._tmp.cleanup()

    def head_receipt_path(self) -> Path:
        doc = json.loads((self.dir / chain.CHAIN_FILE).read_text())
        return self.dir / doc["entries"][-1]["path"]

    def rewrite_head(self, **fields) -> None:
        """Replace the chain head with a self-consistent receipt carrying ``fields``."""
        path = self.head_receipt_path()
        receipt = json.loads(path.read_text()) | fields
        receipt["receipt_digest"] = crown.receipt_digest_of(receipt)
        path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
        doc = chain.project(self.dir, RELEASE)
        (self.dir / chain.CHAIN_FILE).write_text(json.dumps(doc, indent=2, sort_keys=True) + "\n")

    def test_committed_chain_head_is_the_parent(self):
        result = chain.parent_of(self.dir, {TAG_COMMIT})
        self.assertEqual((result.refusals, result.blockers), ([], []))
        self.assertEqual(result.parent_digest, HEAD_DIGEST)

    def test_projection_orders_by_hash_links(self):
        doc = chain.project(HARDENING, RELEASE)
        links = [(e["previous_receipt_digest"], e["receipt_digest"]) for e in doc["entries"]]
        for (_, prev), (link, _) in zip(links, links[1:]):
            self.assertEqual(link, prev)
        self.assertEqual(doc["head"], HEAD_DIGEST)

    def test_absent_ancestry_is_a_typed_blocker_not_a_pass(self):
        result = chain.parent_of(self.dir, None)
        self.assertEqual(result.refusals, [])
        self.assertTrue(any(b.startswith("BLOCKED:OBSERVATION_MISSING:") for b in result.blockers))

    def test_parent_digest(self):
        path = self.head_receipt_path()
        receipt = json.loads(path.read_text())
        receipt["standing"] = "ALIVE "  # bytes change, recorded digest does not
        path.write_text(json.dumps(receipt))
        result = chain.parent_of(self.dir, {TAG_COMMIT})
        self.assertIn("PARENT_DIGEST", tokens(result))
        self.assertIsNone(result.parent)

    def test_parent_refused(self):
        self.rewrite_head(standing="REFUSED")
        self.assertEqual(tokens(chain.parent_of(self.dir, {TAG_COMMIT})), {"PARENT_REFUSED"})

    def test_parent_untyped_blocked(self):
        self.rewrite_head(
            standing="BLOCKED", remaining=[{"id": "AC-02", "state": "BLOCKED", "code": None, "failure_class": None}]
        )
        self.assertEqual(tokens(chain.parent_of(self.dir, {TAG_COMMIT})), {"PARENT_UNTYPED_BLOCKED"})

    def test_typed_blocked_parent_is_admitted(self):
        self.rewrite_head(
            standing="BLOCKED",
            remaining=[
                {
                    "id": "AC-12",
                    "state": "BLOCKED",
                    "code": "NOT_COLD",
                    "failure_class": "EVIDENCE_FAILURE",
                    "broken_term": "R_missing_replay",
                }
            ],
        )
        self.assertEqual(chain.parent_of(self.dir, {TAG_COMMIT}).refusals, [])

    def test_parent_not_ancestor(self):
        self.assertEqual(tokens(chain.parent_of(self.dir, {"f" * 40})), {"PARENT_NOT_ANCESTOR"})

    def test_every_chain_token_has_a_refusing_test(self):
        covered = {"PARENT_DIGEST", "PARENT_REFUSED", "PARENT_UNTYPED_BLOCKED", "PARENT_NOT_ANCESTOR"}
        self.assertEqual(covered, set(CHAIN_TOKENS))

    def test_absent_chain_file_refuses(self):
        (self.dir / chain.CHAIN_FILE).unlink()
        self.assertEqual(tokens(chain.parent_of(self.dir, {TAG_COMMIT})), {"PARENT_DIGEST"})


if __name__ == "__main__":
    unittest.main()
