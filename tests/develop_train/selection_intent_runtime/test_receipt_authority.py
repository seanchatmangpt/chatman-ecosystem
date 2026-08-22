import unittest
from dataclasses import replace
from scripts.develop_train.selection_intent_runtime.receipt import *
from scripts.develop_train.selection_intent_runtime.authority import *
class TestReceiptAuthority(unittest.TestCase):
 def test_tamper_and_do_refusal(self):
  r=QualificationReceipt("a/x@"+"a"*40,"c","RESELECT","a"*64,"b"*64,"REQUALIFYING","MEMORY"); d=r.digest; self.assertTrue(replay(r,d)); self.assertFalse(replay(replace(r,standing="ALIVE"),d)); tampered=replace(r,actuation_performed=True); self.assertFalse(replay(tampered,tampered.digest))
  with self.assertRaisesRegex(PermissionError,"BRCE_REQUIRED"): require(ActionClass.DO)
