import unittest
from datetime import datetime,timezone
from fractions import Fraction
from scripts.measure_train.outcome_capital_transport_msa.subject import Subject,Refused
from scripts.measure_train.outcome_capital_transport_msa.observation import OutcomeObservation
from scripts.measure_train.outcome_capital_transport_msa.calibration import calibrate,CalibrationModel,current
from scripts.measure_train.outcome_capital_transport_msa.drift import Cusum
class T(unittest.TestCase):
 def test_realized_correctness_and_frontier(self):
  s=Subject("o/r","a"*40,"b"*64); now=datetime.now(timezone.utc)
  rows=[OutcomeObservation(s,str(i),"PREDICTION","e","r","root",1,Fraction(1),Fraction(0),"INDEPENDENT","INDEPENDENT",now) for i in range(5)]
  self.assertEqual(calibrate(rows)[2],"CALIBRATED")
  with self.assertRaises(Refused): current([CalibrationModel(1,"a"*64,5,Fraction(0),"CALIBRATED"),CalibrationModel(1,"b"*64,5,Fraction(0),"CALIBRATED")])
  c=Cusum(0.5); self.assertTrue(c.update(0.6))
