import unittest
from fractions import Fraction as F
from scripts.release_train.kantorovich_dual_crown import *
class T(unittest.TestCase):
    def test_current_and_robust(self):
        a=Calibration(2,20,F(1,20),F(1,50),"abcdefgh",True); b=Calibration(1,10,F(1,10),F(1,20),"old-old1",True)
        self.assertEqual(current([a,b]),a)
        self.assertGreater(RobustWitness(F(1),F(3,2),F(1,10),"witness1").worst,F(1))
    def test_split_current_refuses(self):
        with self.assertRaises(Refused): current([Calibration(2,1,0,0,"abcdefgh"),Calibration(2,1,0,0,"ijklmnop")])
