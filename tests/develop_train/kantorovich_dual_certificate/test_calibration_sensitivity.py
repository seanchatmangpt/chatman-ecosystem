from fractions import Fraction as F
import unittest
from scripts.develop_train.kantorovich_dual_certificate import *
CAL=Calibration(3,"c"*64,20,F(19,20),F(0),F(1,20))
class T(unittest.TestCase):
    def test_current_and_sensitivity(self):
        self.assertTrue(current([CAL]).admitted()); result=analyze([(0,1),(F(1,4),F(3,2)),(F(1,2),2)],F(7,4))
        self.assertEqual(result.max_slope,2); self.assertEqual(result.breakdown_radius,F(1,2))
    def test_nonmonotone_refuses(self):
        with self.assertRaises(Refused): analyze([(0,2),(1,1)],3)
    def test_split_current_refuses(self):
        other=Calibration(3,"d"*64,20,F(19,20),F(0),F(1,20))
        with self.assertRaises(Refused): current([CAL,other])
