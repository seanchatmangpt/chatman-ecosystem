import unittest
from fractions import Fraction
from scripts.develop_train.fused_acquisition.calibration import Calibration
from scripts.develop_train.fused_acquisition.sensor import Sensor
from scripts.develop_train.fused_acquisition.currentness import frontier,require_current,CalibrationFrontier
from scripts.develop_train.fused_acquisition.refusals import Refused
class TestCurrentness(unittest.TestCase):
 def test_generation_frontier(self):
  xs=[Sensor('s1','f1','d1',Calibration(1,'1'*64,5,Fraction(0),Fraction(0),Fraction(0))),Sensor('s2','f2','d2',Calibration(2,'2'*64,5,Fraction(0),Fraction(0),Fraction(0)))]
  f=frontier(xs); self.assertEqual(f.generation,2); require_current(xs,f)
  with self.assertRaises(Refused): require_current(xs,CalibrationFrontier(1,('1'*64,)))
