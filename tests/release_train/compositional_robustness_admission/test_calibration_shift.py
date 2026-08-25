import unittest
from fractions import Fraction
from scripts.release_train.compositional_robustness_admission import BoundCalibration, CalibrationFrontier, Interval, calibrated_interval
from scripts.release_train.compositional_robustness_admission.shift import total_variation, shift_adjust
from scripts.release_train.compositional_robustness_admission.refusal import Refused
class T(unittest.TestCase):
    def test_calibration_and_shift_only_widen(self):
        c=BoundCalibration(10,Fraction(9,10),Fraction(1),2,"c"*64); CalibrationFrontier((c,)).require(2,"c"*64)
        i=Interval(Fraction(1),Fraction(2)); self.assertGreaterEqual(calibrated_interval(i,c).width,i.width)
        r=total_variation((Fraction(1,2),Fraction(1,2)),(Fraction(3,4),Fraction(1,4))); self.assertEqual(r,Fraction(1,4)); self.assertGreaterEqual(shift_adjust(i,r,1).width,i.width)
        with self.assertRaises(Refused): BoundCalibration(1,Fraction(1,2),1,1,"d"*64).admitted(3,Fraction(9,10),2)
