import unittest
from scripts.measure_train.sequential_policy_msa.subject import Subject
from scripts.measure_train.sequential_policy_msa.policy import PolicyIdentity
from scripts.measure_train.sequential_policy_msa.receipt import manufacture_receipt,replay
from scripts.measure_train.sequential_policy_msa.refusal import Refused
class T(unittest.TestCase):
 def test_replay_tamper(self):
  r=manufacture_receipt(Subject("o/r","a"*40),PolicyIdentity("p",1,"1"*64,"MAX_INFORMATION"),{"x":1},"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
