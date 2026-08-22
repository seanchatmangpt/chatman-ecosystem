import unittest
from dataclasses import replace
from scripts.develop_train.regime_ensemble.authority import ActionClass,admit_action
from scripts.develop_train.regime_ensemble.receipt import issue,replay
from scripts.develop_train.regime_ensemble.subject import Subject
class TestReceiptAuthority(unittest.TestCase):
    def test_do_refused_and_receipt_tamper_detected(self):
        with self.assertRaisesRegex(PermissionError,"BRCE"): admit_action(ActionClass.DO)
        r,d=issue(Subject("o/r","b"*40),"STABLE",("a","b"),"PARTIAL_ALIVE")
        self.assertTrue(replay(r,d)); self.assertFalse(replay(replace(r,standing="ALIVE"),d))
if __name__ == "__main__": unittest.main()
