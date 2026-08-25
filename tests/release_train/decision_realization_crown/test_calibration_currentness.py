import unittest
from fractions import Fraction
from scripts.release_train.decision_realization_crown import *
from scripts.release_train.decision_realization_crown.drift import Cusum
from scripts.release_train.decision_realization_crown.frontier import current
class T(unittest.TestCase):
  def test_calibration_and_drift(self):
    Calibration(1,"a"*64,8,Fraction(1,10),Fraction(1,5)).admitted()
    self.assertTrue(Cusum(0,Fraction(1,5),0).update(Fraction(3,10),0).changed)
  def test_split_frontier_refuses(self):
    with self.assertRaises(Refused): current([RealizationModel(2,"a"*64),RealizationModel(2,"b"*64)])
