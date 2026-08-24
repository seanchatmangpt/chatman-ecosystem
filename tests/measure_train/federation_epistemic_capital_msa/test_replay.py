import unittest
from fractions import Fraction
from scripts.measure_train.federation_epistemic_capital_msa.subject import Subject
from scripts.measure_train.federation_epistemic_capital_msa.capital import EpistemicCapital
from scripts.measure_train.federation_epistemic_capital_msa.calibration import Calibration
from scripts.measure_train.federation_epistemic_capital_msa.receipt import manufacture
from scripts.measure_train.federation_epistemic_capital_msa.replay import replay
from scripts.measure_train.federation_epistemic_capital_msa.refusal import Refused
class T(unittest.TestCase):
 def test_tamper(self):
  r=manufacture(Subject("o/r","a"*40,"b"*64),EpistemicCapital(3,3,3,3,0),Calibration(10,Fraction(0),Fraction(0),Fraction(0),"CALIBRATED"),"PARTIAL_ALIVE"); self.assertEqual(replay(r),"REPLAY_MATCH"); r["body"]["standing"]="ALIVE"
  with self.assertRaises(Refused): replay(r)
