import unittest
from scripts.release_train.process_evidence_crown import *
from scripts.release_train.process_evidence_crown.receipt import Receipt
class T(unittest.TestCase):
 def test_do_is_brce_only(self):
  with self.assertRaises(Refused): admit(ActionClass.DO)
  self.assertTrue(admit(ActionClass.DO,'BRCE'))
 def test_receipt_replay_tamper_sensitive(self):
  s=Subject.parse('a/b','a'*40,'b'*64); r=Receipt(s,1,'PARTIAL_ALIVE',('e',),())
  self.assertEqual(replay(r,r.digest),'REPLAY_MATCH')
  with self.assertRaises(Refused): replay(r,'0'*64)
