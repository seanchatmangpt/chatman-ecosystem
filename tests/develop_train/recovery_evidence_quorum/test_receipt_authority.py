import unittest
from scripts.develop_train.recovery_evidence_quorum.authority import ActionClass, require_nonconsequential
from scripts.develop_train.recovery_evidence_quorum.policy import Standing
from scripts.develop_train.recovery_evidence_quorum.receipt import QualificationReceipt, replay
from scripts.develop_train.recovery_evidence_quorum.subject import Refused

class TestReceiptAuthority(unittest.TestCase):
    def test_receipt_tamper_and_do_refusal(self):
        r=QualificationReceipt('o/r@'+'a'*40,'attempt',Standing.UNKNOWN,(('e',),),'1/1',(), 'MEMORY','CONSTRUCT')
        self.assertTrue(replay(r,r.digest))
        bad=QualificationReceipt(r.subject,r.attempt_id,r.standing,r.clusters,r.diversity,r.blockers,r.store,r.action,True)
        self.assertFalse(replay(bad,r.digest))
        with self.assertRaisesRegex(Refused,'BRCE_REQUIRED'): require_nonconsequential(ActionClass.DO)
