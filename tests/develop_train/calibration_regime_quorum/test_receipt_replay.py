import unittest
from scripts.develop_train.calibration_regime_quorum.authority_receipt import QualificationReceipt,replay
from scripts.develop_train.calibration_regime_quorum.subject import Subject
class ReceiptReplayCourt(unittest.TestCase):
    def test_deterministic_replay_and_tamper_refusal(self):
        subject=Subject("owner/repo","a"*40); receipt=QualificationReceipt(subject,(("a",1),("b",2)),"ACCEPT_BOUNDED","PARTIAL_ALIVE","SQLITE",()); digest=receipt.digest(); self.assertTrue(replay(receipt,digest)); tampered=QualificationReceipt(subject,(("a",1),("b",3)),"ACCEPT_BOUNDED","PARTIAL_ALIVE","SQLITE",()); self.assertFalse(replay(tampered,digest)); actuating=QualificationReceipt(subject,(("a",1),),"CONTINUE","UNKNOWN","MEMORY",(),True); self.assertFalse(replay(actuating,actuating.digest()))
if __name__=="__main__": unittest.main()
