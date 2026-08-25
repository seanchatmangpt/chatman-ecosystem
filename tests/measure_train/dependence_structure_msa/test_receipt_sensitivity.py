import unittest
from fractions import Fraction
from scripts.measure_train.dependence_structure_msa.subject import Subject,Refused
from scripts.measure_train.dependence_structure_msa.calibration import Calibration
from scripts.measure_train.dependence_structure_msa.sensitivity import compare
from scripts.measure_train.dependence_structure_msa.receipt import manufacture
from scripts.measure_train.dependence_structure_msa.replay import replay
class T(unittest.TestCase):
 def test_sensitivity_and_tamper(self):
  d=compare(Fraction(7,10),Fraction(9,10),Fraction(7,10),Fraction(9,10))
  self.assertGreater(d.lower_gain,0)
  s=Subject("o/r","a"*40,"b"*64); cal=Calibration(10,Fraction(0),Fraction(0),"CALIBRATED")
  r=manufacture(s,(("L","R","INDEPENDENT","INDEPENDENT"),),cal,"PARTIAL_ALIVE")
  self.assertEqual(replay(r),"REPLAY_MATCH")
  r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
