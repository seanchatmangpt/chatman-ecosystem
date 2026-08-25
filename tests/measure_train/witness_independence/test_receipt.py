import unittest
from fractions import Fraction
from scripts.measure_train.witness_independence.subject import Subject,Refused
from scripts.measure_train.witness_independence.standing import IndependencePolicy
from scripts.measure_train.witness_independence.receipt import manufacture_receipt
from scripts.measure_train.witness_independence.replay import replay
class T(unittest.TestCase):
 def test_tamper(self):
  d={"producers":0,"source_kinds":0,"effective_sources":Fraction(0,1)}
  r=manufacture_receipt(Subject("o/r","a"*40),(),d,"UNKNOWN",IndependencePolicy())
  self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="PARTIAL_ALIVE"
  with self.assertRaises(Refused): replay(r)
