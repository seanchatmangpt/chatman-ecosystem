import unittest

from scripts.develop_train.calibrated_recovery_quorum.receipt import (
    QualificationReceipt,
    replay,
)


class TestReceipt(unittest.TestCase):
    def test_replay_and_tamper(self):
        receipt = QualificationReceipt(
            "a/b@" + "a" * 40,
            "att",
            ("s",),
            2,
            "2.1",
            "ACCEPT_BOUNDED",
            (),
            "SQLITE",
            "PARTIAL_ALIVE",
        )
        digest = receipt.digest()
        self.assertTrue(replay(receipt, digest))
        tampered = QualificationReceipt(
            receipt.subject,
            receipt.attempt_id,
            receipt.calibrated_sources,
            receipt.independent_clusters,
            receipt.statistic,
            receipt.decision,
            receipt.blockers,
            receipt.store,
            receipt.standing,
            True,
        )
        self.assertFalse(replay(tampered, tampered.digest()))
