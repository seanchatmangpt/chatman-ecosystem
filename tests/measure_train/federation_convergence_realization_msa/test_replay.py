import unittest
from fractions import Fraction
from scripts.measure_train.federation_convergence_realization_msa.subject import Subject
from scripts.measure_train.federation_convergence_realization_msa.calibration import Calibration
from scripts.measure_train.federation_convergence_realization_msa.receipt import manufacture
from scripts.measure_train.federation_convergence_realization_msa.replay import replay
from scripts.measure_train.federation_convergence_realization_msa.refusals import Refused
class T(unittest.TestCase):
 def test_tamper(self):
  r=manufacture(Subject('o/r','a'*40,'b'*64,1),Calibration(5,Fraction(0),Fraction(0),'CALIBRATED'),Fraction(2),'PARTIAL_ALIVE'); self.assertEqual(replay(r),'REPLAY_MATCH'); r['body']['actuation_performed']=True
  with self.assertRaises(Refused): replay(r)
