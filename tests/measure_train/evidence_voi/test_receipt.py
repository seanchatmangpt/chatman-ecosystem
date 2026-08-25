import unittest
from fractions import Fraction
from scripts.measure_train.evidence_voi.subject import Subject,Refused
from scripts.measure_train.evidence_voi.belief import BeliefState
from scripts.measure_train.evidence_voi.intent import MeasurementIntent
from scripts.measure_train.evidence_voi.receipt import manufacture_receipt,replay
class T(unittest.TestCase):
 def test_tamper_and_no_do(self):
  i=MeasurementIntent(Subject("o/r","a"*40),("x",),"1"*64,"MAX_INFORMATION_GAIN")
  r=manufacture_receipt(i,BeliefState(Fraction(1,2),0),(),"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH"); self.assertFalse(r["body"]["actuation_performed"])
  r["body"]["authority"]="DO"
  with self.assertRaises(Refused): replay(r)
