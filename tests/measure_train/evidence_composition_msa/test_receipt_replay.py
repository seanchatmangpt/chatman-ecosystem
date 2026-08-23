import unittest
from fractions import Fraction
from scripts.measure_train.evidence_composition_msa.subject import Subject,Refused
from scripts.measure_train.evidence_composition_msa.calibration import CompositionCalibration
from scripts.measure_train.evidence_composition_msa.receipt import manufacture
from scripts.measure_train.evidence_composition_msa.replay import replay
class T(unittest.TestCase):
 def test_tamper_refuses(self):
  s=Subject("o/r","a"*40,"b"*64); c=CompositionCalibration(10,Fraction(9,10),Fraction(1,10),Fraction(1,3),"CALIBRATED")
  r=manufacture(s,c,(),"PARTIAL_ALIVE"); self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
