import unittest
from dataclasses import replace
from scripts.develop_train.evidence_acquisition_runtime.subject import Subject,Refusal
from scripts.develop_train.evidence_acquisition_runtime.strategies import Strategy
from scripts.develop_train.evidence_acquisition_runtime.receipt import issue,replay
from scripts.develop_train.evidence_acquisition_runtime.authority import ActionClass,admit_action
class T(unittest.TestCase):
 def test_receipt_tamper_and_do_refusal(self):
  r=issue(Subject('o/r','b'*40),'c'*64,Strategy.MAX_INFORMATION_GAIN,('a',),'PARTIAL_ALIVE'); d=r.digest(); self.assertTrue(replay(r,d)); self.assertFalse(replay(replace(r,standing='ALIVE'),d)); self.assertFalse(replay(replace(r,actuation_performed=True),d))
  with self.assertRaisesRegex(Refusal,'BRCE'): admit_action(ActionClass.DO)
