import unittest
from scripts.develop_train.fused_acquisition.receipt import Receipt,replay
from scripts.develop_train.fused_acquisition.authority import ActionClass,admit_action
from scripts.develop_train.fused_acquisition.refusals import Refused
class TestReceiptAuthority(unittest.TestCase):
 def test_receipt_tamper_and_do_refusal(self):
  r=Receipt('seanchatmangpt/chatman-ecosystem@'+'a'*40,4,'CURRENT','MAX_INFORMATION',None,'PARTIAL_ALIVE'); d=r.digest(); self.assertTrue(replay(r,d))
  with self.assertRaises(Refused): replay(Receipt(r.subject,4,'STALE','MAX_INFORMATION',None,'UNKNOWN'),d)
  with self.assertRaises(Refused): admit_action(ActionClass.DO)
