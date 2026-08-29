import unittest
from fractions import Fraction as F
from scripts.release_train.outcome_capital_transport import OutcomeObservation,Refused
from scripts.release_train.outcome_capital_transport.risk import loss,horvitz_thompson,self_normalized
from scripts.release_train.outcome_capital_transport.calibration import Calibration,current
from scripts.release_train.outcome_capital_transport.drift import Cusum

class T(unittest.TestCase):
 def test_risk_currentness(self):
  o=OutcomeObservation("1",1,"INDEPENDENT","DEPENDENT",F(1,2),F(0),"discovery","beam","us","r")
  self.assertEqual(loss(o),F(5)); self.assertEqual(horvitz_thompson([o],[F(5)]),F(10)); self.assertEqual(self_normalized([o],[F(5)]),F(5))
  self.assertEqual(current([Calibration(1,"x",8,F(1,10),F(1,5))]).digest,"x")
  self.assertTrue(Cusum(F(1,2)).update(F(1,2)))
  with self.assertRaises(Refused): current([Calibration(2,"a",8,F(0),F(0)),Calibration(2,"b",8,F(0),F(0))])
